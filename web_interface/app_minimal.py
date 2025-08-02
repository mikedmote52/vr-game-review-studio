"""
Minimal VR Game Review Studio Web Interface for Render Deployment
"""

from flask import Flask, render_template, jsonify
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'vr_review_studio_secret_key')

# Simple configuration
IS_PRODUCTION = os.getenv('FLASK_DEBUG', 'True').lower() == 'false' or os.getenv('RENDER', False)

@app.route('/')
def dashboard():
    """Main reviewer dashboard"""
    # Mock data for demonstration
    recent_reviews = [
        {
            'id': '1',
            'game_name': 'Half-Life: Alyx',
            'timestamp': datetime.now().isoformat(),
            'overall_score': 9.5,
            'educational_value': 8.0
        },
        {
            'id': '2', 
            'game_name': 'Beat Saber',
            'timestamp': datetime.now().isoformat(),
            'overall_score': 8.5,
            'educational_value': 7.0
        }
    ]
    
    notifications = [
        {
            'title': 'Welcome to VR Review Studio!',
            'message': 'Start creating amazing VR game reviews',
            'timestamp': datetime.now().isoformat()
        }
    ]
    
    stats = {
        'total_reviews': 2,
        'average_score': 9.0,
        'average_educational': 7.5,
        'recent_trend': 'improving'
    }
    
    return render_template('review_dashboard.html', 
                         recent_reviews=recent_reviews,
                         notifications=notifications,
                         stats=stats)

@app.route('/new-review')
def new_review():
    """Start new review creation process"""
    return render_template('game_research_setup.html')

@app.route('/api/search-games')
def search_games():
    """Search VR games for review selection"""
    query = request.args.get('q', '').strip()
    
    # Mock VR games data
    mock_games = [
        {'name': 'Half-Life: Alyx', 'genre': 'Action/Adventure', 'platform': 'PC VR', 'price': 59.99, 'rating': 4.8},
        {'name': 'Beat Saber', 'genre': 'Rhythm', 'platform': 'Multi-Platform VR', 'price': 29.99, 'rating': 4.7},
        {'name': 'Boneworks', 'genre': 'Action/Physics', 'platform': 'PC VR', 'price': 29.99, 'rating': 4.2},
        {'name': 'The Walking Dead: Saints & Sinners', 'genre': 'Survival Horror', 'platform': 'Multi-Platform VR', 'price': 39.99, 'rating': 4.5}
    ]
    
    # Filter by query
    if query:
        games = [g for g in mock_games if query.lower() in g['name'].lower() or query.lower() in g['genre'].lower()]
    else:
        games = mock_games
    
    return jsonify({'games': games})

@app.route('/review-editor')
def review_editor():
    """Review structure editor"""
    return render_template('review_structure_editor.html')

@app.route('/review-analytics')
def review_analytics():
    """Review performance analytics"""
    analytics = {
        'total_reviews': 2,
        'quality_trend': 'improving',
        'genre_performance': {
            'Action/Adventure': {'average_score': 9.5, 'review_count': 1},
            'Rhythm': {'average_score': 8.5, 'review_count': 1}
        }
    }
    
    insights = {
        'strengths': ['Enthusiasm', 'Game knowledge'],
        'improvements': ['Technical explanations', 'Conclusion strength']
    }
    
    return render_template('review_analytics.html',
                         analytics=analytics,
                         insights=insights)

@app.route('/game-database')
def game_database():
    """VR game database"""
    db_stats = {
        'total_games': 4,
        'total_reviews': 2,
        'last_updated': datetime.now().isoformat()
    }
    
    trending_games = [
        {'name': 'Half-Life: Alyx', 'rating': 4.8, 'review_priority': 9},
        {'name': 'Beat Saber', 'rating': 4.7, 'review_priority': 8}
    ]
    
    return render_template('game_database.html',
                         db_stats=db_stats,
                         trending_games=trending_games)

@app.route('/parent-dashboard')
def parent_dashboard():
    """Parent oversight dashboard"""
    activity = {
        'recent_reviews': 2,
        'total_this_week': 1,
        'safety_score': 9.5,
        'educational_progress': 8.2
    }
    
    safety = {
        'content_appropriate': True,
        'language_suitable': True,
        'community_interactions': 'positive',
        'recommendations': ['Continue current approach']
    }
    
    progress = {
        'educational_value_trend': 'improving',
        'clarity_trend': 'stable',
        'engagement_trend': 'improving',
        'areas_of_strength': ['Enthusiasm', 'Game knowledge'],
        'areas_for_improvement': ['Technical explanations']
    }
    
    return render_template('parent_dashboard.html',
                         activity=activity,
                         safety=safety,
                         progress=progress)

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("🎮 VR Game Review Studio (Minimal) starting...")
    print(f"🌐 Production mode: {IS_PRODUCTION}")
    
    # Use environment variables for deployment
    host = os.getenv('FLASK_HOST', 'localhost')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)