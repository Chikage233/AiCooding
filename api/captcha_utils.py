import base64
import random
import string
import uuid
from html import escape

from django.conf import settings
from django.core.cache import cache


CAPTCHA_CACHE_PREFIX = "login_captcha"
DEFAULT_CAPTCHA_LENGTH = 4
DEFAULT_CAPTCHA_EXPIRE_SECONDS = 300
DEFAULT_CAPTCHA_MAX_ATTEMPTS = 5
CAPTCHA_CHARSET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def _cache_key(captcha_id):
    return f"{CAPTCHA_CACHE_PREFIX}:{captcha_id}"


def _attempt_key(captcha_id):
    return f"{CAPTCHA_CACHE_PREFIX}:attempts:{captcha_id}"


def _captcha_ttl():
    return int(getattr(settings, "LOGIN_CAPTCHA_EXPIRE_SECONDS", DEFAULT_CAPTCHA_EXPIRE_SECONDS))


def _captcha_length():
    return int(getattr(settings, "LOGIN_CAPTCHA_LENGTH", DEFAULT_CAPTCHA_LENGTH))


def _captcha_max_attempts():
    return int(getattr(settings, "LOGIN_CAPTCHA_MAX_ATTEMPTS", DEFAULT_CAPTCHA_MAX_ATTEMPTS))


def _random_text(length):
    return "".join(random.choice(CAPTCHA_CHARSET) for _ in range(length))


def _build_svg(text):
    width = 140
    height = 48
    noise_lines = []
    for _ in range(6):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        color = f"rgb({random.randint(120,210)},{random.randint(120,210)},{random.randint(120,210)})"
        noise_lines.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1"/>'
        )

    chars = []
    step = width // (len(text) + 1)
    for idx, ch in enumerate(text, start=1):
        x = step * idx + random.randint(-4, 4)
        y = random.randint(30, 38)
        rotate = random.randint(-18, 18)
        fill = f"rgb({random.randint(20,90)},{random.randint(20,90)},{random.randint(20,90)})"
        chars.append(
            f'<text x="{x}" y="{y}" transform="rotate({rotate},{x},{y})" '
            f'font-size="28" font-family="Arial, sans-serif" font-weight="700" fill="{fill}">{escape(ch)}</text>'
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        '<rect width="100%" height="100%" fill="#f7fafc"/>'
        f'{"".join(noise_lines)}'
        f'{"".join(chars)}'
        "</svg>"
    )
    return svg


def create_login_captcha():
    captcha_id = uuid.uuid4().hex
    text = _random_text(_captcha_length())
    ttl = _captcha_ttl()

    cache.set(_cache_key(captcha_id), text.lower(), ttl)
    cache.set(_attempt_key(captcha_id), 0, ttl)

    svg = _build_svg(text)
    image_base64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")

    return {
        "captcha_id": captcha_id,
        "image_data": f"data:image/svg+xml;base64,{image_base64}",
        "expires_in": ttl,
    }


def verify_login_captcha(captcha_id, captcha_code):
    if not captcha_id or not captcha_code:
        return False, "CAPTCHA_REQUIRED", "请先输入图片验证码", 400

    answer = cache.get(_cache_key(captcha_id))
    if not answer:
        return False, "CAPTCHA_EXPIRED", "验证码已过期，请刷新后重试", 422

    max_attempts = _captcha_max_attempts()
    attempts = int(cache.get(_attempt_key(captcha_id)) or 0)
    if attempts >= max_attempts:
        cache.delete(_cache_key(captcha_id))
        cache.delete(_attempt_key(captcha_id))
        return False, "CAPTCHA_TOO_MANY_ATTEMPTS", "验证码错误次数过多，请刷新后重试", 429

    if str(captcha_code).strip().lower() != str(answer).strip().lower():
        attempts += 1
        cache.set(_attempt_key(captcha_id), attempts, _captcha_ttl())
        return False, "CAPTCHA_INVALID", "验证码错误", 422

    cache.delete(_cache_key(captcha_id))
    cache.delete(_attempt_key(captcha_id))
    return True, "", "", 200
