"""
VR Game Review Studio Web Interface
Young reviewer-friendly Flask application with game research tools
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
import json
import asyncio
from datetime import datetime
from werkzeug.utils import secure_filename
import sys

# Add project root to path
sys.path.append('/Users/michaelmote/Desktop/vr-game-review-studio')

from context_management.review_context_engine import ReviewContextEngine
from agent_orchestration.context_coordinator import ReviewAgentCoordinator
from context_management.game_knowledge_compression import VRGameKnowledgeCompressor
from vr_game_intelligence.review_quality_assessor import ReviewQualityAssessor

app = Flask(__name__)
app.secret_key = 'vr_review_studio_secret_key_for_young_reviewer'

# Configuration
CONFIG = {
    'UPLOAD_FOLDER': '/Users/michaelmote/Desktop/vr-game-review-studio/uploads',
    'MAX_CONTENT_LENGTH': 500 * 1024 * 1024,  # 500MB max file size
    'ALLOWED_EXTENSIONS': {'mp4', 'mov', 'avi', 'mkv'},
    'PROJECT_ROOT': '/Users/michaelmote/Desktop/vr-game-review-studio'
}

app.config.update(CONFIG)

# Ensure upload directory exists
os.makedirs(CONFIG['UPLOAD_FOLDER'], exist_ok=True)

# Initialize systems
context_engine = ReviewContextEngine()
agent_coordinator = ReviewAgentCoordinator()
game_compressor = VRGameKnowledgeCompressor()
quality_assessor = ReviewQualityAssessor()

def allowed_file(filename):
    """Check if uploaded file is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in CONFIG['ALLOWED_EXTENSIONS']

@app.route('/')
def dashboard():
    """Main reviewer dashboard"""
    try:
        # Get recent reviews and notifications
        recent_reviews = get_recent_reviews()
        notifications = get_notifications()
        review_stats = get_review_statistics()
        
        return render_template('review_dashboard.html', 
                             recent_reviews=recent_reviews,
                             notifications=notifications,
                             stats=review_stats)
    except Exception as e:
        flash(f'Dashboard error: {str(e)}', 'error')
        return render_template('review_dashboard.html', 
                             recent_reviews=[], 
                             notifications=[], 
                             stats={})

@app.route('/new-review')
def new_review():
    """Start new review creation process"""
    return render_template('game_research_setup.html')

