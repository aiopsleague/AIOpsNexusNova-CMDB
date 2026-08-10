# -*- coding:utf-8 -*-

import pytest
from api.lib.cmdb.safe_script import UnsafeScriptError
from api.lib.cmdb.safe_script import load_class_from_script


class TestImportAllowlist:
    """Verify that import statements are now allowed in safe scripts."""

    def test_import_json_allowed(self):
        """import json should succeed after removing Import from FORBIDDEN_NODES."""
        script = '''
import json

class AutoDiscovery(object):
    @property
    def unique_key(self):
        return "uuid"

    @staticmethod
    def attributes():
        return [("uuid", "String", "ID")]
'''
        klass = load_class_from_script(script, 'AutoDiscovery')
        assert klass is not None
        inst = klass()
        assert inst.unique_key == "uuid"

    def test_import_from_allowed(self):
        """from ... import should also be allowed."""
        script = '''
from json import dumps, loads

class AutoDiscovery(object):
    @property
    def unique_key(self):
        return "hostname"

    @staticmethod
    def attributes():
        return [("hostname", "String", "Hostname")]
'''
        klass = load_class_from_script(script, 'AutoDiscovery')
        assert klass is not None

    def test_import_multiple_modules(self):
        """Multiple standard library imports should work."""
        script = '''
import json
import socket
import re
import math

class AutoDiscovery(object):
    @property
    def unique_key(self):
        return "uuid"

    @staticmethod
    def attributes():
        return [("uuid", "String", "ID")]
'''
        klass = load_class_from_script(script, 'AutoDiscovery')
        assert klass is not None


class TestForbiddenModuleCalls:
    """Verify that dangerous module.method calls are still blocked."""

    def test_os_system_blocked(self):
        script = '''
import os

class AutoDiscovery(object):
    @property
    def unique_key(self):
        return "uuid"

    @staticmethod
    def attributes(self):
        os.system("echo pwned")
        return [("uuid", "String", "ID")]
'''
        with pytest.raises(UnsafeScriptError, match="os.system"):
            load_class_from_script(script, 'AutoDiscovery')

    def test_subprocess_run_blocked(self):
        script = '''
import subprocess

class AutoDiscovery(object):
    @property
    def unique_key(self):
        return "uuid"

    @staticmethod
    def attributes(self):
        subprocess.run(["echo", "pwned"])
        return [("uuid", "String", "ID")]
'''
        with pytest.raises(UnsafeScriptError, match="subprocess.run"):
            load_class_from_script(script, 'AutoDiscovery')

    def test_subprocess_popen_blocked(self):
        script = '''
import subprocess

class AutoDiscovery(object):
    @property
    def unique_key(self):
        return "uuid"

    @staticmethod
    def attributes(self):
        subprocess.Popen(["echo", "pwned"])
        return [("uuid", "String", "ID")]
'''
        with pytest.raises(UnsafeScriptError, match="subprocess.Popen"):
            load_class_from_script(script, 'AutoDiscovery')

    def test_os_remove_blocked(self):
        script = '''
import os

class AutoDiscovery(object):
    @property
    def unique_key(self):
        return "uuid"

    @staticmethod
    def attributes(self):
        os.remove("/tmp/somefile")
        return [("uuid", "String", "ID")]
'''
        with pytest.raises(UnsafeScriptError, match="os.remove"):
            load_class_from_script(script, 'AutoDiscovery')

    def test_shutil_rmtree_blocked(self):
        script = '''
import shutil

class AutoDiscovery(object):
    @property
    def unique_key(self):
        return "uuid"

    @staticmethod
    def attributes(self):
        shutil.rmtree("/tmp/somedir")
        return [("uuid", "String", "ID")]
'''
        with pytest.raises(UnsafeScriptError, match="shutil.rmtree"):
            load_class_from_script(script, 'AutoDiscovery')

    def test_importlib_import_module_blocked(self):
        script = '''
import importlib

class AutoDiscovery(object):
    @property
    def unique_key(self):
        return "uuid"

    @staticmethod
    def attributes(self):
        importlib.import_module("os")
        return [("uuid", "String", "ID")]
'''
        with pytest.raises(UnsafeScriptError, match="importlib.import_module"):
            load_class_from_script(script, 'AutoDiscovery')


