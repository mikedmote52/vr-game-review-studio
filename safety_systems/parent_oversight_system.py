"""
Parent Oversight System for VR Game Review Studio
Comprehensive monitoring and approval system for parents/guardians
"""

import json
import sqlite3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import os

@dataclass
class ReviewApprovalRequest:
    """Review approval request for parent oversight"""
    request_id: str
    review_title: str
    game_name: str
    game_rating: str
    content_summary: str
    safety_assessment: Dict[str, Any]
    educational_value: float
    estimated_duration: str
    created_timestamp: str
    status: str  # 'pending', 'approved', 'rejected', 'needs_changes'
    parent_comments: str = ""
    approved_timestamp: str = ""

@dataclass
class ActivityReport:
    """Daily/weekly activity report for parents"""
    report_id: str
    date_range: str
    reviews_created: int
    total_screen_time: str
    educational_progress: Dict[str, Any]
    safety_incidents: List[str]
    quality_improvements: List[str]
    community_interactions: Dict[str, Any]
    recommendations: List[str]

class ParentOversightSystem:
    """Comprehensive parent oversight and monitoring system"""
    
    def __init__(self, db_path: str = "/Users/michaelmote/Desktop/vr-game-review-studio/learning_memory/parent_oversight.db"):
        self.db_path = db_path
        self.project_root = "/Users/michaelmote/Desktop/vr-game-review-studio"
        
        # Parent notification settings
        self.notification_settings = {
            'email_notifications': True,
            'daily_reports': True,
            'approval_requests': True,
            'safety_alerts': True,
            'quality_milestones': True
        }
        
        # Safety thresholds requiring parent notification
        self.safety_thresholds = {
            'content_safety_score': 8.0,
            'educational_value': 6.0,
            'age_appropriateness': True,
            'language_appropriate': True,
            'max_daily_screen_time': 180  # 3 hours max
        }
        
        # Initialize database
        self._init_oversight_database()
        
        # Load parent preferences
        self.parent_preferences = self._load_parent_preferences()
    
    def _init_oversight_database(self):
        """Initialize parent oversight database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Review approval requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approval_requests (
                request_id TEXT PRIMARY KEY,
                review_title TEXT NOT NULL,
                game_name TEXT NOT NULL,
                game_rating TEXT,
                content_summary TEXT,
                safety_assessment TEXT,  -- JSON
                educational_value REAL,
                estimated_duration TEXT,
                created_timestamp TEXT,
                status TEXT DEFAULT 'pending',
                parent_comments TEXT,
                approved_timestamp TEXT
            )
        """)
        
        # Daily activity tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_activity (
                date TEXT PRIMARY KEY,
                reviews_created INTEGER DEFAULT 0,
                total_screen_time INTEGER DEFAULT 0,  -- minutes
                content_created INTEGER DEFAULT 0,  -- minutes of content
                safety_incidents INTEGER DEFAULT 0,
                educational_score_avg REAL DEFAULT 0,
                quality_score_avg REAL DEFAULT 0
            )
        """)
        
        # Safety incidents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS safety_incidents (
                incident_id TEXT PRIMARY KEY,
                incident_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                review_id TEXT,
                timestamp TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                parent_notified BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Parent feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parent_feedback (
                feedback_id TEXT PRIMARY KEY,
                review_id TEXT,
                feedback_type TEXT,  -- 'approval', 'suggestion', 'concern'
                feedback_text TEXT,
                timestamp TEXT,
                addressed BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Quality milestones table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_milestones (
                milestone_id TEXT PRIMARY KEY,
                milestone_type TEXT,
                achievement_description TEXT,
                date_achieved TEXT,
                celebration_suggested BOOLEAN DEFAULT TRUE
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_parent_preferences(self) -> Dict[str, Any]:
        """Load parent preferences and settings"""
        preferences_file = os.path.join(self.project_root, 'config', 'parent_preferences.json')
        
        default_preferences = {
            'notification_email': '',
            'approval_required_for_all_reviews': True,
            'safety_alert_threshold': 'medium',
            'daily_report_time': '18:00',
            'max_daily_screen_time': 180,
            'content_warnings_required': True,
            'educational_value_minimum': 6.0,
            'allow_unsupervised_editing': False,
            'community_interaction_allowed': True,
            'platform_permissions': {
                'youtube': True,
                'tiktok': False,
                'instagram': True,
                'reddit': False
            }
        }
        
        try:
            if os.path.exists(preferences_file):
                with open(preferences_file, 'r') as f:
                    preferences = json.load(f)
                # Merge with defaults
                for key, value in default_preferences.items():
                    if key not in preferences:
                        preferences[key] = value
                return preferences
        except Exception as e:
            print(f"Error loading parent preferences: {e}")
        
        return default_preferences
    
    async def request_review_approval(self, review_data: Dict[str, Any], 
                                    safety_assessment: Dict[str, Any]) -> str:
        """Submit review for parent approval"""
        
        # Generate unique request ID
        request_id = hashlib.md5(f"{review_data['game_name']}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        # Create approval request
        approval_request = ReviewApprovalRequest(
            request_id=request_id,
            review_title=f"VR Review: {review_data['game_name']}",
            game_name=review_data['game_name'],
            game_rating=review_data.get('age_rating', 'Unknown'),
            content_summary=self._generate_content_summary(review_data),
            safety_assessment=safety_assessment,
            educational_value=safety_assessment.get('quality_assessment', {}).get('educational_value', 0),
            estimated_duration=review_data.get('estimated_duration', 'Unknown'),
            created_timestamp=datetime.now().isoformat(),
            status='pending'
        )
        
        # Store in database
        await self._store_approval_request(approval_request)
        
        # Send notification to parent
        await self._notify_parent_approval_needed(approval_request)
        
        # Check if immediate safety concerns require urgent attention
        if self._has_safety_concerns(safety_assessment):
            await self._send_urgent_safety_alert(approval_request)
        
        return request_id
    
    async def _store_approval_request(self, request: ReviewApprovalRequest):
        """Store approval request in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO approval_requests 
                (request_id, review_title, game_name, game_rating, content_summary,
                 safety_assessment, educational_value, estimated_duration, 
                 created_timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.request_id, request.review_title, request.game_name,
                request.game_rating, request.content_summary,
                json.dumps(request.safety_assessment), request.educational_value,
                request.estimated_duration, request.created_timestamp, request.status
            ))
            
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error storing approval request: {e}")
        finally:
            conn.close()
    
    def _generate_content_summary(self, review_data: Dict[str, Any]) -> str:
        """Generate parent-friendly content summary"""
        
        game_name = review_data['game_name']
        genre = review_data.get('genre', 'Unknown')
        duration = review_data.get('estimated_duration', 'Unknown')
        
        summary = f"Review of '{game_name}' - a {genre} VR game. "
        summary += f"Estimated review length: {duration}. "
        
        # Add educational elements
        educational_elements = review_data.get('educational_objectives', [])
        if educational_elements:
            summary += f"Educational focus: {', '.join(educational_elements[:3])}. "
        
        # Add content appropriateness
        age_rating = review_data.get('age_rating', 'Unknown')
        if age_rating != 'Unknown':
            summary += f"Game rating: {age_rating}. "
        
        return summary
    
    def _has_safety_concerns(self, safety_assessment: Dict[str, Any]) -> bool:
        """Check if safety assessment has concerning elements"""
        
        safety_score = safety_assessment.get('safety_assessment', {}).get('overall_safety_score', 10)
        if safety_score < self.safety_thresholds['content_safety_score']:
            return True
        
        violations = safety_assessment.get('safety_violations', [])
        if any(v.get('severity') in ['high', 'critical'] for v in violations):
            return True
        
        if not safety_assessment.get('safe_for_publication', True):
            return True
        
        return False
    
    async def _notify_parent_approval_needed(self, request: ReviewApprovalRequest):
        """Send notification to parent about approval needed"""
        
        if not self.parent_preferences.get('approval_required_for_all_reviews', True):
            return
        
        notification_data = {
            'type': 'approval_request',
            'request_id': request.request_id,
            'game_name': request.game_name,
            'content_summary': request.content_summary,
            'educational_value': request.educational_value,
            'safety_score': request.safety_assessment.get('safety_assessment', {}).get('overall_safety_score', 0),
            'estimated_duration': request.estimated_duration,
            'approval_url': f"http://localhost:5000/parent-dashboard/approve/{request.request_id}"
        }
        
        # Store notification
        await self._store_parent_notification(notification_data)
        
        # Send email if configured
        if self.parent_preferences.get('notification_email'):
            await self._send_approval_email(request, notification_data)
        
        print(f"Parent approval notification sent for review: {request.game_name}")
    
    async def _send_urgent_safety_alert(self, request: ReviewApprovalRequest):
        """Send urgent safety alert to parent"""
        
        alert_data = {
            'type': 'urgent_safety_alert',
            'request_id': request.request_id,
            'game_name': request.game_name,
            'safety_concerns': request.safety_assessment.get('safety_violations', []),
            'immediate_action_required': True,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store safety incident
        await self._log_safety_incident('urgent_content_concern', 'high', 
                                       f"Safety concerns in {request.game_name} review", 
                                       request.request_id)
        
        # Send immediate notification
        await self._store_parent_notification(alert_data)
        
        print(f"URGENT: Safety alert sent to parent for {request.game_name}")
    
    async def process_parent_decision(self, request_id: str, decision: str, 
                                    comments: str = "") -> bool:
        """Process parent approval/rejection decision"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Update approval request
            cursor.execute("""
                UPDATE approval_requests 
                SET status = ?, parent_comments = ?, approved_timestamp = ?
                WHERE request_id = ?
            """, (decision, comments, datetime.now().isoformat(), request_id))
            
            conn.commit()
            
            # Log decision
            await self._log_parent_decision(request_id, decision, comments)
            
            # If approved, notify child and update permissions
            if decision == 'approved':
                await self._notify_approval_granted(request_id)
            elif decision == 'needs_changes':
                await self._notify_changes_needed(request_id, comments)
            else:  # rejected
                await self._notify_approval_denied(request_id, comments)
            
            return True
            
        except sqlite3.Error as e:
            print(f"Error processing parent decision: {e}")
            return False
        finally:
            conn.close()
    
    async def generate_daily_activity_report(self, date: str = None) -> ActivityReport:
        """Generate daily activity report for parent"""
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Get daily activity data
        activity_data = await self._get_daily_activity_data(date)
        
        # Get safety incidents
        safety_incidents = await self._get_safety_incidents(date)
        
        # Get quality improvements
        quality_improvements = await self._get_quality_improvements(date)
        
        # Get community interactions
        community_interactions = await self._get_community_interactions(date)
        
        # Generate recommendations
        recommendations = await self._generate_parent_recommendations(activity_data, safety_incidents)
        
        report = ActivityReport(
            report_id=f"daily_{date}",
            date_range=date,
            reviews_created=activity_data.get('reviews_created', 0),
            total_screen_time=self._format_screen_time(activity_data.get('total_screen_time', 0)),
            educational_progress={
                'average_educational_score': activity_data.get('educational_score_avg', 0),
                'average_quality_score': activity_data.get('quality_score_avg', 0),
                'learning_areas': ['VR gaming', 'Content creation', 'Critical thinking']
            },
            safety_incidents=[incident['description'] for incident in safety_incidents],
            quality_improvements=quality_improvements,
            community_interactions=community_interactions,
            recommendations=recommendations
        )
        
        # Store report
        await self._store_activity_report(report)
        
        return report
    
    async def _get_daily_activity_data(self, date: str) -> Dict[str, Any]:
        """Get daily activity data from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM daily_activity WHERE date = ?
            """, (date,))
            
            result = cursor.fetchone()
            if result:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, result))
            else:
                return {}
        except sqlite3.Error as e:
            print(f"Error getting daily activity data: {e}")
            return {}
        finally:
            conn.close()
    
    async def _get_safety_incidents(self, date: str) -> List[Dict[str, Any]]:
        """Get safety incidents for specific date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM safety_incidents 
                WHERE date(timestamp) = ? 
                ORDER BY timestamp DESC
            """, (date,))
            
            results = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            return [dict(zip(columns, row)) for row in results]
        except sqlite3.Error as e:
            print(f"Error getting safety incidents: {e}")
            return []
        finally:
            conn.close()
    
    async def _get_quality_improvements(self, date: str) -> List[str]:
        """Get quality improvements for the day"""
        # This would integrate with the quality assessment system
        # For now, return sample improvements
        return [
            "Improved explanation clarity in VR game mechanics",
            "Better structure in review organization",
            "Enhanced educational value in content"
        ]
    
    async def _get_community_interactions(self, date: str) -> Dict[str, Any]:
        """Get community interaction summary"""
        return {
            'comments_received': 0,
            'positive_feedback': 0,
            'questions_answered': 0,
            'community_engagement': 'positive',
            'inappropriate_interactions': 0
        }
    
    async def _generate_parent_recommendations(self, activity_data: Dict[str, Any], 
                                            safety_incidents: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for parents"""
        recommendations = []
        
        # Screen time recommendations
        screen_time = activity_data.get('total_screen_time', 0)
        max_time = self.parent_preferences.get('max_daily_screen_time', 180)
        
        if screen_time > max_time:
            recommendations.append(f"Consider reducing screen time - exceeded daily limit by {screen_time - max_time} minutes")
        elif screen_time < 30:
            recommendations.append("Great job maintaining balanced screen time!")
        
        # Educational progress recommendations
        edu_score = activity_data.get('educational_score_avg', 0)
        if edu_score >= 8:
            recommendations.append("Excellent educational content quality - consider celebrating this achievement!")
        elif edu_score < 6:
            recommendations.append("Focus on improving educational value in reviews - consider discussing learning goals")
        
        # Safety recommendations
        if safety_incidents:
            recommendations.append("Review safety incidents and discuss appropriate content guidelines")
        else:
            recommendations.append("No safety concerns today - content guidelines are being followed well")
        
        # General encouragement
        reviews_created = activity_data.get('reviews_created', 0)
        if reviews_created > 0:
            recommendations.append(f"Created {reviews_created} review(s) today - great creative productivity!")
        
        return recommendations
    
    async def _store_activity_report(self, report: ActivityReport):
        """Store activity report for future reference"""
        reports_dir = os.path.join(self.project_root, 'learning_memory', 'parent_reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        report_file = os.path.join(reports_dir, f"{report.report_id}.json")
        
        try:
            with open(report_file, 'w') as f:
                json.dump(asdict(report), f, indent=2)
        except Exception as e:
            print(f"Error storing activity report: {e}")
    
    async def _log_safety_incident(self, incident_type: str, severity: str, 
                                 description: str, review_id: str = None):
        """Log safety incident"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        incident_id = hashlib.md5(f"{incident_type}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        try:
            cursor.execute("""
                INSERT INTO safety_incidents 
                (incident_id, incident_type, severity, description, review_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (incident_id, incident_type, severity, description, review_id, datetime.now().isoformat()))
            
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error logging safety incident: {e}")
        finally:
            conn.close()
    
    async def _log_parent_decision(self, request_id: str, decision: str, comments: str):
        """Log parent decision for tracking"""
        feedback_id = hashlib.md5(f"{request_id}{decision}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO parent_feedback 
                (feedback_id, review_id, feedback_type, feedback_text, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (feedback_id, request_id, decision, comments, datetime.now().isoformat()))
            
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error logging parent decision: {e}")
        finally:
            conn.close()
    
    async def _store_parent_notification(self, notification_data: Dict[str, Any]):
        """Store parent notification"""
        notifications_dir = os.path.join(self.project_root, 'web_interface', 'notifications', 'parent')
        os.makedirs(notifications_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        notification_file = os.path.join(notifications_dir, f"parent_notification_{timestamp}.json")
        
        try:
            with open(notification_file, 'w') as f:
                json.dump(notification_data, f, indent=2)
        except Exception as e:
            print(f"Error storing parent notification: {e}")
    
    async def _send_approval_email(self, request: ReviewApprovalRequest, notification_data: Dict[str, Any]):
        """Send approval request email to parent"""
        
        email = self.parent_preferences.get('notification_email')
        if not email:
            return
        
        subject = f"VR Review Approval Needed: {request.game_name}"
        
        body = f"""
        Hi! Your child has created a new VR game review that needs your approval.
        
        Game: {request.game_name}
        Game Rating: {request.game_rating}
        Educational Value: {request.educational_value}/10
        Safety Score: {notification_data.get('safety_score', 'N/A')}/10
        
        Summary: {request.content_summary}
        
        Please review and approve at: {notification_data.get('approval_url', 'Parent Dashboard')}
        
        This is an automated message from VR Game Review Studio.
        """
        
        # Note: Email sending would require SMTP configuration
        # For now, we'll just log the email content
        print(f"Email notification prepared for: {email}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
    
    def _format_screen_time(self, minutes: int) -> str:
        """Format screen time in human-readable format"""
        if minutes < 60:
            return f"{minutes} minutes"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes == 0:
                return f"{hours} hour{'s' if hours != 1 else ''}"
            else:
                return f"{hours} hour{'s' if hours != 1 else ''} {remaining_minutes} minutes"
    
    async def _notify_approval_granted(self, request_id: str):
        """Notify child that review was approved"""
        notification = {
            'type': 'approval_granted',
            'request_id': request_id,
            'message': 'Great news! Your review has been approved by your parent/guardian!',
            'timestamp': datetime.now().isoformat()
        }
        
        await self._store_child_notification(notification)
    
    async def _notify_changes_needed(self, request_id: str, comments: str):
        """Notify child that changes are needed"""
        notification = {
            'type': 'changes_needed',
            'request_id': request_id,
            'message': 'Your review needs some changes before it can be published.',
            'parent_feedback': comments,
            'timestamp': datetime.now().isoformat()
        }
        
        await self._store_child_notification(notification)
    
    async def _notify_approval_denied(self, request_id: str, comments: str):
        """Notify child that review was not approved"""
        notification = {
            'type': 'approval_denied',
            'request_id': request_id,
            'message': 'Your review was not approved for publication.',
            'parent_feedback': comments,
            'timestamp': datetime.now().isoformat()
        }
        
        await self._store_child_notification(notification)
    
    async def _store_child_notification(self, notification: Dict[str, Any]):
        """Store notification for child to see"""
        notifications_dir = os.path.join(self.project_root, 'web_interface', 'notifications')
        os.makedirs(notifications_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        notification_file = os.path.join(notifications_dir, f"child_notification_{timestamp}.json")
        
        try:
            with open(notification_file, 'w') as f:
                json.dump(notification, f, indent=2)
        except Exception as e:
            print(f"Error storing child notification: {e}")
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approval requests for parent dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM approval_requests 
                WHERE status = 'pending' 
                ORDER BY created_timestamp DESC
            """)
            
            results = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            pending_approvals = []
            for row in results:
                approval = dict(zip(columns, row))
                # Parse JSON safety assessment
                if approval['safety_assessment']:
                    approval['safety_assessment'] = json.loads(approval['safety_assessment'])
                pending_approvals.append(approval)
            
            return pending_approvals
            
        except sqlite3.Error as e:
            print(f"Error getting pending approvals: {e}")
            return []
        finally:
            conn.close()
    
    def get_parent_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive data for parent dashboard"""
        
        # Get recent activity
        recent_reports = self._get_recent_activity_reports(7)  # Last 7 days
        
        # Get pending approvals
        pending_approvals = self.get_pending_approvals()
        
        # Get safety summary
        safety_summary = self._get_safety_summary(30)  # Last 30 days
        
        # Get quality progress
        quality_progress = self._get_quality_progress_summary(30)
        
        return {
            'pending_approvals': pending_approvals,
            'recent_activity': recent_reports,
            'safety_summary': safety_summary,
            'quality_progress': quality_progress,
            'preferences': self.parent_preferences,
            'recommendations': self._get_parent_recommendations_summary()
        }
    
    def _get_recent_activity_reports(self, days: int) -> List[Dict[str, Any]]:
        """Get recent activity reports"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        try:
            cursor.execute("""
                SELECT * FROM daily_activity 
                WHERE date >= ? 
                ORDER BY date DESC
            """, (cutoff_date,))
            
            results = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            return [dict(zip(columns, row)) for row in results]
            
        except sqlite3.Error as e:
            print(f"Error getting recent activity reports: {e}")
            return []
        finally:
            conn.close()
    
    def _get_safety_summary(self, days: int) -> Dict[str, Any]:
        """Get safety summary for specified period"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        try:
            cursor.execute("""
                SELECT COUNT(*) as total_incidents,
                       SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high_severity,
                       SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical_severity
                FROM safety_incidents 
                WHERE date(timestamp) >= ?
            """, (cutoff_date,))
            
            result = cursor.fetchone()
            
            return {
                'total_incidents': result[0] if result else 0,
                'high_severity_incidents': result[1] if result else 0,
                'critical_incidents': result[2] if result else 0,
                'safety_status': 'excellent' if (result[0] if result else 0) == 0 else 'needs_attention'
            }
            
        except sqlite3.Error as e:
            print(f"Error getting safety summary: {e}")
            return {'total_incidents': 0, 'safety_status': 'unknown'}
        finally:
            conn.close()
    
    def _get_quality_progress_summary(self, days: int) -> Dict[str, Any]:
        """Get quality progress summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        try:
            cursor.execute("""
                SELECT AVG(educational_score_avg) as avg_educational,
                       AVG(quality_score_avg) as avg_quality,
                       COUNT(*) as days_active
                FROM daily_activity 
                WHERE date >= ? AND reviews_created > 0
            """, (cutoff_date,))
            
            result = cursor.fetchone()
            
            return {
                'average_educational_score': round(result[0], 1) if result[0] else 0,
                'average_quality_score': round(result[1], 1) if result[1] else 0,
                'days_active': result[2] if result else 0,
                'progress_trend': 'improving'  # This would be calculated from historical data
            }
            
        except sqlite3.Error as e:
            print(f"Error getting quality progress: {e}")
            return {'average_educational_score': 0, 'average_quality_score': 0}
        finally:
            conn.close()
    
    def _get_parent_recommendations_summary(self) -> List[str]:
        """Get current recommendations for parents"""
        return [
            "Continue encouraging educational content creation",
            "Monitor screen time and take regular breaks",
            "Celebrate quality improvements and learning milestones",
            "Discuss positive gaming community values",
            "Review content together to support learning"
        ]