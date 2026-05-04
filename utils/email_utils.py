from flask_mail import Message
from flask import url_for
from mail_config import mail
from models import db, EmailVerification, PasswordReset
import secrets
from datetime import datetime, timedelta

def send_verification_email(email):
    """Send email verification link."""
    try:
        # Generate unique token
        token = secrets.token_urlsafe(32)
        
        # Delete old verification for this email
        EmailVerification.query.filter_by(email=email).delete()
        
        # Save new verification
        verification = EmailVerification(email=email, token=token)
        db.session.add(verification)
        db.session.commit()
        
        # Create verification link
        verify_url = url_for('auth.verify_email', token=token, _external=True)
        
        # Create email message
        msg = Message('Verify Your Email - ROOMIO', recipients=[email])
        msg.body = f"""
Hello,

Thank you for registering with ROOMIO!

Please click the link below to verify your email address:

{verify_url}

This link will expire in 10 minutes.

If you did not create an account, please ignore this email.

Thank you for choosing us!
"""
        mail.send(msg)
        print(f"Verification email sent to {email}")
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False

def send_password_reset_email(email, token):
    """Send password reset link."""
    try:
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
        print(f"Password reset email sent to {email}")
        return True
    except Exception as e:
        print(f"Error sending reset email: {e}")
        return False

def send_receipt_email(to_email, booking, receipt):
    """Send booking receipt email."""
    try:
        receipt_url = url_for('bookings.view_receipt', booking_id=booking.id, _external=True)
        
        msg = Message('Booking Confirmation - ROOMIO', recipients=[to_email])
        msg.body = f"""
Hello {booking.user.name},

Your booking has been confirmed!

Booking ID: {booking.id}
Room: {booking.room.room_number}
Check-in: {booking.check_in}
Check-out: {booking.check_out}
Total: ₱{booking.total_amount}

View your receipt here: {receipt_url}

Thank you for choosing ROOMIO!
"""
        mail.send(msg)
        print(f"Receipt email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending receipt email: {e}")
        return False