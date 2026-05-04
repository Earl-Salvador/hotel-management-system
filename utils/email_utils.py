from flask import url_for, current_app
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from threading import Thread

# For async email sending para hindi ma-delay ang response
def send_async_email(app, msg):
    with app.app_context():
        mail = current_app.extensions.get('mail')
        if mail:
            mail.send(msg)

def send_email(subject, recipients, html_body):
    """Send email using Flask-Mail"""
    msg = Message(subject, recipients=recipients)
    msg.html = html_body
    
    # Send asynchronously para mabilis ang response
    thr = Thread(target=send_async_email, args=(current_app._get_current_object(), msg))
    thr.start()
    return True

def generate_verification_token(email):
    """Generate a secure token for email verification"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-verification')

def confirm_verification_token(token, expiration=3600):
    """Verify the token and return the email if valid"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-verification', max_age=expiration)
        return email
    except Exception:
        return None

def send_verification_email(user_email):
    """Send verification email to user"""
    try:
        token = generate_verification_token(user_email)
        verify_url = url_for('auth.verify_email', token=token, _external=True)
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ padding: 20px; max-width: 600px; margin: 0 auto; }}
                .button {{
                    background-color: #92B775;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 5px;
                    display: inline-block;
                }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Welcome to ROOMIO!</h2>
                <p>Please click the button below to verify your email address:</p>
                <p><a href="{verify_url}" class="button">Verify Email</a></p>
                <p>Or copy and paste this link:</p>
                <p>{verify_url}</p>
                <p>This link will expire in 1 hour.</p>
                <div class="footer">
                    <p>If you didn't create an account with ROOMIO, please ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        send_email(
            subject='Verify Your ROOMIO Account',
            recipients=[user_email],
            html_body=html
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_password_reset_email(user_email, token):
    """Send password reset email to user"""
    try:
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ padding: 20px; max-width: 600px; margin: 0 auto; }}
                .button {{
                    background-color: #92B775;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 5px;
                    display: inline-block;
                }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Reset Your ROOMIO Password</h2>
                <p>Click the button below to reset your password:</p>
                <p><a href="{reset_url}" class="button">Reset Password</a></p>
                <p>This link will expire in 10 minutes.</p>
                <div class="footer">
                    <p>If you didn't request a password reset, please ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        send_email(
            subject='Reset Your ROOMIO Password',
            recipients=[user_email],
            html_body=html
        )
        return True
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False