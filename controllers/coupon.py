from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Coupon
from datetime import datetime

bp = Blueprint('coupons', __name__, url_prefix='/admin/coupons')

@bp.route('/')
@login_required
def list_coupons():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template('admin/coupons.html', coupons=coupons)

@bp.route('/create', methods=['POST'])
@login_required
def create_coupon():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    code = data.get('code', '').strip().upper()
    discount_percent = data.get('discount_percent')
    valid_until = data.get('valid_until')
    
    if not code or not discount_percent or not valid_until:
        return jsonify({'error': 'All fields are required'}), 400
    
    # Check if coupon code already exists
    if Coupon.query.filter_by(code=code).first():
        return jsonify({'error': 'Coupon code already exists'}), 400
    
    try:
        discount = float(discount_percent)
        if discount < 0 or discount > 100:
            return jsonify({'error': 'Discount must be between 0 and 100'}), 400
    except:
        return jsonify({'error': 'Invalid discount value'}), 400
    
    coupon = Coupon(
        code=code,
        discount_percent=discount,
        valid_until=datetime.strptime(valid_until, '%Y-%m-%d').date(),
        is_active=True
    )
    db.session.add(coupon)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Coupon created successfully'})

@bp.route('/update/<int:id>', methods=['PUT'])
@login_required
def update_coupon(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    coupon = Coupon.query.get_or_404(id)
    data = request.get_json()
    
    code = data.get('code', '').strip().upper()
    discount_percent = data.get('discount_percent')
    valid_until = data.get('valid_until')
    is_active = data.get('is_active', coupon.is_active)
    
    if not code or not discount_percent or not valid_until:
        return jsonify({'error': 'All fields are required'}), 400
    
    # Check if code exists for another coupon
    existing = Coupon.query.filter(Coupon.code == code, Coupon.id != id).first()
    if existing:
        return jsonify({'error': 'Coupon code already exists'}), 400
    
    try:
        discount = float(discount_percent)
        if discount < 0 or discount > 100:
            return jsonify({'error': 'Discount must be between 0 and 100'}), 400
    except:
        return jsonify({'error': 'Invalid discount value'}), 400
    
    coupon.code = code
    coupon.discount_percent = discount
    coupon.valid_until = datetime.strptime(valid_until, '%Y-%m-%d').date()
    coupon.is_active = is_active
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Coupon updated successfully'})

@bp.route('/delete/<int:id>', methods=['DELETE'])
@login_required
def delete_coupon(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    coupon = Coupon.query.get_or_404(id)
    db.session.delete(coupon)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Coupon deleted successfully'})

@bp.route('/toggle/<int:id>', methods=['POST'])
@login_required
def toggle_coupon(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    coupon = Coupon.query.get_or_404(id)
    coupon.is_active = not coupon.is_active
    db.session.commit()
    
    status = 'activated' if coupon.is_active else 'deactivated'
    return jsonify({'success': True, 'message': f'Coupon {status} successfully'})

@bp.route('/<int:id>/json')
@login_required
def get_coupon_json(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    coupon = Coupon.query.get_or_404(id)
    return jsonify({
        'id': coupon.id,
        'code': coupon.code,
        'discount_percent': float(coupon.discount_percent),
        'valid_until': coupon.valid_until.strftime('%Y-%m-%d'),
        'is_active': coupon.is_active
    })