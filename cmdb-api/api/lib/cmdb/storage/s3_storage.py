# -*- coding:utf-8 -*-
import uuid
from datetime import datetime
from io import BytesIO

import boto3
from botocore.config import Config as BotoConfig

from api.core.context import current_app
from api.lib.cmdb.storage.base import StorageBackend


class S3Storage(StorageBackend):

    def __init__(self):
        cfg = current_app.config
        self._client = boto3.client(
            's3',
            endpoint_url=cfg.get('S3_ENDPOINT_URL') or None,
            aws_access_key_id=cfg.get('S3_ACCESS_KEY') or None,
            aws_secret_access_key=cfg.get('S3_SECRET_KEY') or None,
            region_name=cfg.get('S3_REGION', 'us-east-1'),
            use_ssl=cfg.get('S3_USE_SSL', True),
            config=BotoConfig(signature_version='s3v4'),
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

        self._client.put_object(
            Bucket=self._bucket,
            Key=stored_path,
            Body=file_data,
            ContentType=mime_type,
        )
        return {"stored_path": stored_path, "size": len(file_data)}

    def download(self, stored_path: str) -> tuple:
        response = self._client.get_object(Bucket=self._bucket, Key=stored_path)
        data = response['Body'].read()
        filename = stored_path.rsplit('/', 1)[-1]
        mime_type = response.get('ContentType', 'application/octet-stream')
        return BytesIO(data), filename, mime_type

    def delete(self, stored_path: str) -> bool:
        self._client.delete_object(Bucket=self._bucket, Key=stored_path)
        return True

    def get_url(self, stored_path: str, expires: int = 3600) -> str:
        return self._client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self._bucket, 'Key': stored_path},
            ExpiresIn=expires,
        )
