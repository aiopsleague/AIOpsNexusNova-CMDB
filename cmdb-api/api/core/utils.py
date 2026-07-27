# -*- coding:utf-8 -*-
"""Small framework-independent utilities (vendored from werkzeug)."""
import re
import unicodedata

_filename_ascii_strip_re = re.compile(r"[^A-Za-z0-9_.-]")
_windows_device_files = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(10)),
    *(f"LPT{i}" for i in range(10)),
}


def secure_filename(filename):
    """Vendored ``werkzeug.utils.secure_filename`` (BSD)."""
    if isinstance(filename, bytes):
        filename = filename.decode("utf-8", "ignore")
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("ascii", "ignore").decode("ascii")
    for sep in ("/", "\\"):
        filename = filename.replace(sep, " ")
    filename = str(_filename_ascii_strip_re.sub("", "_".join(filename.split()))).strip("._")
    if filename and filename.split(".")[0].upper() in _windows_device_files:
        filename = f"_{filename}"
    return filename
