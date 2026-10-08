"""totp_startup: lockout reset and one-shot env-driven TOTP reset."""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from django_otp.plugins.otp_totp.models import TOTPDevice


@pytest.fixture
def device(db):
    user = get_user_model().objects.create_user(
        username='otp_admin', password='S3cure-pass-for-tests!', is_staff=True,
    )
    return TOTPDevice.objects.create(user=user, name='old', confirmed=True)


def _date(dt):
    return timezone.localtime(dt).strftime('%Y-%m-%d %H:%M')


def test_clears_lockout_without_reset(device, monkeypatch):
    monkeypatch.delenv('TOTP_RESET_USER', raising=False)
    device.throttle_increment()
    call_command('totp_startup')
    device.refresh_from_db()
    assert device.throttling_failure_count == 0
    assert device.confirmed


def test_reset_is_one_shot(device, monkeypatch):
    TOTPDevice.objects.filter(pk=device.pk).update(
        created_at=timezone.now() - timedelta(days=1),
    )
    monkeypatch.setenv('TOTP_RESET_USER', 'otp_admin')
    monkeypatch.setenv('TOTP_RESET_DATE', _date(timezone.now() - timedelta(minutes=5)))

    call_command('totp_startup')
    devices = list(TOTPDevice.objects.filter(user=device.user))
    assert len(devices) == 1 and not devices[0].confirmed
    pending_pk = devices[0].pk

    call_command('totp_startup')  # container restart with variables still set
    assert list(TOTPDevice.objects.filter(user=device.user).values_list('pk', flat=True)) == [pending_pk]


def test_reset_requires_valid_date(device, monkeypatch):
    monkeypatch.setenv('TOTP_RESET_USER', 'otp_admin')
    monkeypatch.setenv('TOTP_RESET_DATE', 'demain')
    call_command('totp_startup')
    assert TOTPDevice.objects.filter(pk=device.pk, confirmed=True).exists()
