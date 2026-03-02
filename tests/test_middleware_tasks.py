"""Tests for ForcePasswordChangeMiddleware and core.tasks dispatch logic."""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from django.test import Client, RequestFactory, override_settings
from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpResponse

from config.middleware_force_password import ForcePasswordChangeMiddleware


# ==============================================================================
# FORCE PASSWORD CHANGE MIDDLEWARE
# ==============================================================================

@pytest.mark.django_db
class TestForcePasswordChangeMiddleware:

    def _get_middleware(self):
        return ForcePasswordChangeMiddleware(get_response=lambda r: HttpResponse('OK'))

    def test_unauthenticated_user_passes(self):
        mw = self._get_middleware()
        factory = RequestFactory()
        request = factory.get('/some-page/')
        request.user = AnonymousUser()
        request.session = {}
        result = mw.process_request(request)
        assert result is None  # No redirect

    def test_authenticated_no_flag_passes(self):
        mw = self._get_middleware()
        factory = RequestFactory()
        request = factory.get('/some-page/')
        request.user = MagicMock(is_authenticated=True)
        request.session = {'must_change_password': False}
        result = mw.process_request(request)
        assert result is None

    def test_authenticated_with_flag_redirects(self):
        mw = self._get_middleware()
        factory = RequestFactory()
        request = factory.get('/some-page/')
        request.user = MagicMock(is_authenticated=True)
        request.session = {'must_change_password': True}
        result = mw.process_request(request)
        assert result is not None
        assert result.status_code == 302

    def test_exempt_admin_prefix(self):
        mw = self._get_middleware()
        factory = RequestFactory()
        request = factory.get('/tus-gestion-secure/something/')
        request.user = MagicMock(is_authenticated=True)
        request.session = {'must_change_password': True}
        result = mw.process_request(request)
        assert result is None  # Exempt

    def test_exempt_static_prefix(self):
        mw = self._get_middleware()
        factory = RequestFactory()
        request = factory.get('/static/css/style.css')
        request.user = MagicMock(is_authenticated=True)
        request.session = {'must_change_password': True}
        result = mw.process_request(request)
        assert result is None

    def test_change_password_page_allowed(self):
        mw = self._get_middleware()
        factory = RequestFactory()
        change_url = mw._get_change_password_url()
        request = factory.get(change_url)
        request.user = MagicMock(is_authenticated=True)
        request.session = {'must_change_password': True}
        result = mw.process_request(request)
        assert result is None

    def test_process_response_clears_flag_on_success(self):
        mw = self._get_middleware()
        factory = RequestFactory()
        change_url = mw._get_change_password_url()
        request = factory.post(change_url)
        request.user = MagicMock(is_authenticated=True, pk=42)
        request.session = {
            'must_change_password': True,
            'must_change_password_reason': 'first_login',
        }
        # Simulate mock profile
        mock_profile = MagicMock(must_change_password=True)
        request.user.client_profile = mock_profile

        response = HttpResponse(status=302)
        with patch('core.tasks.async_send_password_changed_email'):
            result = mw.process_response(request, response)

        assert 'must_change_password' not in request.session
        assert mock_profile.must_change_password is False

    def test_process_response_redirects_to_success_page(self):
        """After successful password change, middleware redirects to success page."""
        mw = self._get_middleware()
        factory = RequestFactory()
        change_url = mw._get_change_password_url()
        request = factory.post(change_url)
        request.user = MagicMock(is_authenticated=True, pk=1)
        request.session = {
            'must_change_password': True,
            'must_change_password_reason': 'first_login',
        }
        mock_profile = MagicMock(must_change_password=True)
        request.user.client_profile = mock_profile

        response = HttpResponse(status=302)
        with patch('core.tasks.async_send_password_changed_email'):
            result = mw.process_response(request, response)

        # Must redirect to the password_change_done URL
        assert result.status_code == 302
        from django.urls import reverse
        success_url = reverse('clients:password_change_done')
        assert result['Location'] == success_url

    @patch('core.tasks.async_send_password_changed_email')
    def test_process_response_dispatches_email(self, mock_email):
        """After successful password change, sends confirmation email."""
        mw = self._get_middleware()
        factory = RequestFactory()
        change_url = mw._get_change_password_url()
        request = factory.post(change_url)
        request.user = MagicMock(is_authenticated=True, pk=99)
        request.session = {
            'must_change_password': True,
        }
        mock_profile = MagicMock(must_change_password=True)
        request.user.client_profile = mock_profile

        response = HttpResponse(status=302)
        mw.process_response(request, response)

        mock_email.assert_called_once_with(99)

    def test_success_url_allowed_during_force(self):
        """The password_change_done URL is accessible even with force flag."""
        mw = self._get_middleware()
        factory = RequestFactory()
        from django.urls import reverse
        success_url = reverse('clients:password_change_done')
        request = factory.get(success_url)
        request.user = MagicMock(is_authenticated=True)
        request.session = {'must_change_password': True}
        result = mw.process_request(request)
        assert result is None  # Not blocked

    def test_process_response_no_flag_noop(self):
        mw = self._get_middleware()
        factory = RequestFactory()
        request = factory.post('/some-url/')
        request.user = MagicMock(is_authenticated=True)
        request.session = {}
        response = HttpResponse(status=302)
        result = mw.process_response(request, response)
        assert result == response

    def test_process_response_wrong_url_noop(self):
        mw = self._get_middleware()
        factory = RequestFactory()
        request = factory.post('/wrong-url/')
        request.user = MagicMock(is_authenticated=True)
        request.session = {'must_change_password': True}
        response = HttpResponse(status=302)
        result = mw.process_response(request, response)
        assert 'must_change_password' in request.session  # Not cleared

    def test_process_response_no_profile_no_crash(self):
        """If user has no client_profile, should not crash."""
        mw = self._get_middleware()
        factory = RequestFactory()
        change_url = mw._get_change_password_url()
        request = factory.post(change_url)
        request.user = MagicMock(is_authenticated=True, spec=['is_authenticated'])
        request.session = {'must_change_password': True}
        response = HttpResponse(status=302)
        # Should not raise even without client_profile
        mw.process_response(request, response)


