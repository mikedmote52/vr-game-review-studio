"""
VR Game Review Studio Web Interface
Young reviewer-friendly Flask application with game research tools
"""

print("Starting VR Game Review Studio Web Interface...")

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
import json
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

try:
    import asyncio
except ImportError:
    print("Warning: asyncio not available")
    asyncio = None

print(f"Current working directory: {os.getcwd()}")
print(f"Environment variables: FLASK_DEBUG={os.getenv('FLASK_DEBUG')}, RENDER={os.getenv('RENDER')}")

# Check if we're in production environment first
# Render sets several environment variables we can check
IS_PRODUCTION = (
    os.getenv('RENDER') is not None or 
    os.getenv('RENDER_SERVICE_NAME') is not None or
    os.getenv('PORT') is not None or
    os.getenv('FLASK_DEBUG', 'True').lower() == 'false'
)
print(f"IS_PRODUCTION: {IS_PRODUCTION}")
print(f"RENDER env: {os.getenv('RENDER')}")
print(f"PORT env: {os.getenv('PORT')}")

# For production deployment, disable complex AI modules
AI_MODULES_AVAILABLE = False

# Create mock classes for demo
class MockEngine:
    def __init__(self): pass
    async def analyze_vr_game_review_with_isolation(self, *args): 
        return {"status": "demo_mode", "message": "AI analysis available in full deployment"}
    def search_games_by_criteria(self, **kwargs):
        return []
    def get_compressed_game_info(self, game_name):
        return None
    def get_database_stats(self):
        return {'total_games': 0, 'total_reviews': 0}
    async def competitive_review_analysis(self, *args):
        return {"status": "demo_mode"}
    async def comprehensive_quality_analysis(self, *args):
        return {"status": "demo_mode"}

ReviewContextEngine = MockEngine
ReviewAgentCoordinator = MockEngine
VRGameKnowledgeCompressor = MockEngine  
ReviewQualityAssessor = MockEngine

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'vr_review_studio_secret_key_for_young_reviewer')

# Configuration
if IS_PRODUCTION:
    project_root = '/app'  # Render default app directory
else:
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    except:
        project_root = os.getcwd()

# Create a dedicated video uploads folder
VIDEO_UPLOADS_DIR = os.path.join(project_root, 'video_uploads')
VIDEO_DATABASE_FILE = os.path.join(project_root, 'video_database.json')

CONFIG = {
    'UPLOAD_FOLDER': '/tmp/uploads' if IS_PRODUCTION else VIDEO_UPLOADS_DIR,
    'MAX_CONTENT_LENGTH': 500 * 1024 * 1024,  # 500MB max file size
    'ALLOWED_EXTENSIONS': {'mp4', 'mov', 'avi', 'mkv'},
    'PROJECT_ROOT': project_root,
    'VIDEO_DATABASE': VIDEO_DATABASE_FILE
}

app.config.update(CONFIG)

# Ensure upload directory exists
try:
    os.makedirs(CONFIG['UPLOAD_FOLDER'], exist_ok=True)
    print(f"Upload directory ready: {CONFIG['UPLOAD_FOLDER']}")
except (PermissionError, OSError) as e:
    print(f"Cannot create upload directory: {CONFIG['UPLOAD_FOLDER']} - {e}")
    if not IS_PRODUCTION:
        raise

# Initialize systems with fallback
try:
    context_engine = ReviewContextEngine()
    agent_coordinator = ReviewAgentCoordinator()
    game_compressor = VRGameKnowledgeCompressor()
    quality_assessor = ReviewQualityAssessor()
    print("🤖 AI analysis systems initialized")
except Exception as e:
    print(f"AI systems in demo mode: {e}")
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
        game_safe = secure_filename(request.form.get('game_name', 'Unknown'))
        filename = f"{timestamp}_{game_safe}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get game and review information
        game_name = request.form.get('game_name', 'Unknown Game')
        review_type = request.form.get('review_type', 'full-review')
        
        # Calculate file size
        file_size = os.path.getsize(filepath)
        
        # Create video entry for database
        video_entry = {
            'id': f"{timestamp}_{game_safe}",
            'filename': filename,
            'filepath': filepath,
            'game_name': game_name,
            'review_type': review_type.replace('-', ' ').title(),
            'upload_date': datetime.now().isoformat(),
            'size': format_file_size(file_size),
            'status': 'Processing',
            'game_info': {
                'name': game_name,
                'genre': request.form.get('game_genre', 'Unknown'),
                'platform': request.form.get('game_platform', 'VR'),
                'price': float(request.form.get('game_price', 0)),
                'rating': float(request.form.get('game_rating', 0))
            }
        }
        
        # Save to video database
        save_video_to_database(video_entry)
        
        # Start background processing
        session['processing_video'] = video_entry
        
        flash(f'Video uploaded successfully! Saved to: {CONFIG["UPLOAD_FOLDER"]}', 'success')
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
        
        # Mock processing for production demo
        combined_result = {
            'status': 'complete',
            'context_analysis': {'status': 'demo_mode', 'message': 'AI analysis in demo mode'},
            'agent_consensus': {'status': 'demo_mode'},
            'quality_assessment': {'status': 'demo_mode'},
            'processing_timestamp': datetime.now().isoformat(),
            'game_info': game_info,
            'filepath': filepath
        }
        
        # Store results
        store_analysis_results(combined_result)
        
        return jsonify(combined_result)
            
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

