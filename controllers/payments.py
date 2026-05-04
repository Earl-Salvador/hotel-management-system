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
        # I-print ang secret key para ma-verify (temporary)
        print(f"PayMongo Secret Key: {current_app.config.get('PAYMONGO_SECRET_KEY', 'NOT SET')}")
        
        amount = int(booking.total_amount * 100)
        
        url = "https://api.paymongo.com/v1/checkout_sessions"
        auth = (current_app.config['PAYMONGO_SECRET_KEY'], '')
        
        payload = {
            "data": {
                "attributes": {
                    "send_email_receipt": False,
                    "show_description": True,
                    "show_line_items": True,
                    "cancel_url": "https://hotel-management-system.onrender.com/payment/payment-cancelled",
                    "success_url": "https://hotel-management-system.onrender.com/payment/payment-success",
                    "description": f"Booking #{booking.id}",
                    "line_items": [
                        {
                            "currency": "PHP",
                            "amount": amount,
                            "description": f"Room {booking.room.room_number}",
                            "name": "Hotel Room Booking",
                            "quantity": 1,
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
            print(f"Sending request to PayMongo with amount: {amount}")
            response = requests.post(url, json=payload, auth=auth)
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
            
            if response.status_code == 201:
                result = response.json()
                checkout_url = result['data']['attributes']['checkout_url']
                return redirect(checkout_url)
            else:
                error_msg = response.json().get('errors', [{}])[0].get('detail', 'Unknown error')
                flash(f'Payment error: {error_msg}', 'danger')
                return render_template('payment/pay.html', booking=booking)
                
        except Exception as e:
            print(f"Exception: {str(e)}")
            flash(f'Payment failed: {str(e)}', 'danger')
            return render_template('payment/pay.html', booking=booking)
    
    return render_template('payment/pay.html', booking=booking)