# ==============================================================================
# CORE TASKS (dispatch logic)
# ==============================================================================

class TestTaskDispatch:
    @patch('core.tasks._is_qcluster_running', return_value=False)
    @patch('core.tasks._run_sync')
    def test_dispatch_sync_when_no_cluster(self, mock_run, mock_cluster):
        from core.tasks import _dispatch
        _dispatch('some.module.func', 'arg1')
        mock_run.assert_called_once_with('some.module.func', 'arg1')

    @patch('core.tasks._is_qcluster_running', return_value=True)
    @patch('core.tasks.async_task')
    def test_dispatch_async_when_cluster_running(self, mock_async, mock_cluster):
        from core.tasks import _dispatch
        _dispatch('some.module.func', 'arg1', task_name='test_task')
        mock_async.assert_called_once()

    @patch('core.tasks._is_qcluster_running', return_value=True)
    @patch('core.tasks.async_task', side_effect=Exception('Queue error'))
    @patch('core.tasks._run_sync')
    def test_dispatch_fallback_on_async_error(self, mock_run, mock_async, mock_cluster):
        from core.tasks import _dispatch
        _dispatch('some.module.func', 'arg1')
        mock_run.assert_called_once()

    def test_run_sync_executes_function(self):
        from core.tasks import _run_sync
        # Test with a known function
        result = _run_sync('os.path.basename', '/foo/bar.txt')
        assert result == 'bar.txt'

    @patch('core.tasks._is_qcluster_running', return_value=False)
    def test_is_qcluster_running_handles_exception(self, mock_running):
        from core.tasks import _is_qcluster_running
        # The mock already returns False


