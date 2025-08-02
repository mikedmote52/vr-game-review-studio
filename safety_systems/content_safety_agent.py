"""
Content Safety Agent for VR Game Review Studio
Ensures all review content is appropriate for 13-year-old reviewer and teen audiences
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import openai
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass
class SafetyAssessment:
    """Comprehensive safety assessment results"""
    content_safe: bool
    language_appropriate: bool
    topics_suitable: bool
    age_rating_compliant: bool
    educational_focus_maintained: bool
    positive_messaging: bool
    overall_safety_score: float
    
    def is_safe_for_publication(self) -> bool:
        """Determine if content is safe for young reviewer to publish"""
        return (self.content_safe and 
                self.language_appropriate and 
                self.topics_suitable and 
                self.overall_safety_score >= 8.0)

@dataclass
class SafetyViolation:
    """Individual safety violation details"""
    violation_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    timestamp_location: str
    suggested_fix: str
    requires_removal: bool

class ContentSafetyAgent:
    """AI-powered content safety monitoring for young VR game reviewers"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Age-appropriate content guidelines
        self.safety_guidelines = {
            'language': {
                'prohibited_words': [
                    # Explicit language
                    'curse_words', 'profanity', 'vulgar_terms'
                ],
                'discouraged_phrases': [
                    'this sucks', 'this is stupid', 'waste of money'
                ],
                'encouraged_alternatives': {
                    'this sucks': 'this could be better',
                    'this is stupid': 'this design choice is confusing',
                    'waste of money': 'not the best value'
                }
            },
            'content_themes': {
                'prohibited_topics': [
                    'graphic_violence', 'sexual_content', 'drug_use',
                    'gambling', 'hate_speech', 'self_harm'
                ],
                'requires_warning': [
                    'mild_violence', 'scary_content', 'competitive_elements',
                    'in_app_purchases', 'online_interactions'
                ],
                'educational_focus': [
                    'game_mechanics', 'learning_opportunities', 'skill_development',
                    'creativity', 'problem_solving', 'positive_social_interaction'
                ]
            },
            'positive_messaging': {
                'encouraged_values': [
                    'honesty', 'fairness', 'respect_for_others', 'learning',
                    'perseverance', 'creativity', 'inclusivity'
                ],
                'discouraged_attitudes': [
                    'elitism', 'gatekeeping', 'toxic_competition',
                    'dismissiveness', 'negativity_without_constructiveness'
                ]
            }
        }
        
        # Content warning systems
        self.content_warnings = {
            'mild_violence': "This game contains mild cartoon violence",
            'scary_content': "This game has some scary or suspenseful moments",
            'online_interactions': "This game includes online multiplayer with other players",
            'in_app_purchases': "This game offers additional content for purchase"
        }
        
        # Educational content priorities
        self.educational_priorities = [
            'game_mechanics_explanation',
            'decision_making_guidance',
            'technology_education',
            'critical_thinking_development',
            'responsible_gaming_habits',
            'positive_community_interaction'
        ]
    
    async def comprehensive_safety_analysis(self, review_content: str, game_info: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive safety analysis of review content"""
        
        try:
            # Parallel safety analyses
            safety_tasks = [
                self._analyze_language_appropriateness(review_content),
                self._assess_content_themes(review_content, game_info),
                self._evaluate_educational_focus(review_content),
                self._check_positive_messaging(review_content),
                self._verify_age_compliance(review_content, game_info)
            ]
            
            language_analysis, theme_analysis, educational_analysis, messaging_analysis, age_analysis = await asyncio.gather(
                *safety_tasks, return_exceptions=True
            )
            
            # Handle any analysis failures
            if isinstance(language_analysis, Exception):
                language_analysis = self._create_fallback_language_analysis()
            if isinstance(theme_analysis, Exception):
                theme_analysis = self._create_fallback_theme_analysis()
            if isinstance(educational_analysis, Exception):
                educational_analysis = self._create_fallback_educational_analysis()
            if isinstance(messaging_analysis, Exception):
                messaging_analysis = self._create_fallback_messaging_analysis()
            if isinstance(age_analysis, Exception):
                age_analysis = self._create_fallback_age_analysis()
            
            # Combine analyses into comprehensive assessment
            safety_assessment = self._create_safety_assessment(
                language_analysis, theme_analysis, educational_analysis, 
                messaging_analysis, age_analysis
            )
            
            # Generate specific violations and fixes
            violations = self._identify_safety_violations(
                language_analysis, theme_analysis, educational_analysis, messaging_analysis
            )
            
            # Create improvement recommendations
            safety_improvements = self._generate_safety_improvements(violations, safety_assessment)
            
            return {
                'safety_assessment': safety_assessment.__dict__,
                'language_analysis': language_analysis,
                'theme_analysis': theme_analysis,
                'educational_analysis': educational_analysis,
                'messaging_analysis': messaging_analysis,
                'age_compliance': age_analysis,
                'safety_violations': [v.__dict__ for v in violations],
                'safety_improvements': safety_improvements,
                'requires_parent_review': self._requires_parent_review(safety_assessment, violations),
                'safe_for_publication': safety_assessment.is_safe_for_publication(),
                'assessment_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Comprehensive safety analysis error: {e}")
            return self._create_fallback_safety_analysis()
    
    async def _analyze_language_appropriateness(self, content: str) -> Dict[str, Any]:
        """Analyze language appropriateness for teen audiences"""
        
        language_prompt = f"""
        Analyze this VR game review content for language appropriateness for a 13-year-old content creator and teen audience:
        
        Review Content: {content[:2000]}...
        
        Evaluate language elements:
        1. Any inappropriate or offensive language
        2. Vocabulary complexity level for teen audiences
        3. Tone and attitude appropriateness
        4. Professional vs casual language balance
        5. Respectful discussion of game elements
        6. Constructive criticism vs destructive negativity
        7. Inclusive and welcoming language use
        
        Check for specific issues:
        - Profanity or inappropriate expressions
        - Overly negative or discouraging language
        - Complex technical jargon without explanation
        - Disrespectful comments about developers or players
        - Elitist or exclusionary attitudes
        
        Provide suggestions for any language improvements needed.
        
        Respond in JSON format:
        {{
            "language_appropriate": true,
            "vocabulary_level": "appropriate_for_teens",
            "tone_assessment": "positive_and_encouraging",
            "inappropriate_language_detected": false,
            "language_issues": [],
            "suggested_replacements": {{}},
            "professionalism_score": 8,
            "respectfulness_score": 9,
            "inclusivity_score": 8,
            "language_recommendations": []
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a content safety expert specializing in age-appropriate language for young content creators. Focus on ensuring language is suitable for teen audiences and promotes positive values."},
                    {"role": "user", "content": language_prompt}
                ],
                max_tokens=800,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Language analysis error: {e}")
            return self._create_fallback_language_analysis()
    
    async def _assess_content_themes(self, content: str, game_info: Dict[str, Any]) -> Dict[str, Any]:
        """Assess content themes and topics for appropriateness"""
        
        theme_prompt = f"""
        Assess the content themes and topics in this VR game review for appropriateness:
        
        Game: {game_info.get('name', 'Unknown')}
        Game Rating: {game_info.get('age_rating', 'Unknown')}
        Review Content: {content[:2000]}...
        
        Evaluate content themes:
        1. Age-appropriate discussion of game content
        2. Appropriate handling of any mature themes
        3. Educational vs entertainment focus balance
        4. Positive gaming community messaging
        5. Responsible gaming habit promotion
        6. Appropriate context for competitive elements
        7. Constructive approach to criticism
        
        Check for concerning content:
        - Inappropriate discussion of mature game content
        - Promotion of unhealthy gaming habits
        - Negative community attitudes
        - Overly competitive or elitist messaging
        - Lack of content warnings where needed
        
        Assess educational value and positive messaging.
        
        Respond in JSON format:
        {{
            "themes_appropriate": true,
            "educational_focus_maintained": true,
            "positive_messaging_present": true,
            "content_warnings_needed": [],
            "mature_content_handling": "appropriate",
            "community_messaging": "positive",
            "educational_value_score": 8,
            "theme_concerns": [],
            "recommended_content_warnings": [],
            "theme_improvements": []
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a content theme specialist ensuring age-appropriate and educational content for young gaming content creators. Focus on positive community values and educational messaging."},
                    {"role": "user", "content": theme_prompt}
                ],
                max_tokens=800,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Theme analysis error: {e}")
            return self._create_fallback_theme_analysis()
    
    async def _evaluate_educational_focus(self, content: str) -> Dict[str, Any]:
        """Evaluate maintenance of educational focus throughout content"""
        
        educational_prompt = f"""
        Evaluate how well this VR game review maintains educational focus suitable for young content creators:
        
        Review Content: {content[:2000]}...
        
        Educational elements to assess:
        1. Clear explanations of game concepts
        2. Learning opportunities for viewers
        3. Decision-making guidance provided
        4. Technology education elements
        5. Critical thinking skill development
        6. Positive role modeling
        7. Constructive feedback and criticism
        
        Check educational effectiveness:
        - Are complex concepts explained clearly?
        - Does content help viewers learn about VR gaming?
        - Are positive gaming values promoted?
        - Is content genuinely helpful for decision-making?
        - Does reviewer model good behavior and attitudes?
        
        Assess educational value and learning outcomes.
        
        Respond in JSON format:
        {{
            "educational_focus_maintained": true,
            "learning_opportunities_present": true,
            "concepts_explained_clearly": true,
            "decision_guidance_provided": true,
            "positive_role_modeling": true,
            "educational_effectiveness_score": 8,
            "learning_outcomes": [],
            "educational_gaps": [],
            "educational_improvements": []
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an educational content specialist evaluating learning value for young content creators. Focus on educational effectiveness and positive learning outcomes."},
                    {"role": "user", "content": educational_prompt}
                ],
                max_tokens=700,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Educational analysis error: {e}")
            return self._create_fallback_educational_analysis()
    
    async def _check_positive_messaging(self, content: str) -> Dict[str, Any]:
        """Check for positive messaging and community values"""
        
        messaging_prompt = f"""
        Analyze this VR game review for positive messaging and community values:
        
        Review Content: {content[:2000]}...
        
        Positive messaging elements:
        1. Encouraging and supportive tone
        2. Respectful discussion of games and developers
        3. Inclusive language and attitudes
        4. Constructive criticism approach
        5. Positive gaming community promotion
        6. Helpful and educational intent
        7. Inspiring confidence in viewers
        
        Check for negative patterns:
        - Overly harsh or discouraging criticism
        - Elitist or exclusionary attitudes
        - Dismissive comments about other players
        - Unnecessarily negative tone
        - Lack of constructive suggestions
        
        Assess overall positivity and community impact.
        
        Respond in JSON format:
        {{
            "positive_messaging_present": true,
            "encouraging_tone": true,
            "respectful_criticism": true,
            "inclusive_language": true,
            "community_positive_impact": true,
            "positivity_score": 8,
            "negative_patterns_detected": [],
            "positive_elements": [],
            "messaging_improvements": []
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a positive community messaging expert ensuring content promotes healthy gaming communities. Focus on encouraging, inclusive, and constructive communication."},
                    {"role": "user", "content": messaging_prompt}
                ],
                max_tokens=600,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Messaging analysis error: {e}")
            return self._create_fallback_messaging_analysis()
    
    async def _verify_age_compliance(self, content: str, game_info: Dict[str, Any]) -> Dict[str, Any]:
        """Verify age rating compliance and appropriateness"""
        
        age_prompt = f"""
        Verify age rating compliance and appropriateness for this VR game review:
        
        Game: {game_info.get('name', 'Unknown')}
        Game Age Rating: {game_info.get('age_rating', 'Unknown')}
        Review Content: {content[:2000]}...
        
        Age compliance verification:
        1. Appropriate discussion of age-rated content
        2. Suitable content warnings provided
        3. Responsible handling of mature themes
        4. Age-appropriate vocabulary and concepts
        5. Parental guidance considerations
        6. Content suitable for teen creator and audience
        7. Compliance with content rating guidelines
        
        Check compliance factors:
        - Does discussion match game's age rating?
        - Are content warnings provided where needed?
        - Is language appropriate for 13+ audience?
        - Would parents approve of this content?
        - Does content promote age-appropriate gaming?
        
        Assess overall age appropriateness and compliance.
        
        Respond in JSON format:
        {{
            "age_rating_compliant": true,
            "content_appropriate_for_teens": true,
            "parental_approval_likely": true,
            "content_warnings_adequate": true,
            "vocabulary_age_appropriate": true,
            "compliance_score": 9,
            "compliance_issues": [],
            "required_content_warnings": [],
            "age_appropriateness_improvements": []
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an age rating and content compliance expert ensuring content is appropriate for teen content creators and audiences. Focus on age-appropriate content and parental approval factors."},
                    {"role": "user", "content": age_prompt}
                ],
                max_tokens=600,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Age compliance analysis error: {e}")
            return self._create_fallback_age_analysis()
    
    def _create_safety_assessment(self, language_analysis: Dict, theme_analysis: Dict, 
                                 educational_analysis: Dict, messaging_analysis: Dict, 
                                 age_analysis: Dict) -> SafetyAssessment:
        """Create comprehensive safety assessment from individual analyses"""
        
        # Extract key safety indicators
        content_safe = (
            theme_analysis.get('themes_appropriate', True) and
            age_analysis.get('content_appropriate_for_teens', True)
        )
        
        language_appropriate = (
            language_analysis.get('language_appropriate', True) and
            language_analysis.get('respectfulness_score', 5) >= 7
        )
        
        topics_suitable = (
            theme_analysis.get('themes_appropriate', True) and
            not theme_analysis.get('theme_concerns', [])
        )
        
        age_rating_compliant = age_analysis.get('age_rating_compliant', True)
        
        educational_focus_maintained = educational_analysis.get('educational_focus_maintained', True)
        
        positive_messaging = messaging_analysis.get('positive_messaging_present', True)
        
        # Calculate overall safety score
        scores = [
            language_analysis.get('professionalism_score', 5),
            language_analysis.get('respectfulness_score', 5),
            theme_analysis.get('educational_value_score', 5),
            educational_analysis.get('educational_effectiveness_score', 5),
            messaging_analysis.get('positivity_score', 5),
            age_analysis.get('compliance_score', 5)
        ]
        
        overall_safety_score = sum(scores) / len(scores)
        
        return SafetyAssessment(
            content_safe=content_safe,
            language_appropriate=language_appropriate,
            topics_suitable=topics_suitable,
            age_rating_compliant=age_rating_compliant,
            educational_focus_maintained=educational_focus_maintained,
            positive_messaging=positive_messaging,
            overall_safety_score=round(overall_safety_score, 1)
        )
    
    def _identify_safety_violations(self, language_analysis: Dict, theme_analysis: Dict,
                                  educational_analysis: Dict, messaging_analysis: Dict) -> List[SafetyViolation]:
        """Identify specific safety violations from analyses"""
        
        violations = []
        
        # Language violations
        if language_analysis.get('inappropriate_language_detected', False):
            for issue in language_analysis.get('language_issues', []):
                violations.append(SafetyViolation(
                    violation_type='inappropriate_language',
                    severity='high',
                    description=f"Inappropriate language detected: {issue}",
                    timestamp_location='throughout_content',
                    suggested_fix=language_analysis.get('suggested_replacements', {}).get(issue, 'Remove or replace language'),
                    requires_removal=True
                ))
        
        # Theme violations
        for concern in theme_analysis.get('theme_concerns', []):
            violations.append(SafetyViolation(
                violation_type='inappropriate_theme',
                severity='medium',
                description=f"Theme concern: {concern}",
                timestamp_location='content_section',
                suggested_fix='Add content warning or modify discussion approach',
                requires_removal=False
            ))
        
        # Educational focus violations
        if not educational_analysis.get('educational_focus_maintained', True):
            violations.append(SafetyViolation(
                violation_type='educational_focus_loss',
                severity='medium',
                description='Educational focus not maintained throughout content',
                timestamp_location='multiple_sections',
                suggested_fix='Add more educational elements and learning opportunities',
                requires_removal=False
            ))
        
        # Positive messaging violations
        for negative_pattern in messaging_analysis.get('negative_patterns_detected', []):
            violations.append(SafetyViolation(
                violation_type='negative_messaging',
                severity='medium',
                description=f"Negative messaging pattern: {negative_pattern}",
                timestamp_location='content_section',
                suggested_fix='Reframe with more positive, constructive approach',
                requires_removal=False
            ))
        
        return violations
    
    def _generate_safety_improvements(self, violations: List[SafetyViolation], 
                                    safety_assessment: SafetyAssessment) -> List[Dict[str, Any]]:
        """Generate specific safety improvement recommendations"""
        
        improvements = []
        
        # Critical violations requiring immediate attention
        critical_violations = [v for v in violations if v.severity == 'critical']
        if critical_violations:
            improvements.append({
                'priority': 'critical',
                'category': 'content_removal',
                'title': 'Critical Content Issues',
                'description': 'Content contains critical safety violations that must be addressed before publication',
                'actions': [v.suggested_fix for v in critical_violations],
                'estimated_time': '30-60 minutes'
            })
        
        # High priority violations
        high_violations = [v for v in violations if v.severity == 'high']
        if high_violations:
            improvements.append({
                'priority': 'high',
                'category': 'language_and_tone',
                'title': 'Language and Tone Improvements',
                'description': 'Language or tone needs adjustment for teen audience appropriateness',
                'actions': [v.suggested_fix for v in high_violations],
                'estimated_time': '15-30 minutes'
            })
        
        # Educational improvements
        if not safety_assessment.educational_focus_maintained:
            improvements.append({
                'priority': 'medium',
                'category': 'educational_enhancement',
                'title': 'Educational Value Enhancement',
                'description': 'Strengthen educational focus and learning opportunities',
                'actions': [
                    'Add more detailed explanations of game concepts',
                    'Include learning opportunities for viewers',
                    'Provide clearer decision-making guidance',
                    'Explain technical terms for beginners'
                ],
                'estimated_time': '20-40 minutes'
            })
        
        # Positive messaging improvements
        if not safety_assessment.positive_messaging:
            improvements.append({
                'priority': 'medium',
                'category': 'community_positivity',
                'title': 'Community and Messaging Enhancement',
                'description': 'Improve positive messaging and community impact',
                'actions': [
                    'Use more encouraging and supportive language',
                    'Frame criticism constructively',
                    'Include positive community messaging',
                    'Add inspiring and confidence-building elements'
                ],
                'estimated_time': '15-25 minutes'
            })
        
        # General safety enhancements
        if safety_assessment.overall_safety_score < 8.0:
            improvements.append({
                'priority': 'low',
                'category': 'general_safety',
                'title': 'General Safety Enhancements',
                'description': 'Overall improvements to meet safety standards',
                'actions': [
                    'Review content for age appropriateness',
                    'Add content warnings where appropriate',
                    'Ensure parental approval considerations',
                    'Verify educational value throughout'
                ],
                'estimated_time': '10-20 minutes'
            })
        
        return improvements
    
    def _requires_parent_review(self, safety_assessment: SafetyAssessment, 
                               violations: List[SafetyViolation]) -> bool:
        """Determine if content requires parent/guardian review"""
        
        # Always require parent review for critical violations
        if any(v.severity == 'critical' for v in violations):
            return True
        
        # Require parent review if multiple high-severity violations
        high_violations = [v for v in violations if v.severity == 'high']
        if len(high_violations) >= 2:
            return True
        
        # Require parent review if overall safety score is low
        if safety_assessment.overall_safety_score < 7.0:
            return True
        
        # Require parent review if age appropriateness is questionable
        if not safety_assessment.age_rating_compliant:
            return True
        
        return False
    
    # Fallback methods for error handling
    def _create_fallback_language_analysis(self) -> Dict[str, Any]:
        """Create fallback language analysis"""
        return {
            'language_appropriate': True,
            'vocabulary_level': 'needs_review',
            'tone_assessment': 'needs_assessment',
            'inappropriate_language_detected': False,
            'language_issues': [],
            'suggested_replacements': {},
            'professionalism_score': 6,
            'respectfulness_score': 6,
            'inclusivity_score': 6,
            'language_recommendations': ['Manual review recommended'],
            'fallback_used': True
        }
    
    def _create_fallback_theme_analysis(self) -> Dict[str, Any]:
        """Create fallback theme analysis"""
        return {
            'themes_appropriate': True,
            'educational_focus_maintained': True,
            'positive_messaging_present': True,
            'content_warnings_needed': [],
            'mature_content_handling': 'needs_review',
            'community_messaging': 'needs_assessment',
            'educational_value_score': 6,
            'theme_concerns': [],
            'recommended_content_warnings': [],
            'theme_improvements': ['Manual review recommended'],
            'fallback_used': True
        }
    
    def _create_fallback_educational_analysis(self) -> Dict[str, Any]:
        """Create fallback educational analysis"""
        return {
            'educational_focus_maintained': True,
            'learning_opportunities_present': True,
            'concepts_explained_clearly': True,
            'decision_guidance_provided': True,
            'positive_role_modeling': True,
            'educational_effectiveness_score': 6,
            'learning_outcomes': ['Basic review information'],
            'educational_gaps': ['Requires assessment'],
            'educational_improvements': ['Manual review recommended'],
            'fallback_used': True
        }
    
    def _create_fallback_messaging_analysis(self) -> Dict[str, Any]:
        """Create fallback messaging analysis"""
        return {
            'positive_messaging_present': True,
            'encouraging_tone': True,
            'respectful_criticism': True,
            'inclusive_language': True,
            'community_positive_impact': True,
            'positivity_score': 6,
            'negative_patterns_detected': [],
            'positive_elements': ['Needs assessment'],
            'messaging_improvements': ['Manual review recommended'],
            'fallback_used': True
        }
    
    def _create_fallback_age_analysis(self) -> Dict[str, Any]:
        """Create fallback age analysis"""
        return {
            'age_rating_compliant': True,
            'content_appropriate_for_teens': True,
            'parental_approval_likely': True,
            'content_warnings_adequate': True,
            'vocabulary_age_appropriate': True,
            'compliance_score': 6,
            'compliance_issues': [],
            'required_content_warnings': [],
            'age_appropriateness_improvements': ['Manual review recommended'],
            'fallback_used': True
        }
    
    def _create_fallback_safety_analysis(self) -> Dict[str, Any]:
        """Create fallback safety analysis when system fails"""
        
        fallback_assessment = SafetyAssessment(
            content_safe=True,
            language_appropriate=True,
            topics_suitable=True,
            age_rating_compliant=True,
            educational_focus_maintained=True,
            positive_messaging=True,
            overall_safety_score=7.0
        )
        
        return {
            'safety_assessment': fallback_assessment.__dict__,
            'requires_parent_review': True,
            'safe_for_publication': False,
            'manual_review_required': True,
            'fallback_analysis_used': True,
            'error_message': 'Automated safety analysis failed - manual review required',
            'assessment_timestamp': datetime.now().isoformat()
        }
    
    async def quick_safety_check(self, content_snippet: str) -> bool:
        """Quick safety check for real-time content monitoring"""
        
        try:
            # Basic pattern matching for immediate red flags
            prohibited_patterns = [
                r'\b(damn|hell|crap)\b',  # Mild profanity
                r'\b(suck|stupid|dumb)\b',  # Negative language
                r'\b(hate|disgusting|terrible)\b'  # Strongly negative
            ]
            
            for pattern in prohibited_patterns:
                if re.search(pattern, content_snippet, re.IGNORECASE):
                    return False
            
            return True
            
        except Exception as e:
            print(f"Quick safety check error: {e}")
            return False  # Err on side of caution
    
    def get_content_warning_recommendations(self, game_info: Dict[str, Any]) -> List[str]:
        """Get content warning recommendations based on game information"""
        
        warnings = []
        
        # Check game rating
        age_rating = game_info.get('age_rating', '').lower()
        if 'teen' in age_rating or '13+' in age_rating:
            warnings.append("This game is rated Teen (13+)")
        
        # Check game genre for potential concerns
        genre = game_info.get('genre', '').lower()
        if 'horror' in genre or 'scary' in genre:
            warnings.append("This game contains scary or suspenseful content")
        elif 'action' in genre or 'shooter' in genre:
            warnings.append("This game contains mild action violence")
        elif 'competitive' in genre or 'multiplayer' in genre:
            warnings.append("This game includes online multiplayer interactions")
        
        # Check for VR-specific warnings
        vr_features = game_info.get('vr_interactions', [])
        if any('intense' in feature.lower() for feature in vr_features):
            warnings.append("This VR game may cause motion sickness in some players")
        
        return warnings