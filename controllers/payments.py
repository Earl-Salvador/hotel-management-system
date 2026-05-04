from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_required, current_user
from models import db, Booking, Payment
from datetime import datetime
import requests
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
        # Convert amount to cents (PayMongo requires amount in centavos)
        amount = int(booking.total_amount * 100)
        
        # PayMongo API endpoint for checkout session
        url = "https://api.paymongo.com/v1/checkout_sessions"
        
        # Basic authentication using PayMongo secret key
        auth = (current_app.config['PAYMONGO_SECRET_KEY'], '')
        
        # Prepare the payload for PayMongo checkout session
        payload = {
            "data": {
                "attributes": {
                    "send_email_receipt": False,
                    "show_description": True,
                    "show_line_items": True,
                    "cancel_url": url_for('payments.payment_cancelled', booking_id=booking.id, _external=True),
                    "success_url": url_for('payments.payment_success', booking_id=booking.id, _external=True),
                    "description": f"Booking #{booking.id} - {booking.room.room_type.name}",
                    "line_items": [
                        {
                            "currency": "PHP",
                            "amount": amount,
                            "description": f"Room {booking.room.room_number} ({booking.room.room_type.name})",
                            "name": "Hotel Room Booking",
                            "quantity": booking.total_nights,
                            "images": []
                        }
                    ],
                    "payment_method_types": ["gcash", "card", "paymaya"],
                    "metadata": {
                        "booking_id": booking.id
                    }
                }
            }
        }
        
        try:
            # Send request to PayMongo
            response = requests.post(url, json=payload, auth=auth)
            result = response.json()
            
            if response.status_code == 201:
                # Get the checkout URL from response
                checkout_url = result['data']['attributes']['checkout_url']
                
                # Store checkout session ID in session (optional)
                session['checkout_session_id'] = result['data']['id']
                session['pending_booking_id'] = booking.id
                
                # Redirect user to PayMongo checkout page
                return redirect(checkout_url)
            else:
                error_msg = result.get('errors', [{}])[0].get('detail', 'Unknown error')
                flash(f'Payment initialization failed: {error_msg}', 'danger')
                return render_template('payment/pay.html', booking=booking)
                
        except Exception as e:
            print(f"Payment error: {str(e)}")
            flash(f'Payment initialization failed: {str(e)}', 'danger')
            return render_template('payment/pay.html', booking=booking)
    
    # GET request - show payment page
    return render_template('payment/pay.html', booking=booking)


@bp.route('/payment-success/<int:booking_id>')
@login_required
def payment_success(booking_id):
    """Page after successful payment"""
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    
    # Create payment record (webhook should also do this)
    existing_payment = Payment.query.filter_by(booking_id=booking.id).first()
    if not existing_payment:
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
    
    flash('Payment successful! Your booking is pending admin approval.', 'success')
    return render_template('payment/success.html', booking=booking)


@bp.route('/payment-cancelled/<int:booking_id>')
@login_required
def payment_cancelled(booking_id):
    """Page when user cancels payment"""
    booking = Booking.query.get_or_404(booking_id)
    flash('Payment was cancelled. You can try again.', 'warning')
    return render_template('payment/pay.html', booking=booking)


@bp.route('/webhook', methods=['POST'])
def paymongo_webhook():
    """Webhook endpoint for PayMongo to send payment updates"""
    data = request.get_json()
    
    # Check if it's a checkout_session.payment_success event
    event_type = data.get('data', {}).get('attributes', {}).get('type')
    
    if event_type == 'checkout_session.payment_success':
        # Get metadata to find booking_id
        metadata = data.get('data', {}).get('attributes', {}).get('data', {}).get('attributes', {}).get('metadata', {})
        booking_id = metadata.get('booking_id')
        
        if booking_id:
            booking = Booking.query.get(booking_id)
            if booking:
                # Check if payment already recorded
                existing = Payment.query.filter_by(booking_id=booking_id).first()
                if not existing:
                    payment = Payment(
                        booking_id=booking.id,
                        amount=booking.total_amount,
                        payment_method='paymongo',
                        transaction_id=data.get('data', {}).get('id'),
                        status='completed',
                        paid_at=datetime.utcnow()
                    )
                    db.session.add(payment)
                    db.session.commit()
                    print(f"Payment recorded for booking #{booking_id}")
    
    return {'status': 'ok'}, 200