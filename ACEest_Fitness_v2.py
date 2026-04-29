"""
ACEest Fitness & Gym Management System - Version 2.0
New features: Class scheduling, class booking, trainer assignment
"""

from flask import Flask, jsonify, request
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['VERSION'] = '2.0.0'

# In-memory data store
members = {}
classes = {}
bookings = {}

MEMBERSHIP_PLANS = {
    'basic': {'name': 'Basic', 'price': 999, 'duration_days': 30, 'features': ['gym_access']},
    'premium': {'name': 'Premium', 'price': 1999, 'duration_days': 30, 'features': ['gym_access', 'pool_access', 'locker', 'group_classes']},
    'vip': {'name': 'VIP', 'price': 3999, 'duration_days': 30, 'features': ['gym_access', 'pool_access', 'locker', 'personal_trainer', 'sauna', 'group_classes', 'unlimited_classes']},
}

CLASS_TYPES = ['Yoga', 'Zumba', 'CrossFit', 'Pilates', 'Spinning', 'HIIT', 'Boxing', 'Swimming']


# ── Health & Home ─────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return jsonify({
        'app': 'ACEest Fitness & Gym',
        'version': app.config['VERSION'],
        'status': 'running',
        'message': 'Welcome to ACEest Fitness & Gym Management System v2'
    })


@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'version': app.config['VERSION'],
        'timestamp': datetime.utcnow().isoformat(),
        'total_members': len(members),
        'total_classes': len(classes),
        'total_bookings': len(bookings)
    })


# ── Members ───────────────────────────────────────────────────────────────────

@app.route('/members', methods=['GET'])
def get_members():
    return jsonify({'success': True, 'count': len(members), 'members': list(members.values())})


@app.route('/members/<member_id>', methods=['GET'])
def get_member(member_id):
    member = members.get(member_id)
    if not member:
        return jsonify({'success': False, 'error': 'Member not found'}), 404
    return jsonify({'success': True, 'member': member})


@app.route('/members', methods=['POST'])
def register_member():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Request body required'}), 400

    for field in ['name', 'email', 'phone', 'plan']:
        if field not in data:
            return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

    if data['plan'] not in MEMBERSHIP_PLANS:
        return jsonify({'success': False, 'error': f"Invalid plan. Choose from: {list(MEMBERSHIP_PLANS.keys())}"}), 400

    for m in members.values():
        if m['email'] == data['email']:
            return jsonify({'success': False, 'error': 'Email already registered'}), 409

    member_id = str(uuid.uuid4())[:8].upper()
    member = {
        'id': member_id,
        'name': data['name'],
        'email': data['email'],
        'phone': data['phone'],
        'plan': data['plan'],
        'plan_details': MEMBERSHIP_PLANS[data['plan']],
        'joined_at': datetime.utcnow().isoformat(),
        'active': True
    }
    members[member_id] = member
    return jsonify({'success': True, 'message': 'Member registered successfully', 'member': member}), 201


@app.route('/members/<member_id>', methods=['PUT'])
def update_member(member_id):
    member = members.get(member_id)
    if not member:
        return jsonify({'success': False, 'error': 'Member not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Request body required'}), 400

    for key in ['name', 'phone', 'plan', 'active']:
        if key in data:
            if key == 'plan':
                if data['plan'] not in MEMBERSHIP_PLANS:
                    return jsonify({'success': False, 'error': 'Invalid plan'}), 400
                member['plan_details'] = MEMBERSHIP_PLANS[data['plan']]
            member[key] = data[key]

    member['updated_at'] = datetime.utcnow().isoformat()
    return jsonify({'success': True, 'member': member})


@app.route('/members/<member_id>', methods=['DELETE'])
def delete_member(member_id):
    member = members.pop(member_id, None)
    if not member:
        return jsonify({'success': False, 'error': 'Member not found'}), 404
    return jsonify({'success': True, 'message': f"Member {member['name']} deleted"})