class TestExistingRestrictionsStillWork:
    """Verify that pre-existing security restrictions remain in place."""

    def test_eval_still_blocked(self):
        script = '''
class AutoDiscovery(object):
    @property
    def unique_key(self):
        return eval("'uuid'")
'''
        with pytest.raises(UnsafeScriptError, match="eval"):
            load_class_from_script(script, 'AutoDiscovery')

    def test_exec_still_blocked(self):
        script = '''
class AutoDiscovery(object):
    @property
    def unique_key(self):
        return exec("x = 1")
'''
        with pytest.raises(UnsafeScriptError, match="exec"):
            load_class_from_script(script, 'AutoDiscovery')

    def test_open_allowed_for_agent_discovery(self):
        """open is allowed — agent plugins need file I/O for discovery."""
        script = '''
class AutoDiscovery(object):
    @property
    def unique_key(self):
        return "uuid"

    @staticmethod
    def attributes():
        return [("uuid", "String", "ID")]

    @staticmethod
    def run(self):
        with open("/proc/meminfo") as f:
            return f.readline()
'''
        klass = load_class_from_script(script, 'AutoDiscovery')
        assert klass is not None

    def test_compile_still_blocked(self):
        script = '''
class AutoDiscovery(object):
    @property
    def unique_key(self):
        return compile("x=1", "", "exec")
'''
        with pytest.raises(UnsafeScriptError, match="compile"):
            load_class_from_script(script, 'AutoDiscovery')

    def test_underscore_import_still_blocked(self):
        script = '''
class AutoDiscovery(object):
    @property
    def unique_key(self):
        return __import__("os")
'''
        with pytest.raises(UnsafeScriptError, match="__import__"):
            load_class_from_script(script, 'AutoDiscovery')

    def test_global_still_blocked(self):
        script = '''
class AutoDiscovery(object):
    @property
    def unique_key(self):
        global x
        return "uuid"
'''
        with pytest.raises(UnsafeScriptError, match="Global"):
            load_class_from_script(script, 'AutoDiscovery')

    def test_lambda_still_blocked(self):
        script = '''
class AutoDiscovery(object):
    @property
    def unique_key(self):
        f = lambda: "uuid"
        return f()
'''
        with pytest.raises(UnsafeScriptError, match="Lambda"):
            load_class_from_script(script, 'AutoDiscovery')

    def test_safe_os_path_join_allowed(self):
        """os.path.join is not in FORBIDDEN_MODULE_CALLS and should work."""
        script = '''
import os

class AutoDiscovery(object):
    @property
    def unique_key(self):
        return "uuid"

    @staticmethod
    def attributes(self):
        path = os.path.join("/tmp", "foo")
        return [("uuid", "String", path)]
'''
        klass = load_class_from_script(script, 'AutoDiscovery')
        assert klass is not None

    def test_json_dumps_allowed(self):
        """json.dumps is safe and should be allowed."""
        script = '''
import json

class AutoDiscovery(object):
    @property
    def unique_key(self):
        return "uuid"

    @staticmethod
    def attributes(self):
        data = json.dumps({"key": "value"})
        return [("uuid", "String", data)]
'''
        klass = load_class_from_script(script, 'AutoDiscovery')
        assert klass is not None


    def test_with_statement_allowed(self):
        """with statement is a control flow construct, not a security risk."""
        script = '''
class DummyContext(object):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass

class AutoDiscovery(object):
    @property
    def unique_key(self):
        return "uuid"

    @staticmethod
    def attributes(self):
        with DummyContext():
            pass
        return [("uuid", "String", "ID")]
'''
        klass = load_class_from_script(script, 'AutoDiscovery')
        assert klass is not None

    def test_dunder_name_allowed(self):
        """__name__ is a standard Python module attribute, not a security risk."""
        script = '''
class AutoDiscovery(object):
    @property
    def unique_key(self):
        return "uuid"

    @staticmethod
    def attributes(self):
        return [("uuid", "String", "ID")]

if __name__ == "__main__":
    pass
'''
        klass = load_class_from_script(script, 'AutoDiscovery')
        assert klass is not None


class TestChoiceValueScript:
    """Verify ChoiceValue scripts also work with imports."""

    def test_choice_value_with_import(self):
        script = '''
import json

class ChoiceValue(object):
    def values(self):
        return ["option_a", "option_b"]
'''
        klass = load_class_from_script(script, 'ChoiceValue')
        assert klass is not None
        inst = klass()
        assert inst.values() == ["option_a", "option_b"]
