from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, EmailVerification, PasswordReset
from werkzeug.security import generate_password_hash, check_password_hash
from utils.validators import validate_name, validate_email, validate_password
from utils.email_utils import send_verification_email, send_password_reset_email
import secrets
from datetime import datetime, timedelta
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

bp = Blueprint('auth', __name__)

# -------------------- VALIDATION HELPERS --------------------
def validate_name(name):
    return bool(re.match(r"^[A-Za-z\s'-]{2,50}$", name))

def validate_email(email):
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))

def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True

# -------------------- LOGIN --------------------
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            if user.is_blocked:
                flash('Your account has been blocked. Please contact support.', 'danger')
                return redirect(url_for('auth.login'))
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('dashboard.admin_dashboard'))
            elif user.role == 'staff':
                return redirect(url_for('dashboard.staff_dashboard'))
            else:
                return redirect(url_for('dashboard.guest_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

# -------------------- REGISTRATION --------------------
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        full_name = f"{first_name} {last_name}".strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        phone = request.form.get('phone', '').strip()

        errors = []

        if not validate_name(first_name):
            errors.append("First name must be 2-50 letters, spaces, hyphens, apostrophes.")
        if not validate_name(last_name):
            errors.append("Last name must be 2-50 letters, spaces, hyphens, apostrophes.")
        if not validate_email(email):
            errors.append("Invalid email format.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")
        if not validate_password(password):
            errors.append("Password must be at least 8 characters with one uppercase, one lowercase, and one number.")
        if password != confirm:
            errors.append("Passwords do not match.")
        # Phone validation removed - phone is now optional
        # No validation for phone number

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('register.html',
                                   first_name=first_name, last_name=last_name,
                                   email=email, phone=phone)

        # Store registration data in session
        session['reg_data'] = {
            'first_name': first_name,
            'last_name': last_name,
            'full_name': full_name,
            'email': email,
            'password_hash': generate_password_hash(password),
            'phone': phone if phone else None  # Allow empty phone
        }

        # Send verification email
        try:
            if send_verification_email(email):
                flash('Verification link sent to your email. Please check your inbox.', 'info')
                return redirect(url_for('auth.verify_email_page'))
            else:
                flash('Unable to send verification email. Please try again.', 'danger')
                return render_template('register.html', first_name=first_name, last_name=last_name, email=email, phone=phone)
        except Exception as e:
            print(f"Error: {e}")
            flash('Unable to send verification email. Please try again.', 'danger')
            return render_template('register.html', first_name=first_name, last_name=last_name, email=email, phone=phone)

    return render_template('register.html')

# -------------------- EMAIL VERIFICATION --------------------
# Sa auth.py, i-update ang verify_email route:

@bp.route('/verify-email/<token>')
def verify_email(token):
    from utils.email_utils import confirm_verification_token
    
    email = confirm_verification_token(token)
    
    if not email:
        flash('The verification link is invalid or has expired. Please register again.', 'danger')
        return redirect(url_for('auth.register'))
    
    reg_data = session.get('reg_data')
    if not reg_data or reg_data.get('email') != email:
        flash('Registration session expired. Please register again.', 'danger')
        return redirect(url_for('auth.register'))
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('Email already registered. Please login.', 'info')
        session.pop('reg_data', None)
        return redirect(url_for('auth.login'))
    
    # Create user - ALISIN MUNA ANG is_verified
    user = User(
        name=reg_data['full_name'],
        email=email,
        password=reg_data['password_hash'],
        phone=reg_data.get('phone'),
        role='guest'
        # is_verified = True  # I-REMOVE MUNA ITO
    )
    db.session.add(user)
    db.session.commit()
    
    session.pop('reg_data', None)
    login_user(user)
    flash('Email verified! Registration successful. Welcome to ROOMIO!', 'success')
    
    if user.role == 'admin':
        return redirect(url_for('dashboard.admin_dashboard'))
    elif user.role == 'staff':
        return redirect(url_for('dashboard.staff_dashboard'))
    else:
        return redirect(url_for('dashboard.guest_dashboard'))

@bp.route('/verify-email-page')
def verify_email_page():
    return render_template('verify_email.html')

@bp.route('/resend-verification')
def resend_verification():
    if 'reg_data' not in session:
        flash('Please register first.', 'danger')
        return redirect(url_for('auth.register'))
    
    email = session['reg_data']['email']
    if send_verification_email(email):
        flash('A new verification link has been sent to your email.', 'success')
    else:
        flash('Unable to send verification email. Please try again.', 'danger')
    return redirect(url_for('auth.verify_email_page'))

# -------------------- LOGOUT --------------------
@bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    if request.method == 'GET':
        return redirect(url_for('index'))
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# -------------------- PASSWORD RESET --------------------
# -------------------- PASSWORD RESET --------------------
@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not validate_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('forgot_pass.html')

        user = User.query.filter_by(email=email).first()
        
        # For security, don't reveal if email exists
        if not user:
            flash('If that email is registered, you will receive a reset link.', 'info')
            return redirect(url_for('auth.login'))

        # Generate unique token
        token = secrets.token_urlsafe(32)
        
        # Delete any existing reset tokens for this email
        PasswordReset.query.filter_by(email=email).delete()
        
        # Save new token
        db.session.add(PasswordReset(email=email, token=token))
        db.session.commit()

        try:
            send_password_reset_email(email, token)
            flash('Password reset link sent to your email. It will expire in 10 minutes.', 'success')
        except Exception as e:
            print(f"Error sending reset email: {e}")
            flash('Unable to send reset email. Please try again later.', 'danger')
        
        return redirect(url_for('auth.login'))

    return render_template('forgot_pass.html')


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Verify token and allow user to set new password."""
    reset = PasswordReset.query.filter_by(token=token).first()
    
    # Check if token exists and is not expired
    if not reset or reset.is_expired():
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        errors = []
        if not validate_password(password):
            errors.append("Password must be at least 8 characters with one uppercase, one lowercase, and one number.")
        if password != confirm:
            errors.append("Passwords do not match.")
        
        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('reset_password.html', token=token)

        # Update user's password
        user = User.query.filter_by(email=reset.email).first()
        if user:
            user.password = generate_password_hash(password)
            db.session.commit()
            
            # Delete the used token
            db.session.delete(reset)
            db.session.commit()
            
            # Auto-login after password reset
            login_user(user)
            flash('Your password has been updated. You are now logged in!', 'success')
            
            # Redirect to appropriate dashboard
            if user.role == 'admin':
                return redirect(url_for('dashboard.admin_dashboard'))
            elif user.role == 'staff':
                return redirect(url_for('dashboard.staff_dashboard'))
            else:
                return redirect(url_for('dashboard.guest_dashboard'))
        else:
            flash('User not found. Please contact support.', 'danger')
            return redirect(url_for('auth.forgot_password'))

    return render_template('reset_password.html', token=token)

# -------------------- AJAX ENDPOINTS --------------------
@bp.route('/check-email')
def check_email():
    email = request.args.get('email', '').strip()
    if not email:
        return jsonify({'exists': False})
    user = User.query.filter_by(email=email).first()
    return jsonify({'exists': user is not None})

@bp.route('/check-phone')
def check_phone():
    phone = request.args.get('phone', '').strip()
    if not phone:
        return jsonify({'exists': False})
    user = User.query.filter_by(phone=phone).first()
    return jsonify({'exists': user is not None})