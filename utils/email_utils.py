import random
import string
from flask_mail import Message
from flask import url_for
from mail_config import mail

def send_verification_email(email):
    """Send email verification link."""
    try:
        msg = Message('Verify Your Email', recipients=[email])
        msg.body = f"""
        Hello,

        Thank you for registering with ROOMIO!

        Your registration is almost complete. Please use the link below to verify your email:

        Please login to your account using your email and password.

        Thank you for choosing us!
        """
        mail.send(msg)
        print(f"Verification email sent to {email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_password_reset_email(email, token):
    """Send password reset link."""
    try:
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        msg = Message('Password Reset Request', recipients=[email])
        msg.body = f"""
        Hello,

        You requested to reset your password. Click the link below:

        {reset_url}

        This link expires in 1 hour.

        If you did not request this, please ignore this email.
        """
        mail.send(msg)
        print(f"Password reset email sent to {email}")
        return True
    except Exception as e:
        print(f"Error sending reset email: {e}")
        return False