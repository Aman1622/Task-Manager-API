import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Task

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_user(db):
    def make_user(username='testuser', role='user'):
        from accounts.models import role as RoleModel
        role_obj, _ = RoleModel.objects.get_or_create(name=role)
        return User.objects.create_user(username=username, password='password', role=role_obj)
    return make_user

@pytest.fixture
def create_task(db):
    def make_task(user, title='Test Task', completed=False):
        return Task.objects.create(user=user, title=title, completed=completed)
    return make_task

@pytest.mark.django_db
class TestTaskAPI:

    def test_list_tasks_unauthenticated(self, api_client, create_user, create_task):
        user = create_user()
        create_task(user=user, title='Public Task')
        res = api_client.get('/api/tasks/')
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data['results']) == 1

    def test_create_task_authenticated(self, api_client, create_user):
        user = create_user()
        api_client.force_authenticate(user=user)
        res = api_client.post('/api/tasks/', {'title': 'New Task', 'description': 'desc'})
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['title'] == 'New Task'
        assert Task.objects.count() == 1

    def test_regular_user_can_see_all_tasks(self, api_client, create_user, create_task):
        user1 = create_user(username='user1')
        user2 = create_user(username='user2')
        task = create_task(user=user2, title='User2 Task')
        create_task(user=user1, title='User1 Task')
        
        api_client.force_authenticate(user=user1)
        res = api_client.get('/api/tasks/')
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data['results']) == 2
        
        # Test they cannot edit it
        res_put = api_client.put(f'/api/tasks/{task.id}/', {'title': 'Hacked Title'})
        assert res_put.status_code == status.HTTP_403_FORBIDDEN

    def test_update_task(self, api_client, create_user, create_task):
        user = create_user()
        task = create_task(user=user, title='Old Title')
        
        api_client.force_authenticate(user=user)
        res = api_client.put(f'/api/tasks/{task.id}/', {'title': 'New Title', 'completed': True})
        assert res.status_code == status.HTTP_200_OK
        assert res.data['title'] == 'New Title'
        assert res.data['completed'] is True

    def test_delete_task(self, api_client, create_user, create_task):
        user = create_user()
        task = create_task(user=user)
        
        api_client.force_authenticate(user=user)
        res = api_client.delete(f'/api/tasks/{task.id}/')
        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert Task.objects.count() == 0

    def test_task_filtering(self, api_client, create_user, create_task):
        user = create_user()
        create_task(user=user, title='Incomplete Task', completed=False)
        create_task(user=user, title='Completed Task', completed=True)

        api_client.force_authenticate(user=user)
        res = api_client.get('/api/tasks/?completed=true')
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data['results']) == 1
        assert res.data['results'][0]['title'] == 'Completed Task'
