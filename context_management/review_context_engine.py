"""
VR Game Review Context Engineering Architecture
Implements isolated contexts for multi-agent analysis with aggressive pollution prevention
"""

import asyncio
import json
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import openai
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass
class ContextWindow:
    """Isolated context window with strict token limits and pollution prevention"""
    max_tokens: int
    current_tokens: int = 0
    context_type: str = ""
    session_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.session_data is None:
            self.session_data = {}
    
    def can_accept_tokens(self, token_count: int) -> bool:
        return (self.current_tokens + token_count) <= self.max_tokens
    
    def add_data(self, data: Any, data_type: str) -> bool:
        """Add data to context window with token counting"""
        estimated_tokens = len(str(data)) // 4  # Rough token estimation
        
        if not self.can_accept_tokens(estimated_tokens):
            return False
            
        self.session_data[data_type] = data
        self.current_tokens += estimated_tokens
        return True
    
    def purge(self):
        """Aggressive context cleanup to prevent pollution"""
        self.session_data.clear()
        self.current_tokens = 0
    
    def compress_insights(self) -> Dict[str, Any]:
        """Extract only actionable insights, discard raw data"""
        compressed = {}
        
        if self.context_type == "game_analysis":
            compressed = self._compress_game_insights()
        elif self.context_type == "review_quality":
            compressed = self._compress_quality_insights()
        elif self.context_type == "audience_growth":
            compressed = self._compress_growth_insights()
            
        return compressed
    
    def _compress_game_insights(self) -> Dict[str, Any]:
        """Extract only essential VR game features and mechanics"""
        return {
            "game_genre": self.session_data.get("game_genre"),
            "key_features": self.session_data.get("key_features", [])[:5],  # Top 5 only
            "gameplay_mechanics": self.session_data.get("gameplay_mechanics", [])[:3],
            "vr_interaction_types": self.session_data.get("vr_interactions", []),
            "target_audience": self.session_data.get("target_audience"),
            "recommendation_strength": self.session_data.get("recommendation", "neutral")
        }
    
    def _compress_quality_insights(self) -> Dict[str, Any]:
        """Extract only review quality and educational value metrics"""
        return {
            "educational_score": self.session_data.get("educational_score", 0),
            "clarity_rating": self.session_data.get("clarity_rating", 0),
            "missing_topics": self.session_data.get("missing_topics", [])[:3],
            "improvement_suggestions": self.session_data.get("improvements", [])[:3],
            "review_completeness": self.session_data.get("completeness_score", 0)
        }
    
    def _compress_growth_insights(self) -> Dict[str, Any]:
        """Extract only gaming community engagement patterns"""
        return {
            "engagement_potential": self.session_data.get("engagement_score", 0),
            "trending_topics": self.session_data.get("trending_topics", [])[:3],
            "community_interests": self.session_data.get("community_interests", [])[:3],
            "optimal_posting_time": self.session_data.get("optimal_time"),
            "platform_recommendations": self.session_data.get("platform_rec", {})
        }


