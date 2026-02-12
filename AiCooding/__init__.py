# AiCooding/__init__.py
# 从 from .celery import app as celery_app
# 改为：
from .celery_app import app as celery_app

__all__ = ("celery_app",)