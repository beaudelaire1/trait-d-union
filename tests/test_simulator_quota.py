"""Tests for simulator quota tracking."""
from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.contrib.auth.models import User
from apps.pages.models import SimulatorQuotaUsage
from apps.pages.views import simulateur_increment
import json


class SimulatorQuotaTrackingTestCase(TestCase):
    """Test IP+User-Agent based quota tracking."""
    
    def setUp(self):
        """Set up test client and factory."""
        self.client = Client()
        self.factory = RequestFactory()
        # Create an authenticated user for testing
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_simulator_quota_model_creation(self):
        """Test SimulatorQuotaUsage model can be created."""
        quota = SimulatorQuotaUsage.objects.create(
            ip_address='192.168.1.1',
            user_agent='TestBrowser/1.0',
            user_agent_hash='abc123def456',
            generation_count=1
        )
        self.assertEqual(quota.generation_count, 1)
        self.assertEqual(quota.ip_address, '192.168.1.1')
        self.assertFalse(quota.is_quota_exceeded(quota=5, window_hours=24))
    
    def test_quota_exceeded_check(self):
        """Test is_quota_exceeded method."""
        quota = SimulatorQuotaUsage.objects.create(
            ip_address='192.168.1.1',
            user_agent='TestBrowser/1.0',
            user_agent_hash='abc123def456',
            generation_count=5  # Exactly at limit
        )
        # Should be exceeded if last_generation is recent
        self.assertTrue(quota.is_quota_exceeded(quota=5, window_hours=24))
        
        # Should not be exceeded if limit is higher
        self.assertFalse(quota.is_quota_exceeded(quota=6, window_hours=24))
    
    def test_increment_and_save(self):
        """Test increment_and_save method."""
        quota = SimulatorQuotaUsage.objects.create(
            ip_address='192.168.1.1',
            user_agent='TestBrowser/1.0',
            user_agent_hash='abc123def456',
            generation_count=2
        )
        quota.increment_and_save()
        quota.refresh_from_db()
        self.assertEqual(quota.generation_count, 3)
    
    def test_get_or_create_for_request(self):
        """Test get_or_create_for_request method."""
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'TestBrowser/1.0'
        
        quota = SimulatorQuotaUsage.get_or_create_for_request(request)
        self.assertEqual(quota.ip_address, '192.168.1.1')
        self.assertEqual(quota.user_agent, 'TestBrowser/1.0')
        
        # Second call should return same object
        quota2 = SimulatorQuotaUsage.get_or_create_for_request(request)
        self.assertEqual(quota.id, quota2.id)
    
    def test_get_client_ip_with_x_forwarded_for(self):
        """Test IP extraction with X-Forwarded-For header."""
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.1, 198.51.100.1'
        
        ip = SimulatorQuotaUsage.get_client_ip(request)
        self.assertEqual(ip, '203.0.113.1')  # Should use first IP
    
    def test_get_client_ip_without_x_forwarded_for(self):
        """Test IP extraction from REMOTE_ADDR."""
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        ip = SimulatorQuotaUsage.get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')
    
    def test_authenticated_user_no_quota(self):
        """Test that authenticated users are not rate-limited."""
        # Login the user
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(
            '/simulateur/increment/',
            content_type='application/json'
        )
        data = json.loads(response.content)
        # For authenticated users, remaining should be -1 (no limit)
        self.assertEqual(data['remaining'], -1)
        self.assertTrue(data['allowed'])
