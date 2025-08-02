#!/usr/bin/env node

/**
 * Claude Code Hook: Review Quality Check
 * Assesses review structure and educational value before publishing
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

// Configuration
const CONFIG = {
    projectRoot: '/Users/michaelmote/Desktop/vr-game-review-studio',
    qualityThresholds: {
        educational_value: 6,      // Minimum educational value score
        clarity_rating: 6,         // Minimum clarity score  
        completeness_score: 6,     // Minimum completeness score
        age_appropriate: true      // Must be age appropriate
    },
    criticalTopics: [
        'gameplay mechanics',
        'graphics quality', 
        'price evaluation',
        'recommendation strength',
        'target audience'
    ],
    maxProcessingTime: 180000,     // 3 minutes
    logFile: '/Users/michaelmote/Desktop/vr-game-review-studio/logs/quality-check.log'
};

/**
 * Main quality check execution
 */
async function executeQualityCheck() {
    const startTime = Date.now();
    
    try {
        log('INFO', 'Review quality check initiated');
        
        // Get review information from environment or arguments  
        const reviewPath = process.env.REVIEW_PATH || process.argv[2];
        const gameInfo = process.env.GAME_INFO || process.argv[3];
        const analysisResults = process.env.ANALYSIS_RESULTS || process.argv[4];
        
        if (!reviewPath) {
            log('ERROR', 'No review path provided for quality check');
            process.exit(1);
        }
        
        // Load existing analysis if available
        let existingAnalysis = null;
        if (analysisResults) {
            try {
                existingAnalysis = JSON.parse(analysisResults);
            } catch (e) {
                log('WARN', 'Could not parse existing analysis results');
            }
        }
        
        // Parse game information
        let parsedGameInfo = {};
        if (gameInfo) {
            try {
                parsedGameInfo = JSON.parse(gameInfo);
            } catch (e) {
                log('WARN', 'Could not parse game info for quality check');
                parsedGameInfo = { name: 'Unknown Game' };
            }
        }
        
        // Perform comprehensive quality assessment
        log('INFO', 'Starting comprehensive review quality assessment');
        const qualityAssessment = await performQualityAssessment(reviewPath, parsedGameInfo, existingAnalysis);
        
        // Check against quality thresholds
        const qualityCheck = await evaluateQualityThresholds(qualityAssessment);
        
        // Generate improvement recommendations
        const improvements = await generateImprovementPlan(qualityAssessment, qualityCheck);
        
        // Create quality report
        const qualityReport = {
            timestamp: new Date().toISOString(),
            review_path: reviewPath,
            game_info: parsedGameInfo,
            quality_assessment: qualityAssessment,
            threshold_evaluation: qualityCheck,
            improvement_plan: improvements,
            ready_for_publish: qualityCheck.meets_standards,
            processing_time: Date.now() - startTime
        };
        
        // Store quality check results
        await storeQualityCheckResults(qualityReport);
        
        // Send appropriate notifications
        if (qualityCheck.meets_standards) {
            await notifyQualityPassed(qualityReport);
        } else {
            await notifyQualityIssues(qualityReport);
        }
        
        log('INFO', `Quality check completed in ${qualityReport.processing_time}ms`);
        
        // Exit with appropriate code
        process.exit(qualityCheck.meets_standards ? 0 : 1);
        
    } catch (error) {
        log('ERROR', `Quality check failed: ${error.message}`);
        await notifyQualityCheckError(error);
        process.exit(1);
    }
}

/**
 * Perform comprehensive quality assessment
 */
