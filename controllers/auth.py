from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, EmailVerification, PasswordReset
from werkzeug.security import generate_password_hash, check_password_hash
from utils.validators import validate_name, validate_email, validate_password
from utils.email_utils import send_verification_email, send_password_reset_email
import secrets
from datetime import datetime, timedelta
import re
import random
import string

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

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

# Phone validation rules per country
PHONE_RULES = {
    '+63': {'min': 10, 'max': 10, 'regex': r'^\d{10}$'},
    '+1': {'min': 10, 'max': 10, 'regex': r'^\d{10}$'},
    '+44': {'min': 10, 'max': 10, 'regex': r'^\d{10}$'},
    '+61': {'min': 9, 'max': 9, 'regex': r'^\d{9}$'},
    '+86': {'min': 11, 'max': 11, 'regex': r'^\d{11}$'},
    '+81': {'min': 10, 'max': 10, 'regex': r'^\d{10}$'},
    '+82': {'min': 9, 'max': 10, 'regex': r'^\d{9,10}$'},
    '+49': {'min': 10, 'max': 11, 'regex': r'^\d{10,11}$'},
    '+33': {'min': 9, 'max': 9, 'regex': r'^\d{9}$'},
    '+39': {'min': 10, 'max': 10, 'regex': r'^\d{10}$'}
}

def validate_phone_by_country(phone, country_code):
    """Validate phone number based on country code."""
    if not phone or not phone.isdigit():
        return False, "Phone number must contain only digits."
    
    rules = PHONE_RULES.get(country_code, {'min': 5, 'max': 15})
    if len(phone) < rules['min']:
        return False, f"Phone number must be at least {rules['min']} digits."
    if len(phone) > rules['max']:
        return False, f"Phone number cannot exceed {rules['max']} digits."
    
    if 'regex' in rules and not re.match(rules['regex'], phone):
        return False, f"Invalid phone number format for selected country."
    
    return True, ""

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

# -------------------- REGISTRATION (with OTP email verification) --------------------
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        full_name = f"{first_name} {last_name}".strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        country_code = request.form.get('country_code', '+63')
        raw_phone = request.form.get('phone', '').strip()

        errors = []

        # Name validation
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

        # Phone number validation based on country
        if not raw_phone:
            errors.append("Phone number is required.")
        else:
            is_valid, phone_error = validate_phone_by_country(raw_phone, country_code)
            if not is_valid:
                errors.append(phone_error)
            else:
                full_phone = f"{country_code}{raw_phone}"
                if User.query.filter_by(phone=full_phone).first():
                    errors.append("Phone number already registered.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('register.html',
                                   first_name=first_name, last_name=last_name,
                                   email=email, phone=raw_phone, country_code=country_code)

        # Store registration data in session for OTP verification
        session['reg_data'] = {
            'first_name': first_name,
            'last_name': last_name,
            'full_name': full_name,
            'email': email,
            'password_hash': generate_password_hash(password),
            'country_code': country_code,
            'phone': f"{country_code}{raw_phone}"
        }

        # Send OTP verification email
        try:
            send_verification_email(email)
            flash('Verification code sent to your email. Please enter it to complete registration.', 'info')
            return redirect(url_for('auth.verify_email'))
        except Exception as e:
            print(f"Error sending email: {e}")
            flash('Error sending verification email. Please try again.', 'danger')
            return render_template('register.html',
                                   first_name=first_name, last_name=last_name,
                                   email=email, phone=raw_phone, country_code=country_code)

    return render_template('register.html')

# -------------------- EMAIL VERIFICATION --------------------
@bp.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    if 'reg_data' not in session:
        flash('Registration session expired. Please register again.', 'danger')
        return redirect(url_for('auth.register'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        email = session['reg_data']['email']
        verification = EmailVerification.query.filter_by(email=email).first()
        
        if verification and verification.code == code and not verification.is_expired():
            # Create user
            user = User(
                name=session['reg_data']['full_name'],
                email=email,
                password=session['reg_data']['password_hash'],
                country_code=session['reg_data']['country_code'],
                phone=session['reg_data']['phone'],
                role='guest'
            )
            db.session.add(user)
            db.session.delete(verification)
            db.session.commit()
            
            # Clear session data
            session.pop('reg_data', None)
            
            # Auto-login after verification
            login_user(user)
            flash('Registration successful! Welcome to ROOMIO!', 'success')
            
            # Redirect to appropriate dashboard
            if user.role == 'admin':
                return redirect(url_for('dashboard.admin_dashboard'))
            elif user.role == 'staff':
                return redirect(url_for('dashboard.staff_dashboard'))
            else:
                return redirect(url_for('dashboard.guest_dashboard'))
        else:
            flash('Invalid or expired verification code. Please try again.', 'danger')
            return render_template('verify_email.html')

    return render_template('verify_email.html')

@bp.route('/resend-code')
def resend_code():
    if 'reg_data' not in session:
        return redirect(url_for('auth.register'))
    email = session['reg_data']['email']
    send_verification_email(email)
    flash('A new verification code has been sent to your email.', 'info')
    return redirect(url_for('auth.verify_email'))

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
@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not validate_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('forgot_pass.html')

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('If that email is registered, you will receive a reset link.', 'info')
            return redirect(url_for('auth.login'))

        token = secrets.token_urlsafe(32)
        PasswordReset.query.filter_by(email=email).delete()
        db.session.add(PasswordReset(email=email, token=token))
        db.session.commit()

        try:
            send_password_reset_email(email, token)
            flash('Password reset link sent to your email.', 'success')
        except Exception as e:
            print(f"Error sending reset email: {e}")
            flash('Unable to send reset email. Please try again later.', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('forgot_pass.html')

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset = PasswordReset.query.filter_by(token=token).first()
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

        user = User.query.filter_by(email=reset.email).first()
        if user:
            user.password = generate_password_hash(password)
            db.session.commit()
            db.session.delete(reset)
            db.session.commit()
            login_user(user)
            flash('Your password has been updated. You are now logged in.', 'success')
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

@bp.route('/verification-remaining')
def verification_remaining():
    if 'reg_data' not in session:
        return jsonify({'error': 'No registration session'}), 400
    email = session['reg_data']['email']
    verification = EmailVerification.query.filter_by(email=email).first()
    if not verification:
        return jsonify({'remaining': 0, 'expired': True})
    elapsed = (datetime.utcnow() - verification.created_at).total_seconds()
    remaining = max(0, 120 - int(elapsed))
    return jsonify({'remaining': remaining, 'expired': remaining <= 0})