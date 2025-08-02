"""
Multi-Agent Context Coordinator for VR Game Review Analysis
Implements agent competition, parallel execution, and budget management
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import openai
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass
class AgentBudget:
    """Track agent usage and budget"""
    agent_name: str
    budget_limit: float
    current_spend: float = 0.0
    request_count: int = 0
    avg_cost_per_request: float = 0.0
    
    def can_spend(self, estimated_cost: float) -> bool:
        return (self.current_spend + estimated_cost) <= self.budget_limit
    
    def record_spend(self, actual_cost: float):
        self.current_spend += actual_cost
        self.request_count += 1
        self.avg_cost_per_request = self.current_spend / self.request_count


@dataclass
class AgentInsight:
    """Individual agent analysis result"""
    agent_name: str
    confidence_score: float
    analysis_type: str
    insights: Dict[str, Any]
    processing_time: float
    cost: float
    context_tokens_used: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class ConsensuResult:
    """Combined agent consensus with disagreement tracking"""
    primary_recommendation: Dict[str, Any]
    confidence_level: float
    agent_agreement_score: float
    disagreements: List[Dict[str, Any]]
    cost_breakdown: Dict[str, float]
    processing_metrics: Dict[str, Any]


class ReviewAgentCoordinator:
    """Coordinates multiple AI agents for VR game review analysis"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Initialize agent budgets ($0.20 total per review)
        self.agent_budgets = {
            'game_analyst': AgentBudget("VR Game Analysis Agent", 0.07),
            'review_quality': AgentBudget("Review Quality Agent", 0.07),
            'audience_growth': AgentBudget("Gaming Audience Agent", 0.06)
        }
        
        self.total_budget_per_review = 0.20
        self.agent_timeout = 120  # 2 minutes per agent
        
        # Performance tracking
        self.session_metrics = {
            "reviews_processed": 0,
            "total_cost": 0.0,
            "avg_processing_time": 0.0,
            "agent_performance": {}
        }
    
    async def competitive_review_analysis(self, review_video_path: str, game_info: Dict[str, Any]) -> ConsensuResult:
        """Run competing agent analyses in parallel with budget awareness"""
        
        start_time = time.time()
        
        # Verify budget availability
        total_estimated_cost = sum(budget.budget_limit for budget in self.agent_budgets.values())
        if total_estimated_cost > self.total_budget_per_review:
            raise ValueError("Agent budgets exceed review budget limit")
        
        try:
            # Create agent tasks with isolated contexts
            agent_tasks = [
                self._run_game_analysis_agent(review_video_path, game_info),
                self._run_review_quality_agent(review_video_path),
                self._run_audience_growth_agent(review_video_path, game_info)
            ]
            
            # Execute agents in parallel with timeout
            agent_results = await asyncio.gather(
                *agent_tasks,
                timeout=self.agent_timeout,
                return_exceptions=True
            )
            
            # Process results and handle any failures
            processed_results = []
            for i, result in enumerate(agent_results):
                if isinstance(result, Exception):
                    print(f"Agent {i} failed: {result}")
                    # Create fallback result
                    processed_results.append(self._create_fallback_result(i))
                else:
                    processed_results.append(result)
            
            # Run agent competition and build consensus
            consensus = await self._build_consensus_with_competition(processed_results)
            
            # Update performance metrics
            processing_time = time.time() - start_time
            self._update_session_metrics(consensus, processing_time)
            
            return consensus
            
        except asyncio.TimeoutError:
            print("Agent analysis timeout - using fallback analysis")
            return self._create_emergency_fallback_consensus()
        except Exception as e:
            print(f"Agent coordination error: {e}")
            return self._create_error_consensus(str(e))
    
    async def _run_game_analysis_agent(self, review_video_path: str, game_info: Dict[str, Any]) -> AgentInsight:
        """VR Game Analysis Agent - focuses on game features and mechanics"""
        
        agent_name = "game_analyst"
        start_time = time.time()
        
        # Check budget before proceeding
        if not self.agent_budgets[agent_name].can_spend(0.07):
            raise ValueError(f"{agent_name} budget exceeded")
        
        analysis_prompt = f"""
        As a VR gaming expert, analyze this game for review guidance:
        
        Game: {game_info.get('name', 'Unknown')}
        Genre: {game_info.get('genre', 'Unknown')}
        Platform: {game_info.get('platform', 'VR')}
        Price: ${game_info.get('price', 0)}
        
        ANALYZE ONLY VR-SPECIFIC ASPECTS:
        1. Core VR gameplay mechanics (hand tracking, room scale, etc.)
        2. Key features that make this game unique in VR
        3. VR interaction quality and innovation
        4. Technical performance in VR (comfort, motion sickness)
        5. Comparison to similar VR games in genre
        6. What a reviewer MUST cover for complete analysis
        7. Recommendation strength (1-10) with justification
        
        Provide structured analysis optimized for a 13-year-old reviewer creating educational content.
        Focus on helping other gamers make informed purchasing decisions.
        
        Return analysis in this JSON format:
        {{
            "vr_mechanics": ["mechanic1", "mechanic2"],
            "unique_features": ["feature1", "feature2"],
            "interaction_quality": 8,
            "comfort_rating": 7,
            "must_cover_topics": ["topic1", "topic2"],
            "genre_comparison": "Better/worse than similar games because...",
            "recommendation_score": 8,
            "recommendation_reason": "Clear explanation",
            "target_audience_match": "Perfect for teens/families/adults",
            "review_talking_points": ["point1", "point2"]
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a VR gaming expert who analyzes games for young content creators. Focus ONLY on VR-specific features and provide structured guidance."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=1200,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            analysis_text = response.choices[0].message.content
            try:
                analysis_data = json.loads(analysis_text)
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                analysis_data = self._parse_fallback_game_analysis(analysis_text)
            
            # Calculate cost (rough estimate)
            estimated_cost = 0.05  # Estimated based on token usage
            self.agent_budgets[agent_name].record_spend(estimated_cost)
            
            processing_time = time.time() - start_time
            
            return AgentInsight(
                agent_name="VR Game Analyst",
                confidence_score=analysis_data.get("recommendation_score", 5) / 10.0,
                analysis_type="vr_game_features",
                insights=analysis_data,
                processing_time=processing_time,
                cost=estimated_cost,
                context_tokens_used=len(analysis_prompt) // 4
            )
            
        except Exception as e:
            print(f"Game analysis agent error: {e}")
            return self._create_fallback_game_insight()
    
    async def _run_review_quality_agent(self, review_video_path: str) -> AgentInsight:
        """Review Quality Agent - assesses educational value and clarity"""
        
        agent_name = "review_quality"
        start_time = time.time()
        
        if not self.agent_budgets[agent_name].can_spend(0.07):
            raise ValueError(f"{agent_name} budget exceeded")
        
        quality_prompt = """
        As a content quality expert specializing in educational gaming content, assess this VR game review:
        
        EVALUATE EDUCATIONAL VALUE AND CLARITY:
        1. Educational value for other gamers (1-10)
        2. Review structure and organization (1-10)
        3. Clarity of explanations (1-10)
        4. Missing important information or topics
        5. Age-appropriateness for teen audience
        6. Specific improvement suggestions
        7. Overall review completeness (1-10)
        8. Engagement factor for young viewers (1-10)
        
        Focus on helping a 13-year-old reviewer create better educational content
        that helps other gamers make informed decisions about VR games.
        
        Return assessment in this JSON format:
        {{
            "educational_value": 8,
            "structure_quality": 7,
            "clarity_score": 8,
            "missing_topics": ["price comparison", "system requirements"],
            "age_appropriate": true,
            "improvement_suggestions": ["add more gameplay footage", "explain VR controls better"],
            "completeness_score": 7,
            "engagement_score": 8,
            "strengths": ["good explanations", "honest opinions"],
            "areas_for_improvement": ["need more examples", "speak slower"],
            "educational_recommendations": ["add learning value", "help decision making"]
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an educational content expert who helps young creators make better gaming content. Focus on clarity, educational value, and age-appropriate improvement suggestions."},
                    {"role": "user", "content": quality_prompt}
                ],
                max_tokens=1000,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            quality_text = response.choices[0].message.content
            try:
                quality_data = json.loads(quality_text)
            except json.JSONDecodeError:
                quality_data = self._parse_fallback_quality_analysis(quality_text)
            
            estimated_cost = 0.05
            self.agent_budgets[agent_name].record_spend(estimated_cost)
            
            processing_time = time.time() - start_time
            
            return AgentInsight(
                agent_name="Review Quality Analyst",
                confidence_score=quality_data.get("educational_value", 5) / 10.0,
                analysis_type="review_quality_assessment",
                insights=quality_data,
                processing_time=processing_time,
                cost=estimated_cost,
                context_tokens_used=len(quality_prompt) // 4
            )
            
        except Exception as e:
            print(f"Quality analysis agent error: {e}")
            return self._create_fallback_quality_insight()
    
    async def _run_audience_growth_agent(self, review_video_path: str, game_info: Dict[str, Any]) -> AgentInsight:
        """Gaming Audience Growth Agent - analyzes community engagement potential"""
        
        agent_name = "audience_growth"
        start_time = time.time()
        
        if not self.agent_budgets[agent_name].can_spend(0.06):
            raise ValueError(f"{agent_name} budget exceeded")
        
        growth_prompt = f"""
        As a gaming community and audience growth expert, analyze the engagement potential 
        for this VR game review by a 13-year-old content creator:
        
        Game: {game_info.get('name', 'Unknown')}
        Genre: {game_info.get('genre', 'Unknown')}
        Target Audience: {game_info.get('target_audience', 'General')}
        
        ANALYZE GAMING COMMUNITY ENGAGEMENT:
        1. Community interest level in this VR game (1-10)
        2. Trending VR gaming topics alignment (1-10)
        3. Young audience appeal and safety (1-10)
        4. Platform optimization recommendations (YouTube/TikTok/Instagram/Reddit)
        5. Best posting timing for gaming community
        6. Hashtag and keyword recommendations
        7. Community engagement opportunities (comments, discussions)
        8. Growth potential for teen gaming content creator (1-10)
        
        Focus on safe, positive community engagement suitable for a young reviewer.
        
        Return analysis in this JSON format:
        {{
            "community_interest": 8,
            "trend_alignment": 7,
            "young_audience_appeal": 9,
            "platform_scores": {{"youtube": 9, "tiktok": 7, "instagram": 6, "reddit": 5}},
            "optimal_posting_time": "weekday_evening",
            "recommended_hashtags": ["#VRGaming", "#GameReview", "#VirtualReality"],
            "engagement_opportunities": ["respond to comments", "join VR gaming discussions"],
            "growth_potential": 8,
            "safety_considerations": ["avoid mature gaming communities", "parent oversight"],
            "content_optimization": ["add subtitles", "create shorts", "show gameplay"]
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a gaming community expert focused on safe, positive growth for young content creators. Prioritize educational value and appropriate community engagement."},
                    {"role": "user", "content": growth_prompt}
                ],
                max_tokens=800,
                temperature=0.4,
                response_format={"type": "json_object"}
            )
            
            growth_text = response.choices[0].message.content
            try:
                growth_data = json.loads(growth_text)
            except json.JSONDecodeError:
                growth_data = self._parse_fallback_growth_analysis(growth_text)
            
            estimated_cost = 0.04
            self.agent_budgets[agent_name].record_spend(estimated_cost)
            
            processing_time = time.time() - start_time
            
            return AgentInsight(
                agent_name="Gaming Audience Growth Analyst",
                confidence_score=growth_data.get("growth_potential", 5) / 10.0,
                analysis_type="audience_growth_analysis",
                insights=growth_data,
                processing_time=processing_time,
                cost=estimated_cost,
                context_tokens_used=len(growth_prompt) // 4
            )
            
        except Exception as e:
            print(f"Growth analysis agent error: {e}")
            return self._create_fallback_growth_insight()
    
    async def _build_consensus_with_competition(self, agent_results: List[AgentInsight]) -> ConsensuResult:
        """Build consensus from competing agent analyses"""
        
        if len(agent_results) != 3:
            raise ValueError(f"Expected 3 agent results, got {len(agent_results)}")
        
        game_insight, quality_insight, growth_insight = agent_results
        
        # Calculate agent agreement scores
        agreement_scores = self._calculate_agent_agreement(agent_results)
        
        # Identify disagreements
        disagreements = self._identify_disagreements(agent_results)
        
        # Build primary recommendation based on weighted consensus
        primary_recommendation = {
            "overall_score": self._calculate_weighted_score(agent_results),
            "game_analysis": game_insight.insights,
            "quality_assessment": quality_insight.insights,
            "growth_strategy": growth_insight.insights,
            "combined_recommendation": self._generate_final_recommendation(agent_results),
            "confidence_factors": {
                "game_expertise": game_insight.confidence_score,
                "educational_value": quality_insight.confidence_score,
                "audience_appeal": growth_insight.confidence_score
            }
        }
        
        # Calculate overall confidence
        overall_confidence = sum(result.confidence_score for result in agent_results) / len(agent_results)
        
        # Cost breakdown
        cost_breakdown = {
            result.agent_name: result.cost for result in agent_results
        }
        cost_breakdown["total"] = sum(cost_breakdown.values())
        
        # Processing metrics
        processing_metrics = {
            "total_processing_time": sum(result.processing_time for result in agent_results),
            "agent_timeouts": 0,
            "context_efficiency": self._calculate_context_efficiency(agent_results),
            "budget_utilization": cost_breakdown["total"] / self.total_budget_per_review
        }
        
        return ConsensuResult(
            primary_recommendation=primary_recommendation,
            confidence_level=overall_confidence,
            agent_agreement_score=agreement_scores["overall"],
            disagreements=disagreements,
            cost_breakdown=cost_breakdown,
            processing_metrics=processing_metrics
        )
    
    def _calculate_agent_agreement(self, results: List[AgentInsight]) -> Dict[str, float]:
        """Calculate how much agents agree with each other"""
        
        # Compare confidence scores
        confidence_scores = [result.confidence_score for result in results]
        confidence_variance = sum((score - sum(confidence_scores)/len(confidence_scores))**2 for score in confidence_scores) / len(confidence_scores)
        confidence_agreement = max(0, 1 - confidence_variance)
        
        # Compare recommendation strengths where available
        recommendation_scores = []
        for result in results:
            if "recommendation_score" in result.insights:
                recommendation_scores.append(result.insights["recommendation_score"])
            elif "educational_value" in result.insights:
                recommendation_scores.append(result.insights["educational_value"])
            elif "growth_potential" in result.insights:
                recommendation_scores.append(result.insights["growth_potential"])
        
        if len(recommendation_scores) >= 2:
            rec_variance = sum((score - sum(recommendation_scores)/len(recommendation_scores))**2 for score in recommendation_scores) / len(recommendation_scores)
            recommendation_agreement = max(0, 1 - rec_variance / 25)  # Normalize to variance of 5 points
        else:
            recommendation_agreement = 0.5  # Neutral if can't compare
        
        overall_agreement = (confidence_agreement + recommendation_agreement) / 2
        
        return {
            "confidence_agreement": confidence_agreement,
            "recommendation_agreement": recommendation_agreement,
            "overall": overall_agreement
        }
    
    def _identify_disagreements(self, results: List[AgentInsight]) -> List[Dict[str, Any]]:
        """Identify significant disagreements between agents"""
        disagreements = []
        
        # Check for confidence score disagreements
        confidence_scores = [result.confidence_score for result in results]
        max_conf = max(confidence_scores)
        min_conf = min(confidence_scores)
        
        if max_conf - min_conf > 0.3:  # Significant confidence disagreement
            disagreements.append({
                "type": "confidence_disagreement",
                "description": f"Agent confidence varies from {min_conf:.2f} to {max_conf:.2f}",
                "agents_involved": [result.agent_name for result in results],
                "severity": "medium" if max_conf - min_conf < 0.5 else "high"
            })
        
        # Check for recommendation disagreements
        game_rec = results[0].insights.get("recommendation_score", 5)
        quality_rec = results[1].insights.get("educational_value", 5)
        
        if abs(game_rec - quality_rec) > 3:
            disagreements.append({
                "type": "recommendation_disagreement",
                "description": f"Game quality ({game_rec}) vs Educational value ({quality_rec}) differ significantly",
                "resolution": "Prioritize educational value for young reviewer audience",
                "severity": "medium"
            })
        
        return disagreements
    
    def _calculate_weighted_score(self, results: List[AgentInsight]) -> float:
        """Calculate overall weighted score from all agents"""
        
        game_insight, quality_insight, growth_insight = results
        
        # Extract scores with defaults
        game_score = game_insight.insights.get("recommendation_score", 5)
        quality_score = quality_insight.insights.get("educational_value", 5)
        growth_score = growth_insight.insights.get("growth_potential", 5)
        
        # Weight: 40% educational value, 35% game quality, 25% growth potential
        weighted_score = (quality_score * 0.4) + (game_score * 0.35) + (growth_score * 0.25)
        
        return round(weighted_score, 2)
    
    def _generate_final_recommendation(self, results: List[AgentInsight]) -> Dict[str, Any]:
        """Generate final recommendation combining all agent insights"""
        
        game_insight, quality_insight, growth_insight = results
        
        return {
            "action": self._determine_recommendation_action(results),
            "priority_improvements": self._extract_priority_improvements(results),
            "publishing_strategy": growth_insight.insights.get("platform_scores", {}),
            "educational_enhancements": quality_insight.insights.get("improvement_suggestions", []),
            "game_coverage_completeness": game_insight.insights.get("must_cover_topics", []),
            "safety_considerations": growth_insight.insights.get("safety_considerations", []),
            "next_steps": self._generate_next_steps(results)
        }
    
    def _determine_recommendation_action(self, results: List[AgentInsight]) -> str:
        """Determine primary recommendation action"""
        
        overall_score = self._calculate_weighted_score(results)
        quality_score = results[1].insights.get("educational_value", 5)
        
        if overall_score >= 8 and quality_score >= 7:
            return "publish_with_minor_improvements"
        elif overall_score >= 6 and quality_score >= 6:
            return "improve_then_publish"
        elif quality_score < 5:
            return "focus_on_educational_value"
        else:
            return "substantial_improvements_needed"
    
    def _extract_priority_improvements(self, results: List[AgentInsight]) -> List[str]:
        """Extract top priority improvements from all agents"""
        
        improvements = []
        
        # From quality agent
        quality_improvements = results[1].insights.get("improvement_suggestions", [])
        improvements.extend(quality_improvements[:2])  # Top 2
        
        # From game analysis agent
        must_cover = results[0].insights.get("must_cover_topics", [])
        if must_cover:
            improvements.append(f"Ensure coverage of: {', '.join(must_cover[:2])}")
        
        # From growth agent
        safety_items = results[2].insights.get("safety_considerations", [])
        if safety_items:
            improvements.append(f"Safety: {safety_items[0]}")
        
        return improvements[:4]  # Top 4 priorities
    
    def _generate_next_steps(self, results: List[AgentInsight]) -> List[str]:
        """Generate actionable next steps for the reviewer"""
        
        action = self._determine_recommendation_action(results)
        
        if action == "publish_with_minor_improvements":
            return [
                "Make minor improvements suggested by quality analysis",
                "Optimize for recommended platforms",
                "Schedule publication during optimal time",
                "Prepare for community engagement"
            ]
        elif action == "improve_then_publish":
            return [
                "Address educational value improvements first",
                "Add missing game coverage topics",
                "Test review with parent/guardian approval",
                "Implement platform-specific optimizations"
            ]
        else:
            return [
                "Focus on improving educational clarity",
                "Add more detailed game analysis",
                "Ensure age-appropriate content",
                "Consider review format changes"
            ]
    
    def _calculate_context_efficiency(self, results: List[AgentInsight]) -> float:
        """Calculate how efficiently context tokens were used"""
        
        total_tokens = sum(result.context_tokens_used for result in results)
        total_insights = sum(len(result.insights) for result in results)
        
        if total_tokens == 0:
            return 0.0
        
        return min(1.0, total_insights / (total_tokens / 100))  # Insights per 100 tokens
    
    def _update_session_metrics(self, consensus: ConsensuResult, processing_time: float):
        """Update session performance metrics"""
        
        self.session_metrics["reviews_processed"] += 1
        self.session_metrics["total_cost"] += consensus.cost_breakdown["total"]
        
        # Update average processing time
        current_avg = self.session_metrics["avg_processing_time"]
        review_count = self.session_metrics["reviews_processed"]
        self.session_metrics["avg_processing_time"] = ((current_avg * (review_count - 1)) + processing_time) / review_count
        
        # Update agent performance tracking
        for agent_name, cost in consensus.cost_breakdown.items():
            if agent_name != "total":
                if agent_name not in self.session_metrics["agent_performance"]:
                    self.session_metrics["agent_performance"][agent_name] = {
                        "total_cost": 0.0,
                        "avg_confidence": 0.0,
                        "request_count": 0
                    }
                
                perf = self.session_metrics["agent_performance"][agent_name]
                perf["total_cost"] += cost
                perf["request_count"] += 1
    
    # Fallback methods for error handling
    def _create_fallback_result(self, agent_index: int) -> AgentInsight:
        """Create fallback result when agent fails"""
        
        fallback_agents = [
            self._create_fallback_game_insight,
            self._create_fallback_quality_insight,
            self._create_fallback_growth_insight
        ]
        
        return fallback_agents[agent_index]()
    
    def _create_fallback_game_insight(self) -> AgentInsight:
        """Fallback game analysis insight"""
        return AgentInsight(
            agent_name="VR Game Analyst (Fallback)",
            confidence_score=0.5,
            analysis_type="fallback_game_analysis",
            insights={
                "recommendation_score": 5,
                "must_cover_topics": ["gameplay", "graphics", "price"],
                "unique_features": ["VR experience"],
                "recommendation_reason": "Standard VR game review needed"
            },
            processing_time=1.0,
            cost=0.01,
            context_tokens_used=100
        )
    
    def _create_fallback_quality_insight(self) -> AgentInsight:
        """Fallback quality analysis insight"""
        return AgentInsight(
            agent_name="Review Quality Analyst (Fallback)",
            confidence_score=0.5,
            analysis_type="fallback_quality_analysis",
            insights={
                "educational_value": 5,
                "improvement_suggestions": ["add more detail", "explain clearly"],
                "completeness_score": 5,
                "age_appropriate": True
            },
            processing_time=1.0,
            cost=0.01,
            context_tokens_used=100
        )
    
    def _create_fallback_growth_insight(self) -> AgentInsight:
        """Fallback growth analysis insight"""
        return AgentInsight(
            agent_name="Gaming Audience Growth Analyst (Fallback)",
            confidence_score=0.5,
            analysis_type="fallback_growth_analysis",
            insights={
                "growth_potential": 5,
                "platform_scores": {"youtube": 7, "tiktok": 5},
                "safety_considerations": ["parent oversight required"],
                "optimal_posting_time": "weekday_evening"
            },
            processing_time=1.0,
            cost=0.01,
            context_tokens_used=100
        )
    
    def _create_emergency_fallback_consensus(self) -> ConsensuResult:
        """Emergency fallback when all agents fail"""
        return ConsensuResult(
            primary_recommendation={
                "overall_score": 5.0,
                "action": "manual_review_required",
                "message": "Automated analysis failed - manual review recommended"
            },
            confidence_level=0.1,
            agent_agreement_score=0.0,
            disagreements=[{"type": "system_failure", "description": "All agents failed"}],
            cost_breakdown={"total": 0.01},
            processing_metrics={"system_failure": True}
        )
    
    def _create_error_consensus(self, error_message: str) -> ConsensuResult:
        """Create error consensus result"""
        return ConsensuResult(
            primary_recommendation={
                "overall_score": 0.0,
                "action": "system_error",
                "error": error_message
            },
            confidence_level=0.0,
            agent_agreement_score=0.0,
            disagreements=[{"type": "system_error", "description": error_message}],
            cost_breakdown={"total": 0.0},
            processing_metrics={"error": True}
        )
    
    def _parse_fallback_game_analysis(self, text: str) -> Dict[str, Any]:
        """Parse game analysis when JSON fails"""
        return {
            "recommendation_score": 5,
            "must_cover_topics": ["gameplay", "graphics"],
            "unique_features": ["VR experience"],
            "recommendation_reason": "Analysis parsing failed"
        }
    
    def _parse_fallback_quality_analysis(self, text: str) -> Dict[str, Any]:
        """Parse quality analysis when JSON fails"""
        return {
            "educational_value": 5,
            "improvement_suggestions": ["improve clarity"],
            "completeness_score": 5,
            "age_appropriate": True
        }
    
    def _parse_fallback_growth_analysis(self, text: str) -> Dict[str, Any]:
        """Parse growth analysis when JSON fails"""
        return {
            "growth_potential": 5,
            "platform_scores": {"youtube": 6},
            "safety_considerations": ["supervision needed"]
        }
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget utilization status"""
        return {
            "total_budget_per_review": self.total_budget_per_review,
            "agent_budgets": {name: asdict(budget) for name, budget in self.agent_budgets.items()},
            "session_metrics": self.session_metrics,
            "budget_warnings": self._get_budget_warnings()
        }
    
    def _get_budget_warnings(self) -> List[str]:
        """Get budget warning messages"""
        warnings = []
        
        for name, budget in self.agent_budgets.items():
            utilization = budget.current_spend / budget.budget_limit
            if utilization > 0.9:
                warnings.append(f"{name} budget {utilization:.1%} utilized")
        
        total_session_cost = self.session_metrics["total_cost"]
        if total_session_cost > 10.0:  # More than $10 in session
            warnings.append(f"Session cost high: ${total_session_cost:.2f}")
        
        return warnings
    
    def reset_session_budgets(self):
        """Reset all agent budgets for new session"""
        for budget in self.agent_budgets.values():
            budget.current_spend = 0.0
            budget.request_count = 0
            budget.avg_cost_per_request = 0.0
        
        self.session_metrics = {
            "reviews_processed": 0,
            "total_cost": 0.0,
            "avg_processing_time": 0.0,
            "agent_performance": {}
        }