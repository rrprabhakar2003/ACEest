"""
ACEest Fitness & Gym Management System - Version 3.0
Full features: Members, Classes, Bookings, Workouts, Trainers, Equipment, Dashboard
"""

from flask import Flask, jsonify, request, render_template
from datetime import datetime
import uuid
import os

app = Flask(__name__)
app.config['VERSION'] = '3.0.0'
app.config['APP_NAME'] = 'ACEest Fitness & Gym'

# ── In-memory data stores ─────────────────────────────────────────────────────
members = {}
classes = {}
bookings = {}
workouts = {}
trainers = {}
equipment = {}

MEMBERSHIP_PLANS = {
    'basic': {
        'name': 'Basic', 'price': 999, 'duration_days': 30,
        'features': ['gym_access', 'locker']
    },
    'premium': {
        'name': 'Premium', 'price': 1999, 'duration_days': 30,
        'features': ['gym_access', 'pool_access', 'locker', 'group_classes', 'sauna']
    },
    'vip': {
        'name': 'VIP', 'price': 3999, 'duration_days': 30,
        'features': ['gym_access', 'pool_access', 'locker', 'personal_trainer',
                     'sauna', 'group_classes', 'unlimited_classes', 'nutrition_plan']
    },
}

CLASS_TYPES = ['Yoga', 'Zumba', 'CrossFit', 'Pilates', 'Spinning', 'HIIT', 'Boxing', 'Swimming']
EQUIPMENT_CATEGORIES = ['Cardio', 'Strength', 'Flexibility', 'Free Weights', 'Machines']


# ── Home & Health ─────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('index.html', version=app.config['VERSION'])


@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'version': app.config['VERSION'],
        'timestamp': datetime.utcnow().isoformat(),
        'stats': {
            'members': len(members),
            'classes': len(classes),
            'bookings': len(bookings),
            'workouts': len(workouts),
            'trainers': len(trainers),
            'equipment': len(equipment)
        }
    })


@app.route('/dashboard')
def dashboard():
    active_members = sum(1 for m in members.values() if m.get('active'))
    plan_distribution = {}
    for m in members.values():
        plan = m.get('plan', 'unknown')
        plan_distribution[plan] = plan_distribution.get(plan, 0) + 1

    total_workouts = len(workouts)
    total_classes = len(classes)
    available_slots = sum(max(0, c['capacity'] - c['enrolled']) for c in classes.values())

    return jsonify({
        'success': True,
        'dashboard': {
            'total_members': len(members),
            'active_members': active_members,
            'plan_distribution': plan_distribution,
            'total_classes': total_classes,
            'total_bookings': len(bookings),
            'available_class_slots': available_slots,
            'total_workouts_logged': total_workouts,
            'total_trainers': len(trainers),
            'total_equipment': len(equipment),
            'generated_at': datetime.utcnow().isoformat()
        }
    })


# ── Members ───────────────────────────────────────────────────────────────────

@app.route('/members', methods=['GET'])
def get_members():
    plan_filter = request.args.get('plan')
    active_filter = request.args.get('active')

    result = list(members.values())
    if plan_filter:
        result = [m for m in result if m['plan'] == plan_filter]
    if active_filter is not None:
        is_active = active_filter.lower() == 'true'
        result = [m for m in result if m['active'] == is_active]

    return jsonify({'success': True, 'count': len(result), 'members': result})


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
        'age': data.get('age'),
        'fitness_goal': data.get('fitness_goal', 'general_fitness'),
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

    for key in ['name', 'phone', 'plan', 'active', 'age', 'fitness_goal']:
        if key in data:
            if key == 'plan':
                if data['plan'] not in MEMBERSHIP_PLANS:
                    return jsonify({'success': False, 'error': 'Invalid plan'}), 400
                member['plan_details'] = MEMBERSHIP_PLANS[data['plan']]
            member[key] = data[key]

    member['updated_at'] = datetime.utcnow().isoformat()
    return jsonify({'success': True, 'message': 'Member updated', 'member': member})


@app.route('/members/<member_id>', methods=['DELETE'])
def delete_member(member_id):
    member = members.pop(member_id, None)
    if not member:
        return jsonify({'success': False, 'error': 'Member not found'}), 404
    return jsonify({'success': True, 'message': f"Member {member['name']} deleted successfully"})


@app.route('/plans', methods=['GET'])
def get_plans():
    return jsonify({'success': True, 'plans': MEMBERSHIP_PLANS})


# ── Trainers ──────────────────────────────────────────────────────────────────

@app.route('/trainers', methods=['GET'])
def get_trainers():
    return jsonify({'success': True, 'count': len(trainers), 'trainers': list(trainers.values())})


@app.route('/trainers/<trainer_id>', methods=['GET'])
def get_trainer(trainer_id):
    trainer = trainers.get(trainer_id)
    if not trainer:
        return jsonify({'success': False, 'error': 'Trainer not found'}), 404
    return jsonify({'success': True, 'trainer': trainer})


@app.route('/trainers', methods=['POST'])
def add_trainer():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Request body required'}), 400

    for field in ['name', 'email', 'specialization', 'experience_years']:
        if field not in data:
            return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

    trainer_id = str(uuid.uuid4())[:8].upper()
    trainer = {
        'id': trainer_id,
        'name': data['name'],
        'email': data['email'],
        'phone': data.get('phone', ''),
        'specialization': data['specialization'],
        'experience_years': int(data['experience_years']),
        'certifications': data.get('certifications', []),
        'available': data.get('available', True),
        'rating': data.get('rating', 5.0),
        'joined_at': datetime.utcnow().isoformat()
    }
    trainers[trainer_id] = trainer
    return jsonify({'success': True, 'message': 'Trainer added', 'trainer': trainer}), 201


