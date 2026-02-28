import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_user(db):
    def make_user(**kwargs):
        kwargs['password'] = kwargs.get('password', 'testpass123')
        if 'username' not in kwargs:
            kwargs['username'] = 'testuser'
        if 'role' in kwargs and isinstance(kwargs['role'], str):
            from accounts.models import role as RoleModel
            role_obj, _ = RoleModel.objects.get_or_create(name=kwargs.pop('role'))
            kwargs['role'] = role_obj
        user = User.objects.create_user(**kwargs)
        return user
    return make_user

@pytest.mark.django_db
class TestAuthentication:
    
    def test_user_registration(self, api_client):
        url = '/api/auth/register/'
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'role': 'user'
        }
        res = api_client.post(url, data)
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['username'] == 'newuser'
        assert res.data['role'] == 'user'
        assert 'password' not in res.data

    def test_user_login(self, api_client, create_user):
        user = create_user(username='loginuser', password='mypassword')
        url = '/api/auth/login/'
        data = {
            'username': 'loginuser',
            'password': 'mypassword'
        }
        res = api_client.post(url, data)
        assert res.status_code == status.HTTP_200_OK
        assert 'access' in res.data
        assert 'refresh' in res.data

    def test_profile_retrieval(self, api_client, create_user):
        user = create_user()
        api_client.force_authenticate(user=user)
        url = '/api/auth/profile/'
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        assert res.data['username'] == user.username

    def test_user_logout(self, api_client, create_user):
        user = create_user(username='logoutuser', password='mypassword')
        
        # 1. Login to get tokens
        login_url = '/api/auth/login/'
        login_res = api_client.post(login_url, {'username': 'logoutuser', 'password': 'mypassword'})
        refresh_token = login_res.data['refresh']
        access_token = login_res.data['access']

        # 2. Logout by blacklisting the refresh token
        api_client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
        logout_url = '/api/auth/logout/'
        logout_res = api_client.post(logout_url, {'refresh': refresh_token})
        assert logout_res.status_code == status.HTTP_205_RESET_CONTENT

        # 3. Try to use the blacklisted refresh token to get a new access token
        refresh_url = '/api/auth/login/refresh/'
        refresh_res = api_client.post(refresh_url, {'refresh': refresh_token})
        assert refresh_res.status_code == status.HTTP_401_UNAUTHORIZED
        assert refresh_res.data['code'] == 'token_not_valid'
