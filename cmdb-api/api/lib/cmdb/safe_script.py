# -*- coding:utf-8 -*-

import ast
import builtins


class UnsafeScriptError(Exception):
    pass


class _RestrictedScriptChecker(ast.NodeVisitor):
    FORBIDDEN_NODES = (
        ast.Global,
        ast.Nonlocal,
        ast.AsyncFunctionDef,
        ast.Await,
        ast.Yield,
        ast.YieldFrom,
        ast.Lambda,
        ast.Delete,
    )
    FORBIDDEN_NAMES = {
        "eval",
        "exec",
        "compile",
        "input",
        "globals",
        "locals",
        "vars",
        "dir",
        "getattr",
        "setattr",
        "delattr",
        "help",
        "breakpoint",
    }
    FORBIDDEN_MODULE_CALLS = {
        # Command execution
        "os.system",
        "os.popen",
        "subprocess.call",
        "subprocess.run",
        "subprocess.Popen",
        "subprocess.check_call",
        "subprocess.check_output",
        "subprocess.getoutput",
        "subprocess.getstatusoutput",
        # Dynamic imports (bypass restriction)
        "importlib.import_module",
        # File system destruction
        "os.remove",
        "os.unlink",
        "os.rmdir",
        "os.removedirs",
        "shutil.rmtree",
        # Process control
        "os.kill",
        "os.killpg",
    }

    def visit(self, node):
        if isinstance(node, self.FORBIDDEN_NODES):
            raise UnsafeScriptError("forbidden syntax: {0}".format(node.__class__.__name__))
        return super(_RestrictedScriptChecker, self).visit(node)

    ALLOWED_DUNDER_NAMES = {"__name__"}

    def visit_Name(self, node):
        if node.id in self.ALLOWED_DUNDER_NAMES:
            return self.generic_visit(node)
        if node.id.startswith("__") or node.id in self.FORBIDDEN_NAMES:
            raise UnsafeScriptError("forbidden name: {0}".format(node.id))
        return self.generic_visit(node)

    def visit_Attribute(self, node):
        if node.attr.startswith("__"):
            raise UnsafeScriptError("forbidden attribute access: {0}".format(node.attr))
        return self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id.startswith("__") or node.func.id in self.FORBIDDEN_NAMES:
                raise UnsafeScriptError("forbidden function call: {0}".format(node.func.id))
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr.startswith("__"):
                raise UnsafeScriptError("forbidden function call: {0}".format(node.func.attr))
            if isinstance(node.func.value, ast.Name):
                full_name = f"{node.func.value.id}.{node.func.attr}"
                if full_name in self.FORBIDDEN_MODULE_CALLS:
                    raise UnsafeScriptError(f"forbidden function call: {full_name}")
        return self.generic_visit(node)


_ALLOWED_BUILTINS = {
    "__build_class__": builtins.__build_class__,
    "__import__": builtins.__import__,
    "object": object,
    "Exception": Exception,
    "open": builtins.open,
    "print": builtins.print,
    "property": property,
    "staticmethod": staticmethod,
    "classmethod": classmethod,
    "type": type,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "dict": dict,
    "list": list,
    "set": set,
    "tuple": tuple,
    "len": len,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "sorted": sorted,
    "all": all,
    "any": any,
}


def load_class_from_script(script, class_name):
    if not isinstance(script, str):
        raise UnsafeScriptError("script must be a string")

    try:
        tree = ast.parse(script, mode='exec')
    except Exception as e:
        raise UnsafeScriptError("invalid script: {0}".format(e))

    _RestrictedScriptChecker().visit(tree)
    code = compile(tree, '<cmdb-safe-script>', "exec")

    local_ns = {}
    global_ns = {
        "__builtins__": _ALLOWED_BUILTINS,
        "__name__": "__cmdb_safe_script__",
    }
    exec(code, global_ns, local_ns)

    klass = local_ns.get(class_name) or global_ns.get(class_name)
    if klass is None:
        raise UnsafeScriptError("class {0} is required".format(class_name))

    return klass
