"""Root conftest — shared pytest fixtures for TUS."""
import pytest
from django.contrib.auth.models import User
from django.test import Client


@pytest.fixture
def client():
    """Django test client."""
    return Client()


@pytest.fixture
def user(db):
    """Standard user without admin privileges."""
    return User.objects.create_user(
        username="testuser",
        email="test@traitdunion.it",
        password="T3stP@ssw0rd!",
    )


@pytest.fixture
def admin_user(db):
    """Super-user for admin views."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@traitdunion.it",
        password="Adm1nP@ssw0rd!",
    )
