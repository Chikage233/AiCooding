# 必须导入 path 和自定义的 TestView
from django.urls import path
from .views import TestView  # 从当前目录的 views.py 导入 TestView

# URL 规则列表，path 第一个参数是 "test/"（带末尾斜杠）
urlpatterns = [
    path('test/', TestView.as_view(), name='test'),
]