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
        # Kunin ang payment method mula sa form (kung gusto mo pa rin ito)
        payment_method = request.form.get('payment_method', 'paymongo')
        
        # I-convert ang amount sa cents (kailangan ng PayMongo)
        amount = int(booking.total_amount * 100)
        
        # PayMongo API endpoint
        url = "https://api.paymongo.com/v1/checkout_sessions"
        
        # Basic authentication gamit ang secret key
        auth = (current_app.config['PAYMONGO_SECRET_KEY'], '')
        
        # Payload para sa checkout session
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
                            "description": f"Room {booking.room.room_number} - {booking.room.room_type.name}",
                            "name": "Hotel Booking",
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
            # Tawagin ang PayMongo API para gumawa ng checkout session
            response = requests.post(url, json=payload, auth=auth)
            result = response.json()
            
            if response.status_code == 201:
                # Kunin ang checkout URL mula sa response
                checkout_url = result['data']['attributes']['checkout_url']
                
                # I-save ang checkout session ID sa session (opsyonal)
                session['checkout_session_id'] = result['data']['id']
                session['pending_booking_id'] = booking.id
                
                # I-redirect ang user sa PayMongo checkout page
                return redirect(checkout_url)
            else:
                error_msg = result.get('errors', [{}])[0].get('detail', 'Unknown error')
                flash(f'Payment initialization failed: {error_msg}', 'danger')
                return render_template('payment/pay.html', booking=booking)
                
        except Exception as e:
            flash(f'Payment initialization failed: {str(e)}', 'danger')
            return render_template('payment/pay.html', booking=booking)
    
    # GET request - ipakita ang payment page
    return render_template('payment/pay.html', booking=booking)


@bp.route('/payment-success/<int:booking_id>')
@login_required
def payment_success(booking_id):
    """Page na pagkatapos ng matagumpay na payment"""
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    
    flash('Payment successful! Your booking is pending admin approval.', 'success')
    return render_template('payment/success.html', booking=booking)


@bp.route('/payment-cancelled/<int:booking_id>')
@login_required
def payment_cancelled(booking_id):
    """Page kapag nag-cancel ang user ng payment"""
    booking = Booking.query.get_or_404(booking_id)
    flash('Payment was cancelled. You can try again.', 'warning')
    return render_template('payment/pay.html', booking=booking)


@bp.route('/webhook', methods=['POST'])
def paymongo_webhook():
    """Webhook na tatawagin ng PayMongo pagkatapos ng successful payment"""
    data = request.get_json()
    
    # I-verify kung ito ay checkout_session.payment_success event
    event_type = data.get('data', {}).get('attributes', {}).get('type')
    
    if event_type == 'checkout_session.payment_success':
        # Kunin ang metadata para makuha ang booking_id
        metadata = data.get('data', {}).get('attributes', {}).get('data', {}).get('attributes', {}).get('metadata', {})
        booking_id = metadata.get('booking_id')
        
        if booking_id:
            booking = Booking.query.get(booking_id)
            if booking:
                # I-update ang payment status
                payment = Payment(
                    booking_id=booking.id,
                    amount=booking.total_amount,
                    payment_method='paymongo',
                    transaction_id=data.get('data', {}).get('id'),
                    status='completed',
                    paid_at=datetime.utcnow()
                )
                db.session.add(payment)
                # Huwag i-confirm agad ang booking - hintayin ang admin approval
                db.session.commit()
                
                print(f"Payment received for booking #{booking_id}")
    
    return {'status': 'ok'}, 200