async function performQualityAssessment(reviewPath, gameInfo, existingAnalysis) {
    return new Promise((resolve, reject) => {
        log('INFO', 'Analyzing review quality and educational value');
        
        const assessmentScript = `
import sys
import json
import asyncio
sys.path.append('${CONFIG.projectRoot}')

from agent_orchestration.context_coordinator import ReviewAgentCoordinator
from vr_game_intelligence.review_quality_assessor import ReviewQualityAssessor

async def assess_quality():
    try:
        # Initialize assessment systems
        coordinator = ReviewAgentCoordinator()
        quality_assessor = ReviewQualityAssessor()
        
        review_path = '${reviewPath}'
        game_info = ${JSON.stringify(gameInfo)}
        existing_analysis = ${JSON.stringify(existingAnalysis) || 'null'}
        
        print(json.dumps({"status": "starting", "message": "Beginning quality assessment"}))
        
        # Use existing analysis if available, otherwise run new analysis
        if existing_analysis and existing_analysis.get('agent_consensus'):
            agent_result = existing_analysis['agent_consensus']
            print(json.dumps({"status": "using_existing", "message": "Using existing agent analysis"}))
        else:
            print(json.dumps({"status": "analyzing", "message": "Running new agent analysis"}))
            agent_result = await coordinator.competitive_review_analysis(review_path, game_info)
        
        # Perform detailed quality assessment
        print(json.dumps({"status": "quality_check", "message": "Performing detailed quality assessment"}))
        detailed_assessment = await quality_assessor.comprehensive_quality_analysis(
            review_path, game_info, agent_result
        )
        
        # Educational value analysis
        educational_analysis = await quality_assessor.analyze_educational_value(
            review_path, game_info
        )
        
        # Age appropriateness check
        age_check = await quality_assessor.verify_age_appropriateness(review_path)
        
        # Combine all assessments
        combined_assessment = {
            "agent_analysis": agent_result if hasattr(agent_result, '__dict__') else str(agent_result),
            "detailed_quality": detailed_assessment,
            "educational_analysis": educational_analysis,
            "age_appropriateness": age_check,
            "assessment_timestamp": "${new Date().toISOString()}"
        }
        
        print(json.dumps({"status": "complete", "assessment": combined_assessment}))
        
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))

asyncio.run(assess_quality())
        `;
        
        const pythonProcess = spawn('python3', ['-c', assessmentScript], {
            stdio: ['pipe', 'pipe', 'pipe']
        });
        
        let output = '';
        let errorOutput = '';
        
        pythonProcess.stdout.on('data', (data) => {
            output += data.toString();
        });
        
        pythonProcess.stderr.on('data', (data) => {
            errorOutput += data.toString();
            log('WARN', `Assessment stderr: ${data.toString().trim()}`);
        });
        
        // Set timeout
        const timeout = setTimeout(() => {
            pythonProcess.kill();
            reject(new Error('Quality assessment timeout'));
        }, CONFIG.maxProcessingTime);
        
        pythonProcess.on('close', (code) => {
            clearTimeout(timeout);
            
            if (code !== 0) {
                reject(new Error(`Assessment failed with code ${code}: ${errorOutput}`));
                return;
            }
            
            try {
                // Parse output for final assessment
                const lines = output.trim().split('\n');
                let assessment = null;
                
                for (const line of lines) {
                    try {
                        const parsed = JSON.parse(line);
                        if (parsed.status === 'complete') {
                            assessment = parsed.assessment;
                            break;
                        } else if (parsed.status === 'error') {
                            throw new Error(parsed.error);
                        }
                    } catch (e) {
                        // Skip non-JSON lines
                    }
                }
                
                if (!assessment) {
                    // Create fallback assessment
                    assessment = createFallbackAssessment(existingAnalysis);
                }
                
                resolve(assessment);
                
            } catch (error) {
                reject(new Error(`Failed to parse assessment: ${error.message}`));
            }
        });
        
        pythonProcess.on('error', (error) => {
            clearTimeout(timeout);
            reject(new Error(`Assessment process error: ${error.message}`));
        });
    });
}

/**
 * Create fallback assessment when analysis fails
 */
function createFallbackAssessment(existingAnalysis) {
    return {
        detailed_quality: {
            educational_value: 5,
            clarity_rating: 5,
            completeness_score: 5,
            structure_quality: 5,
            engagement_score: 5
        },
        educational_analysis: {
            learning_value: 5,
            decision_helping: 5,
            information_accuracy: 5,
            age_appropriate_language: true
        },
        age_appropriateness: {
            content_safe: true,
            language_appropriate: true,
            topics_suitable: true,
            requires_supervision: true
        },
        fallback_used: true,
        existing_analysis: existingAnalysis
    };
}

/**
 * Evaluate quality against thresholds
 */
