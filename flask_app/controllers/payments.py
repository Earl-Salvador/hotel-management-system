from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from models import db, Booking, Payment
from datetime import datetime
import requests
import base64
import hmac
import hashlib

bp = Blueprint('payments', __name__, url_prefix='/payment')

def get_paymongo_headers():
    api_key = current_app.config.get('PAYMONGO_SECRET_KEY')
    auth_str = f"{api_key}:"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    return {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Basic {base64_auth}"
    }

@bp.route('/pay/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def pay(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Siguraduhin na ang may-ari ng booking ang nagbabayad
    if booking.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Kunin ang piniling payment method mula sa form (hal. 'gcash', 'card', etc.)
        # Pero gagamit tayo ng PayMongo Links para sa automation
        amount_in_cents = int(booking.total_amount * 100)
        url = "https://api.paymongo.com/v1/links"
        
        payload = {
            "data": {
                "attributes": {
                    "amount": amount_in_cents,
                    "description": f"ROOMIO Booking #{booking.id}",
                    "remarks": f"Room {booking.room.room_number}"
                }
            }
        }

        try:
            response = requests.post(url, json=payload, headers=get_paymongo_headers())
            res_data = response.json()

            if response.status_code == 200:
                checkout_url = res_data['data']['attributes']['checkout_url']
                link_id = res_data['data']['id']

                # I-save muna ang payment record bilang 'pending'
                # Ginamit ang link_id bilang transaction_id para sa tracking sa webhook
                payment = Payment(
                    booking_id=booking.id,
                    amount=booking.total_amount,
                    payment_method="paymongo_link",
                    transaction_id=link_id,
                    status='pending',
                    paid_at=None
                )
                db.session.add(payment)
                db.session.commit()

                # I-redirect ang user sa PayMongo Checkout page
                return redirect(checkout_url)
            else:
                flash("Failed to create payment link. Please try again.", "danger")
        except Exception as e:
            flash(f"Error connecting to payment gateway: {str(e)}", "danger")

    return render_template('payment/pay.html', booking=booking)

# ---------------------------------------------------------
# WEBHOOK ROUTE (Dito tatawag si PayMongo kapag tapos na ang bayad)
# ---------------------------------------------------------
@bp.route('/webhook', methods=['POST'])
def webhook():
    payload = request.data
    signature_header = request.headers.get('Paymongo-Signature')
    webhook_secret = current_app.config.get('PAYMONGO_WEBHOOK_SECRET')

    # Verification ng signature para sa security
    if signature_header and webhook_secret:
        labels = signature_header.split(',')
        timestamp = labels[0].split('=')[1]
        signature = labels[1].split('=')[1]
        base_string = f"{timestamp}.{payload.decode('utf-8')}"
        
        hashed = hmac.new(
            webhook_secret.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if hashed != signature:
            return jsonify({'error': 'Invalid signature'}), 401

    data = request.json
    event_type = data['data']['attributes']['type']

    # Kapag success ang bayad sa PayMongo link
    if event_type == 'link.payment.paid':
        link_id = data['data']['attributes']['data']['attributes']['link_id']
        
        # Hanapin ang payment record gamit ang transaction_id (link_id)
        payment = Payment.query.filter_by(transaction_id=link_id).first()
        
        if payment:
            # I-update ang payment status
            payment.status = 'completed'
            payment.paid_at = datetime.utcnow()
            
            # PINALITAN DITO: Ang booking.status ay HINDI magiging 'confirmed' agad.
            # Mananatili itong 'pending' para sa admin approval (base sa hiningi mo).
            booking = Booking.query.get(payment.booking_id)
            if booking:
                booking.status = 'pending' # Explicitly set to pending/stays pending
            
            db.session.commit()
            return jsonify({'success': True}), 200

    return jsonify({'message': 'Event ignored'}), 200