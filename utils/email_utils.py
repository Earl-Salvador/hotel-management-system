from flask_mail import Message
from flask import url_for
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
                <p>You requested to reset your password. Click the button below to set a new password:</p>
                <p style="text-align: center;">
                    <a href="{reset_url}" style="display: inline-block; background-color: #057013; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0;">Reset Password</a>
                </p>
                <p>Or copy and paste this link:</p>
                <p>{reset_url}</p>
                <p><strong>This link will expire in 10 minutes.</strong></p>
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

def send_cancellation_email(booking):
    """Send email notification to user when admin cancels their booking."""
    try:
        subject = f"Booking Cancelled - ROOMIO (Booking #{booking.id})"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #dc3545;">Booking Cancelled</h2>
                <p>Hello <strong>{booking.user.name}</strong>,</p>
                <p>We regret to inform you that your booking has been cancelled by the admin.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin: 20px 0;">
                    <h4 style="margin-top: 0;">Booking Details:</h4>
                    <p><strong>Booking ID:</strong> #{booking.id}</p>
                    <p><strong>Room:</strong> Room {booking.room.room_number} ({booking.room.room_type.name})</p>
                    <p><strong>Check-in:</strong> {booking.check_in}</p>
                    <p><strong>Check-out:</strong> {booking.check_out}</p>
                    <p><strong>Nights:</strong> {booking.total_nights}</p>
                    <p><strong>Total Amount:</strong> ₱{booking.total_amount}</p>
                </div>
                
                <p>If you have any questions, please contact our support team.</p>
                <p>We hope to serve you better in the future.</p>
                <hr>
                <p style="font-size: 12px; color: #666;">&copy; 2026 ROOMIO. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        msg = Message(subject, recipients=[booking.user.email])
        msg.html = html_content
        mail.send(msg)
        print(f"Cancellation email sent to {booking.user.email}")
        return True
    except Exception as e:
        print(f"Error sending cancellation email: {e}")
        return False

def send_receipt_email(to_email, booking, receipt):
    """Send booking receipt email (currently disabled)."""
    print(f"[INFO] Receipt email would be sent to {to_email} for booking {booking.id}")
    return True