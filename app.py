from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, flash
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sqlite3
import os
from datetime import datetime
import csv
import json
from io import StringIO, BytesIO
# import pandas as pd  # Temporarily disabled for Python 3.13 compatibility
from dotenv import load_dotenv

# Import our custom modules
from config import config
from utils.logger import setup_logging, log_error, log_activity
from utils.validators import validate_youtuber_data, validate_video_data, ValidationError
from database.migrations import init_database

# Load environment variables
load_dotenv()

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    CORS(app)
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    limiter.init_app(app)
    
    # Setup logging
    setup_logging(app)
    
    # Initialize database (using simple initialization for now)
    # init_database(app.config['DATABASE_PATH'])  # Temporarily disabled
    from init_db_simple import init_simple_db
    init_simple_db()
    
    return app, limiter

app, limiter = create_app()

# Database configuration
DATABASE = app.config.get('DATABASE_PATH', 'database/data.db')

# Error handling decorator
def handle_errors(f):
    """Decorator to handle errors gracefully"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            flash(f'Validation Error: {str(e)}', 'error')
            log_error(e, f'Validation error in {f.__name__}')
            return redirect(request.referrer or url_for('dashboard'))
        except sqlite3.Error as e:
            flash('Database error occurred. Please try again.', 'error')
            log_error(e, f'Database error in {f.__name__}')
            return redirect(request.referrer or url_for('dashboard'))
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'error')
            log_error(e, f'Unexpected error in {f.__name__}')
            return redirect(request.referrer or url_for('dashboard'))
    
    return decorated_function

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_dashboard_stats():
    """Get dashboard statistics"""
    conn = get_db_connection()
    
    total_youtubers = conn.execute('SELECT COUNT(*) FROM youtubers').fetchone()[0]
    total_videos = conn.execute('SELECT COUNT(*) FROM videos').fetchone()[0]
    
    paid_amount = conn.execute('SELECT COALESCE(SUM(amount), 0) FROM videos WHERE payment_status = "paid"').fetchone()[0]
    pending_amount = conn.execute('SELECT COALESCE(SUM(amount), 0) FROM videos WHERE payment_status = "pending"').fetchone()[0]
    
    conn.close()
    
    return {
        'total_youtubers': total_youtubers,
        'total_videos': total_videos,
        'total_paid': paid_amount,
        'pending_payments': pending_amount,
        'total_amount': paid_amount + pending_amount
    }

@app.route('/')
@handle_errors
def dashboard():
    """Dashboard overview"""
    log_activity('Dashboard accessed')
    
    stats = get_dashboard_stats()
    
    # Get recent videos for dashboard
    conn = get_db_connection()
    try:
        recent_videos = conn.execute('''
            SELECT v.*, y.name as youtuber_name 
            FROM videos v 
            JOIN youtubers y ON v.youtuber_id = y.id 
            ORDER BY v.created_at DESC 
            LIMIT 5
        ''').fetchall()
        
        # Get payment status distribution
        payment_stats = conn.execute('''
            SELECT payment_status, COUNT(*) as count, COALESCE(SUM(amount), 0) as total
            FROM videos 
            GROUP BY payment_status
        ''').fetchall()
        
    finally:
        conn.close()
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         recent_videos=recent_videos,
                         payment_stats=payment_stats)

@app.route('/youtubers', methods=['GET', 'POST'])
@handle_errors
@limiter.limit("30 per minute")
def youtubers():
    """Manage YouTubers"""
    conn = get_db_connection()
    
    try:
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'add':
                # Validate input data
                validated_data = validate_youtuber_data(request.form)
                
                conn.execute('''
                    INSERT INTO youtubers (name, channel_link, niche, contact, notes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (validated_data['name'], validated_data['channel_link'], 
                      validated_data['niche'], validated_data['contact'], 
                      validated_data['notes']))
                conn.commit()
                
                flash(f'YouTuber "{validated_data["name"]}" added successfully!', 'success')
                log_activity('YouTuber added', {'name': validated_data['name']})
                
            elif action == 'edit':
                youtuber_id = int(request.form['id'])
                validated_data = validate_youtuber_data(request.form)
                
                conn.execute('''
                    UPDATE youtubers 
                    SET name=?, channel_link=?, niche=?, contact=?, notes=?
                    WHERE id=?
                ''', (validated_data['name'], validated_data['channel_link'], 
                      validated_data['niche'], validated_data['contact'], 
                      validated_data['notes'], youtuber_id))
                conn.commit()
                
                flash(f'YouTuber "{validated_data["name"]}" updated successfully!', 'success')
                log_activity('YouTuber updated', {'id': youtuber_id, 'name': validated_data['name']})
                
            elif action == 'delete':
                youtuber_id = int(request.form['id'])
                
                # Check if YouTuber has videos
                video_count = conn.execute('SELECT COUNT(*) FROM videos WHERE youtuber_id = ?', (youtuber_id,)).fetchone()[0]
                if video_count > 0:
                    flash(f'Cannot delete YouTuber: {video_count} videos are associated with this YouTuber.', 'error')
                else:
                    youtuber_name = conn.execute('SELECT name FROM youtubers WHERE id = ?', (youtuber_id,)).fetchone()[0]
                    conn.execute('DELETE FROM youtubers WHERE id=?', (youtuber_id,))
                    conn.commit()
                    
                    flash(f'YouTuber "{youtuber_name}" deleted successfully!', 'success')
                    log_activity('YouTuber deleted', {'id': youtuber_id, 'name': youtuber_name})
            
            return redirect(url_for('youtubers'))
        
        # GET request - display YouTubers list
        search = request.args.get('search', '')
        niche_filter = request.args.get('niche', '')
        
        query = '''
            SELECT y.*, 
                   COUNT(v.id) as video_count,
                   COALESCE(SUM(CASE WHEN v.payment_status = 'paid' THEN v.amount ELSE 0 END), 0) as total_paid,
                   COALESCE(SUM(CASE WHEN v.payment_status = 'pending' THEN v.amount ELSE 0 END), 0) as total_pending
            FROM youtubers y
            LEFT JOIN videos v ON y.id = v.youtuber_id
            WHERE 1=1
        '''
        params = []
        
        if search:
            query += ' AND y.name LIKE ?'
            params.append(f'%{search}%')
        
        if niche_filter:
            query += ' AND y.niche = ?'
            params.append(niche_filter)
        
        query += ' GROUP BY y.id ORDER BY y.name'
        
        youtubers_list = conn.execute(query, params).fetchall()
        
        # Get unique niches for filter
        niches = conn.execute('SELECT DISTINCT niche FROM youtubers WHERE niche IS NOT NULL AND niche != ""').fetchall()
        
        return render_template('youtubers.html', 
                             youtubers=youtubers_list, 
                             niches=niches,
                             search=search,
                             niche_filter=niche_filter)
    
    finally:
        conn.close()

@app.route('/videos', methods=['GET', 'POST'])
@handle_errors
@limiter.limit("30 per minute")
def videos():
    """Manage Videos"""
    conn = get_db_connection()
    
    try:
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'add':
                # Validate input data
                validated_data = validate_video_data(request.form)
                
                conn.execute('''
                    INSERT INTO videos (title, youtuber_id, date_uploaded, payment_status, amount, video_link, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (validated_data['title'], validated_data['youtuber_id'], 
                      validated_data['date_uploaded'], validated_data['payment_status'], 
                      validated_data['amount'], validated_data['video_link'], 
                      validated_data['description']))
                conn.commit()
                
                flash(f'Video "{validated_data["title"]}" added successfully!', 'success')
                log_activity('Video added', {'title': validated_data['title'], 'youtuber_id': validated_data['youtuber_id']})
                
            elif action == 'edit':
                video_id = int(request.form['id'])
                validated_data = validate_video_data(request.form)
                
                conn.execute('''
                    UPDATE videos 
                    SET title=?, youtuber_id=?, date_uploaded=?, payment_status=?, amount=?, video_link=?, description=?
                    WHERE id=?
                ''', (validated_data['title'], validated_data['youtuber_id'], 
                      validated_data['date_uploaded'], validated_data['payment_status'], 
                      validated_data['amount'], validated_data['video_link'], 
                      validated_data['description'], video_id))
                conn.commit()
                
                flash(f'Video "{validated_data["title"]}" updated successfully!', 'success')
                log_activity('Video updated', {'id': video_id, 'title': validated_data['title']})
                
            elif action == 'delete':
                video_id = int(request.form['id'])
                video_title = conn.execute('SELECT title FROM videos WHERE id = ?', (video_id,)).fetchone()[0]
                
                conn.execute('DELETE FROM videos WHERE id=?', (video_id,))
                conn.commit()
                
                flash(f'Video "{video_title}" deleted successfully!', 'success')
                log_activity('Video deleted', {'id': video_id, 'title': video_title})
                
            elif action == 'mark_paid':
                video_id = int(request.form['id'])
                video_info = conn.execute('SELECT title, amount FROM videos WHERE id = ?', (video_id,)).fetchone()
                
                conn.execute('UPDATE videos SET payment_status="paid" WHERE id=?', (video_id,))
                conn.commit()
                
                flash(f'Video "{video_info[0]}" marked as paid (${video_info[1]:.2f})!', 'success')
                log_activity('Video marked as paid', {'id': video_id, 'title': video_info[0], 'amount': video_info[1]})
            
            return redirect(url_for('videos'))
    
        # GET request - display videos list
        status_filter = request.args.get('status', '')
        youtuber_filter = request.args.get('youtuber', '')
        
        query = '''
            SELECT v.*, y.name as youtuber_name 
            FROM videos v 
            JOIN youtubers y ON v.youtuber_id = y.id 
            WHERE 1=1
        '''
        params = []
        
        if status_filter:
            query += ' AND v.payment_status = ?'
            params.append(status_filter)
        
        if youtuber_filter:
            query += ' AND v.youtuber_id = ?'
            params.append(youtuber_filter)
        
        query += ' ORDER BY v.date_uploaded DESC'
        
        videos_list = conn.execute(query, params).fetchall()
        
        # Get all YouTubers for dropdown
        youtubers_list = conn.execute('SELECT id, name FROM youtubers ORDER BY name').fetchall()
        
        return render_template('videos.html', 
                             videos=videos_list, 
                             youtubers=youtubers_list,
                             status_filter=status_filter,
                             youtuber_filter=youtuber_filter)
    
    finally:
        conn.close()

@app.route('/payments')
@handle_errors
def payments():
    """Payment management and reports"""
    log_activity('Payments page accessed')
    conn = get_db_connection()
    
    try:
        # Get payment summary by YouTuber
        payment_summary = conn.execute('''
            SELECT y.name, y.contact,
                   COUNT(v.id) as total_videos,
                   COALESCE(SUM(CASE WHEN v.payment_status = 'paid' THEN v.amount ELSE 0 END), 0) as total_paid,
                   COALESCE(SUM(CASE WHEN v.payment_status = 'pending' THEN v.amount ELSE 0 END), 0) as total_pending,
                   COALESCE(SUM(v.amount), 0) as total_amount
            FROM youtubers y
            LEFT JOIN videos v ON y.id = v.youtuber_id
            GROUP BY y.id, y.name, y.contact
            HAVING total_videos > 0
            ORDER BY total_pending DESC, total_paid DESC
        ''').fetchall()
        
        # Get monthly payment trends
        monthly_trends = conn.execute('''
            SELECT strftime('%Y-%m', date_uploaded) as month,
                   COUNT(*) as video_count,
                   COALESCE(SUM(amount), 0) as total_amount,
                   COALESCE(SUM(CASE WHEN payment_status = 'paid' THEN amount ELSE 0 END), 0) as paid_amount
            FROM videos
            WHERE date_uploaded IS NOT NULL
            GROUP BY strftime('%Y-%m', date_uploaded)
            ORDER BY month DESC
            LIMIT 12
        ''').fetchall()
        
        return render_template('payments.html', 
                             payment_summary=payment_summary,
                             monthly_trends=[dict(row) for row in monthly_trends])
    
    finally:
        conn.close()

@app.route('/export')
@handle_errors
@limiter.limit("10 per minute")
def export_data():
    """Export data to CSV/Excel"""
    export_type = request.args.get('type', 'all')
    log_activity('Data export requested', {'type': export_type})
    
    conn = get_db_connection()
    
    try:
        if export_type == 'youtubers':
            data = conn.execute('SELECT * FROM youtubers').fetchall()
            filename = 'youtubers_export.csv'
        elif export_type == 'videos':
            data = conn.execute('''
                SELECT v.*, y.name as youtuber_name 
                FROM videos v 
                JOIN youtubers y ON v.youtuber_id = y.id
            ''').fetchall()
            filename = 'videos_export.csv'
        elif export_type == 'payments':
            data = conn.execute('''
                SELECT y.name as youtuber_name, y.contact,
                       COUNT(v.id) as total_videos,
                       COALESCE(SUM(CASE WHEN v.payment_status = 'paid' THEN v.amount ELSE 0 END), 0) as total_paid,
                       COALESCE(SUM(CASE WHEN v.payment_status = 'pending' THEN v.amount ELSE 0 END), 0) as total_pending
                FROM youtubers y
                LEFT JOIN videos v ON y.id = v.youtuber_id
                GROUP BY y.id
            ''').fetchall()
            filename = 'payments_export.csv'
        else:
            # Export all data as Excel
            youtubers = conn.execute('SELECT * FROM youtubers').fetchall()
            videos = conn.execute('''
                SELECT v.*, y.name as youtuber_name 
                FROM videos v 
                JOIN youtubers y ON v.youtuber_id = y.id
            ''').fetchall()
            
            # Create CSV export instead of Excel (pandas not available in Python 3.13)
            output = StringIO()
            writer = csv.writer(output)
            
            # Write YouTubers data
            output.write("=== YOUTUBERS ===\n")
            if youtubers:
                writer.writerow(youtubers[0].keys())
                for row in youtubers:
                    writer.writerow(row)
            
            output.write("\n\n=== VIDEOS ===\n")
            if videos:
                writer.writerow(videos[0].keys())
                for row in videos:
                    writer.writerow(row)
            
            # Create response
            response_output = BytesIO()
            response_output.write(output.getvalue().encode('utf-8'))
            response_output.seek(0)
            
            return send_file(response_output,
                            download_name='complete_export.csv',
                            as_attachment=True,
                            mimetype='text/csv')
        
        # Create CSV for single table exports
        output = StringIO()
        writer = csv.writer(output)
        
        if data:
            # Write headers
            writer.writerow(data[0].keys())
            # Write data
            for row in data:
                writer.writerow(row)
        
        # Create response
        response_output = BytesIO()
        response_output.write(output.getvalue().encode('utf-8'))
        response_output.seek(0)
        
        return send_file(response_output,
                        download_name=filename,
                        as_attachment=True,
                        mimetype='text/csv')
    
    finally:
        conn.close()

@app.route('/api/dashboard-data')
@handle_errors
@limiter.limit("60 per minute")
def api_dashboard_data():
    """API endpoint for dashboard charts"""
    conn = get_db_connection()
    
    try:
        # Payment status distribution
        payment_dist = conn.execute('''
            SELECT payment_status, COUNT(*) as count, COALESCE(SUM(amount), 0) as total
            FROM videos 
            GROUP BY payment_status
        ''').fetchall()
        
        # Monthly trends
        monthly_data = conn.execute('''
            SELECT strftime('%Y-%m', date_uploaded) as month,
                   COALESCE(SUM(CASE WHEN payment_status = 'paid' THEN amount ELSE 0 END), 0) as paid,
                   COALESCE(SUM(CASE WHEN payment_status = 'pending' THEN amount ELSE 0 END), 0) as pending
            FROM videos
            WHERE date_uploaded IS NOT NULL
            GROUP BY strftime('%Y-%m', date_uploaded)
            ORDER BY month
            LIMIT 6
        ''').fetchall()
        
        return jsonify({
            'payment_distribution': [dict(row) for row in payment_dist],
            'monthly_trends': [dict(row) for row in monthly_data]
        })
    
    finally:
        conn.close()

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    log_error(error, '404 - Page not found')
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    log_error(error, '500 - Internal server error')
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    log_error(error, '403 - Forbidden')
    flash('Access denied. You do not have permission to access this resource.', 'error')
    return redirect(url_for('dashboard'))

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        conn = get_db_connection()
        conn.execute('SELECT 1').fetchone()
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0'
        }), 200
    except Exception as e:
        log_error(e, 'Health check failed')
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

if __name__ == '__main__':
    # Get configuration from environment
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.logger.info(f'Starting YouTube Management System on {host}:{port}')
    app.run(debug=debug, host=host, port=port)
