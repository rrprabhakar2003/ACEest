"""
ACEest Fitness & Gym Management System - Version 1.0
Core features: Member registration, membership plans, basic health check
"""

from flask import Flask, jsonify, request
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['VERSION'] = '1.0.0'

# In-memory data store
members = {}
MEMBERSHIP_PLANS = {
    'basic': {'name': 'Basic', 'price': 999, 'duration_days': 30, 'features': ['gym_access']},
    'premium': {'name': 'Premium', 'price': 1999, 'duration_days': 30, 'features': ['gym_access', 'pool_access', 'locker']},
    'vip': {'name': 'VIP', 'price': 3999, 'duration_days': 30, 'features': ['gym_access', 'pool_access', 'locker', 'personal_trainer', 'sauna']},
}


@app.route('/')
def home():
    return jsonify({
        'app': 'ACEest Fitness & Gym',
        'version': app.config['VERSION'],
        'status': 'running',
        'message': 'Welcome to ACEest Fitness & Gym Management System'
    })


@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'version': app.config['VERSION'],
        'timestamp': datetime.utcnow().isoformat(),
        'total_members': len(members)
    })


@app.route('/members', methods=['GET'])
def get_members():
    return jsonify({
        'success': True,
        'count': len(members),
        'members': list(members.values())
    })


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

    required_fields = ['name', 'email', 'phone', 'plan']
    for field in required_fields:
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

    allowed_updates = ['name', 'phone', 'plan', 'active']
    for key in allowed_updates:
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
