from django.conf import settings
from django.core.cache import cache


CACHE_PREFIX = "email_verification_security"


def _setting_int(name, default):
    try:
        return int(getattr(settings, name, default))
    except (TypeError, ValueError):
        return default


def _safe_part(value):
    if value is None:
        return "unknown"
    text = str(value).strip().lower()
    return text or "unknown"


def _key(*parts):
    return ":".join([CACHE_PREFIX, *parts])


def _counter_get(key):
    try:
        return int(cache.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def _counter_inc(key, ttl_seconds):
    count = _counter_get(key) + 1
    cache.set(key, count, ttl_seconds)
    return count


def check_send_code_rate_limit(email, client_ip):
    email_key = _safe_part(email)
    ip_key = _safe_part(client_ip)

    max_per_email = _setting_int("EMAIL_VERIFICATION_MAX_SENDS_PER_HOUR_PER_EMAIL", 5)
    max_per_ip = _setting_int("EMAIL_VERIFICATION_MAX_SENDS_PER_HOUR_PER_IP", 20)

    email_cooldown_key = _key("send", "cooldown", email_key)
    if cache.get(email_cooldown_key):
        return False, "EMAIL_CODE_COOLDOWN", "Requests are too frequent. Please try again later.", 429

    email_count_key = _key("send", "count", "email", email_key)
    if _counter_get(email_count_key) >= max_per_email:
        return False, "EMAIL_CODE_EMAIL_RATE_LIMIT", "Too many requests for this email. Please try again later.", 429

    ip_count_key = _key("send", "count", "ip", ip_key)
    if _counter_get(ip_count_key) >= max_per_ip:
        return False, "EMAIL_CODE_IP_RATE_LIMIT", "Too many requests from this IP. Please try again later.", 429

    return True, "", "", 200


def record_send_code_request(email, client_ip):
    email_key = _safe_part(email)
    ip_key = _safe_part(client_ip)

    cooldown_seconds = _setting_int("EMAIL_VERIFICATION_SEND_COOLDOWN_SECONDS", 60)
    window_seconds = 3600

    cache.set(_key("send", "cooldown", email_key), 1, cooldown_seconds)
    _counter_inc(_key("send", "count", "email", email_key), window_seconds)
    _counter_inc(_key("send", "count", "ip", ip_key), window_seconds)


def check_verify_code_rate_limit(email, client_ip):
    email_key = _safe_part(email)
    ip_key = _safe_part(client_ip)

    max_attempts_per_email = _setting_int("EMAIL_VERIFICATION_MAX_VERIFY_ATTEMPTS_PER_EMAIL", 10)
    max_attempts_per_ip = _setting_int("EMAIL_VERIFICATION_MAX_VERIFY_ATTEMPTS_PER_IP", 30)

    email_fail_key = _key("verify", "fail", "email", email_key)
    if _counter_get(email_fail_key) >= max_attempts_per_email:
        return False, "EMAIL_CODE_VERIFY_EMAIL_LOCKED", "Too many failed verification attempts for this email.", 429

    ip_fail_key = _key("verify", "fail", "ip", ip_key)
    if _counter_get(ip_fail_key) >= max_attempts_per_ip:
        return False, "EMAIL_CODE_VERIFY_IP_LOCKED", "Too many failed verification attempts from this IP.", 429

    return True, "", "", 200


def record_verify_code_failure(email, client_ip):
    email_key = _safe_part(email)
    ip_key = _safe_part(client_ip)
    verify_window_seconds = _setting_int("EMAIL_VERIFICATION_VERIFY_WINDOW_SECONDS", 600)

    _counter_inc(_key("verify", "fail", "email", email_key), verify_window_seconds)
    _counter_inc(_key("verify", "fail", "ip", ip_key), verify_window_seconds)


def clear_verify_code_failures(email, client_ip):
    email_key = _safe_part(email)
    ip_key = _safe_part(client_ip)
    cache.delete(_key("verify", "fail", "email", email_key))
    cache.delete(_key("verify", "fail", "ip", ip_key))