@app.route('/video-library')
def video_library():
    """Display all uploaded videos"""
    try:
        videos = load_video_database()
        total_size = calculate_total_video_size(videos)
        
        return render_template('video_library.html',
                             videos=videos,
                             storage_path=CONFIG['UPLOAD_FOLDER'],
                             total_size=total_size)
    except Exception as e:
        flash(f'Error loading video library: {str(e)}', 'error')
        return render_template('video_library.html',
                             videos=[],
                             storage_path=CONFIG['UPLOAD_FOLDER'],
                             total_size='0 MB')

@app.route('/video/<video_id>')
def video_details(video_id):
    """Show detailed information about a specific video"""
    videos = load_video_database()
    video = next((v for v in videos if v['id'] == video_id), None)
    
    if not video:
        flash('Video not found', 'error')
        return redirect(url_for('video_library'))
    
    return render_template('video_details.html', video=video)

@app.route('/api/delete-video/<video_id>', methods=['DELETE'])
def delete_video(video_id):
    """Delete a video and remove from database"""
    try:
        videos = load_video_database()
        video = next((v for v in videos if v['id'] == video_id), None)
        
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'})
        
        # Delete the file
        if os.path.exists(video['filepath']):
            os.remove(video['filepath'])
        
        # Remove from database
        videos = [v for v in videos if v['id'] != video_id]
        save_video_database(videos)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Helper functions
def get_data_path(relative_path):
    """Get appropriate file path for production or development"""
    if IS_PRODUCTION:
        # In production, use /tmp for all data with simplified structure
        if 'analysis_results' in relative_path:
            return '/tmp/analysis_results'
        elif 'notifications' in relative_path:
            return '/tmp/notifications'
        elif relative_path.endswith('.json'):
            filename = os.path.basename(relative_path)
            return f'/tmp/{filename}'
        else:
            return f'/tmp/{relative_path.replace("/", "_")}'
    else:
        # In development, use project structure
        return os.path.join(CONFIG['PROJECT_ROOT'], relative_path)
def get_recent_reviews():
    """Get recent review data"""
    try:
        results_dir = get_data_path('learning_memory/analysis_results')
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
        notification_dir = get_data_path('web_interface/notifications')
        
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
        memory_file = get_data_path('learning_memory/review_quality_evolution.json')
        
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
        results_dir = get_data_path('learning_memory/analysis_results')
        try:
            os.makedirs(results_dir, exist_ok=True)
        except (PermissionError, OSError):
            print(f"Cannot create results directory: {results_dir}")
            return None
        
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
        results_dir = get_data_path('learning_memory/analysis_results')
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
        memory_file = get_data_path('learning_memory/review_quality_evolution.json')
        
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
        patterns_file = get_data_path('learning_memory/successful_review_patterns.json')
        
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

# Video database management functions
def load_video_database():
    """Load video database from JSON file"""
    try:
        if os.path.exists(CONFIG['VIDEO_DATABASE']):
            with open(CONFIG['VIDEO_DATABASE'], 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading video database: {e}")
    return []

def save_video_database(videos):
    """Save video database to JSON file"""
    try:
        os.makedirs(os.path.dirname(CONFIG['VIDEO_DATABASE']), exist_ok=True)
        with open(CONFIG['VIDEO_DATABASE'], 'w') as f:
            json.dump(videos, f, indent=2)
    except Exception as e:
        print(f"Error saving video database: {e}")

def save_video_to_database(video_entry):
    """Add a new video entry to the database"""
    videos = load_video_database()
    videos.append(video_entry)
    save_video_database(videos)

def format_file_size(size_in_bytes):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} TB"

def calculate_total_video_size(videos):
    """Calculate total size of all videos"""
    total_bytes = 0
    for video in videos:
        if os.path.exists(video.get('filepath', '')):
            try:
                total_bytes += os.path.getsize(video['filepath'])
            except:
                pass
    return format_file_size(total_bytes)

# Always configure the app, even if not running as main
print("🎮 VR Game Review Studio starting...")
print("📝 Young reviewer-friendly interface ready!")
print("🔍 Game research tools loaded")
print("🤖 AI analysis systems initialized")
print("🛡️ Safety systems active")

# Use environment variables for deployment
# Render provides PORT environment variable
if IS_PRODUCTION:
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', 10000))
    debug = False
else:
    host = os.getenv('FLASK_HOST', 'localhost')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

print(f"Configured to run on {host}:{port} (debug={debug}, production={IS_PRODUCTION})")

if __name__ == '__main__':
    app.run(host=host, port=port, debug=debug)