@app.route('/plans', methods=['GET'])
def get_plans():
    return jsonify({'success': True, 'plans': MEMBERSHIP_PLANS})


# ── Classes ───────────────────────────────────────────────────────────────────

@app.route('/classes', methods=['GET'])
def get_classes():
    return jsonify({'success': True, 'count': len(classes), 'classes': list(classes.values())})


@app.route('/classes/<class_id>', methods=['GET'])
def get_class(class_id):
    cls = classes.get(class_id)
    if not cls:
        return jsonify({'success': False, 'error': 'Class not found'}), 404
    return jsonify({'success': True, 'class': cls})


@app.route('/classes', methods=['POST'])
def create_class():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Request body required'}), 400

    for field in ['name', 'type', 'trainer', 'schedule', 'capacity']:
        if field not in data:
            return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

    if data['type'] not in CLASS_TYPES:
        return jsonify({'success': False, 'error': f"Invalid class type. Choose from: {CLASS_TYPES}"}), 400

    class_id = str(uuid.uuid4())[:8].upper()
    gym_class = {
        'id': class_id,
        'name': data['name'],
        'type': data['type'],
        'trainer': data['trainer'],
        'schedule': data['schedule'],
        'capacity': int(data['capacity']),
        'enrolled': 0,
        'duration_minutes': data.get('duration_minutes', 60),
        'description': data.get('description', ''),
        'created_at': datetime.utcnow().isoformat()
    }
    classes[class_id] = gym_class
    return jsonify({'success': True, 'message': 'Class created', 'class': gym_class}), 201


@app.route('/classes/<class_id>', methods=['DELETE'])
def delete_class(class_id):
    cls = classes.pop(class_id, None)
    if not cls:
        return jsonify({'success': False, 'error': 'Class not found'}), 404
    return jsonify({'success': True, 'message': f"Class {cls['name']} deleted"})


@app.route('/class-types', methods=['GET'])
def get_class_types():
    return jsonify({'success': True, 'class_types': CLASS_TYPES})


# ── Bookings ──────────────────────────────────────────────────────────────────

@app.route('/bookings', methods=['GET'])
def get_bookings():
    return jsonify({'success': True, 'count': len(bookings), 'bookings': list(bookings.values())})


@app.route('/bookings', methods=['POST'])
def create_booking():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Request body required'}), 400

    for field in ['member_id', 'class_id']:
        if field not in data:
            return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

    member = members.get(data['member_id'])
    if not member:
        return jsonify({'success': False, 'error': 'Member not found'}), 404

    cls = classes.get(data['class_id'])
    if not cls:
        return jsonify({'success': False, 'error': 'Class not found'}), 404

    if cls['enrolled'] >= cls['capacity']:
        return jsonify({'success': False, 'error': 'Class is fully booked'}), 409

    booking_key = f"{data['member_id']}_{data['class_id']}"
    if booking_key in bookings:
        return jsonify({'success': False, 'error': 'Already booked this class'}), 409

    booking_id = str(uuid.uuid4())[:8].upper()
    booking = {
        'id': booking_id,
        'member_id': data['member_id'],
        'member_name': member['name'],
        'class_id': data['class_id'],
        'class_name': cls['name'],
        'booked_at': datetime.utcnow().isoformat(),
        'status': 'confirmed'
    }
    bookings[booking_key] = booking
    cls['enrolled'] += 1
    return jsonify({'success': True, 'message': 'Booking confirmed', 'booking': booking}), 201


@app.route('/bookings/<member_id>', methods=['GET'])
def get_member_bookings(member_id):
    if member_id not in members:
        return jsonify({'success': False, 'error': 'Member not found'}), 404
    member_bookings = [b for k, b in bookings.items() if b['member_id'] == member_id]
    return jsonify({'success': True, 'count': len(member_bookings), 'bookings': member_bookings})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
