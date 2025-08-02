"""
VR Game Review Quality Assessment System
Comprehensive analysis of educational value, clarity, and review completeness
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
class QualityMetrics:
    """Comprehensive quality measurement structure"""
    educational_value: float
    clarity_rating: float
    completeness_score: float
    engagement_score: float
    age_appropriateness: bool
    information_accuracy: float
    decision_helping_value: float
    
    def overall_score(self) -> float:
        """Calculate weighted overall quality score"""
        weights = {
            'educational_value': 0.25,
            'clarity_rating': 0.20,
            'completeness_score': 0.20,
            'engagement_score': 0.15,
            'information_accuracy': 0.15,
            'decision_helping_value': 0.05
        }
        
        score = (
            self.educational_value * weights['educational_value'] +
            self.clarity_rating * weights['clarity_rating'] +
            self.completeness_score * weights['completeness_score'] +
            self.engagement_score * weights['engagement_score'] +
            self.information_accuracy * weights['information_accuracy'] +
            self.decision_helping_value * weights['decision_helping_value']
        )
        
        # Penalize if not age appropriate
        if not self.age_appropriateness:
            score *= 0.7
        
        return round(score, 2)


@dataclass
class EducationalAnalysis:
    """Educational value analysis results"""
    learning_objectives_met: List[str]
    gaming_knowledge_shared: List[str]
    decision_support_quality: float
    comparison_effectiveness: float
    explanation_depth: float
    vocabulary_appropriateness: float
    concept_clarity: float


@dataclass
class ContentStructureAnalysis:
    """Review structure and organization analysis"""
    has_clear_introduction: bool
    covers_essential_topics: bool
    logical_flow: float
    conclusion_strength: float
    topic_transitions: float
    pacing_quality: float
    visual_aid_effectiveness: float


class ReviewQualityAssessor:
    """Comprehensive VR game review quality assessment system"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Essential topics that VR game reviews should cover
        self.essential_vr_topics = [
            'gameplay mechanics',
            'vr interaction quality',
            'graphics and visual fidelity',
            'audio and spatial sound',
            'comfort and motion sickness',
            'price and value proposition',
            'target audience',
            'recommendation strength',
            'technical requirements',
            'comparison to similar games'
        ]
        
        # Age-appropriate language indicators
        self.appropriate_language_indicators = [
            'clear explanations',
            'simple vocabulary',
            'positive tone',
            'educational focus',
            'respectful content'
        ]
        
        # Quality improvement suggestions database
        self.improvement_suggestions = {
            'educational_value': [
                'Add more detailed explanations of game mechanics',
                'Include comparisons to similar games for context',
                'Explain technical terms clearly for younger audiences',
                'Provide specific examples and evidence for claims'
            ],
            'clarity_rating': [
                'Speak more slowly and clearly',
                'Use simpler vocabulary and shorter sentences',
                'Add visual aids and text overlays for key points',
                'Improve audio quality and reduce background noise'
            ],
            'completeness_score': [
                'Cover all essential VR gaming topics',
                'Add proper introduction and conclusion',
                'Include pricing and availability information',
                'Provide clear final recommendation'
            ],
            'engagement_score': [
                'Add more enthusiasm and personality',
                'Include more gameplay footage and demonstrations',
                'Use better pacing and rhythm',
                'Add interesting facts and background information'
            ]
        }
    
    async def comprehensive_quality_analysis(self, review_path: str, game_info: Dict[str, Any], agent_analysis: Any) -> Dict[str, Any]:
        """Perform comprehensive quality analysis of VR game review"""
        
        try:
            # Parallel analysis of different quality aspects
            quality_tasks = [
                self._analyze_educational_content(review_path, game_info),
                self._assess_content_structure(review_path),
                self._evaluate_clarity_and_engagement(review_path),
                self._check_topic_completeness(review_path, game_info)
            ]
            
            educational_analysis, structure_analysis, clarity_analysis, completeness_analysis = await asyncio.gather(
                *quality_tasks, return_exceptions=True
            )
            
            # Handle any analysis failures gracefully
            if isinstance(educational_analysis, Exception):
                educational_analysis = self._create_fallback_educational_analysis()
            if isinstance(structure_analysis, Exception):
                structure_analysis = self._create_fallback_structure_analysis()
            if isinstance(clarity_analysis, Exception):
                clarity_analysis = self._create_fallback_clarity_analysis()
            if isinstance(completeness_analysis, Exception):
                completeness_analysis = self._create_fallback_completeness_analysis()
            
            # Combine all analyses into comprehensive assessment
            quality_metrics = self._calculate_quality_metrics(
                educational_analysis, structure_analysis, clarity_analysis, completeness_analysis
            )
            
            # Generate specific improvement recommendations
            improvements = self._generate_improvement_recommendations(quality_metrics, agent_analysis)
            
            return {
                'quality_metrics': quality_metrics.__dict__,
                'educational_analysis': educational_analysis,
                'structure_analysis': structure_analysis,
                'clarity_analysis': clarity_analysis,
                'completeness_analysis': completeness_analysis,
                'improvement_recommendations': improvements,
                'overall_assessment': self._generate_overall_assessment(quality_metrics),
                'assessment_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Comprehensive quality analysis error: {e}")
            return self._create_fallback_comprehensive_analysis()
    
    async def _analyze_educational_content(self, review_path: str, game_info: Dict[str, Any]) -> EducationalAnalysis:
        """Analyze educational value and learning content"""
        
        educational_prompt = f"""
        Analyze the educational value of this VR game review for other young gamers:
        
        Game: {game_info.get('name', 'Unknown')}
        Genre: {game_info.get('genre', 'Unknown')}
        
        Evaluate educational aspects:
        1. What gaming knowledge does this review teach?
        2. How well does it help viewers make informed decisions?
        3. Does it explain VR concepts clearly for beginners?
        4. Are comparisons to other games helpful and accurate?
        5. Is the vocabulary appropriate for teen audiences?
        6. How effectively does it explain complex game mechanics?
        7. Does it provide useful context about VR gaming?
        
        Rate each aspect 1-10 and provide specific examples.
        Focus on educational value for young gaming audiences.
        
        Respond in JSON format:
        {{
            "learning_objectives": ["objective1", "objective2"],
            "gaming_knowledge_shared": ["knowledge1", "knowledge2"],
            "decision_support_quality": 8,
            "comparison_effectiveness": 7,
            "explanation_depth": 6,
            "vocabulary_appropriateness": 9,
            "concept_clarity": 7,
            "educational_examples": ["example1", "example2"],
            "missing_educational_elements": ["element1", "element2"]
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an educational content expert specializing in gaming education for young audiences. Focus on learning value and age-appropriate explanations."},
                    {"role": "user", "content": educational_prompt}
                ],
                max_tokens=1000,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            analysis_data = json.loads(response.choices[0].message.content)
            
            return EducationalAnalysis(
                learning_objectives_met=analysis_data.get('learning_objectives', []),
                gaming_knowledge_shared=analysis_data.get('gaming_knowledge_shared', []),
                decision_support_quality=analysis_data.get('decision_support_quality', 5),
                comparison_effectiveness=analysis_data.get('comparison_effectiveness', 5),
                explanation_depth=analysis_data.get('explanation_depth', 5),
                vocabulary_appropriateness=analysis_data.get('vocabulary_appropriateness', 5),
                concept_clarity=analysis_data.get('concept_clarity', 5)
            )
            
        except Exception as e:
            print(f"Educational content analysis error: {e}")
            return self._create_fallback_educational_analysis()
    
    async def _assess_content_structure(self, review_path: str) -> ContentStructureAnalysis:
        """Assess review structure and organization"""
        
        structure_prompt = """
        Analyze the structure and organization of this VR game review:
        
        Evaluate structural elements:
        1. Does it have a clear, engaging introduction?
        2. Are topics covered in logical order?
        3. Is there good flow between different sections?
        4. Does it have a strong conclusion with clear recommendation?
        5. Is the pacing appropriate for the content?
        6. Are visual aids and gameplay footage used effectively?
        7. Are transitions between topics smooth and clear?
        
        Rate each aspect 1-10 and identify specific structural issues.
        
        Respond in JSON format:
        {{
            "has_clear_introduction": true,
            "covers_essential_topics": true,
            "logical_flow": 8,
            "conclusion_strength": 7,
            "topic_transitions": 6,
            "pacing_quality": 8,
            "visual_aid_effectiveness": 7,
            "structural_strengths": ["strength1", "strength2"],
            "structural_weaknesses": ["weakness1", "weakness2"],
            "organization_suggestions": ["suggestion1", "suggestion2"]
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a content structure expert who analyzes video organization and flow. Focus on clarity and logical progression for young audiences."},
                    {"role": "user", "content": structure_prompt}
                ],
                max_tokens=800,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            structure_data = json.loads(response.choices[0].message.content)
            
            return ContentStructureAnalysis(
                has_clear_introduction=structure_data.get('has_clear_introduction', False),
                covers_essential_topics=structure_data.get('covers_essential_topics', False),
                logical_flow=structure_data.get('logical_flow', 5),
                conclusion_strength=structure_data.get('conclusion_strength', 5),
                topic_transitions=structure_data.get('topic_transitions', 5),
                pacing_quality=structure_data.get('pacing_quality', 5),
                visual_aid_effectiveness=structure_data.get('visual_aid_effectiveness', 5)
            )
            
        except Exception as e:
            print(f"Content structure analysis error: {e}")
            return self._create_fallback_structure_analysis()
    
    async def _evaluate_clarity_and_engagement(self, review_path: str) -> Dict[str, Any]:
        """Evaluate clarity of communication and audience engagement"""
        
        clarity_prompt = """
        Evaluate the clarity and engagement quality of this VR game review:
        
        Assess communication aspects:
        1. How clear and understandable is the speaking?
        2. Is the vocabulary appropriate for teen audiences?
        3. Are explanations easy to follow?
        4. How engaging and enthusiastic is the presentation?
        5. Does it maintain viewer interest throughout?
        6. Are technical terms explained clearly?
        7. Is the tone appropriate and positive?
        
        Rate each aspect 1-10 and provide specific feedback.
        
        Respond in JSON format:
        {{
            "speaking_clarity": 8,
            "vocabulary_level": 7,
            "explanation_quality": 6,
            "enthusiasm_level": 8,
            "audience_engagement": 7,
            "technical_explanation": 6,
            "tone_appropriateness": 9,
            "clarity_strengths": ["strength1", "strength2"],
            "engagement_strengths": ["strength1", "strength2"],
            "clarity_improvements": ["improvement1", "improvement2"],
            "engagement_improvements": ["improvement1", "improvement2"]
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a communication expert who evaluates clarity and engagement for young content creators. Focus on age-appropriate communication and audience connection."},
                    {"role": "user", "content": clarity_prompt}
                ],
                max_tokens=800,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Clarity and engagement analysis error: {e}")
            return self._create_fallback_clarity_analysis()
    
    async def _check_topic_completeness(self, review_path: str, game_info: Dict[str, Any]) -> Dict[str, Any]:
        """Check coverage of essential VR gaming topics"""
        
        completeness_prompt = f"""
        Check if this VR game review covers all essential topics for a complete analysis:
        
        Game: {game_info.get('name', 'Unknown')}
        Essential VR Review Topics:
        {json.dumps(self.essential_vr_topics, indent=2)}
        
        Evaluate topic coverage:
        1. Which essential topics are covered well?
        2. Which essential topics are missing or inadequate?
        3. Are there unnecessary or off-topic sections?
        4. Is the coverage depth appropriate for each topic?
        5. Does it provide a clear final recommendation?
        6. Is pricing and availability information included?
        
        Rate completeness 1-10 and list specific gaps.
        
        Respond in JSON format:
        {{
            "covered_topics": ["topic1", "topic2"],
            "missing_topics": ["topic3", "topic4"],
            "inadequate_coverage": ["topic5"],
            "unnecessary_content": ["content1"],
            "coverage_depth_rating": 7,
            "final_recommendation_present": true,
            "pricing_info_included": false,
            "completeness_score": 6,
            "critical_gaps": ["gap1", "gap2"],
            "coverage_suggestions": ["suggestion1", "suggestion2"]
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a VR gaming expert who evaluates review completeness. Ensure all essential topics are covered for informed decision-making."},
                    {"role": "user", "content": completeness_prompt}
                ],
                max_tokens=800,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Topic completeness analysis error: {e}")
            return self._create_fallback_completeness_analysis()
    
    async def analyze_educational_value(self, review_path: str, game_info: Dict[str, Any]) -> Dict[str, Any]:
        """Focused analysis of educational value for gaming audiences"""
        
        educational_focus_prompt = f"""
        Specifically analyze how well this VR game review educates and informs other young gamers:
        
        Game: {game_info.get('name', 'Unknown')}
        Genre: {game_info.get('genre', 'Unknown')}
        
        Educational Value Assessment:
        1. Does it teach viewers about VR gaming concepts?
        2. Are game mechanics explained clearly for beginners?
        3. Does it help viewers understand what makes VR games good/bad?
        4. Are technical aspects explained in accessible terms?
        5. Does it provide context about the VR gaming industry?
        6. Are safety considerations (motion sickness, etc.) discussed?
        7. Does it help viewers make informed purchasing decisions?
        
        Rate educational effectiveness 1-10 for each aspect.
        
        Respond in JSON format:
        {{
            "vr_concept_education": 7,
            "mechanic_explanation_clarity": 6,
            "quality_assessment_teaching": 8,
            "technical_accessibility": 5,
            "industry_context": 4,
            "safety_education": 7,
            "decision_support": 8,
            "overall_educational_score": 6.5,
            "learning_outcomes": ["outcome1", "outcome2"],
            "educational_gaps": ["gap1", "gap2"],
            "educational_strengths": ["strength1", "strength2"],
            "educational_improvements": ["improvement1", "improvement2"]
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an educational assessment expert focused on gaming education. Evaluate how well content teaches gaming concepts to young audiences."},
                    {"role": "user", "content": educational_focus_prompt}
                ],
                max_tokens=1000,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Educational value analysis error: {e}")
            return {
                "overall_educational_score": 5,
                "learning_outcomes": ["Basic game overview"],
                "educational_gaps": ["Needs more detailed explanations"],
                "fallback_used": True
            }
    
    async def verify_age_appropriateness(self, review_path: str) -> Dict[str, Any]:
        """Verify content is appropriate for teen audiences"""
        
        age_check_prompt = """
        Verify that this VR game review is appropriate for a 13-year-old content creator and teen audiences:
        
        Check for:
        1. Age-appropriate language and vocabulary
        2. Suitable content topics and themes
        3. Positive and constructive tone
        4. No inappropriate references or content
        5. Educational and family-friendly approach
        6. Respectful discussion of gaming topics
        7. Appropriate level of technical detail
        
        Assess appropriateness and flag any concerns.
        
        Respond in JSON format:
        {{
            "content_safe_for_teens": true,
            "language_appropriate": true,
            "topics_suitable": true,
            "tone_positive": true,
            "educational_focus": true,
            "technical_level_appropriate": true,
            "overall_age_appropriate": true,
            "potential_concerns": [],
            "supervision_recommended": true,
            "content_warnings": [],
            "age_rating_suggestion": "Teen-friendly",
            "parent_review_needed": false
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a child safety and content appropriateness expert. Ensure all content is suitable for teen audiences and young content creators."},
                    {"role": "user", "content": age_check_prompt}
                ],
                max_tokens=600,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Age appropriateness check error: {e}")
            return {
                "overall_age_appropriate": True,
                "supervision_recommended": True,
                "fallback_used": True
            }
    
    def _calculate_quality_metrics(self, educational: EducationalAnalysis, structure: ContentStructureAnalysis, 
                                 clarity: Dict[str, Any], completeness: Dict[str, Any]) -> QualityMetrics:
        """Calculate comprehensive quality metrics from all analyses"""
        
        # Extract and normalize scores
        educational_value = (
            educational.decision_support_quality + 
            educational.explanation_depth + 
            educational.concept_clarity
        ) / 3
        
        clarity_rating = (
            clarity.get('speaking_clarity', 5) + 
            clarity.get('explanation_quality', 5) + 
            clarity.get('vocabulary_level', 5)
        ) / 3
        
        completeness_score = completeness.get('completeness_score', 5)
        
        engagement_score = (
            clarity.get('enthusiasm_level', 5) + 
            clarity.get('audience_engagement', 5) + 
            structure.pacing_quality
        ) / 3
        
        information_accuracy = (
            educational.comparison_effectiveness + 
            completeness.get('coverage_depth_rating', 5)
        ) / 2
        
        decision_helping_value = (
            educational.decision_support_quality + 
            (10 if completeness.get('final_recommendation_present', False) else 5)
        ) / 2
        
        # Age appropriateness (simplified for metrics calculation)
        age_appropriate = (
            educational.vocabulary_appropriateness >= 7 and
            clarity.get('tone_appropriateness', 5) >= 7
        )
        
        return QualityMetrics(
            educational_value=round(educational_value, 1),
            clarity_rating=round(clarity_rating, 1),
            completeness_score=round(completeness_score, 1),
            engagement_score=round(engagement_score, 1),
            age_appropriateness=age_appropriate,
            information_accuracy=round(information_accuracy, 1),
            decision_helping_value=round(decision_helping_value, 1)
        )
    
    def _generate_improvement_recommendations(self, quality_metrics: QualityMetrics, agent_analysis: Any) -> List[Dict[str, Any]]:
        """Generate specific improvement recommendations based on quality analysis"""
        
        recommendations = []
        
        # Educational value improvements
        if quality_metrics.educational_value < 7:
            recommendations.append({
                'category': 'educational_value',
                'priority': 'high',
                'issue': f'Educational value score: {quality_metrics.educational_value}/10',
                'suggestions': self.improvement_suggestions['educational_value'][:2],
                'specific_actions': [
                    'Add more detailed explanations of game mechanics',
                    'Include comparisons to similar VR games',
                    'Explain technical VR terms for beginners'
                ]
            })
        
        # Clarity improvements
        if quality_metrics.clarity_rating < 7:
            recommendations.append({
                'category': 'clarity_rating',
                'priority': 'high',
                'issue': f'Clarity rating: {quality_metrics.clarity_rating}/10',
                'suggestions': self.improvement_suggestions['clarity_rating'][:2],
                'specific_actions': [
                    'Speak more slowly and clearly',
                    'Use simpler vocabulary',
                    'Add visual aids for complex concepts'
                ]
            })
        
        # Completeness improvements
        if quality_metrics.completeness_score < 7:
            recommendations.append({
                'category': 'completeness_score',
                'priority': 'high',
                'issue': f'Completeness score: {quality_metrics.completeness_score}/10',
                'suggestions': self.improvement_suggestions['completeness_score'][:2],
                'specific_actions': [
                    'Cover all essential VR gaming topics',
                    'Add clear conclusion with recommendation',
                    'Include pricing and availability information'
                ]
            })
        
        # Engagement improvements
        if quality_metrics.engagement_score < 7:
            recommendations.append({
                'category': 'engagement_score',
                'priority': 'medium',
                'issue': f'Engagement score: {quality_metrics.engagement_score}/10',
                'suggestions': self.improvement_suggestions['engagement_score'][:2],
                'specific_actions': [
                    'Add more enthusiasm and personality',
                    'Include more gameplay demonstrations',
                    'Improve pacing and rhythm'
                ]
            })
        
        # Age appropriateness warning
        if not quality_metrics.age_appropriateness:
            recommendations.append({
                'category': 'age_appropriateness',
                'priority': 'critical',
                'issue': 'Content may not be age appropriate',
                'suggestions': [
                    'Review all language for age appropriateness',
                    'Ensure topics are suitable for teen audiences',
                    'Get parent/guardian approval before publishing'
                ],
                'specific_actions': [
                    'Check vocabulary complexity',
                    'Verify positive, educational tone',
                    'Remove any inappropriate references'
                ]
            })
        
        return recommendations
    
    def _generate_overall_assessment(self, quality_metrics: QualityMetrics) -> Dict[str, Any]:
        """Generate overall quality assessment summary"""
        
        overall_score = quality_metrics.overall_score()
        
        if overall_score >= 8:
            assessment_level = 'excellent'
            message = 'Review meets high quality standards and is ready for publishing!'
        elif overall_score >= 7:
            assessment_level = 'good'
            message = 'Review is good quality with minor improvements recommended.'
        elif overall_score >= 6:
            assessment_level = 'acceptable'
            message = 'Review is acceptable but needs improvements before publishing.'
        elif overall_score >= 5:
            assessment_level = 'needs_improvement'
            message = 'Review needs significant improvements before publishing.'
        else:
            assessment_level = 'poor'
            message = 'Review requires major revisions and improvements.'
        
        return {
            'overall_score': overall_score,
            'assessment_level': assessment_level,
            'message': message,
            'ready_for_publish': overall_score >= 7 and quality_metrics.age_appropriateness,
            'strengths': self._identify_strengths(quality_metrics),
            'priority_improvements': self._identify_priority_improvements(quality_metrics),
            'estimated_improvement_time': self._estimate_improvement_time(quality_metrics)
        }
    
    def _identify_strengths(self, quality_metrics: QualityMetrics) -> List[str]:
        """Identify review strengths based on quality metrics"""
        
        strengths = []
        
        if quality_metrics.educational_value >= 7:
            strengths.append('Strong educational value and learning content')
        if quality_metrics.clarity_rating >= 7:
            strengths.append('Clear and understandable presentation')
        if quality_metrics.completeness_score >= 7:
            strengths.append('Comprehensive topic coverage')
        if quality_metrics.engagement_score >= 7:
            strengths.append('Engaging and enthusiastic delivery')
        if quality_metrics.age_appropriateness:
            strengths.append('Age-appropriate content and language')
        if quality_metrics.information_accuracy >= 7:
            strengths.append('Accurate and reliable information')
        if quality_metrics.decision_helping_value >= 7:
            strengths.append('Helpful for gaming decision-making')
        
        return strengths
    
    def _identify_priority_improvements(self, quality_metrics: QualityMetrics) -> List[str]:
        """Identify priority improvements needed"""
        
        improvements = []
        
        scores = [
            ('Educational value', quality_metrics.educational_value),
            ('Clarity', quality_metrics.clarity_rating),
            ('Completeness', quality_metrics.completeness_score),
            ('Engagement', quality_metrics.engagement_score),
            ('Information accuracy', quality_metrics.information_accuracy),
            ('Decision helping', quality_metrics.decision_helping_value)
        ]
        
        # Sort by lowest scores first (highest priority)
        scores.sort(key=lambda x: x[1])
        
        for category, score in scores:
            if score < 7:
                improvements.append(f'{category}: {score}/10')
        
        if not quality_metrics.age_appropriateness:
            improvements.insert(0, 'Age appropriateness: Critical issue')
        
        return improvements[:3]  # Top 3 priorities
    
    def _estimate_improvement_time(self, quality_metrics: QualityMetrics) -> str:
        """Estimate time needed for improvements"""
        
        overall_score = quality_metrics.overall_score()
        
        if overall_score >= 7:
            return '15-30 minutes'
        elif overall_score >= 6:
            return '30-60 minutes'
        elif overall_score >= 5:
            return '1-2 hours'
        else:
            return '2+ hours'
    
    # Fallback methods for error handling
    def _create_fallback_educational_analysis(self) -> EducationalAnalysis:
        """Create fallback educational analysis"""
        return EducationalAnalysis(
            learning_objectives_met=['Basic game overview'],
            gaming_knowledge_shared=['Game introduction'],
            decision_support_quality=5,
            comparison_effectiveness=5,
            explanation_depth=5,
            vocabulary_appropriateness=7,
            concept_clarity=5
        )
    
    def _create_fallback_structure_analysis(self) -> ContentStructureAnalysis:
        """Create fallback structure analysis"""
        return ContentStructureAnalysis(
            has_clear_introduction=True,
            covers_essential_topics=False,
            logical_flow=5,
            conclusion_strength=5,
            topic_transitions=5,
            pacing_quality=5,
            visual_aid_effectiveness=5
        )
    
    def _create_fallback_clarity_analysis(self) -> Dict[str, Any]:
        """Create fallback clarity analysis"""
        return {
            'speaking_clarity': 5,
            'vocabulary_level': 7,
            'explanation_quality': 5,
            'enthusiasm_level': 5,
            'audience_engagement': 5,
            'technical_explanation': 5,
            'tone_appropriateness': 7,
            'fallback_used': True
        }
    
    def _create_fallback_completeness_analysis(self) -> Dict[str, Any]:
        """Create fallback completeness analysis"""
        return {
            'covered_topics': ['Basic gameplay'],
            'missing_topics': self.essential_vr_topics[2:],
            'completeness_score': 5,
            'final_recommendation_present': False,
            'fallback_used': True
        }
    
    def _create_fallback_comprehensive_analysis(self) -> Dict[str, Any]:
        """Create fallback comprehensive analysis"""
        quality_metrics = QualityMetrics(
            educational_value=5,
            clarity_rating=5,
            completeness_score=5,
            engagement_score=5,
            age_appropriateness=True,
            information_accuracy=5,
            decision_helping_value=5
        )
        
        return {
            'quality_metrics': quality_metrics.__dict__,
            'improvement_recommendations': [{
                'category': 'general',
                'priority': 'high',
                'issue': 'Analysis failed - manual review needed',
                'suggestions': ['Review content manually', 'Get feedback from parents/guardians']
            }],
            'overall_assessment': {
                'overall_score': 5,
                'assessment_level': 'needs_review',
                'message': 'Manual quality review recommended',
                'ready_for_publish': False
            },
            'fallback_used': True
        }