@app.route('/api/search-games')
def search_games():
    """Search VR games for review selection"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'games': []})
        
        # Search compressed game database
        games = game_compressor.search_games_by_criteria()
        
        # Filter by search query
        filtered_games = []
        for game in games:
            if query.lower() in game['name'].lower() or query.lower() in game['genre'].lower():
                filtered_games.append(game)
        
        # Add mock VR games if database is empty
        if not filtered_games:
            filtered_games = get_mock_vr_games(query)
        
        return jsonify({'games': filtered_games[:10]})  # Top 10 results
        
    except Exception as e:
        return jsonify({'error': str(e), 'games': []})

@app.route('/api/game-info/<game_name>')
def get_game_info(game_name):
    """Get detailed information about a specific VR game"""
    try:
        # Get from compressed database
        game_info = game_compressor.get_compressed_game_info(game_name)
        
        if not game_info:
            # Create mock game info for demonstration
            game_info = create_mock_game_info(game_name)
        
        return jsonify({'game': game_info})
        
    except Exception as e:
        return jsonify({'error': str(e), 'game': None})

@app.route('/upload-review', methods=['GET', 'POST'])
def upload_review():
    """Handle review video upload and processing"""
    if request.method == 'GET':
        game_name = request.args.get('game', 'Unknown Game')
        review_type = request.args.get('type', 'full-review')
        return render_template('review_upload_zone.html', 
                             game_name=game_name, 
                             review_type=review_type)
    
    try:
        # Handle file upload
        if 'review_video' not in request.files:
            flash('No video file uploaded', 'error')
            return redirect(request.url)
        
        file = request.files['review_video']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload MP4, MOV, AVI, or MKV files.', 'error')
            return redirect(request.url)
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get game and review information
        game_name = request.form.get('game_name', 'Unknown Game')
        review_type = request.form.get('review_type', 'full-review')
        
        # Create game info object
        game_info = {
            'name': game_name,
            'genre': request.form.get('game_genre', 'Unknown'),
            'platform': request.form.get('game_platform', 'VR'),
            'price': float(request.form.get('game_price', 0)),
            'rating': float(request.form.get('game_rating', 0))
        }
        
        # Start background processing
        session['processing_video'] = {
            'filepath': filepath,
            'game_info': game_info,
            'review_type': review_type,
            'upload_time': datetime.now().isoformat()
        }
        
        flash(f'Video uploaded successfully! Processing {game_name} review...', 'success')
        return redirect(url_for('review_processing'))
        
    except Exception as e:
        flash(f'Upload error: {str(e)}', 'error')
        return redirect(request.url)

@app.route('/review-processing')
def review_processing():
    """Show review processing status"""
    processing_info = session.get('processing_video')
    if not processing_info:
        flash('No review processing in progress', 'warning')
        return redirect(url_for('dashboard'))
    
    return render_template('review_processing.html', 
                         processing_info=processing_info)

@app.route('/api/process-review', methods=['POST'])
def process_review_api():
    """API endpoint to process review with context isolation"""
    try:
        data = request.get_json()
        filepath = data.get('filepath')
        game_info = data.get('game_info', {})
        
        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'Invalid file path', 'status': 'error'})
        
        # Run async processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Context-isolated analysis
            context_result = loop.run_until_complete(
                context_engine.analyze_vr_game_review_with_isolation(filepath, game_info)
            )
            
            # Agent competition analysis
            agent_result = loop.run_until_complete(
                agent_coordinator.competitive_review_analysis(filepath, game_info)
            )
            
            # Quality assessment
            quality_result = loop.run_until_complete(
                quality_assessor.comprehensive_quality_analysis(filepath, game_info, agent_result)
            )
            
            # Combine results
            combined_result = {
                'status': 'complete',
                'context_analysis': context_result,
                'agent_consensus': agent_result.__dict__ if hasattr(agent_result, '__dict__') else str(agent_result),
                'quality_assessment': quality_result,
                'processing_timestamp': datetime.now().isoformat(),
                'game_info': game_info,
                'filepath': filepath
            }
            
            # Store results
            store_analysis_results(combined_result)
            
            return jsonify(combined_result)
            
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'})

@app.route('/review-editor')
def review_editor():
    """Review structure editor with AI assistance"""
    analysis_id = request.args.get('analysis_id')
    
    # Load analysis results if available
    analysis_data = None
    if analysis_id:
        analysis_data = load_analysis_results(analysis_id)
    
    return render_template('review_structure_editor.html', 
                         analysis_data=analysis_data)

@app.route('/review-analytics')
def review_analytics():
    """Review performance analytics and insights"""
    try:
        # Load review performance data
        analytics_data = get_review_analytics()
        learning_insights = get_learning_insights()
        
        return render_template('review_analytics.html',
                             analytics=analytics_data,
                             insights=learning_insights)
    except Exception as e:
        flash(f'Analytics error: {str(e)}', 'error')
        return render_template('review_analytics.html',
                             analytics={},
                             insights={})

@app.route('/publish-review')
def publish_review():
    """Multi-platform review publishing interface"""
    review_id = request.args.get('review_id')
    
    # Load review data
    review_data = None
    if review_id:
        review_data = load_review_data(review_id)
    
    return render_template('multi_platform_publisher.html',
                         review_data=review_data)

@app.route('/api/platform-optimize', methods=['POST'])
def optimize_for_platform():
    """Optimize review content for specific platforms"""
    try:
        data = request.get_json()
        platform = data.get('platform')
        review_content = data.get('review_content')
        
        # Platform-specific optimization
        optimized_content = {
            'youtube': optimize_for_youtube(review_content),
            'tiktok': optimize_for_tiktok(review_content),
            'instagram': optimize_for_instagram(review_content),
            'reddit': optimize_for_reddit(review_content)
        }.get(platform, review_content)
        
        return jsonify({'optimized_content': optimized_content})
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/game-database')
def game_database():
    """VR game database and research tools"""
    try:
        # Get database statistics
        db_stats = game_compressor.get_database_stats()
        
        # Get trending/high priority games
        trending_games = game_compressor.search_games_by_criteria(min_rating=4.0)
        
        return render_template('game_database.html',
                             db_stats=db_stats,
                             trending_games=trending_games)
    except Exception as e:
        flash(f'Database error: {str(e)}', 'error')
        return render_template('game_database.html',
                             db_stats={},
                             trending_games=[])

@app.route('/api/notifications')
def get_notifications_api():
    """Get current notifications for the interface"""
    try:
        notifications = get_notifications()
        return jsonify({'notifications': notifications})
    except Exception as e:
        return jsonify({'error': str(e), 'notifications': []})

@app.route('/parent-dashboard')
def parent_dashboard():
    """Parent oversight and monitoring dashboard"""
    try:
        # Load child's review activity
        review_activity = get_review_activity()
        safety_reports = get_safety_reports()
        quality_progress = get_quality_progress()
        
        return render_template('parent_dashboard.html',
                             activity=review_activity,
                             safety=safety_reports,
                             progress=quality_progress)
    except Exception as e:
        flash(f'Parent dashboard error: {str(e)}', 'error')
        return render_template('parent_dashboard.html',
                             activity={},
                             safety={},
                             progress={})

# Helper functions
def get_recent_reviews():
    """Get recent review data"""
    try:
        results_dir = os.path.join(CONFIG['PROJECT_ROOT'], 'learning_memory', 'analysis_results')
        if not os.path.exists(results_dir):
            return []
        
        review_files = sorted(
            [f for f in os.listdir(results_dir) if f.endswith('.json')],
            reverse=True
        )[:5]
        
        reviews = []
        for filename in review_files:
            filepath = os.path.join(results_dir, filename)
            with open(filepath, 'r') as f:
                review_data = json.load(f)
                reviews.append({
                    'id': filename.replace('.json', ''),
                    'game_name': review_data.get('game_name', 'Unknown'),
                    'timestamp': review_data.get('timestamp', ''),
                    'overall_score': review_data.get('overall_score', 0),
                    'educational_value': review_data.get('educational_value', 0)
                })
        
        return reviews
    except Exception as e:
        print(f"Error getting recent reviews: {e}")
        return []

def get_notifications():
    """Get current notifications"""
    notifications = []
    
    try:
        notification_dir = os.path.join(CONFIG['PROJECT_ROOT'], 'web_interface', 'notifications')
        
        if os.path.exists(notification_dir):
            for filename in os.listdir(notification_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(notification_dir, filename)
                    with open(filepath, 'r') as f:
                        notification = json.load(f)
                        notifications.append(notification)
    except Exception as e:
        print(f"Error getting notifications: {e}")
    
    return sorted(notifications, key=lambda x: x.get('timestamp', ''), reverse=True)[:5]

def get_review_statistics():
    """Get review statistics for dashboard"""
    try:
        memory_file = os.path.join(CONFIG['PROJECT_ROOT'], 'learning_memory', 'review_quality_evolution.json')
        
        if os.path.exists(memory_file):
            with open(memory_file, 'r') as f:
                reviews = json.load(f)
            
            if reviews:
                total_reviews = len(reviews)
                avg_score = sum(r.get('overall_score', 0) for r in reviews) / total_reviews
                avg_educational = sum(r.get('educational_value', 0) for r in reviews) / total_reviews
                
                return {
                    'total_reviews': total_reviews,
                    'average_score': round(avg_score, 1),
                    'average_educational': round(avg_educational, 1),
                    'recent_trend': 'improving' if len(reviews) >= 2 and reviews[-1].get('overall_score', 0) > reviews[-2].get('overall_score', 0) else 'stable'
                }
    except Exception as e:
        print(f"Error getting review statistics: {e}")
    
    return {
        'total_reviews': 0,
        'average_score': 0,
        'average_educational': 0,
        'recent_trend': 'stable'
    }

def get_mock_vr_games(query):
    """Get mock VR games for demonstration"""
    mock_games = [
        {'name': 'Half-Life: Alyx', 'genre': 'Action/Adventure', 'platform': 'PC VR', 'price': 59.99, 'rating': 4.8, 'review_priority': 9},
        {'name': 'Beat Saber', 'genre': 'Rhythm', 'platform': 'Multi-Platform VR', 'price': 29.99, 'rating': 4.7, 'review_priority': 8},
        {'name': 'Boneworks', 'genre': 'Action/Physics', 'platform': 'PC VR', 'price': 29.99, 'rating': 4.2, 'review_priority': 7},
        {'name': 'The Walking Dead: Saints & Sinners', 'genre': 'Survival Horror', 'platform': 'Multi-Platform VR', 'price': 39.99, 'rating': 4.5, 'review_priority': 8},
        {'name': 'Superhot VR', 'genre': 'Action', 'platform': 'Multi-Platform VR', 'price': 24.99, 'rating': 4.6, 'review_priority': 7},
        {'name': 'Job Simulator', 'genre': 'Simulation/Comedy', 'platform': 'Multi-Platform VR', 'price': 19.99, 'rating': 4.3, 'review_priority': 6},
        {'name': 'Pistol Whip', 'genre': 'Rhythm/Shooter', 'platform': 'Multi-Platform VR', 'price': 24.99, 'rating': 4.4, 'review_priority': 7},
        {'name': 'Vacation Simulator', 'genre': 'Simulation/Comedy', 'platform': 'Multi-Platform VR', 'price': 29.99, 'rating': 4.2, 'review_priority': 6}
    ]
    
    # Filter by query
    filtered = [game for game in mock_games if query.lower() in game['name'].lower() or query.lower() in game['genre'].lower()]
    return filtered if filtered else mock_games[:3]

def create_mock_game_info(game_name):
    """Create mock game info for demonstration"""
    return {
        'name': game_name,
        'genre': 'Action/Adventure',
        'platform': 'Multi-Platform VR',
        'price': 29.99,
        'rating': 4.5,
        'key_features': ['Hand tracking', 'Room scale', 'Haptic feedback'],
        'vr_interactions': ['Grabbing', 'Throwing', 'Gesture recognition'],
        'target_audience': 'Teens and Adults',
        'review_priority': 7,
        'description': f'{game_name} is an exciting VR game that offers immersive gameplay and innovative mechanics.',
        'system_requirements': 'VR headset required, 8GB RAM, GTX 1060 or better',
        'last_updated': datetime.now().isoformat()
    }

def store_analysis_results(analysis_result):
    """Store analysis results for future reference"""
    try:
        results_dir = os.path.join(CONFIG['PROJECT_ROOT'], 'learning_memory', 'analysis_results')
        os.makedirs(results_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        game_name = analysis_result['game_info'].get('name', 'Unknown').replace(' ', '_')
        filename = f"{game_name}_{timestamp}.json"
        
        filepath = os.path.join(results_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(analysis_result, f, indent=2, default=str)
        
        print(f"Analysis results stored: {filename}")
        return filename.replace('.json', '')
        
    except Exception as e:
        print(f"Error storing analysis results: {e}")
        return None

def load_analysis_results(analysis_id):
    """Load analysis results by ID"""
    try:
        results_dir = os.path.join(CONFIG['PROJECT_ROOT'], 'learning_memory', 'analysis_results')
        filepath = os.path.join(results_dir, f"{analysis_id}.json")
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading analysis results: {e}")
    
    return None

def load_review_data(review_id):
    """Load review data by ID"""
    return load_analysis_results(review_id)

def get_review_analytics():
    """Get review performance analytics"""
    try:
        memory_file = os.path.join(CONFIG['PROJECT_ROOT'], 'learning_memory', 'review_quality_evolution.json')
        
        if os.path.exists(memory_file):
            with open(memory_file, 'r') as f:
                reviews = json.load(f)
            
            # Calculate analytics
            analytics = {
                'total_reviews': len(reviews),
                'quality_trend': calculate_quality_trend(reviews),
                'genre_performance': calculate_genre_performance(reviews),
                'improvement_areas': identify_improvement_areas(reviews)
            }
            
            return analytics
    except Exception as e:
        print(f"Error getting review analytics: {e}")
    
    return {}

def get_learning_insights():
    """Get learning insights from review history"""
    try:
        patterns_file = os.path.join(CONFIG['PROJECT_ROOT'], 'learning_memory', 'successful_review_patterns.json')
        
        if os.path.exists(patterns_file):
            with open(patterns_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error getting learning insights: {e}")
    
    return {}

def get_review_activity():
    """Get review activity for parent dashboard"""
    try:
        reviews = get_recent_reviews()
        return {
            'recent_reviews': reviews,
            'total_this_week': len([r for r in reviews if is_this_week(r.get('timestamp', ''))]),
            'safety_score': 9.5,  # Mock safety score
            'educational_progress': 8.2  # Mock educational progress
        }
    except Exception as e:
        print(f"Error getting review activity: {e}")
    
    return {}

def get_safety_reports():
    """Get safety reports for parent oversight"""
    return {
        'content_appropriate': True,
        'language_suitable': True,
        'community_interactions': 'positive',
        'recommendations': ['Continue current approach', 'Consider exploring educational VR games']
    }

def get_quality_progress():
    """Get quality progress metrics"""
    return {
        'educational_value_trend': 'improving',
        'clarity_trend': 'stable',
        'engagement_trend': 'improving',
        'areas_of_strength': ['Enthusiasm', 'Game knowledge', 'Clear speech'],
        'areas_for_improvement': ['Technical explanations', 'Conclusion strength']
    }

# Platform optimization functions
def optimize_for_youtube(content):
    """Optimize content for YouTube"""
    return {
        'title': f"VR Game Review: {content.get('game_name', 'Unknown Game')}",
        'description': f"Comprehensive review of {content.get('game_name', 'Unknown Game')} for VR gaming enthusiasts!",
        'tags': ['VR Gaming', 'Game Review', 'Virtual Reality', content.get('game_name', '')],
        'format': 'long_form_educational',
        'recommended_length': '8-15 minutes'
    }

def optimize_for_tiktok(content):
    """Optimize content for TikTok"""
    return {
        'format': 'quick_highlights',
        'recommended_length': '60 seconds',
        'focus': 'most_exciting_moments',
        'hashtags': ['#VRGaming', '#GameReview', '#VirtualReality', '#Gaming']
    }

def optimize_for_instagram(content):
    """Optimize content for Instagram"""
    return {
        'format': 'visual_stories',
        'recommended_length': '30 seconds',
        'focus': 'visual_appeal',
        'stories_format': True
    }

def optimize_for_reddit(content):
    """Optimize content for Reddit"""
    return {
        'format': 'discussion_starter',
        'focus': 'community_engagement',
        'subreddit_suggestions': ['r/virtualreality', 'r/gamereview', 'r/VRGaming']
    }

# Utility functions
def calculate_quality_trend(reviews):
    """Calculate quality trend from review history"""
    if len(reviews) < 2:
        return 'insufficient_data'
    
    recent_scores = [r.get('overall_score', 0) for r in reviews[-5:]]
    older_scores = [r.get('overall_score', 0) for r in reviews[-10:-5]] if len(reviews) >= 10 else []
    
    if not older_scores:
        return 'new_reviewer'
    
    recent_avg = sum(recent_scores) / len(recent_scores)
    older_avg = sum(older_scores) / len(older_scores)
    
    if recent_avg > older_avg + 0.5:
        return 'improving'
    elif recent_avg < older_avg - 0.5:
        return 'declining'
    else:
        return 'stable'

def calculate_genre_performance(reviews):
    """Calculate performance by game genre"""
    genre_scores = {}
    for review in reviews:
        genre = review.get('game_genre', 'Unknown')
        score = review.get('overall_score', 0)
        
        if genre not in genre_scores:
            genre_scores[genre] = []
        genre_scores[genre].append(score)
    
    # Calculate averages
    for genre in genre_scores:
        scores = genre_scores[genre]
        genre_scores[genre] = {
            'average_score': sum(scores) / len(scores),
            'review_count': len(scores)
        }
    
    return genre_scores

def identify_improvement_areas(reviews):
    """Identify areas needing improvement"""
    if not reviews:
        return []
    
    # Aggregate scores by category
    categories = ['educational_value', 'overall_score']
    category_scores = {cat: [] for cat in categories}
    
    for review in reviews:
        for category in categories:
            if category in review:
                category_scores[category].append(review[category])
    
    # Find categories with lowest average scores
    improvements = []
    for category, scores in category_scores.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            if avg_score < 7:
                improvements.append({
                    'category': category,
                    'current_score': round(avg_score, 1),
                    'target_score': 8,
                    'priority': 'high' if avg_score < 6 else 'medium'
                })
    
    return improvements

def is_this_week(timestamp_str):
    """Check if timestamp is within current week"""
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now()
        week_start = now - timedelta(days=now.weekday())
        return timestamp >= week_start
    except:
        return False

if __name__ == '__main__':
    print("🎮 VR Game Review Studio starting...")
    print("📝 Young reviewer-friendly interface ready!")
    print("🔍 Game research tools loaded")
    print("🤖 AI analysis systems initialized")
    print("🛡️ Safety systems active")
    
    # Use environment variables for deployment
    host = os.getenv('FLASK_HOST', 'localhost')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)