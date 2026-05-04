from flask_mail import Message
from flask import url_for
from mail_config import mail

def send_password_reset_email(email, token):
    """Send password reset link (expires in 10 minutes)."""
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    msg = Message('Password Reset Request - ROOMIO', recipients=[email])
    msg.body = f"""
    Hello,

    You requested to reset your password. Click the link below to set a new password:

    {reset_url}

    This link will expire in 10 minutes.

    If you did not request this, please ignore this email.
    """
    mail.send(msg)