async function evaluateQualityThresholds(qualityAssessment) {
    const thresholds = CONFIG.qualityThresholds;
    
    // Extract scores from assessment
    const scores = {
        educational_value: qualityAssessment.detailed_quality?.educational_value || 0,
        clarity_rating: qualityAssessment.detailed_quality?.clarity_rating || 0,
        completeness_score: qualityAssessment.detailed_quality?.completeness_score || 0,
        structure_quality: qualityAssessment.detailed_quality?.structure_quality || 0,
        engagement_score: qualityAssessment.detailed_quality?.engagement_score || 0
    };
    
    // Check age appropriateness
    const ageAppropriate = qualityAssessment.age_appropriateness?.content_safe === true &&
                          qualityAssessment.age_appropriateness?.language_appropriate === true;
    
    // Evaluate against thresholds
    const evaluations = {
        educational_value: {
            score: scores.educational_value,
            threshold: thresholds.educational_value,
            passes: scores.educational_value >= thresholds.educational_value,
            message: scores.educational_value >= thresholds.educational_value ? 
                    'Educational value meets standards' : 
                    `Educational value too low: ${scores.educational_value}/${thresholds.educational_value}`
        },
        clarity_rating: {
            score: scores.clarity_rating,
            threshold: thresholds.clarity_rating,
            passes: scores.clarity_rating >= thresholds.clarity_rating,
            message: scores.clarity_rating >= thresholds.clarity_rating ? 
                    'Clarity meets standards' : 
                    `Clarity too low: ${scores.clarity_rating}/${thresholds.clarity_rating}`
        },
        completeness_score: {
            score: scores.completeness_score,
            threshold: thresholds.completeness_score,
            passes: scores.completeness_score >= thresholds.completeness_score,
            message: scores.completeness_score >= thresholds.completeness_score ? 
                    'Completeness meets standards' : 
                    `Review incomplete: ${scores.completeness_score}/${thresholds.completeness_score}`
        },
        age_appropriate: {
            passes: ageAppropriate,
            message: ageAppropriate ? 
                    'Content is age appropriate' : 
                    'Content may not be age appropriate'
        }
    };
    
    // Check for critical missing topics
    const missingCriticalTopics = await checkCriticalTopics(qualityAssessment);
    
    // Overall evaluation
    const allPass = Object.values(evaluations).every(eval => eval.passes) && 
                   missingCriticalTopics.length === 0;
    
    return {
        meets_standards: allPass,
        individual_evaluations: evaluations,
        missing_critical_topics: missingCriticalTopics,
        overall_score: Object.values(scores).reduce((a, b) => a + b, 0) / Object.keys(scores).length,
        recommendations: generateQualityRecommendations(evaluations, missingCriticalTopics)
    };
}

/**
 * Check for critical missing topics
 */
async function checkCriticalTopics(qualityAssessment) {
    const missingTopics = [];
    
    // Extract covered topics from assessment
    const coveredTopics = [
        ...(qualityAssessment.detailed_quality?.covered_topics || []),
        ...(qualityAssessment.agent_analysis?.game_analysis?.must_cover_topics || [])
    ];
    
    // Check each critical topic
    for (const criticalTopic of CONFIG.criticalTopics) {
        const isCovered = coveredTopics.some(topic => 
            topic.toLowerCase().includes(criticalTopic.toLowerCase()) ||
            criticalTopic.toLowerCase().includes(topic.toLowerCase())
        );
        
        if (!isCovered) {
            missingTopics.push(criticalTopic);
        }
    }
    
    return missingTopics;
}

/**
 * Generate quality recommendations
 */
function generateQualityRecommendations(evaluations, missingTopics) {
    const recommendations = [];
    
    // Add recommendations for failed evaluations
    Object.entries(evaluations).forEach(([criteria, evaluation]) => {
        if (!evaluation.passes) {
            switch (criteria) {
                case 'educational_value':
                    recommendations.push('Add more detailed explanations to help viewers understand the game better');
                    recommendations.push('Include specific examples and comparisons to similar games');
                    break;
                case 'clarity_rating':
                    recommendations.push('Speak more clearly and at a steady pace');
                    recommendations.push('Organize content with clear sections and transitions');
                    break;
                case 'completeness_score':
                    recommendations.push('Cover all essential aspects of the game');
                    recommendations.push('Add concluding recommendation and target audience guidance');
                    break;
                case 'age_appropriate':
                    recommendations.push('Review content for age-appropriate language and topics');
                    recommendations.push('Ensure all game content shown is suitable for teen audiences');
                    break;
            }
        }
    });
    
    // Add recommendations for missing topics
    if (missingTopics.length > 0) {
        recommendations.push(`Make sure to cover these important topics: ${missingTopics.join(', ')}`);
    }
    
    return recommendations;
}

