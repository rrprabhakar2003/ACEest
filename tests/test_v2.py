"""
Unit tests for ACEest Fitness & Gym - Version 2.0
Tests: classes, bookings (in addition to v1 features)
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ACEest_Fitness_v2 import app, members, classes, bookings, CLASS_TYPES


@pytest.fixture(autouse=True)
def clear_data():
    members.clear()
    classes.clear()
    bookings.clear()
    yield
    members.clear()
    classes.clear()
    bookings.clear()


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def registered_member(client):
    response = client.post('/members', json={
        'name': 'Priya Singh',
        'email': 'priya@example.com',
        'phone': '9000000001',
        'plan': 'premium'
    })
    return response.get_json()['member']


@pytest.fixture
def created_class(client):
    response = client.post('/classes', json={
        'name': 'Morning Yoga',
        'type': 'Yoga',
        'trainer': 'Anjali Mehta',
        'schedule': 'Mon-Wed-Fri 07:00',
        'capacity': 20,
        'duration_minutes': 60
    })
    return response.get_json()['class']


class TestHealth:
    def test_health_includes_class_count(self, client):
        data = client.get('/health').get_json()
        assert 'total_classes' in data

    def test_health_includes_booking_count(self, client):
        data = client.get('/health').get_json()
        assert 'total_bookings' in data

    def test_version_is_two(self, client):
        data = client.get('/').get_json()
        assert data['version'] == '2.0.0'


class TestClasses:
    def test_create_class_success(self, client):
        response = client.post('/classes', json={
            'name': 'Evening Zumba',
            'type': 'Zumba',
            'trainer': 'Ravi Kumar',
            'schedule': 'Tue-Thu 18:00',
            'capacity': 15
        })
        assert response.status_code == 201

    def test_create_class_returns_data(self, client):
        data = client.post('/classes', json={
            'name': 'HIIT Blast',
            'type': 'HIIT',
            'trainer': 'Karan Verma',
            'schedule': 'Daily 06:00',
            'capacity': 10
        }).get_json()
        assert data['success'] is True
        assert data['class']['name'] == 'HIIT Blast'

    def test_create_class_assigns_id(self, client):
        data = client.post('/classes', json={
            'name': 'Pilates Core',
            'type': 'Pilates',
            'trainer': 'Sneha Rao',
            'schedule': 'Mon-Fri 09:00',
            'capacity': 12
        }).get_json()
        assert 'id' in data['class']

    def test_create_class_invalid_type(self, client):
        response = client.post('/classes', json={
            'name': 'Test',
            'type': 'Dance',
            'trainer': 'X',
            'schedule': 'Mon',
            'capacity': 5
        })
        assert response.status_code == 400

    def test_create_class_missing_field(self, client):
        response = client.post('/classes', json={
            'name': 'Test',
            'type': 'Yoga',
            'trainer': 'X'
        })
        assert response.status_code == 400

    def test_get_classes_empty(self, client):
        data = client.get('/classes').get_json()
        assert data['count'] == 0

    def test_get_classes_returns_created(self, client, created_class):
        data = client.get('/classes').get_json()
        assert data['count'] == 1

    def test_get_class_by_id(self, client, created_class):
        class_id = created_class['id']
        data = client.get(f'/classes/{class_id}').get_json()
        assert data['success'] is True
        assert data['class']['id'] == class_id

    def test_get_nonexistent_class_404(self, client):
        response = client.get('/classes/NOPE')
        assert response.status_code == 404

    def test_delete_class_success(self, client, created_class):
        class_id = created_class['id']
        response = client.delete(f'/classes/{class_id}')
        assert response.status_code == 200

    def test_delete_removes_class(self, client, created_class):
        class_id = created_class['id']
        client.delete(f'/classes/{class_id}')
        response = client.get(f'/classes/{class_id}')
        assert response.status_code == 404

    def test_class_types_endpoint(self, client):
        data = client.get('/class-types').get_json()
        assert 'class_types' in data
        assert 'Yoga' in data['class_types']

    def test_initial_enrolled_count_is_zero(self, client, created_class):
        assert created_class['enrolled'] == 0


class TestBookings:
    def test_create_booking_success(self, client, registered_member, created_class):
        response = client.post('/bookings', json={
            'member_id': registered_member['id'],
            'class_id': created_class['id']
        })
        assert response.status_code == 201

    def test_booking_increments_enrolled(self, client, registered_member, created_class):
        client.post('/bookings', json={
            'member_id': registered_member['id'],
            'class_id': created_class['id']
        })
        data = client.get(f"/classes/{created_class['id']}").get_json()
        assert data['class']['enrolled'] == 1

    def test_duplicate_booking_returns_409(self, client, registered_member, created_class):
        payload = {'member_id': registered_member['id'], 'class_id': created_class['id']}
        client.post('/bookings', json=payload)
        response = client.post('/bookings', json=payload)
        assert response.status_code == 409

    def test_booking_nonexistent_member_404(self, client, created_class):
        response = client.post('/bookings', json={
            'member_id': 'GHOST001',
            'class_id': created_class['id']
        })
        assert response.status_code == 404

    def test_booking_nonexistent_class_404(self, client, registered_member):
        response = client.post('/bookings', json={
            'member_id': registered_member['id'],
            'class_id': 'GHOST001'
        })
        assert response.status_code == 404

    def test_booking_full_class_returns_409(self, client, registered_member):
        cls = client.post('/classes', json={
            'name': 'Tiny Class',
            'type': 'Yoga',
            'trainer': 'X',
            'schedule': 'Mon 10:00',
            'capacity': 1
        }).get_json()['class']

        client.post('/bookings', json={
            'member_id': registered_member['id'],
            'class_id': cls['id']
        })

        # Register a second member and try to book the full class
        m2 = client.post('/members', json={
            'name': 'Member Two',
            'email': 'm2@example.com',
            'phone': '9000000002',
            'plan': 'basic'
        }).get_json()['member']

        response = client.post('/bookings', json={
            'member_id': m2['id'],
            'class_id': cls['id']
        })
        assert response.status_code == 409

    def test_get_member_bookings(self, client, registered_member, created_class):
        client.post('/bookings', json={
            'member_id': registered_member['id'],
            'class_id': created_class['id']
        })
        data = client.get(f"/bookings/{registered_member['id']}").get_json()
        assert data['count'] == 1

    def test_get_bookings_nonexistent_member_404(self, client):
        response = client.get('/bookings/NOPE')
        assert response.status_code == 404

    def test_get_all_bookings(self, client, registered_member, created_class):
        client.post('/bookings', json={
            'member_id': registered_member['id'],
            'class_id': created_class['id']
        })
        data = client.get('/bookings').get_json()
        assert data['count'] == 1
