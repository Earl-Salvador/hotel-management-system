import random
import string
from flask_mail import Message
from models import db, EmailVerification
from mail_config import mail

def send_verification_email(email):
    """Generate a 6-digit code and send email verification."""
    code = ''.join(random.choices(string.digits, k=6))
    # Delete any existing verification for this email
    EmailVerification.query.filter_by(email=email).delete()
    db.session.add(EmailVerification(email=email, code=code))
    db.session.commit()

    try:
        msg = Message('Email Verification', recipients=[email])
        msg.body = f'Your verification code is: {code}\nThis code expires in 10 minutes.'
        mail.send(msg)
        print(f"Verification email sent to {email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        # Still return the code for testing (you'll see it in terminal)
        print(f"VERIFICATION CODE for {email}: {code}")
    return code

def send_password_reset_email(email, token):
    """Send password reset email with link."""
    from flask import url_for
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