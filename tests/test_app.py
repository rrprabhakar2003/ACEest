"""
Unit tests for ACEest Fitness & Gym - Version 3.0 (main)
Tests: all v3 features including workouts, trainers, equipment, dashboard
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ACEest_Fitness import app, members, classes, bookings, workouts, trainers, equipment


@pytest.fixture(autouse=True)
def clear_data():
    members.clear()
    classes.clear()
    bookings.clear()
    workouts.clear()
    trainers.clear()
    equipment.clear()
    yield
    members.clear()
    classes.clear()
    bookings.clear()
    workouts.clear()
    trainers.clear()
    equipment.clear()


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def member(client):
    r = client.post('/members', json={
        'name': 'Amit Patel',
        'email': 'amit@example.com',
        'phone': '9800000001',
        'plan': 'vip',
        'age': 28,
        'fitness_goal': 'weight_loss'
    })
    return r.get_json()['member']


@pytest.fixture
def trainer(client):
    r = client.post('/trainers', json={
        'name': 'Coach Raj',
        'email': 'raj@aceest.com',
        'specialization': 'CrossFit',
        'experience_years': 8,
        'certifications': ['NSCA', 'ACE']
    })
    return r.get_json()['trainer']


@pytest.fixture
def gym_class(client):
    r = client.post('/classes', json={
        'name': 'Power Lifting',
        'type': 'CrossFit',
        'trainer': 'Coach Raj',
        'schedule': 'Mon-Wed-Fri 06:00',
        'capacity': 15,
        'level': 'advanced'
    })
    return r.get_json()['class']


class TestHomeAndHealth:
    def test_home_200(self, client):
        assert client.get('/').status_code == 200

    def test_version_is_three(self, client):
        response = client.get('/')
        assert b'3.0.0' in response.data

    def test_home_has_endpoints(self, client):
        response = client.get('/')
        assert b'/health' in response.data or b'health' in response.data

    def test_health_healthy(self, client):
        data = client.get('/health').get_json()
        assert data['status'] == 'healthy'

    def test_health_has_stats(self, client):
        data = client.get('/health').get_json()
        assert 'stats' in data
        stats = data['stats']
        for key in ['members', 'classes', 'bookings', 'workouts', 'trainers', 'equipment']:
            assert key in stats


class TestDashboard:
    def test_dashboard_returns_success(self, client):
        data = client.get('/dashboard').get_json()
        assert data['success'] is True

    def test_dashboard_has_all_stats(self, client):
        data = client.get('/dashboard').get_json()
        d = data['dashboard']
        for key in ['total_members', 'active_members', 'plan_distribution',
                    'total_classes', 'total_bookings', 'total_workouts_logged',
                    'total_trainers', 'total_equipment']:
            assert key in d

    def test_dashboard_counts_after_registration(self, client, member):
        data = client.get('/dashboard').get_json()
        assert data['dashboard']['total_members'] == 1
        assert data['dashboard']['active_members'] == 1

    def test_dashboard_plan_distribution(self, client, member):
        data = client.get('/dashboard').get_json()
        assert 'vip' in data['dashboard']['plan_distribution']


class TestMembersV3:
    def test_register_with_age_and_goal(self, client):
        data = client.post('/members', json={
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '9000000099',
            'plan': 'basic',
            'age': 25,
            'fitness_goal': 'muscle_gain'
        }).get_json()
        assert data['member']['age'] == 25
        assert data['member']['fitness_goal'] == 'muscle_gain'

    def test_filter_members_by_plan(self, client, member):
        data = client.get('/members?plan=vip').get_json()
        assert data['count'] == 1

    def test_filter_members_by_active(self, client, member):
        data = client.get('/members?active=true').get_json()
        assert data['count'] == 1

    def test_update_fitness_goal(self, client, member):
        data = client.put(f"/members/{member['id']}", json={'fitness_goal': 'endurance'}).get_json()
        assert data['member']['fitness_goal'] == 'endurance'

    def test_member_count_in_health(self, client, member):
        data = client.get('/health').get_json()
        assert data['stats']['members'] == 1


class TestTrainers:
    def test_add_trainer_success(self, client):
        response = client.post('/trainers', json={
            'name': 'Nisha Gupta',
            'email': 'nisha@aceest.com',
            'specialization': 'Yoga',
            'experience_years': 5
        })
        assert response.status_code == 201

    def test_trainer_has_id(self, client):
        data = client.post('/trainers', json={
            'name': 'Trainer X',
            'email': 'x@aceest.com',
            'specialization': 'HIIT',
            'experience_years': 3
        }).get_json()
        assert 'id' in data['trainer']

    def test_get_all_trainers(self, client, trainer):
        data = client.get('/trainers').get_json()
        assert data['count'] == 1

    def test_get_trainer_by_id(self, client, trainer):
        data = client.get(f"/trainers/{trainer['id']}").get_json()
        assert data['trainer']['id'] == trainer['id']

    def test_get_nonexistent_trainer_404(self, client):
        response = client.get('/trainers/NOPE')
        assert response.status_code == 404

    def test_delete_trainer(self, client, trainer):
        response = client.delete(f"/trainers/{trainer['id']}")
        assert response.status_code == 200

    def test_delete_removes_trainer(self, client, trainer):
        client.delete(f"/trainers/{trainer['id']}")
        response = client.get(f"/trainers/{trainer['id']}")
        assert response.status_code == 404

    def test_trainer_missing_field_400(self, client):
        response = client.post('/trainers', json={
            'name': 'Incomplete',
            'email': 'inc@aceest.com'
        })
        assert response.status_code == 400

    def test_trainer_certifications_stored(self, client, trainer):
        assert trainer['certifications'] == ['NSCA', 'ACE']

    def test_trainer_count_in_health(self, client, trainer):
        data = client.get('/health').get_json()
        assert data['stats']['trainers'] == 1


class TestClassesV3:
    def test_create_class_with_level(self, client):
        data = client.post('/classes', json={
            'name': 'Advanced Boxing',
            'type': 'Boxing',
            'trainer': 'Coach Ali',
            'schedule': 'Tue-Thu 19:00',
            'capacity': 8,
            'level': 'advanced'
        }).get_json()
        assert data['class']['level'] == 'advanced'

    def test_filter_classes_by_type(self, client, gym_class):
        data = client.get('/classes?type=CrossFit').get_json()
        assert data['count'] == 1

    def test_filter_classes_wrong_type(self, client, gym_class):
        data = client.get('/classes?type=Yoga').get_json()
        assert data['count'] == 0


class TestWorkouts:
    def test_log_workout_success(self, client, member):
        response = client.post('/workouts', json={
            'member_id': member['id'],
            'exercises': [
                {'name': 'Bench Press', 'sets': 3, 'reps': 10, 'weight_kg': 60},
                {'name': 'Squats', 'sets': 4, 'reps': 12, 'weight_kg': 80}
            ],
            'duration_minutes': 75,
            'calories_burned': 450,
            'notes': 'Great session!'
        })
        assert response.status_code == 201

    def test_workout_has_id(self, client, member):
        data = client.post('/workouts', json={
            'member_id': member['id'],
            'exercises': [{'name': 'Running', 'duration_minutes': 30}]
        }).get_json()
        assert 'id' in data['workout']

    def test_workout_nonexistent_member_404(self, client):
        response = client.post('/workouts', json={
            'member_id': 'GHOST',
            'exercises': [{'name': 'Push-ups'}]
        })
        assert response.status_code == 404

    def test_workout_empty_exercises_400(self, client, member):
        response = client.post('/workouts', json={
            'member_id': member['id'],
            'exercises': []
        })
        assert response.status_code == 400

    def test_get_workouts_by_member(self, client, member):
        client.post('/workouts', json={
            'member_id': member['id'],
            'exercises': [{'name': 'Plank', 'duration_seconds': 60}]
        })
        data = client.get(f"/workouts?member_id={member['id']}").get_json()
        assert data['count'] == 1

    def test_get_workout_stats(self, client, member):
        client.post('/workouts', json={
            'member_id': member['id'],
            'exercises': [{'name': 'Deadlift'}],
            'duration_minutes': 60,
            'calories_burned': 400
        })
        data = client.get(f"/workouts/{member['id']}/stats").get_json()
        assert data['stats']['total_sessions'] == 1
        assert data['stats']['total_calories_burned'] == 400
        assert data['stats']['total_minutes'] == 60

    def test_workout_stats_nonexistent_member_404(self, client):
        response = client.get('/workouts/GHOST/stats')
        assert response.status_code == 404

    def test_average_session_minutes(self, client, member):
        for mins in [30, 60, 90]:
            client.post('/workouts', json={
                'member_id': member['id'],
                'exercises': [{'name': 'Cardio'}],
                'duration_minutes': mins
            })
        data = client.get(f"/workouts/{member['id']}/stats").get_json()
        assert data['stats']['average_session_minutes'] == 60.0

    def test_missing_exercises_field_400(self, client, member):
        response = client.post('/workouts', json={'member_id': member['id']})
        assert response.status_code == 400


class TestEquipment:
    def test_add_equipment_success(self, client):
        response = client.post('/equipment', json={
            'name': 'Treadmill',
            'category': 'Cardio',
            'quantity': 5
        })
        assert response.status_code == 201

    def test_equipment_has_id(self, client):
        data = client.post('/equipment', json={
            'name': 'Dumbbell Set',
            'category': 'Free Weights',
            'quantity': 20
        }).get_json()
        assert 'id' in data['equipment']

    def test_get_all_equipment(self, client):
        client.post('/equipment', json={'name': 'Barbell', 'category': 'Strength', 'quantity': 10})
        data = client.get('/equipment').get_json()
        assert data['count'] == 1

    def test_equipment_invalid_category_400(self, client):
        response = client.post('/equipment', json={
            'name': 'Weird Machine',
            'category': 'Unknown',
            'quantity': 1
        })
        assert response.status_code == 400

    def test_delete_equipment(self, client):
        eq = client.post('/equipment', json={
            'name': 'Rowing Machine',
            'category': 'Cardio',
            'quantity': 3
        }).get_json()['equipment']
        response = client.delete(f"/equipment/{eq['id']}")
        assert response.status_code == 200

    def test_equipment_missing_field_400(self, client):
        response = client.post('/equipment', json={'name': 'Bench', 'category': 'Strength'})
        assert response.status_code == 400


class TestBookingsV3:
    def test_booking_includes_class_type(self, client, member, gym_class):
        data = client.post('/bookings', json={
            'member_id': member['id'],
            'class_id': gym_class['id']
        }).get_json()
        assert data['booking']['class_type'] == 'CrossFit'

    def test_booking_count_in_health(self, client, member, gym_class):
        client.post('/bookings', json={
            'member_id': member['id'],
            'class_id': gym_class['id']
        })
        data = client.get('/health').get_json()
        assert data['stats']['bookings'] == 1