@app.route('/trainers/<trainer_id>', methods=['DELETE'])
def delete_trainer(trainer_id):
    trainer = trainers.pop(trainer_id, None)
    if not trainer:
        return jsonify({'success': False, 'error': 'Trainer not found'}), 404
    return jsonify({'success': True, 'message': f"Trainer {trainer['name']} removed"})


# ── Classes ───────────────────────────────────────────────────────────────────

@app.route('/classes', methods=['GET'])
def get_classes():
    type_filter = request.args.get('type')
    result = list(classes.values())
    if type_filter:
        result = [c for c in result if c['type'] == type_filter]
    return jsonify({'success': True, 'count': len(result), 'classes': result})


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
        return jsonify({'success': False, 'error': f"Invalid type. Choose from: {CLASS_TYPES}"}), 400

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
        'level': data.get('level', 'all_levels'),
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
        'class_type': cls['type'],
        'booked_at': datetime.utcnow().isoformat(),
        'status': 'confirmed'
    }
    bookings[booking_key] = booking
    cls['enrolled'] += 1
    return jsonify({'success': True, 'message': 'Class booked successfully', 'booking': booking}), 201


@app.route('/bookings/<member_id>', methods=['GET'])
def get_member_bookings(member_id):
    if member_id not in members:
        return jsonify({'success': False, 'error': 'Member not found'}), 404
    member_bookings = [b for b in bookings.values() if b['member_id'] == member_id]
    return jsonify({'success': True, 'count': len(member_bookings), 'bookings': member_bookings})


# ── Workouts ──────────────────────────────────────────────────────────────────

@app.route('/workouts', methods=['GET'])
def get_workouts():
    member_id = request.args.get('member_id')
    result = list(workouts.values())
    if member_id:
        result = [w for w in result if w['member_id'] == member_id]
    return jsonify({'success': True, 'count': len(result), 'workouts': result})


@app.route('/workouts', methods=['POST'])
def log_workout():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Request body required'}), 400

    for field in ['member_id', 'exercises']:
        if field not in data:
            return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

    if data['member_id'] not in members:
        return jsonify({'success': False, 'error': 'Member not found'}), 404

    if not isinstance(data['exercises'], list) or len(data['exercises']) == 0:
        return jsonify({'success': False, 'error': 'exercises must be a non-empty list'}), 400

    workout_id = str(uuid.uuid4())[:8].upper()
    workout = {
        'id': workout_id,
        'member_id': data['member_id'],
        'member_name': members[data['member_id']]['name'],
        'exercises': data['exercises'],
        'duration_minutes': data.get('duration_minutes', 0),
        'calories_burned': data.get('calories_burned', 0),
        'notes': data.get('notes', ''),
        'logged_at': datetime.utcnow().isoformat()
    }
    workouts[workout_id] = workout
    return jsonify({'success': True, 'message': 'Workout logged', 'workout': workout}), 201


@app.route('/workouts/<member_id>/stats', methods=['GET'])
def get_workout_stats(member_id):
    if member_id not in members:
        return jsonify({'success': False, 'error': 'Member not found'}), 404

    member_workouts = [w for w in workouts.values() if w['member_id'] == member_id]
    total_calories = sum(w.get('calories_burned', 0) for w in member_workouts)
    total_minutes = sum(w.get('duration_minutes', 0) for w in member_workouts)

    return jsonify({
        'success': True,
        'member_id': member_id,
        'stats': {
            'total_sessions': len(member_workouts),
            'total_calories_burned': total_calories,
            'total_minutes': total_minutes,
            'average_session_minutes': round(total_minutes / len(member_workouts), 1) if member_workouts else 0
        }
    })


# ── Equipment ─────────────────────────────────────────────────────────────────

@app.route('/equipment', methods=['GET'])
def get_equipment():
    return jsonify({'success': True, 'count': len(equipment), 'equipment': list(equipment.values())})


@app.route('/equipment', methods=['POST'])
def add_equipment():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Request body required'}), 400

    for field in ['name', 'category', 'quantity']:
        if field not in data:
            return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

    if data['category'] not in EQUIPMENT_CATEGORIES:
        return jsonify({'success': False, 'error': f"Invalid category. Choose from: {EQUIPMENT_CATEGORIES}"}), 400

    eq_id = str(uuid.uuid4())[:8].upper()
    item = {
        'id': eq_id,
        'name': data['name'],
        'category': data['category'],
        'quantity': int(data['quantity']),
        'status': data.get('status', 'operational'),
        'last_maintenance': data.get('last_maintenance', datetime.utcnow().isoformat()),
        'added_at': datetime.utcnow().isoformat()
    }
    equipment[eq_id] = item
    return jsonify({'success': True, 'message': 'Equipment added', 'equipment': item}), 201


@app.route('/equipment/<eq_id>', methods=['DELETE'])
def delete_equipment(eq_id):
    item = equipment.pop(eq_id, None)
    if not item:
        return jsonify({'success': False, 'error': 'Equipment not found'}), 404
    return jsonify({'success': True, 'message': f"Equipment {item['name']} removed"})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
