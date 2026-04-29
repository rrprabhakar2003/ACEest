"""
Unit tests for ACEest Fitness & Gym - Version 1.0
Tests: member CRUD, membership plans, health endpoint
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ACEest_Fitness_v1 import app, members, MEMBERSHIP_PLANS


@pytest.fixture(autouse=True)
def clear_data():
    members.clear()
    yield
    members.clear()


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def sample_member():
    return {
        'name': 'Rahul Sharma',
        'email': 'rahul@example.com',
        'phone': '9876543210',
        'plan': 'premium'
    }


class TestHomeAndHealth:
    def test_home_returns_200(self, client):
        response = client.get('/')
        assert response.status_code == 200

    def test_home_returns_app_name(self, client):
        data = client.get('/').get_json()
        assert data['app'] == 'ACEest Fitness & Gym'

    def test_home_returns_version(self, client):
        data = client.get('/').get_json()
        assert data['version'] == '1.0.0'

    def test_health_returns_healthy(self, client):
        data = client.get('/health').get_json()
        assert data['status'] == 'healthy'

    def test_health_returns_member_count(self, client):
        data = client.get('/health').get_json()
        assert data['total_members'] == 0

    def test_health_has_timestamp(self, client):
        data = client.get('/health').get_json()
        assert 'timestamp' in data


class TestMemberRegistration:
    def test_register_member_success(self, client, sample_member):
        response = client.post('/members', json=sample_member)
        assert response.status_code == 201

    def test_register_returns_member_data(self, client, sample_member):
        data = client.post('/members', json=sample_member).get_json()
        assert data['success'] is True
        assert data['member']['name'] == sample_member['name']
        assert data['member']['email'] == sample_member['email']

    def test_register_assigns_member_id(self, client, sample_member):
        data = client.post('/members', json=sample_member).get_json()
        assert 'id' in data['member']
        assert len(data['member']['id']) == 8

    def test_register_missing_name_returns_400(self, client):
        response = client.post('/members', json={'email': 'a@b.com', 'phone': '123', 'plan': 'basic'})
        assert response.status_code == 400

    def test_register_missing_email_returns_400(self, client):
        response = client.post('/members', json={'name': 'Test', 'phone': '123', 'plan': 'basic'})
        assert response.status_code == 400

    def test_register_missing_phone_returns_400(self, client):
        response = client.post('/members', json={'name': 'Test', 'email': 'a@b.com', 'plan': 'basic'})
        assert response.status_code == 400

    def test_register_missing_plan_returns_400(self, client):
        response = client.post('/members', json={'name': 'Test', 'email': 'a@b.com', 'phone': '123'})
        assert response.status_code == 400

    def test_register_invalid_plan_returns_400(self, client):
        response = client.post('/members', json={'name': 'Test', 'email': 'a@b.com', 'phone': '123', 'plan': 'gold'})
        assert response.status_code == 400

    def test_register_duplicate_email_returns_409(self, client, sample_member):
        client.post('/members', json=sample_member)
        response = client.post('/members', json=sample_member)
        assert response.status_code == 409

    def test_register_no_body_returns_400(self, client):
        response = client.post('/members', content_type='application/json')
        assert response.status_code == 400

    def test_register_sets_active_true(self, client, sample_member):
        data = client.post('/members', json=sample_member).get_json()
        assert data['member']['active'] is True

    def test_register_includes_plan_details(self, client, sample_member):
        data = client.post('/members', json=sample_member).get_json()
        assert 'plan_details' in data['member']
        assert data['member']['plan_details']['name'] == 'Premium'


class TestGetMembers:
    def test_get_members_empty(self, client):
        data = client.get('/members').get_json()
        assert data['success'] is True
        assert data['count'] == 0
        assert data['members'] == []

    def test_get_members_after_registration(self, client, sample_member):
        client.post('/members', json=sample_member)
        data = client.get('/members').get_json()
        assert data['count'] == 1

    def test_get_member_by_id(self, client, sample_member):
        created = client.post('/members', json=sample_member).get_json()
        member_id = created['member']['id']
        data = client.get(f'/members/{member_id}').get_json()
        assert data['success'] is True
        assert data['member']['id'] == member_id

    def test_get_nonexistent_member_returns_404(self, client):
        response = client.get('/members/NOTEXIST')
        assert response.status_code == 404


class TestUpdateMember:
    def test_update_member_phone(self, client, sample_member):
        created = client.post('/members', json=sample_member).get_json()
        member_id = created['member']['id']
        data = client.put(f'/members/{member_id}', json={'phone': '1111111111'}).get_json()
        assert data['member']['phone'] == '1111111111'

    def test_update_member_plan(self, client, sample_member):
        created = client.post('/members', json=sample_member).get_json()
        member_id = created['member']['id']
        data = client.put(f'/members/{member_id}', json={'plan': 'vip'}).get_json()
        assert data['member']['plan'] == 'vip'

    def test_update_invalid_plan_returns_400(self, client, sample_member):
        created = client.post('/members', json=sample_member).get_json()
        member_id = created['member']['id']
        response = client.put(f'/members/{member_id}', json={'plan': 'diamond'})
        assert response.status_code == 400

    def test_update_nonexistent_member_returns_404(self, client):
        response = client.put('/members/NOTEXIST', json={'phone': '123'})
        assert response.status_code == 404


class TestDeleteMember:
    def test_delete_member_success(self, client, sample_member):
        created = client.post('/members', json=sample_member).get_json()
        member_id = created['member']['id']
        response = client.delete(f'/members/{member_id}')
        assert response.status_code == 200

    def test_delete_removes_member(self, client, sample_member):
        created = client.post('/members', json=sample_member).get_json()
        member_id = created['member']['id']
        client.delete(f'/members/{member_id}')
        response = client.get(f'/members/{member_id}')
        assert response.status_code == 404

    def test_delete_nonexistent_returns_404(self, client):
        response = client.delete('/members/NOTEXIST')
        assert response.status_code == 404


class TestPlans:
    def test_get_plans_returns_all(self, client):
        data = client.get('/plans').get_json()
        assert 'basic' in data['plans']
        assert 'premium' in data['plans']
        assert 'vip' in data['plans']

    def test_plan_has_price(self, client):
        data = client.get('/plans').get_json()
        for plan in data['plans'].values():
            assert 'price' in plan

    def test_plan_has_features(self, client):
        data = client.get('/plans').get_json()
        for plan in data['plans'].values():
            assert 'features' in plan
            assert isinstance(plan['features'], list)
