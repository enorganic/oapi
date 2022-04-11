from oapi.client import _get_relative_module_import

print(_get_relative_module_import("a/b/c.py", "a/b/f.py"))