/**
 * Generate comprehensive improvement plan
 */
async function generateImprovementPlan(qualityAssessment, qualityCheck) {
    const plan = {
        priority_level: qualityCheck.meets_standards ? 'minor' : 'major',
        immediate_actions: [],
        content_improvements: [],
        technical_suggestions: [],
        educational_enhancements: []
    };
    
    if (!qualityCheck.meets_standards) {
        // High priority improvements
        plan.immediate_actions = [
            'Address all quality threshold issues before publishing',
            'Focus on educational value and clarity improvements',
            'Ensure all critical topics are covered'
        ];
        
        plan.content_improvements = qualityCheck.recommendations.slice(0, 3);
        
        plan.technical_suggestions = [
            'Improve audio quality and clarity',
            'Add better visual elements and gameplay footage',
            'Include text overlays for key information'
        ];
        
        plan.educational_enhancements = [
            'Add more detailed game analysis',
            'Include pros and cons comparison',
            'Provide clear buying recommendation with reasoning'
        ];
    } else {
        // Minor improvements for already good content
        plan.immediate_actions = [
            'Review content once more for polish',
            'Optimize for target platforms',
            'Prepare for publication'
        ];
        
        plan.content_improvements = [
            'Add any final polish or extra details',
            'Ensure strong opening and conclusion'
        ];
    }
    
    return plan;
}

/**
 * Store quality check results
 */
async function storeQualityCheckResults(qualityReport) {
    try {
        const resultsDir = path.join(CONFIG.projectRoot, 'learning_memory', 'quality_checks');
        
        if (!fs.existsSync(resultsDir)) {
            fs.mkdirSync(resultsDir, { recursive: true });
        }
        
        // Create filename based on review and timestamp
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const basename = path.basename(qualityReport.review_path, path.extname(qualityReport.review_path));
        const resultFile = path.join(resultsDir, `quality-check-${basename}-${timestamp}.json`);
        
        // Store compressed quality report
        const compressedReport = {
            timestamp: qualityReport.timestamp,
            game_name: qualityReport.game_info?.name || 'Unknown',
            meets_standards: qualityReport.ready_for_publish,
            overall_score: qualityReport.threshold_evaluation?.overall_score || 0,
            failed_criteria: Object.entries(qualityReport.threshold_evaluation?.individual_evaluations || {})
                .filter(([_, eval]) => !eval.passes)
                .map(([criteria, _]) => criteria),
            improvement_count: qualityReport.improvement_plan?.content_improvements?.length || 0,
            processing_time: qualityReport.processing_time
        };
        
        fs.writeFileSync(resultFile, JSON.stringify(qualityReport, null, 2));
        log('INFO', `Quality check results stored: ${resultFile}`);
        
        // Update quality learning memory
        await updateQualityLearning(compressedReport);
        
    } catch (error) {
        log('ERROR', `Failed to store quality check results: ${error.message}`);
    }
}

/**
 * Update quality learning memory
 */
async function updateQualityLearning(compressedReport) {
    try {
        const memoryFile = path.join(CONFIG.projectRoot, 'learning_memory', 'quality_check_history.json');
        
        let memory = [];
        if (fs.existsSync(memoryFile)) {
            memory = JSON.parse(fs.readFileSync(memoryFile, 'utf8'));
        }
        
        memory.push(compressedReport);
        
        // Keep only last 30 quality checks
        if (memory.length > 30) {
            memory = memory.slice(-30);
        }
        
        fs.writeFileSync(memoryFile, JSON.stringify(memory, null, 2));
        log('INFO', 'Quality learning memory updated');
        
    } catch (error) {
        log('WARN', `Failed to update quality learning: ${error.message}`);
    }
}

/**
 * Notify when quality standards are met
 */
