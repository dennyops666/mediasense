import pytest
import pytest_asyncio
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from asgiref.sync import sync_to_async
import uuid

User = get_user_model()

def pytest_configure():
    settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'mediasense',
            'USER': 'mediasense',
            'PASSWORD': 'mediasense',
            'HOST': 'localhost',
            'PORT': '3306',
            'TEST': {
                'NAME': 'mediasense',
                'MIGRATE': False,
                'CREATE_DB': False
            },
        }
    }

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_password():
    return 'testpass123'

@pytest_asyncio.fixture
async def test_user(test_password):
    username = f'testuser_{uuid.uuid4().hex[:8]}'
    return await sync_to_async(User.objects.create_user)(
        username=username,
        password=test_password,
        email=f'{username}@example.com'
    )

@pytest_asyncio.fixture
async def authenticated_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client 