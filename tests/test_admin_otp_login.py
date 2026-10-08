"""Admin TOTP login: valid codes must be accepted, lockouts must not self-extend."""
import time

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django_otp.oath import TOTP
from django_otp.plugins.otp_totp.models import TOTPDevice

from core.forms import TUSOTPAdminAuthenticationForm

PASSWORD = 'S3cure-pass-for-tests!'


@pytest.fixture
def staff_device(db):
    user = get_user_model().objects.create_user(
        username='otp_admin', password=PASSWORD, is_staff=True,
    )
    return TOTPDevice.objects.create(user=user, name='test', confirmed=True, tolerance=3)


def _current_code(device):
    totp = TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift)
    totp.time = time.time()
    return f'{totp.token():0{device.digits}d}'


def _form(token):
    request = RequestFactory().post('/tus-gestion-secure/login/')
    return TUSOTPAdminAuthenticationForm(request, data={
        'username': 'otp_admin', 'password': PASSWORD, 'otp_token': token,
    })


def test_valid_code_is_accepted(staff_device):
    assert _form(_current_code(staff_device)).is_valid()


def test_code_with_space_is_accepted(staff_device):
    code = _current_code(staff_device)
    assert _form(f'{code[:3]} {code[3:]}').is_valid()


def test_wrong_code_is_rejected(staff_device):
    code = _current_code(staff_device)
    wrong = f'{(int(code) + 500000) % 1000000:06d}'
    form = _form(wrong)
    assert not form.is_valid()
    assert form.non_field_errors()


def test_lockout_shows_reason_and_does_not_extend(staff_device):
    staff_device.throttle_increment()
    staff_device.throttle_increment()
    form = _form(_current_code(staff_device))
    assert not form.is_valid()
    assert form.non_field_errors()
    staff_device.refresh_from_db()
    assert staff_device.throttling_failure_count == 2
