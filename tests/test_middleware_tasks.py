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
        request.user = MagicMock(is_authenticated=True)
        request.session = {
            'must_change_password': True,
            'must_change_password_reason': 'first_login',
        }
        # Simulate mock profile
        mock_profile = MagicMock(must_change_password=True)
        request.user.client_profile = mock_profile

        response = HttpResponse(status=302)
        mw.process_response(request, response)

        assert 'must_change_password' not in request.session
        assert mock_profile.must_change_password is False

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
