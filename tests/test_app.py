"""
Test suite for YouTube Management System
"""
import pytest
import tempfile
import os
from app import create_app
from database.migrations import init_database

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    app, _ = create_app('testing')
    app.config['DATABASE_PATH'] = db_path
    app.config['TESTING'] = True
    
    with app.app_context():
        init_database(db_path)
    
    yield app
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

class TestDashboard:
    """Test dashboard functionality"""
    
    def test_dashboard_loads(self, client):
        """Test that dashboard loads successfully"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Dashboard' in response.data
    
    def test_dashboard_stats(self, client):
        """Test dashboard statistics"""
        response = client.get('/')
        assert response.status_code == 200
        # Should show 0 stats for empty database
        assert b'0' in response.data

class TestYouTubers:
    """Test YouTuber management"""
    
    def test_youtubers_page_loads(self, client):
        """Test YouTubers page loads"""
        response = client.get('/youtubers')
        assert response.status_code == 200
        assert b'YouTubers' in response.data
    
    def test_add_youtuber_valid_data(self, client):
        """Test adding a YouTuber with valid data"""
        response = client.post('/youtubers', data={
            'action': 'add',
            'name': 'Test YouTuber',
            'channel_link': 'https://youtube.com/test',
            'niche': 'Technology',
            'contact': 'test@example.com',
            'notes': 'Test notes'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Test YouTuber' in response.data
    
    def test_add_youtuber_invalid_data(self, client):
        """Test adding a YouTuber with invalid data"""
        response = client.post('/youtubers', data={
            'action': 'add',
            'name': '',  # Empty name should fail
            'channel_link': 'invalid-url',
            'contact': 'invalid-email'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show error message
        assert b'error' in response.data.lower() or b'required' in response.data.lower()
    
    def test_search_youtubers(self, client):
        """Test searching YouTubers"""
        # First add a YouTuber
        client.post('/youtubers', data={
            'action': 'add',
            'name': 'Searchable YouTuber',
            'niche': 'Gaming'
        })
        
        # Search for it
        response = client.get('/youtubers?search=Searchable')
        assert response.status_code == 200
        assert b'Searchable YouTuber' in response.data

class TestVideos:
    """Test video management"""
    
    def test_videos_page_loads(self, client):
        """Test videos page loads"""
        response = client.get('/videos')
        assert response.status_code == 200
        assert b'Videos' in response.data or b'videos' in response.data
    
    def test_add_video_requires_youtuber(self, client):
        """Test that adding video requires existing YouTuber"""
        # First add a YouTuber
        client.post('/youtubers', data={
            'action': 'add',
            'name': 'Video Creator'
        })
        
        # Then add a video
        response = client.post('/videos', data={
            'action': 'add',
            'title': 'Test Video',
            'youtuber_id': '1',
            'amount': '100.00',
            'payment_status': 'pending'
        }, follow_redirects=True)
        
        assert response.status_code == 200

class TestPayments:
    """Test payment functionality"""
    
    def test_payments_page_loads(self, client):
        """Test payments page loads"""
        response = client.get('/payments')
        assert response.status_code == 200
        assert b'Payment' in response.data or b'payment' in response.data

class TestExport:
    """Test export functionality"""
    
    def test_export_youtubers_csv(self, client):
        """Test exporting YouTubers as CSV"""
        response = client.get('/export?type=youtubers')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'
    
    def test_export_all_excel(self, client):
        """Test exporting all data as Excel"""
        response = client.get('/export?type=all')
        assert response.status_code == 200
        assert 'excel' in response.headers['Content-Type'] or 'spreadsheet' in response.headers['Content-Type']

class TestAPI:
    """Test API endpoints"""
    
    def test_dashboard_api(self, client):
        """Test dashboard API endpoint"""
        response = client.get('/api/dashboard-data')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'payment_distribution' in data
        assert 'monthly_trends' in data

class TestValidation:
    """Test input validation"""
    
    def test_email_validation(self):
        """Test email validation"""
        from utils.validators import validate_email, ValidationError
        
        # Valid emails
        assert validate_email('test@example.com') == 'test@example.com'
        assert validate_email('  test@example.com  ') == 'test@example.com'
        assert validate_email('') is None
        
        # Invalid emails
        with pytest.raises(ValidationError):
            validate_email('invalid-email')
        
        with pytest.raises(ValidationError):
            validate_email('test@')
    
    def test_url_validation(self):
        """Test URL validation"""
        from utils.validators import validate_url, ValidationError
        
        # Valid URLs
        assert validate_url('https://example.com') == 'https://example.com'
        assert validate_url('http://test.com/path') == 'http://test.com/path'
        assert validate_url('') is None
        
        # Invalid URLs
        with pytest.raises(ValidationError):
            validate_url('not-a-url')
        
        with pytest.raises(ValidationError):
            validate_url('ftp://invalid')
    
    def test_amount_validation(self):
        """Test amount validation"""
        from utils.validators import validate_amount, ValidationError
        
        # Valid amounts
        assert validate_amount('100.50') == 100.50
        assert validate_amount('0') == 0.0
        assert validate_amount('') == 0.0
        
        # Invalid amounts
        with pytest.raises(ValidationError):
            validate_amount('-10')
        
        with pytest.raises(ValidationError):
            validate_amount('not-a-number')

if __name__ == '__main__':
    pytest.main([__file__])
