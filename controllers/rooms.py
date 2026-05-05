from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Room, RoomType, Booking
from datetime import datetime
import os
from werkzeug.utils import secure_filename

bp = Blueprint('rooms', __name__, url_prefix='/admin/rooms')

# -------------------- ROOM TYPES --------------------
@bp.route('/room_types')
@login_required
def list_room_types():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    room_types = RoomType.query.all()
    return render_template('admin/room_types.html', room_types=room_types)

@bp.route('/room_types', methods=['POST'])
@login_required
def create_room_type():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json() or request.form
    name = data.get('name')
    description = data.get('description')
    base_price = data.get('base_price')
    capacity = data.get('capacity')
    if not name or not base_price or not capacity:
        return jsonify({'error': 'Missing required fields'}), 400
    rt = RoomType(name=name, description=description, base_price=base_price, capacity=capacity)
    db.session.add(rt)
    db.session.commit()
    return jsonify({'success': True, 'id': rt.id}), 201

@bp.route('/room_types/<int:id>', methods=['PUT'])
@login_required
def update_room_type(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    rt = RoomType.query.get_or_404(id)
    data = request.get_json() or request.form
    rt.name = data.get('name', rt.name)
    rt.description = data.get('description', rt.description)
    rt.base_price = data.get('base_price', rt.base_price)
    rt.capacity = data.get('capacity', rt.capacity)
    db.session.commit()
    return jsonify({'success': True}), 200

@bp.route('/room_types/<int:id>', methods=['DELETE'])
@login_required
def delete_room_type(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    rt = RoomType.query.get_or_404(id)
    if rt.rooms and len(rt.rooms) > 0:
        return jsonify({'success': False, 'error': 'Cannot delete room type because rooms are using it.'}), 400
    db.session.delete(rt)
    db.session.commit()
    return jsonify({'success': True}), 200

@bp.route('/room_types/<int:id>/json')
@login_required
def get_room_type_json(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    rt = RoomType.query.get_or_404(id)
    return jsonify({
        'id': rt.id,
        'name': rt.name,
        'description': rt.description,
        'base_price': float(rt.base_price),
        'capacity': rt.capacity
    })

# -------------------- ROOMS --------------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'room_types')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/rooms', methods=['POST'])
@login_required
def create_room():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    room_number = data.get('room_number')
    room_type_id = data.get('room_type_id')
    status = data.get('status', 'available')
    if not room_number or not room_type_id:
        return jsonify({'error': 'Missing fields'}), 400
    if Room.query.filter_by(room_number=room_number).first():
        return jsonify({'error': f'Room number {room_number} already exists'}), 400
    room = Room(room_number=room_number, room_type_id=room_type_id, status=status)
    db.session.add(room)
    db.session.commit()
    return jsonify({'success': True, 'id': room.id}), 201

@bp.route('/rooms/<int:id>', methods=['PUT'])
@login_required
def update_room(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    room = Room.query.get_or_404(id)
    data = request.get_json()
    new_number = data.get('room_number', room.room_number)
    if new_number != room.room_number and Room.query.filter_by(room_number=new_number).first():
        return jsonify({'error': 'Room number already exists'}), 400
    room.room_number = new_number
    room.room_type_id = data.get('room_type_id', room.room_type_id)
    room.status = data.get('status', room.status)
    db.session.commit()
    return jsonify({'success': True}), 200

@bp.route('/rooms/<int:id>/maintenance', methods=['POST'])
@login_required
def set_maintenance(id):
    """Set room status to maintenance (replaces delete)"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    room = Room.query.get_or_404(id)
    today = datetime.now().date()
    # Check if room has active booking today
    active_booking = Booking.query.filter(
        Booking.room_id == id,
        Booking.status == 'confirmed',
        Booking.check_in <= today,
        Booking.check_out > today
    ).first()
    if active_booking:
        return jsonify({'success': False, 'error': 'Cannot set to maintenance. Room has active booking today.'}), 400
    room.status = 'maintenance'
    db.session.commit()
    return jsonify({'success': True, 'message': f'Room {room.room_number} set to maintenance mode'}), 200

@bp.route('/rooms/<int:id>/set-available', methods=['POST'])
@login_required
def set_available(id):
    """Set room status back to available from maintenance"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    room = Room.query.get_or_404(id)
    
    if room.status != 'maintenance':
        return jsonify({'success': False, 'error': 'Room is not in maintenance mode.'}), 400
    
    room.status = 'available'
    db.session.commit()
    return jsonify({'success': True, 'message': f'Room {room.room_number} is now available for booking.'}), 200

@bp.route('/rooms/<int:id>/force-checkout', methods=['POST'])
@login_required
def force_checkout(id):
    """Force checkout a room - ends current active booking"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    room = Room.query.get_or_404(id)
    today = datetime.now().date()
    
    # Find active booking for this room
    active_booking = Booking.query.filter(
        Booking.room_id == id,
        Booking.status == 'confirmed',
        Booking.check_in <= today,
        Booking.check_out > today
    ).first()
    
    if not active_booking:
        return jsonify({'success': False, 'error': 'No active booking found for this room.'}), 400
    
    # Update booking check-out date to today
    active_booking.check_out = today
    active_booking.total_nights = (active_booking.check_out - active_booking.check_in).days
    db.session.commit()
    
    # Update room status to available
    room.status = 'available'
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Room {room.room_number} has been checked out.'}), 200

@bp.route('/rooms/<int:id>/json')
@login_required
def get_room_json(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    room = Room.query.get_or_404(id)
    return jsonify({
        'id': room.id,
        'room_number': room.room_number,
        'room_type_id': room.room_type_id,
        'status': room.status,
        'room_type_name': room.room_type.name if room.room_type else ''
    })

@bp.route('/room_types/<int:id>/upload-image', methods=['POST'])
@login_required
def upload_room_type_image(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    rt = RoomType.query.get_or_404(id)
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(f"roomtype_{id}_{file.filename}")
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        if rt.image_filename and os.path.exists(os.path.join(UPLOAD_FOLDER, rt.image_filename)):
            os.remove(os.path.join(UPLOAD_FOLDER, rt.image_filename))
        rt.image_filename = filename
        db.session.commit()
        return jsonify({'success': True, 'filename': filename})
    return jsonify({'error': 'File type not allowed'}), 400