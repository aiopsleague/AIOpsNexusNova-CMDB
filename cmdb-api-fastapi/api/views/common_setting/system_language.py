import os

from fastapi import APIRouter
from fastapi import Depends

from api.lib.perm.auth import auth_abandoned
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])

prefix = "/system"


@router.get(f"{prefix}/language")
@auth_abandoned
def system_language_view_get():
    """Get system default language
    Read from environment variable SYSTEM_DEFAULT_LANGUAGE, default to Chinese if not set
    """
    default_language = os.environ.get("SYSTEM_DEFAULT_LANGUAGE", "")

    return dict(
        language=default_language,
        language_name=_get_language_name(default_language),
    )


def _get_language_name(language_code):
    """Return language name based on language code"""
    language_mapping = {
        "zh-CN": "中文(简体)",
        "zh-TW": "中文(繁体)",
        "en-US": "English",
        "ja-JP": "日本語",
        "ko-KR": "한국어",
    }
    return language_mapping.get(language_code, "")