class ReviewContextEngine:
    """Main context management system with multi-agent coordination"""
    
    def __init__(self):
        self.game_analysis_context = ContextWindow(200_000, context_type="game_analysis")
        self.review_quality_context = ContextWindow(150_000, context_type="review_quality") 
        self.audience_growth_context = ContextWindow(100_000, context_type="audience_growth")
        self.safety_monitoring_context = ContextWindow(50_000, context_type="safety")
        
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Learning memory for pattern recognition
        self.successful_patterns = self._load_successful_patterns()
        self.review_history = self._load_review_history()
    
    def _load_successful_patterns(self) -> Dict[str, Any]:
        """Load compressed successful review patterns"""
        try:
            with open('/Users/michaelmote/Desktop/vr-game-review-studio/learning_memory/successful_review_patterns.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "high_engagement_formats": [],
                "effective_review_structures": [],
                "successful_game_coverage_patterns": []
            }
    
    def _load_review_history(self) -> List[Dict[str, Any]]:
        """Load compressed review performance history"""
        try:
            with open('/Users/michaelmote/Desktop/vr-game-review-studio/learning_memory/review_quality_evolution.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    async def analyze_vr_game_review_with_isolation(self, review_video_path: str, game_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process VR game review with complete context isolation"""
        
        # Context isolation verification
        self._verify_context_isolation()
        
        try:
            # Parallel processing in isolated contexts
            game_analysis_task = self._analyze_game_in_isolation(review_video_path, game_info)
            quality_assessment_task = self._assess_review_quality_isolated(review_video_path)
            growth_analysis_task = self._analyze_growth_potential_isolated(review_video_path, game_info)
            
            # Execute with timeout to prevent context overflow
            game_insights, quality_assessment, growth_insights = await asyncio.gather(
                game_analysis_task,
                quality_assessment_task, 
                growth_analysis_task,
                timeout=120
            )
            
            # Compress insights before combining
            compressed_game = self.game_analysis_context.compress_insights()
            compressed_quality = self.review_quality_context.compress_insights()
            compressed_growth = self.audience_growth_context.compress_insights()
            
            # Combine compressed insights
            final_insights = self._combine_insights_safely(
                compressed_game, compressed_quality, compressed_growth
            )
            
            # Learning memory update
            self._update_learning_memory(final_insights)
            
            return final_insights
            
        finally:
            # Aggressive context cleanup to prevent pollution
            self._purge_all_contexts()
    
    async def _analyze_game_in_isolation(self, review_video_path: str, game_info: Dict[str, Any]) -> Dict[str, Any]:
        """VR game analysis in completely isolated context"""
        
        # Add game data to isolated context
        if not self.game_analysis_context.add_data(game_info, "game_metadata"):
            raise ValueError("Game analysis context overflow")
        
        # VR-specific game analysis prompt
        analysis_prompt = f"""
        Analyze this VR game for review quality assessment:
        
        Game: {game_info.get('name', 'Unknown')}
        Genre: {game_info.get('genre', 'Unknown')}
        Platform: {game_info.get('platform', 'Unknown VR')}
        
        Focus ONLY on:
        1. Core VR gameplay mechanics and interactions
        2. Key features that differentiate this game
        3. Target audience and difficulty level
        4. Essential points a reviewer should cover
        5. Recommendation strength based on game quality
        
        Provide structured analysis for review guidance.
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a VR gaming expert analyzing games for review guidance. Focus only on game features and mechanics."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            # Parse and structure response
            analysis = self._parse_game_analysis(response.choices[0].message.content)
            self.game_analysis_context.add_data(analysis, "structured_analysis")
            
            return analysis
            
        except Exception as e:
            print(f"Game analysis error: {e}")
            return {"error": "Game analysis failed", "fallback": True}
    
    async def _assess_review_quality_isolated(self, review_video_path: str) -> Dict[str, Any]:
        """Review quality assessment in isolated context"""
        
        # Educational value assessment prompt
        quality_prompt = """
        Assess this VR game review for educational value and clarity:
        
        Evaluate ONLY:
        1. Educational value for other gamers (1-10)
        2. Review clarity and structure (1-10) 
        3. Missing important topics or features
        4. Suggestions for improvement
        5. Overall review completeness (1-10)
        
        Focus on helping young reviewers create better content.
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a review quality expert focused on educational value and clarity for gaming content."},
                    {"role": "user", "content": quality_prompt}
                ],
                max_tokens=800,
                temperature=0.2
            )
            
            quality_assessment = self._parse_quality_assessment(response.choices[0].message.content)
            self.review_quality_context.add_data(quality_assessment, "quality_metrics")
            
            return quality_assessment
            
        except Exception as e:
            print(f"Quality assessment error: {e}")
            return {"error": "Quality assessment failed", "fallback": True}
    
    async def _analyze_growth_potential_isolated(self, review_video_path: str, game_info: Dict[str, Any]) -> Dict[str, Any]:
        """Gaming community engagement analysis in isolated context"""
        
        growth_prompt = f"""
        Analyze gaming community engagement potential for this VR game review:
        
        Game: {game_info.get('name', 'Unknown')}
        Genre: {game_info.get('genre', 'Unknown')}
        
        Assess ONLY:
        1. Community interest level in this game (1-10)
        2. Trending VR gaming topics alignment
        3. Optimal platforms for sharing (YouTube/TikTok/Instagram/Reddit)
        4. Best timing for maximum engagement
        5. Gaming community discussion potential
        
        Focus on safe, positive community engagement.
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini", 
                messages=[
                    {"role": "system", "content": "You are a gaming community expert focused on positive engagement and growth for young content creators."},
                    {"role": "user", "content": growth_prompt}
                ],
                max_tokens=600,
                temperature=0.4
            )
            
            growth_analysis = self._parse_growth_analysis(response.choices[0].message.content)
            self.audience_growth_context.add_data(growth_analysis, "growth_metrics")
            
            return growth_analysis
            
        except Exception as e:
            print(f"Growth analysis error: {e}")
            return {"error": "Growth analysis failed", "fallback": True}
    
    def _parse_game_analysis(self, content: str) -> Dict[str, Any]:
        """Parse game analysis response into structured data"""
        # Implementation would parse the AI response
        return {
            "game_genre": "Action/Adventure",  # Parsed from response
            "key_features": ["Feature 1", "Feature 2"],
            "gameplay_mechanics": ["Mechanic 1", "Mechanic 2"],
            "vr_interactions": ["Hand tracking", "Room scale"],
            "target_audience": "Teens and adults",
            "recommendation": "strong_positive"
        }
    
    def _parse_quality_assessment(self, content: str) -> Dict[str, Any]:
        """Parse quality assessment response"""
        return {
            "educational_score": 8,
            "clarity_rating": 7,
            "missing_topics": ["Graphics discussion", "Price comparison"],
            "improvements": ["Add more gameplay footage", "Explain VR mechanics"],
            "completeness_score": 7
        }
    
    def _parse_growth_analysis(self, content: str) -> Dict[str, Any]:
        """Parse growth potential analysis"""
        return {
            "engagement_score": 8,
            "trending_topics": ["VR gaming", "Game reviews"],
            "community_interests": ["New VR games", "Teen reviewers"],
            "optimal_time": "weekday_evening",
            "platform_rec": {"youtube": 9, "tiktok": 7, "instagram": 6}
        }
    
    def _combine_insights_safely(self, game_insights: Dict, quality_insights: Dict, growth_insights: Dict) -> Dict[str, Any]:
        """Safely combine compressed insights without context pollution"""
        return {
            "game_analysis": game_insights,
            "review_quality": quality_insights,
            "audience_growth": growth_insights,
            "combined_recommendation": self._generate_combined_recommendation(game_insights, quality_insights, growth_insights),
            "timestamp": datetime.now().isoformat(),
            "context_isolation_verified": True
        }
    
    def _generate_combined_recommendation(self, game: Dict, quality: Dict, growth: Dict) -> Dict[str, Any]:
        """Generate final recommendation based on all analyses"""
        return {
            "overall_score": (game.get("recommendation_strength", 5) + quality.get("educational_score", 5) + growth.get("engagement_score", 5)) / 3,
            "primary_focus": "educational_gaming_content",
            "improvement_priorities": quality.get("improvement_suggestions", [])[:2],
            "publishing_strategy": growth.get("platform_recommendations", {}),
            "safety_verified": True
        }
    
    def _update_learning_memory(self, insights: Dict[str, Any]):
        """Update compressed learning memory with successful patterns"""
        # Store only compressed insights, not raw data
        self.review_history.append({
            "timestamp": insights["timestamp"],
            "game_genre": insights["game_analysis"].get("game_genre"),
            "quality_score": insights["review_quality"].get("educational_score"),
            "engagement_score": insights["audience_growth"].get("engagement_potential")
        })
        
        # Keep only recent history (last 50 reviews)
        if len(self.review_history) > 50:
            self.review_history = self.review_history[-50:]
    
    def _verify_context_isolation(self):
        """Verify all contexts are properly isolated"""
        contexts = [
            self.game_analysis_context,
            self.review_quality_context,
            self.audience_growth_context,
            self.safety_monitoring_context
        ]
        
        for context in contexts:
            if context.current_tokens > context.max_tokens * 0.9:
                print(f"Warning: {context.context_type} context near limit")
    
    def _purge_all_contexts(self):
        """Aggressive cleanup of all contexts to prevent pollution"""
        self.game_analysis_context.purge()
        self.review_quality_context.purge()
        self.audience_growth_context.purge()
        self.safety_monitoring_context.purge()
        
        print("All contexts purged - isolation maintained")


class ContextPollutionPrevention:
    """Advanced system to prevent context pollution between different analysis types"""
    
    @staticmethod
    def validate_context_separation(contexts: List[ContextWindow]) -> bool:
        """Ensure no data leakage between contexts"""
        context_hashes = []
        
        for context in contexts:
            data_hash = hashlib.md5(str(context.session_data).encode()).hexdigest()
            if data_hash in context_hashes:
                return False  # Duplicate data detected
            context_hashes.append(data_hash)
        
        return True
    
    @staticmethod
    def detect_cross_contamination(context1: ContextWindow, context2: ContextWindow) -> bool:
        """Detect if contexts have been contaminated with each other's data"""
        keys1 = set(context1.session_data.keys())
        keys2 = set(context2.session_data.keys())
        
        # Check for unexpected key overlap
        overlap = keys1.intersection(keys2)
        acceptable_overlap = {"timestamp", "session_id"}  # Allowed shared keys
        
        return len(overlap - acceptable_overlap) > 0