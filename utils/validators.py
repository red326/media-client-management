"""
Input validation and sanitization utilities
"""
import re
from urllib.parse import urlparse
from datetime import datetime
import bleach

class ValidationError(Exception):
    """Custom validation error"""
    pass

def validate_required(value, field_name):
    """Validate required field"""
    if not value or not value.strip():
        raise ValidationError(f"{field_name} is required")
    return value.strip()

def validate_email(email):
    """Validate email format"""
    if not email:
        return None
    
    email = email.strip()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError("Invalid email format")
    return email

def validate_url(url):
    """Validate URL format"""
    if not url:
        return None
    
    url = url.strip()
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValidationError("Invalid URL format")
        return url
    except Exception:
        raise ValidationError("Invalid URL format")

def validate_youtube_url(url):
    """Validate YouTube URL specifically"""
    if not url:
        return None
    
    url = validate_url(url)
    youtube_patterns = [
        r'youtube\.com',
        r'youtu\.be',
        r'youtube-nocookie\.com'
    ]
    
    if not any(re.search(pattern, url, re.IGNORECASE) for pattern in youtube_patterns):
        raise ValidationError("Must be a valid YouTube URL")
    
    return url

def validate_amount(amount):
    """Validate monetary amount"""
    if not amount:
        return 0.0
    
    try:
        amount = float(amount)
        if amount < 0:
            raise ValidationError("Amount cannot be negative")
        if amount > 999999.99:
            raise ValidationError("Amount too large")
        return round(amount, 2)
    except (ValueError, TypeError):
        raise ValidationError("Invalid amount format")

def validate_date(date_str):
    """Validate date format"""
    if not date_str:
        return None
    
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValidationError("Invalid date format (YYYY-MM-DD required)")

def sanitize_text(text, max_length=None):
    """Sanitize text input"""
    if not text:
        return ""
    
    # Remove HTML tags and clean text
    clean_text = bleach.clean(text.strip(), tags=[], strip=True)
    
    if max_length and len(clean_text) > max_length:
        raise ValidationError(f"Text too long (max {max_length} characters)")
    
    return clean_text

def validate_payment_status(status):
    """Validate payment status"""
    valid_statuses = ['pending', 'paid', 'cancelled']
    if status not in valid_statuses:
        raise ValidationError(f"Invalid payment status. Must be one of: {', '.join(valid_statuses)}")
    return status

def validate_youtuber_data(data):
    """Validate YouTuber form data"""
    validated = {}
    
    # Required fields
    validated['name'] = validate_required(data.get('name'), 'Name')
    validated['name'] = sanitize_text(validated['name'], 100)
    
    # Optional fields
    validated['channel_link'] = validate_youtube_url(data.get('channel_link'))
    validated['niche'] = sanitize_text(data.get('niche', ''), 50)
    validated['contact'] = validate_email(data.get('contact')) if data.get('contact') else None
    validated['notes'] = sanitize_text(data.get('notes', ''), 500)
    
    return validated

def validate_video_data(data):
    """Validate video form data"""
    validated = {}
    
    # Required fields
    validated['title'] = validate_required(data.get('title'), 'Title')
    validated['title'] = sanitize_text(validated['title'], 200)
    
    validated['youtuber_id'] = int(data.get('youtuber_id'))
    if validated['youtuber_id'] <= 0:
        raise ValidationError("Invalid YouTuber selection")
    
    # Optional fields
    validated['date_uploaded'] = validate_date(data.get('date_uploaded'))
    validated['payment_status'] = validate_payment_status(data.get('payment_status', 'pending'))
    validated['amount'] = validate_amount(data.get('amount', 0))
    validated['video_link'] = validate_youtube_url(data.get('video_link'))
    validated['description'] = sanitize_text(data.get('description', ''), 1000)
    
    return validated
