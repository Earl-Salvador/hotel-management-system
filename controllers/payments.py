from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_required, current_user
from models import db, Booking, Payment
from datetime import datetime
import requests
import base64
import json

bp = Blueprint('payments', __name__, url_prefix='/payment')

@bp.route('/pay/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def pay(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # Convert amount to centavos
            amount = int(booking.total_amount * 100)
            
            # PayMongo API endpoint
            url = "https://api.paymongo.com/v1/checkout_sessions"
            
            # Get secret key from config
            secret_key = current_app.config.get('PAYMONGO_SECRET_KEY')
            
            # Create Basic Auth header
            auth_string = f"{secret_key}:"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_auth}',
                'Content-Type': 'application/json'
            }
            
            # Success and cancel URLs
            success_url = url_for('payments.payment_success', booking_id=booking.id, _external=True)
            cancel_url = url_for('payments.payment_cancelled', booking_id=booking.id, _external=True)
            
            # Prepare payload
            payload = {
                "data": {
                    "attributes": {
                        "send_email_receipt": False,
                        "show_description": True,
                        "show_line_items": True,
                        "cancel_url": cancel_url,
                        "success_url": success_url,
                        "description": f"Booking #{booking.id}",
                        "line_items": [
                            {
                                "currency": "PHP",
                                "amount": amount,
                                "description": f"Room {booking.room.room_number} - {booking.room.room_type.name}",
                                "name": "Hotel Room Booking",
                                "quantity": 1,
                                "images": []
                            }
                        ],
                        "payment_method_types": ["card", "gcash", "paymaya"],
                        "metadata": {
                            "booking_id": booking.id
                        }
                    }
                }
            }
            
            # Make request to PayMongo
            response = requests.post(url, json=payload, headers=headers)
            
            # Log response for debugging
            print(f"PayMongo Response Status: {response.status_code}")
            
            # Check if request was successful (200 or 201)
            if response.status_code in [200, 201]:
                result = response.json()
                checkout_url = result['data']['attributes']['checkout_url']
                # Store checkout session ID in session
                session['checkout_session_id'] = result['data']['id']
                session['pending_booking_id'] = booking.id
                print(f"Redirecting to: {checkout_url}")
                # Redirect to PayMongo checkout page
                return redirect(checkout_url)
            else:
                # Handle error
                error_data = response.json()
                if 'errors' in error_data:
                    error_msg = error_data['errors'][0].get('detail', 'Unknown error')
                else:
                    error_msg = response.text
                flash(f'Payment error: {error_msg}', 'danger')
                return render_template('payment/pay.html', booking=booking)
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            flash(f'Network error: {str(e)}', 'danger')
            return render_template('payment/pay.html', booking=booking)
        except Exception as e:
            print(f"Unexpected error: {e}")
            flash(f'Payment failed: {str(e)}', 'danger')
            return render_template('payment/pay.html', booking=booking)
    
    return render_template('payment/pay.html', booking=booking)


@bp.route('/payment-success/<int:booking_id>')
@login_required
def payment_success(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    
    # Check if payment already recorded
    existing_payment = Payment.query.filter_by(booking_id=booking.id).first()
    if not existing_payment:
        # Create payment record
        payment = Payment(
            booking_id=booking.id,
            amount=booking.total_amount,
            payment_method='paymongo',
            transaction_id=session.get('checkout_session_id', 'unknown'),
            status='completed',
            paid_at=datetime.utcnow()
        )
        db.session.add(payment)
        db.session.commit()
        print(f"Payment recorded for booking #{booking.id}")
    
    flash('Payment successful! Your booking is pending admin approval.', 'success')
    return render_template('payment/success.html', booking=booking)


@bp.route('/payment-cancelled/<int:booking_id>')
@login_required
def payment_cancelled(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    flash('Payment was cancelled. You can try again.', 'warning')
    return render_template('payment/pay.html', booking=booking)