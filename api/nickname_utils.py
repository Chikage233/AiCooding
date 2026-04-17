import re
import unicodedata


NICKNAME_MIN_LENGTH = 2
NICKNAME_MAX_LENGTH = 20
NICKNAME_ALLOWED_PATTERN = re.compile(r"^[A-Za-z0-9_\-一-鿿 ]+$")
NICKNAME_HAS_VISIBLE_PATTERN = re.compile(r"[A-Za-z0-9一-鿿]")
NICKNAME_REPEAT_PATTERN = re.compile(r"(.)\1{3,}")
NICKNAME_DAILY_LIMIT = 3

RESERVED_WORDS = {
    "admin",
    "administrator",
    "root",
    "system",
    "official",
    "support",
    "moderator",
    "客服",
    "管理员",
    "系统",
    "官方",
}

SENSITIVE_WORDS = {
    "傻逼",
    "垃圾",
    "妈的",
    "fuck",
    "shit",
}


def normalize_nickname(raw_value):
    if raw_value is None:
        return ""
    normalized = unicodedata.normalize("NFKC", str(raw_value))
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def validate_nickname(raw_value):
    """
    Return:
      (True, normalized, "", "") on success
      (False, normalized, hit_rule, message) on failure
    """
    normalized = normalize_nickname(raw_value)

    if not normalized:
        return False, normalized, "empty", "昵称不能为空"

    length = len(normalized)
    if length < NICKNAME_MIN_LENGTH or length > NICKNAME_MAX_LENGTH:
        return False, normalized, "length", "昵称长度需在2到20个字符之间"

    if not NICKNAME_ALLOWED_PATTERN.fullmatch(normalized):
        return False, normalized, "charset", "昵称仅支持中英文、数字、空格、下划线和中划线"

    if not NICKNAME_HAS_VISIBLE_PATTERN.search(normalized):
        return False, normalized, "charset", "昵称至少包含一个中英文或数字字符"

    if NICKNAME_REPEAT_PATTERN.search(normalized):
        return False, normalized, "repeat_chars", "昵称包含异常重复字符"

    lower_name = normalized.lower()
    if any(word in lower_name for word in RESERVED_WORDS):
        return False, normalized, "reserved_word", "昵称包含保留词，请更换"

    if any(word in lower_name for word in SENSITIVE_WORDS):
        return False, normalized, "sensitive_word", "昵称包含敏感词，请更换"

    return True, normalized, "", ""