async function notifyQualityPassed(qualityReport) {
    try {
        log('INFO', 'Review meets quality standards - ready for publishing');
        
        // Create success notification
        const notificationFile = path.join(CONFIG.projectRoot, 'web_interface', 'notifications', 'quality_passed.json');
        const notificationDir = path.dirname(notificationFile);
        
        if (!fs.existsSync(notificationDir)) {
            fs.mkdirSync(notificationDir, { recursive: true });
        }
        
        fs.writeFileSync(notificationFile, JSON.stringify({
            type: 'quality_check_passed',
            timestamp: new Date().toISOString(),
            game_name: qualityReport.game_info?.name || 'Unknown Game',
            overall_score: qualityReport.threshold_evaluation?.overall_score || 0,
            message: 'Review meets quality standards and is ready for publishing!',
            next_steps: [
                'Review final content once more',
                'Choose publication platforms',
                'Schedule or publish immediately'
            ]
        }));
        
        // Play success sound
        await playNotificationSound('/Users/michaelmote/Desktop/vr-game-review-studio/sounds/quality-passed.wav');
        
    } catch (error) {
        log('WARN', `Quality passed notification failed: ${error.message}`);
    }
}

/**
 * Notify when quality issues are found
 */
async function notifyQualityIssues(qualityReport) {
    try {
        log('WARN', 'Review quality issues found - improvements needed');
        
        const notificationFile = path.join(CONFIG.projectRoot, 'web_interface', 'notifications', 'quality_issues.json');
        const notificationDir = path.dirname(notificationFile);
        
        if (!fs.existsSync(notificationDir)) {
            fs.mkdirSync(notificationDir, { recursive: true });
        }
        
        fs.writeFileSync(notificationFile, JSON.stringify({
            type: 'quality_check_failed',
            timestamp: new Date().toISOString(),
            game_name: qualityReport.game_info?.name || 'Unknown Game',
            overall_score: qualityReport.threshold_evaluation?.overall_score || 0,
            failed_criteria: Object.entries(qualityReport.threshold_evaluation?.individual_evaluations || {})
                .filter(([_, eval]) => !eval.passes)
                .map(([criteria, eval]) => ({ criteria, message: eval.message })),
            improvement_plan: qualityReport.improvement_plan,
            message: 'Review needs improvements before publishing'
        }));
        
        // Play notification sound for issues
        await playNotificationSound('/Users/michaelmote/Desktop/vr-game-review-studio/sounds/quality-issues.wav');
        
    } catch (error) {
        log('WARN', `Quality issues notification failed: ${error.message}`);
    }
}

/**
 * Notify when quality check encounters errors
 */
async function notifyQualityCheckError(error) {
    try {
        log('ERROR', `Quality check error: ${error.message}`);
        
        const notificationFile = path.join(CONFIG.projectRoot, 'web_interface', 'notifications', 'quality_error.json');
        const notificationDir = path.dirname(notificationFile);
        
        if (!fs.existsSync(notificationDir)) {
            fs.mkdirSync(notificationDir, { recursive: true });
        }
        
        fs.writeFileSync(notificationFile, JSON.stringify({
            type: 'quality_check_error',
            timestamp: new Date().toISOString(),
            error: error.message,
            message: 'Quality check failed - manual review recommended'
        }));
        
    } catch (e) {
        log('ERROR', `Quality error notification failed: ${e.message}`);
    }
}

/**
 * Play notification sound
 */
async function playNotificationSound(soundPath) {
    return new Promise((resolve) => {
        if (!fs.existsSync(soundPath)) {
            resolve();
            return;
        }
        
        const player = spawn('afplay', [soundPath]);
        
        player.on('close', () => resolve());
        player.on('error', () => resolve());
        
        setTimeout(() => {
            player.kill();
            resolve();
        }, 3000);
    });
}

/**
 * Logging utility
 */
function log(level, message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${level}: ${message}`;
    
    console.log(logMessage);
    
    try {
        const logDir = path.dirname(CONFIG.logFile);
        if (!fs.existsSync(logDir)) {
            fs.mkdirSync(logDir, { recursive: true });
        }
        
        fs.appendFileSync(CONFIG.logFile, logMessage + '\n');
    } catch (e) {
        // Fail silently for logging errors
    }
}

// Execute hook if run directly
if (require.main === module) {
    executeQualityCheck().catch((error) => {
        log('ERROR', `Quality check execution failed: ${error.message}`);
        process.exit(1);
    });
}

module.exports = {
    executeQualityCheck,
    performQualityAssessment,
    evaluateQualityThresholds,
    generateImprovementPlan,
    log
};