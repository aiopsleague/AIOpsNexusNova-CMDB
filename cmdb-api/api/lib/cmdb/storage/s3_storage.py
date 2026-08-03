# -*- coding:utf-8 -*-
import logging
import uuid
from datetime import datetime
from io import BytesIO

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError

from api.core.context import current_app
from api.lib.cmdb.storage.base import StorageBackend

logger = logging.getLogger('cmdb')


class S3Storage(StorageBackend):

    def __init__(self):
        cfg = current_app.config
        endpoint_url = cfg.get('S3_ENDPOINT_URL') or None
        access_key = cfg.get('S3_ACCESS_KEY') or None
        secret_key = cfg.get('S3_SECRET_KEY') or None

        # Fail fast with a clear message when S3 backend is used but
        # credentials or endpoint are missing (common MinIO misconfiguration).
        if not endpoint_url:
            raise ValueError(
                "S3 storage backend is configured but S3_ENDPOINT_URL is not set. "
                "For MinIO, set S3_ENDPOINT_URL=http://<host>:<port> in .env"
            )
        if not access_key or not secret_key:
            raise ValueError(
                "S3 storage backend is configured but S3_ACCESS_KEY and/or "
                "S3_SECRET_KEY are not set. Please configure them in .env"
            )

        self._client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=cfg.get('S3_REGION', 'us-east-1'),
            use_ssl=cfg.get('S3_USE_SSL', True),
            config=BotoConfig(
                signature_version='s3v4',
                s3={'addressing_style': 'path'},
            ),
        )
        self._bucket = cfg.get('S3_BUCKET_NAME', 'cmdb-files')

    def upload(self, file_data: bytes, file_path: str = None, mime_type: str = 'application/octet-stream') -> dict:
        now = datetime.now()
        date_prefix = now.strftime('%Y/%m/%d')
        uid = str(uuid.uuid4())[:8]
        safe_name = file_path if file_path else f"{uid}.bin"
        if file_path and '.' in file_path:
            name, ext = file_path.rsplit('.', 1)
            safe_name = f"{uid}_{name}.{ext}"
        stored_path = f"{date_prefix}/{safe_name}"

        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=stored_path,
                Body=file_data,
                ContentType=mime_type,
            )
        except (BotoCoreError, ClientError) as e:
            logger.exception(f"S3 upload failed: {e}")
            raise RuntimeError(f"Failed to upload file to S3/MinIO: {e}") from e

        return {"stored_path": stored_path, "size": len(file_data)}

    def download(self, stored_path: str) -> tuple:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=stored_path)
        except (BotoCoreError, ClientError) as e:
            logger.exception(f"S3 download failed for {stored_path}: {e}")
            raise RuntimeError(f"Failed to download file from S3/MinIO: {e}") from e
        data = response['Body'].read()
        filename = stored_path.rsplit('/', 1)[-1]
        mime_type = response.get('ContentType', 'application/octet-stream')
        return BytesIO(data), filename, mime_type

    def delete(self, stored_path: str) -> bool:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=stored_path)
        except (BotoCoreError, ClientError) as e:
            logger.warning(f"S3 delete failed for {stored_path}: {e}")
            return False
        return True

    def get_url(self, stored_path: str, expires: int = 3600) -> str:
        try:
            return self._client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self._bucket, 'Key': stored_path},
                ExpiresIn=expires,
            )
        except (BotoCoreError, ClientError) as e:
            logger.exception(f"S3 presigned URL failed for {stored_path}: {e}")
            raise RuntimeError(f"Failed to generate S3 presigned URL: {e}") from e
