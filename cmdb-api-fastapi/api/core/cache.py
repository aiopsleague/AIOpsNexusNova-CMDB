# -*- coding:utf-8 -*-
"""Redis-backed cache with the Flask-Caching API surface used by this
project: ``get`` / ``set`` / ``delete`` / ``clear``."""
import pickle

import redis

import settings


class RedisCache(object):
    def __init__(self, host=None, port=None, password=None, key_prefix=None,
                 default_timeout=None, db=1):
        self._client = redis.Redis(
            host=host or settings.CACHE_REDIS_HOST,
            port=int(port or settings.CACHE_REDIS_PORT),
            password=password or settings.CACHE_REDIS_PASSWORD or None,
            db=db,
        )
        self.key_prefix = key_prefix or settings.CACHE_KEY_PREFIX
        self.default_timeout = default_timeout or settings.CACHE_DEFAULT_TIMEOUT

    def _normalize_key(self, key):
        return f"{self.key_prefix}{key}"

    def get(self, key):
        value = self._client.get(self._normalize_key(key))
        if value is None:
            return None
        try:
            return pickle.loads(value)
        except Exception:
            return None

    def set(self, key, value, timeout=None):
        timeout = self.default_timeout if timeout is None else timeout
        dumped = pickle.dumps(value)
        if timeout == 0:
            return self._client.set(self._normalize_key(key), dumped)
        return self._client.setex(self._normalize_key(key), timeout, dumped)

    def add(self, key, value, timeout=None):
        return self.set(key, value, timeout=timeout)

    def delete(self, key):
        return self._client.delete(self._normalize_key(key))

    def delete_many(self, *keys):
        return self._client.delete(*[self._normalize_key(k) for k in keys])

    def clear(self):
        cursor = 0
        while True:
            cursor, keys = self._client.scan(cursor, match=f"{self.key_prefix}*", count=1000)
            if keys:
                self._client.delete(*keys)
            if cursor == 0:
                break
        return True

    def has(self, key):
        return self._client.exists(self._normalize_key(key)) > 0
