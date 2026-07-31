# -*- coding:utf-8 -*-
from io import BytesIO
from unittest import mock

import pytest

from api.lib.cmdb.ci_file import CIFileManager
from api.lib.cmdb.ci_file import DEFAULT_ALLOWED_EXTENSIONS


class _FakeFile(object):
    def __init__(self, filename, content, content_type='application/octet-stream'):
        self.filename = filename
        self.content_type = content_type
        self._data = content

    def read(self):
        return self._data


@pytest.fixture
def manager():
    return CIFileManager()


def test_svg_not_in_default_allowed_extensions():
    """B3: svg must not be an allowed upload extension (stored-XSS vector)."""
    assert 'svg' not in DEFAULT_ALLOWED_EXTENSIONS


def _mock_config_get():
    """config.get returning 'local' for FILE_STORAGE_BACKEND (the settings.py
    default) and the passed default for FILE_ALLOWED_EXTENSIONS."""
    def _get(key, default=None):
        if key == 'FILE_ALLOWED_EXTENSIONS':
            return default
        if key == 'FILE_STORAGE_BACKEND':
            return 'local'
        return None
    return _get


def test_upload_files_rejects_svg(manager):
    """B3: upload of an .svg file must fail extension validation."""
    with mock.patch('api.lib.cmdb.ci_file.current_app') as m_app:
        m_app.config.get.side_effect = _mock_config_get()
        with pytest.raises(ValueError):
            manager.upload_files([_FakeFile('evil.svg', '<script>')])


def test_upload_files_records_storage_backend(manager):
    """B2: upload_files must tag each file with its storage backend name."""
    with mock.patch('api.lib.cmdb.ci_file.current_app') as m_app, \
            mock.patch('api.lib.cmdb.ci_file.get_storage_backend') as m_get:
        m_app.config.get.side_effect = _mock_config_get()  # global backend -> 'local'
        m_backend = mock.Mock()
        m_backend.upload.return_value = {'stored_path': '2026/07/31/abc_a.png', 'size': 10}
        m_get.return_value = m_backend

        results = manager.upload_files([_FakeFile('a.png', b'data')])

        m_get.assert_called_once_with('local')
        assert results[0]['storage_backend'] == 'local'
        assert results[0]['stored_path'] == '2026/07/31/abc_a.png'


def test_get_file_passes_backend_to_factory(manager):
    """B2: get_file must resolve the explicitly-requested backend."""
    with mock.patch('api.lib.cmdb.ci_file.get_storage_backend') as m_get:
        m_backend = mock.Mock()
        m_backend.download.return_value = (BytesIO(b'x'), 'a.png', 'image/png')
        m_get.return_value = m_backend

        stream, filename, mime_type = manager.get_file('2026/07/31/abc_a.png', storage_backend='s3')

        m_get.assert_called_once_with('s3')
        assert filename == 'a.png'


def test_delete_files_accepts_backend_dicts(manager):
    """B2: delete_files must accept {path, storage_backend} dicts and strings."""
    deleted_paths = []
    deleted_backends = []

    def _fake_backend(name):
        def _delete(path):
            deleted_paths.append(path)
            deleted_backends.append(name)
            return True
        return mock.Mock(delete=_delete)

    with mock.patch('api.lib.cmdb.ci_file.get_storage_backend') as m_get:
        m_get.side_effect = _fake_backend

        deleted = manager.delete_files([
            {'path': 'a.png', 'storage_backend': 's3'},
            {'path': 'b.png', 'storage_backend': None},
            'c.png',  # legacy string form -> global backend
        ])

        assert deleted == 3
        assert deleted_paths == ['a.png', 'b.png', 'c.png']
        assert deleted_backends == ['s3', None, None]
