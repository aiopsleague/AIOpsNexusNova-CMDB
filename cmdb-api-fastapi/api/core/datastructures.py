# -*- coding:utf-8 -*-
"""Minimal MultiDict, compatible with the subset of
``werkzeug.datastructures.MultiDict`` used by this project (mainly feeding
WTForms): ``getlist``, ``to_dict``, ``items(multi=True)``, ``get``."""

import six


class MultiDict(object):
    def __init__(self, mapping=None):
        self._data = {}
        if mapping is None:
            return
        if isinstance(mapping, MultiDict):
            for k, v in mapping.items(multi=True):
                self.add(k, v)
        elif hasattr(mapping, "items"):
            for k, v in mapping.items():
                if isinstance(v, (list, tuple)):
                    for item in v:
                        self.add(k, item)
                else:
                    self.add(k, v)
        else:
            for k, v in mapping:
                self.add(k, v)

    def add(self, key, value):
        self._data.setdefault(key, []).append(value)

    def __getitem__(self, key):
        values = self._data[key]
        if not values:
            raise KeyError(key)
        return values[0]

    def __setitem__(self, key, value):
        self._data[key] = [value]

    def __contains__(self, key):
        return key in self._data

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def get(self, key, default=None, type=None):
        values = self._data.get(key)
        if not values:
            return default
        value = values[0]
        if type is not None:
            try:
                return type(value)
            except (ValueError, TypeError):
                return default
        return value

    def getlist(self, key, type=None):
        values = self._data.get(key, [])
        if type is not None:
            result = []
            for v in values:
                try:
                    result.append(type(v))
                except (ValueError, TypeError):
                    pass
            return result
        return list(values)

    def setlist(self, key, new_list):
        self._data[key] = list(new_list)

    def items(self, multi=False):
        for key, values in self._data.items():
            if multi:
                for v in values:
                    yield key, v
            else:
                yield key, (values[0] if values else None)

    def keys(self):
        return self._data.keys()

    def values(self):
        for values in self._data.values():
            yield values[0] if values else None

    def lists(self):
        for key, values in self._data.items():
            yield key, list(values)

    def to_dict(self, flat=True):
        if flat:
            return {k: (v[0] if v else None) for k, v in self._data.items()}
        return {k: list(v) for k, v in self._data.items()}

    def pop(self, key, default=None):
        values = self._data.pop(key, None)
        if values is None:
            return default
        return values[0] if values else default

    def update(self, other):
        if hasattr(other, "items"):
            for k, v in other.items():
                self[k] = v

    def copy(self):
        return MultiDict(self)

    def __repr__(self):
        return f"MultiDict({self.to_dict()!r})"
