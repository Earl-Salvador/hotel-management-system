import random
import string
from flask_mail import Message
from flask import url_for
from models import db, EmailVerification
from mail_config import mail

def send_verification_email(email, token):
    """Send email verification link."""
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    msg = Message('Verify Your Email', recipients=[email])
    msg.body = f"""
    Hello,

    Thank you for registering! Please click the link below to verify your email address:

    {verify_url}

    This link will expire in 24 hours.

    If you did not register, please ignore this email.
    """
    mail.send(msg)

def send_password_reset_email(email, token):
    """Send password reset link."""
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    msg = Message('Password Reset Request', recipients=[email])
    msg.body = f"""
    Hello,

    You requested to reset your password. Click the link below to set a new password:

    {reset_url}

    This link will expire in 1 hour.

    If you did not request this, please ignore this email.
    """
    mail.send(msg)

def send_receipt_email(to_email, booking, receipt):
    """Send receipt email to user."""
    receipt_url = url_for('bookings.view_receipt', booking_id=booking.id, _external=True)
    msg = Message('Booking Receipt', recipients=[to_email])
    msg.body = f"""
    Hello {booking.user.name},

    Your booking has been confirmed!

    Booking ID: {booking.id}
    Room: {booking.room.room_number}
    Check-in: {booking.check_in}
    Check-out: {booking.check_out}
    Total: ₱{booking.total_amount}

    View your receipt here: {receipt_url}

    Thank you for choosing us!
    """
    mail.send(msg)