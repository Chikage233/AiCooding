# api/services.py
from django.core.mail import send_mail
from django.conf import settings

def send_verification_code(email, code):
    """
    发送验证码邮件
    """
    subject = 'AiCooding - 邮箱验证码'
    message = f'您的验证码是：{code}，请在5分钟内完成验证。'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    
    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return True
    except Exception as e:
        print(f"发送邮件失败: {e}")
        return False