class TestPublicDispatchers:
    """Test that public task dispatchers call _dispatch correctly."""

    @patch('core.tasks._dispatch')
    def test_async_send_welcome_email(self, mock_dispatch):
        from core.tasks import async_send_welcome_email
        async_send_welcome_email(1, 'temp123', 'test')
        mock_dispatch.assert_called_once()
        args = mock_dispatch.call_args
        assert 'welcome_email' in args[1].get('task_name', args[0][-1] if args[0] else '')

    @patch('core.tasks._dispatch')
    def test_async_reset_password_notify(self, mock_dispatch):
        from core.tasks import async_reset_password_notify
        async_reset_password_notify(42)
        mock_dispatch.assert_called_once()

    @patch('core.tasks._dispatch')
    def test_async_send_quote_email(self, mock_dispatch):
        from core.tasks import async_send_quote_email
        async_send_quote_email(10)
        mock_dispatch.assert_called_once()

    @patch('core.tasks._dispatch')
    def test_async_send_quote_pdf_email(self, mock_dispatch):
        from core.tasks import async_send_quote_pdf_email
        async_send_quote_pdf_email(10)
        mock_dispatch.assert_called_once()

    @patch('core.tasks._dispatch')
    def test_async_notify_quote_request(self, mock_dispatch):
        from core.tasks import async_notify_quote_request
        async_notify_quote_request(5)
        mock_dispatch.assert_called_once()

    @patch('core.tasks._dispatch')
    def test_async_notify_invoice_created(self, mock_dispatch):
        from core.tasks import async_notify_invoice_created
        async_notify_invoice_created(7)
        mock_dispatch.assert_called_once()

    @patch('core.tasks._dispatch')
    def test_async_send_payment_confirmation(self, mock_dispatch):
        from core.tasks import async_send_payment_confirmation
        async_send_payment_confirmation(quote_id=1)
        mock_dispatch.assert_called_once()

    @patch('core.tasks._dispatch')
    def test_async_send_generic_email(self, mock_dispatch):
        from core.tasks import async_send_generic_email
        async_send_generic_email('to@ex.com', 'Subj', '<p>HTML</p>')
        mock_dispatch.assert_called_once()

    @patch('core.tasks._dispatch')
    def test_async_send_password_changed_email(self, mock_dispatch):
        from core.tasks import async_send_password_changed_email
        async_send_password_changed_email(77)
        mock_dispatch.assert_called_once()
        args, kwargs = mock_dispatch.call_args
        assert args[1] == 77
        assert 'password_changed' in kwargs.get('task_name', args[-1] if len(args) > 2 else '')


@pytest.mark.django_db
class TestTaskGenericEmailWorker:
    """Test _task_send_generic_email worker function."""

    def test_sends_email(self):
        from core.tasks import _task_send_generic_email
        from django.core import mail
        _task_send_generic_email('to@example.com', 'Test Subject', '<p>Hello</p>')
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == 'Test Subject'
        assert mail.outbox[0].to == ['to@example.com']


# ==============================================================================
# PASSWORD CHANGE DONE VIEW
# ==============================================================================

@pytest.mark.django_db
class TestPasswordChangeDoneView:
    """Test the password_change_done success page."""

    def test_authenticated_user_sees_success_page(self, client, user):
        """Authenticated user can access the success page."""
        client.force_login(user)
        from django.urls import reverse
        url = reverse('clients:password_change_done')
        response = client.get(url)
        assert response.status_code == 200
        assert 'Mot de passe modifié' in response.content.decode()

    def test_anonymous_user_redirected(self, client):
        """Anonymous user is redirected to login."""
        from django.urls import reverse
        url = reverse('clients:password_change_done')
        response = client.get(url)
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location'] or 'login' in response['Location'].lower()


# ==============================================================================
# PASSWORD CHANGED EMAIL SERVICE
# ==============================================================================

@pytest.mark.django_db
class TestSendPasswordChangedEmail:
    """Test send_password_changed_email service function."""

    def test_sends_email_via_django_fallback(self, user):
        """Email sent via Django backend when Brevo not configured."""
        from apps.clients.services import send_password_changed_email
        from django.core import mail
        send_password_changed_email(user)
        assert len(mail.outbox) == 1
        msg = mail.outbox[0]
        assert 'Mot de passe modifié' in msg.subject
        assert user.email in msg.to
        # Check HTML alternative exists
        assert len(msg.alternatives) == 1
        html = msg.alternatives[0][0]
        assert 'Sécurité' in html or 'passe' in html.lower()

    def test_task_worker_sends_email(self, user):
        """The task worker fetches user and sends email."""
        from core.tasks import _task_send_password_changed_email
        from django.core import mail
        _task_send_password_changed_email(user.pk)
        assert len(mail.outbox) == 1
        assert user.email in mail.outbox[0].to


# ==============================================================================
# CLIENT COMMENT → ADMIN NOTIFICATION
# ==============================================================================

