from flask_mail import Message
from flask import url_for, current_app
from mail_config import mail

def send_verification_email(email):
    """Send email verification link."""
    try:
        subject = "Verify Your Email - ROOMIO"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #057013;">Welcome to ROOMIO!</h2>
                <p>Thank you for registering! Please login to your account to continue.</p>
                <p>If you did not create an account, please ignore this email.</p>
                <hr>
                <p style="font-size: 12px; color: #666;">&copy; 2026 ROOMIO. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        msg = Message(subject, recipients=[email])
        msg.html = html_content
        mail.send(msg)
        print(f"Verification email sent to {email}")
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False

def send_password_reset_email(email, token):
    """Send password reset link (expires in 10 minutes)."""
    try:
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        
        subject = "Password Reset Request - ROOMIO"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #057013;">Password Reset Request</h2>
                <p>You requested to reset your password. Click the link below to set a new password:</p>
                <p><a href="{reset_url}" style="background-color: #057013; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
                <p>This link will expire in 10 minutes.</p>
                <p>If you did not request this, please ignore this email.</p>
                <hr>
                <p style="font-size: 12px; color: #666;">&copy; 2026 ROOMIO. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        msg = Message(subject, recipients=[email])
        msg.html = html_content
        mail.send(msg)
        print(f"Password reset email sent to {email}")
        return True
    except Exception as e:
        print(f"Error sending reset email: {e}")
        return False

def send_receipt_email(to_email, booking, receipt):
    """Send booking receipt email (currently disabled)."""
    print(f"[INFO] Receipt email would be sent to {to_email} for booking {booking.id}")
    print(f"[INFO] Receipt URL: {url_for('bookings.view_receipt', booking_id=booking.id, _external=True)}")
    return True