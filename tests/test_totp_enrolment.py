"""Security regressions: initial enrolment, confirmed secret protection, recovery."""
import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django_otp.oath import TOTP
from django_otp.plugins.otp_totp.models import TOTPDevice

User = get_user_model()
QR = '/tus-gestion-secure/totp-qr/'
VERIFY = '/tus-gestion-secure/totp-verify/'


def otp_for(device):
    generator = TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift)
    return str(generator.token()).zfill(device.digits)


@pytest.fixture
def staff(db):
    return User.objects.create_user(
        username='otp_staff', password='a-long-strong-password-123',
        is_staff=True, is_active=True,
    )


@pytest.mark.django_db
def test_enrolment_never_confirms_before_valid_code(client, staff):
    response = client.post(QR, {'username': staff.username, 'password': 'a-long-strong-password-123'})
    assert response.status_code == 200
    assert response['Content-Type'] == 'image/png'
    assert 'no-store' in response['Cache-Control']
    assert TOTPDevice.objects.filter(user=staff, confirmed=False).count() == 1
    assert not TOTPDevice.objects.filter(user=staff, confirmed=True).exists()
    second = client.post(QR, {'username': staff.username, 'password': 'a-long-strong-password-123'})
    assert second.status_code == 200
    assert TOTPDevice.objects.filter(user=staff).count() == 1


@pytest.mark.django_db
def test_enrolment_invalid_code_stays_pending(client, staff):
    client.post(QR, {'username': staff.username, 'password': 'a-long-strong-password-123'})
    device = TOTPDevice.objects.get(user=staff)
    response = client.post(VERIFY, {
        'username': staff.username, 'password': 'a-long-strong-password-123',
        'token': 'nope',
    })
    assert response.status_code == 400
    device.refresh_from_db()
    assert not device.confirmed
    assert 'otp_device_id' not in client.session


@pytest.mark.django_db
def test_valid_enrolment_verifies_session_and_admin_access(client, staff):
    client.post(QR, {'username': staff.username, 'password': 'a-long-strong-password-123'})
    device = TOTPDevice.objects.get(user=staff)
    response = client.post(VERIFY, {
        'username': staff.username, 'password': 'a-long-strong-password-123',
        'token': otp_for(device),
    })
    assert response.status_code == 200, response.content
    device.refresh_from_db()
    assert device.confirmed
    assert client.session['otp_device_id'] == device.persistent_id
    assert client.get('/tus-gestion-secure/').status_code == 200


@pytest.mark.django_db
def test_password_does_not_reveal_confirmed_secret(client, staff):
    device = TOTPDevice.objects.create(user=staff, confirmed=True)
    response = client.post(QR, {
        'username': staff.username, 'password': 'a-long-strong-password-123',
    })
    assert response.status_code == 409
    assert device.key.encode() not in response.content
    assert TOTPDevice.objects.filter(user=staff).count() == 1
    attempt = client.post(VERIFY, {
        'username': staff.username, 'password': 'a-long-strong-password-123',
        'token': otp_for(device),
    })
    assert attempt.status_code == 409
    assert 'otp_device_id' not in client.session


@pytest.mark.django_db
def test_wrong_password_and_nonstaff_cannot_enrol(client, staff):
    assert client.post(QR, {'username': staff.username, 'password': 'bad'}).status_code == 403
    unprivileged = User.objects.create_user(username='ordinary', password='correct-password-123')
    assert client.post(QR, {
        'username': unprivileged.username, 'password': 'correct-password-123',
    }).status_code == 403
    assert not TOTPDevice.objects.exists()


@pytest.mark.django_db
def test_explicit_console_recovery_creates_only_pending_factor(staff, capsys):
    previous = TOTPDevice.objects.create(user=staff, confirmed=True)
    old_pk = previous.pk
    call_command('setup_totp', staff.username)
    assert TOTPDevice.objects.filter(pk=old_pk).exists()
    call_command('setup_totp', staff.username, '--reset')
    assert not TOTPDevice.objects.filter(pk=old_pk).exists()
    pending = TOTPDevice.objects.get(user=staff)
    assert not pending.confirmed
    output = capsys.readouterr().out
    assert previous.key not in output
    assert 'otpauth://' not in output