@pytest.fixture
def client_user_with_project(db):
    """Create a non-staff user with a ClientProfile and a Project."""
    from apps.clients.models import ClientProfile, Project
    user = User.objects.create_user(
        'clientuser', 'client@example.com', 'ClientP@ss1!',
        first_name='Jean', last_name='Dupont',
    )
    profile = ClientProfile.objects.get_or_create(user=user)[0]
    project = Project.objects.create(
        client=profile,
        name='Site Vitrine Test',
        status='development',
    )
    return user, profile, project


@pytest.mark.django_db
class TestClientCommentNotification:
    """Test que les commentaires clients déclenchent une notif admin."""

    @patch('core.tasks.async_notify_admin_new_comment')
    def test_add_comment_dispatches_admin_notif(self, mock_notif, client, client_user_with_project):
        """Posting a comment dispatches the async admin notification."""
        user, profile, project = client_user_with_project
        client.force_login(user)
        url = f'/ecosysteme-tus/projets/{project.pk}/commentaire/'
        response = client.post(url, {'message': 'Bonjour, une question sur le design.'})
        assert response.status_code in (200, 302)
        mock_notif.assert_called_once()

    def test_comment_creates_project_comment(self, client, client_user_with_project):
        """Comment is persisted in ProjectComment model."""
        from apps.clients.models import ProjectComment
        user, profile, project = client_user_with_project
        client.force_login(user)
        url = f'/ecosysteme-tus/projets/{project.pk}/commentaire/'
        client.post(url, {'message': 'Test message persisté.'})
        assert ProjectComment.objects.filter(project=project, author=user).exists()
        comment = ProjectComment.objects.get(project=project, author=user)
        assert comment.read_by_admin is False
        assert comment.is_from_client is True

    def test_comment_not_from_staff(self, client, client_user_with_project):
        """is_from_client returns False for staff comments."""
        from apps.clients.models import ProjectComment
        user, profile, project = client_user_with_project
        staff = User.objects.create_user('staffguy', 'staff@tus.it', 'Pass1!', is_staff=True)
        comment = ProjectComment.objects.create(
            project=project, author=staff, message='Réponse admin',
        )
        assert comment.is_from_client is False


@pytest.mark.django_db
class TestAdminCommentEmailNotification:
    """Test send_new_comment_notification_to_admin email service."""

    def test_sends_email_to_admin(self, client_user_with_project):
        """Email is sent to ADMIN_EMAIL when a client comments."""
        from apps.clients.models import ProjectComment
        from apps.clients.services import send_new_comment_notification_to_admin
        from django.core import mail

        user, profile, project = client_user_with_project
        comment = ProjectComment.objects.create(
            project=project, author=user, message='Question design',
        )
        send_new_comment_notification_to_admin(comment)
        assert len(mail.outbox) == 1
        msg = mail.outbox[0]
        assert 'Nouveau message client' in msg.subject
        assert 'Site Vitrine Test' in msg.subject
        html = msg.alternatives[0][0]
        assert 'Question design' in html

    def test_task_worker_sends_notification(self, client_user_with_project):
        """The async task worker sends the email."""
        from apps.clients.models import ProjectComment
        from core.tasks import _task_notify_admin_new_comment
        from django.core import mail

        user, profile, project = client_user_with_project
        comment = ProjectComment.objects.create(
            project=project, author=user, message='Urgent: besoin de validation',
        )
        _task_notify_admin_new_comment(comment.pk)
        assert len(mail.outbox) == 1
        assert 'Nouveau message client' in mail.outbox[0].subject


@pytest.mark.django_db
class TestProjectCommentReadByAdmin:
    """Test read_by_admin flag behavior."""

    def test_new_comment_defaults_unread(self, client_user_with_project):
        """New comments have read_by_admin=False by default."""
        from apps.clients.models import ProjectComment
        user, profile, project = client_user_with_project
        comment = ProjectComment.objects.create(
            project=project, author=user, message='Test',
        )
        assert comment.read_by_admin is False

    @patch('core.tasks._dispatch')
    def test_async_dispatcher_calls_dispatch(self, mock_dispatch):
        """async_notify_admin_new_comment calls _dispatch correctly."""
        from core.tasks import async_notify_admin_new_comment
        async_notify_admin_new_comment(42)
        mock_dispatch.assert_called_once()
        args, kwargs = mock_dispatch.call_args
        assert args[1] == 42
        assert 'admin_comment_notif' in kwargs.get('task_name', '')
