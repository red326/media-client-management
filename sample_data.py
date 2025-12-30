#!/usr/bin/env python3
"""
Sample Data Generator for YouTuber Management System
Run this script to populate the database with sample data for testing
"""

import sqlite3
from datetime import datetime, timedelta
import random

DATABASE = 'database/data.db'

def create_sample_data():
    """Create sample data for testing the application"""
    
    # Sample YouTubers data
    youtubers_data = [
        {
            'name': 'TechReviewer Pro',
            'channel_link': 'https://youtube.com/@techreviewerpro',
            'niche': 'Technology',
            'contact': 'tech@example.com',
            'notes': 'Specializes in smartphone and laptop reviews. Very reliable content creator.'
        },
        {
            'name': 'Gaming Master',
            'channel_link': 'https://youtube.com/@gamingmaster',
            'niche': 'Gaming',
            'contact': 'gaming@example.com',
            'notes': 'Popular gaming channel with focus on indie games and reviews.'
        },
        {
            'name': 'Lifestyle Guru',
            'channel_link': 'https://youtube.com/@lifestyleguru',
            'niche': 'Lifestyle',
            'contact': 'lifestyle@example.com',
            'notes': 'Lifestyle and wellness content. Great engagement rates.'
        },
        {
            'name': 'Cooking Adventures',
            'channel_link': 'https://youtube.com/@cookingadventures',
            'niche': 'Food',
            'contact': 'cooking@example.com',
            'notes': 'Recipe videos and cooking tutorials. Family-friendly content.'
        },
        {
            'name': 'Fitness Journey',
            'channel_link': 'https://youtube.com/@fitnessjourney',
            'niche': 'Fitness',
            'contact': 'fitness@example.com',
            'notes': 'Workout routines and fitness tips. Consistent upload schedule.'
        },
        {
            'name': 'Travel Explorer',
            'channel_link': 'https://youtube.com/@travelexplorer',
            'niche': 'Travel',
            'contact': 'travel@example.com',
            'notes': 'Travel vlogs and destination guides. High production quality.'
        }
    ]
    
    # Sample video titles by niche
    video_titles = {
        'Technology': [
            'iPhone 15 Pro Max Complete Review',
            'Best Laptops Under $1000 in 2024',
            'Samsung Galaxy S24 vs iPhone 15 Comparison',
            'Top 10 Tech Gadgets You Need',
            'MacBook Air M3 Unboxing and First Impressions',
            'Android vs iOS: Which is Better?',
            'Best Gaming Headsets for 2024',
            'Smart Home Setup Guide'
        ],
        'Gaming': [
            'Baldur\'s Gate 3 Complete Walkthrough',
            'Top 10 Indie Games This Month',
            'Cyberpunk 2077 Review After Updates',
            'Best Gaming Setup Under $2000',
            'Elden Ring Boss Fight Strategies',
            'New Steam Deck Games to Try',
            'Gaming Chair Review and Comparison',
            'Retro Gaming: Best Classic Consoles'
        ],
        'Lifestyle': [
            'Morning Routine for Productivity',
            '10 Life Hacks That Actually Work',
            'Minimalist Home Tour',
            'Self-Care Sunday Routine',
            'Productivity Apps I Can\'t Live Without',
            'How to Build Better Habits',
            'Weekend Reset Routine',
            'Decluttering Your Digital Life'
        ],
        'Food': [
            'Easy 15-Minute Pasta Recipes',
            'Perfect Chocolate Chip Cookies',
            'Healthy Meal Prep for Beginners',
            'Traditional Italian Carbonara',
            'Vegan Desserts That Don\'t Suck',
            'BBQ Ribs: Low and Slow Method',
            'Homemade Pizza Dough Recipe',
            'Asian Fusion Cooking Techniques'
        ],
        'Fitness': [
            '30-Day Ab Challenge Results',
            'Full Body Workout at Home',
            'Nutrition Tips for Muscle Gain',
            'Yoga for Beginners: First Week',
            'HIIT Workout for Fat Loss',
            'Gym Equipment You Actually Need',
            'Running Form: Common Mistakes',
            'Strength Training for Women'
        ],
        'Travel': [
            'Japan Travel Guide: First Timer Tips',
            'Budget Backpacking Through Europe',
            'Hidden Gems in Southeast Asia',
            'Solo Female Travel Safety Tips',
            'Best Travel Gear for 2024',
            'New York City in 48 Hours',
            'Digital Nomad Setup and Tips',
            'Photography Tips for Travelers'
        ]
    }
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("Creating sample YouTubers...")
    
    # Insert YouTubers
    youtuber_ids = []
    for youtuber in youtubers_data:
        cursor.execute('''
            INSERT INTO youtubers (name, channel_link, niche, contact, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (youtuber['name'], youtuber['channel_link'], youtuber['niche'], 
              youtuber['contact'], youtuber['notes']))
        youtuber_ids.append(cursor.lastrowid)
    
    print(f"Created {len(youtuber_ids)} YouTubers")
    
    # Insert Videos
    print("Creating sample videos...")
    
    video_count = 0
    base_date = datetime.now() - timedelta(days=90)  # Start 90 days ago
    
    for i, youtuber_id in enumerate(youtuber_ids):
        youtuber_niche = youtubers_data[i]['niche']
        titles = video_titles[youtuber_niche]
        
        # Create 8-12 videos per YouTuber
        num_videos = random.randint(8, 12)
        
        for j in range(num_videos):
            # Random date within the last 90 days
            days_offset = random.randint(0, 90)
            upload_date = base_date + timedelta(days=days_offset)
            
            # Random title from the niche
            title = random.choice(titles)
            
            # Random payment amount between ₹500-₹5000 (realistic Indian amounts)
            amount = round(random.uniform(500, 5000), 2)
            
            # 70% chance of being paid, 30% pending
            payment_status = 'paid' if random.random() < 0.7 else 'pending'
            
            # Generate a fake YouTube link
            video_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=11))
            video_link = f'https://youtube.com/watch?v={video_id}'
            
            # Random description
            descriptions = [
                'Great video with excellent engagement!',
                'High-quality content as always.',
                'Sponsored content - brand partnership.',
                'Tutorial video with step-by-step guide.',
                'Review video with detailed analysis.',
                'Entertaining content with good retention.',
                'Educational video with valuable insights.',
                'Collaboration with other creators.'
            ]
            description = random.choice(descriptions)
            
            cursor.execute('''
                INSERT INTO videos (title, youtuber_id, date_uploaded, payment_status, 
                                  amount, video_link, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, youtuber_id, upload_date.strftime('%Y-%m-%d'), 
                  payment_status, amount, video_link, description))
            
            video_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"Created {video_count} videos")
    print("\nSample data created successfully!")
    print("You can now run the application and see the sample data.")
    
    # Print summary statistics
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    total_paid = cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM videos WHERE payment_status = "paid"').fetchone()[0]
    total_pending = cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM videos WHERE payment_status = "pending"').fetchone()[0]
    
    print(f"\nSummary:")
    print(f"- Total YouTubers: {len(youtuber_ids)}")
    print(f"- Total Videos: {video_count}")
    print(f"- Total Paid: ₹{total_paid:.2f}")
    print(f"- Total Pending: ₹{total_pending:.2f}")
    print(f"- Total Amount: ₹{total_paid + total_pending:.2f}")
    
    conn.close()

if __name__ == '__main__':
    import os
    
    # Create database directory if it doesn't exist
    os.makedirs('database', exist_ok=True)
    
    # Check if database already has data
    if os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        try:
            youtuber_count = cursor.execute('SELECT COUNT(*) FROM youtubers').fetchone()[0]
            if youtuber_count > 0:
                response = input(f"Database already contains {youtuber_count} YouTubers. Do you want to add more sample data? (y/n): ")
                if response.lower() != 'y':
                    print("Cancelled.")
                    exit()
        except sqlite3.OperationalError:
            # Tables don't exist yet, that's fine
            pass
        
        conn.close()
    
    # Import and initialize the database first
    try:
        from app import init_db
        print("Initializing database...")
        init_db()
        print("Database initialized.")
    except ImportError:
        print("Error: Could not import app.py. Make sure it exists in the same directory.")
        exit(1)
    
    # Create sample data
    create_sample_data()
