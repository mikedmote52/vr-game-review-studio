#!/usr/bin/env node

/**
 * Claude Code Hook: Post-Upload Review Processing
 * Triggers context-aware VR game review analysis after video upload
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

// Hook configuration
const CONFIG = {
    projectRoot: '/Users/michaelmote/Desktop/vr-game-review-studio',
    maxVideoSize: 500 * 1024 * 1024, // 500MB max
    supportedFormats: ['.mp4', '.mov', '.avi', '.mkv'],
    processingTimeout: 300000, // 5 minutes
    logFile: '/Users/michaelmote/Desktop/vr-game-review-studio/logs/upload-processing.log'
};

/**
 * Main hook execution
 */
async function executePostUploadHook() {
    const startTime = Date.now();
    
    try {
        log('INFO', 'Post-upload hook triggered');
        
        // Get upload information from environment or arguments
        const uploadPath = process.env.UPLOAD_PATH || process.argv[2];
        const gameInfo = process.env.GAME_INFO || process.argv[3];
        
        if (!uploadPath) {
            log('ERROR', 'No upload path provided');
            process.exit(1);
        }
        
        // Validate uploaded file
        const validation = await validateUpload(uploadPath);
        if (!validation.valid) {
            log('ERROR', `Upload validation failed: ${validation.error}`);
            await notifyValidationFailure(validation.error);
            process.exit(1);
        }
        
        // Parse game information
        let parsedGameInfo = {};
        if (gameInfo) {
            try {
                parsedGameInfo = JSON.parse(gameInfo);
            } catch (e) {
                log('WARN', 'Could not parse game info, using defaults');
                parsedGameInfo = { name: 'Unknown Game', genre: 'Unknown' };
            }
        }
        
        // Initialize context-aware review processing
        log('INFO', 'Starting context-aware review analysis');
        const analysisResult = await processReviewWithContextIsolation(uploadPath, parsedGameInfo);
        
        // Store analysis results
        await storeAnalysisResults(analysisResult, uploadPath);
        
        // Trigger quality enhancement workflow
        await triggerQualityEnhancement(analysisResult);
        
        // Send completion notification
        await notifyProcessingComplete(analysisResult);
        
        const processingTime = Date.now() - startTime;
        log('INFO', `Review processing completed in ${processingTime}ms`);
        
    } catch (error) {
        log('ERROR', `Hook execution failed: ${error.message}`);
        await notifyProcessingError(error);
        process.exit(1);
    }
}

/**
 * Validate uploaded video file
 */
async function validateUpload(uploadPath) {
    try {
        // Check if file exists
        if (!fs.existsSync(uploadPath)) {
            return { valid: false, error: 'Upload file not found' };
        }
        
        // Check file size
        const stats = fs.statSync(uploadPath);
        if (stats.size > CONFIG.maxVideoSize) {
            return { valid: false, error: `File too large: ${Math.round(stats.size / 1024 / 1024)}MB (max: ${CONFIG.maxVideoSize / 1024 / 1024}MB)` };
        }
        
        // Check file format
        const ext = path.extname(uploadPath).toLowerCase();
        if (!CONFIG.supportedFormats.includes(ext)) {
            return { valid: false, error: `Unsupported format: ${ext}. Supported: ${CONFIG.supportedFormats.join(', ')}` };
        }
        
        // Validate video content (basic check)
        const isValidVideo = await validateVideoContent(uploadPath);
        if (!isValidVideo) {
            return { valid: false, error: 'Invalid video content or corrupted file' };
        }
        
        return { valid: true };
        
    } catch (error) {
        return { valid: false, error: `Validation error: ${error.message}` };
    }
}

/**
 * Basic video content validation
 */
async function validateVideoContent(filePath) {
    return new Promise((resolve) => {
        // Use ffprobe to validate video (if available)
        const ffprobe = spawn('ffprobe', ['-v', 'quiet', '-print_format', 'json', '-show_format', filePath]);
        
        let output = '';
        ffprobe.stdout.on('data', (data) => {
            output += data.toString();
        });
        
        ffprobe.on('close', (code) => {
            if (code === 0 && output.includes('duration')) {
                resolve(true);
            } else {
                // Fallback: assume valid if file exists and has content
                resolve(fs.statSync(filePath).size > 1024);
            }
        });
        
        ffprobe.on('error', () => {
            // Fallback: assume valid if file exists and has content
            resolve(fs.statSync(filePath).size > 1024);
        });
    });
}

/**
 * Process review with context isolation
 */
async function processReviewWithContextIsolation(uploadPath, gameInfo) {
    return new Promise((resolve, reject) => {
        log('INFO', 'Initializing context-isolated review analysis');
        
        const pythonScript = path.join(CONFIG.projectRoot, 'context_management', 'review_context_engine.py');
        const coordinator = path.join(CONFIG.projectRoot, 'agent_orchestration', 'context_coordinator.py');
        
        // Prepare analysis command
        const analysisCmd = spawn('python3', [
            '-c', `
import sys
import asyncio
import json
sys.path.append('${CONFIG.projectRoot}')

from context_management.review_context_engine import ReviewContextEngine
from agent_orchestration.context_coordinator import ReviewAgentCoordinator

async def main():
    try:
        # Initialize systems
        context_engine = ReviewContextEngine()
        agent_coordinator = ReviewAgentCoordinator()
        
        # Game info
        game_info = ${JSON.stringify(gameInfo)}
        upload_path = '${uploadPath}'
        
        print(json.dumps({"status": "processing", "message": "Starting context-isolated analysis"}))
        
        # Process with context isolation
        context_result = await context_engine.analyze_vr_game_review_with_isolation(upload_path, game_info)
        
        print(json.dumps({"status": "context_complete", "result": "Context analysis complete"}))
        
        # Run competitive agent analysis
        agent_result = await agent_coordinator.competitive_review_analysis(upload_path, game_info)
        
        # Combine results
        combined_result = {
            "context_analysis": context_result,
            "agent_consensus": agent_result.__dict__ if hasattr(agent_result, '__dict__') else str(agent_result),
            "processing_timestamp": "${new Date().toISOString()}",
            "upload_path": upload_path,
            "game_info": game_info
        }
        
        print(json.dumps({"status": "complete", "analysis": combined_result}))
        
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))

asyncio.run(main())
            `
        ], { stdio: ['pipe', 'pipe', 'pipe'] });
        
        let output = '';
        let errorOutput = '';
        
        analysisCmd.stdout.on('data', (data) => {
            output += data.toString();
        });
        
        analysisCmd.stderr.on('data', (data) => {
            errorOutput += data.toString();
            log('WARN', `Analysis stderr: ${data.toString().trim()}`);
        });
        
        // Set timeout
        const timeout = setTimeout(() => {
            analysisCmd.kill();
            reject(new Error('Analysis timeout'));
        }, CONFIG.processingTimeout);
        
        analysisCmd.on('close', (code) => {
            clearTimeout(timeout);
            
            if (code !== 0) {
                reject(new Error(`Analysis failed with code ${code}: ${errorOutput}`));
                return;
            }
            
            try {
                // Parse output for final result
                const lines = output.trim().split('\n');
                let analysisResult = null;
                
                for (const line of lines) {
                    try {
                        const parsed = JSON.parse(line);
                        if (parsed.status === 'complete') {
                            analysisResult = parsed.analysis;
                            break;
                        } else if (parsed.status === 'error') {
                            throw new Error(parsed.error);
                        }
                    } catch (e) {
                        // Skip non-JSON lines
                    }
                }
                
                if (!analysisResult) {
                    throw new Error('No analysis result found in output');
                }
                
                resolve(analysisResult);
                
            } catch (error) {
                reject(new Error(`Failed to parse analysis result: ${error.message}`));
            }
        });
        
        analysisCmd.on('error', (error) => {
            clearTimeout(timeout);
            reject(new Error(`Analysis process error: ${error.message}`));
        });
    });
}

/**
 * Store analysis results for future reference
 */
async function storeAnalysisResults(analysisResult, uploadPath) {
    try {
        const resultsDir = path.join(CONFIG.projectRoot, 'learning_memory', 'analysis_results');
        
        // Ensure directory exists
        if (!fs.existsSync(resultsDir)) {
            fs.mkdirSync(resultsDir, { recursive: true });
        }
        
        // Create unique filename
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const basename = path.basename(uploadPath, path.extname(uploadPath));
        const resultFile = path.join(resultsDir, `${basename}-${timestamp}.json`);
        
        // Store compressed result
        const compressedResult = {
            timestamp: analysisResult.processing_timestamp,
            game_name: analysisResult.game_info?.name || 'Unknown',
            game_genre: analysisResult.game_info?.genre || 'Unknown',
            overall_score: analysisResult.context_analysis?.combined_recommendation?.overall_score || 0,
            educational_value: analysisResult.context_analysis?.review_quality?.educational_score || 0,
            growth_potential: analysisResult.context_analysis?.audience_growth?.engagement_potential || 0,
            agent_consensus: {
                confidence: analysisResult.agent_consensus?.confidence_level || 0,
                agreement: analysisResult.agent_consensus?.agent_agreement_score || 0,
                cost: analysisResult.agent_consensus?.cost_breakdown?.total || 0
            },
            improvement_priorities: analysisResult.context_analysis?.combined_recommendation?.improvement_priorities || [],
            upload_file: path.basename(uploadPath)
        };
        
        fs.writeFileSync(resultFile, JSON.stringify(compressedResult, null, 2));
        log('INFO', `Analysis results stored: ${resultFile}`);
        
        // Update aggregated learning memory
        await updateLearningMemory(compressedResult);
        
    } catch (error) {
        log('ERROR', `Failed to store analysis results: ${error.message}`);
    }
}

/**
 * Update learning memory with new analysis
 */
async function updateLearningMemory(compressedResult) {
    try {
        const memoryFile = path.join(CONFIG.projectRoot, 'learning_memory', 'review_quality_evolution.json');
        
        let memory = [];
        if (fs.existsSync(memoryFile)) {
            memory = JSON.parse(fs.readFileSync(memoryFile, 'utf8'));
        }
        
        // Add new result
        memory.push(compressedResult);
        
        // Keep only last 50 results
        if (memory.length > 50) {
            memory = memory.slice(-50);
        }
        
        // Save updated memory
        fs.writeFileSync(memoryFile, JSON.stringify(memory, null, 2));
        
        log('INFO', 'Learning memory updated');
        
    } catch (error) {
        log('WARN', `Failed to update learning memory: ${error.message}`);
    }
}

/**
 * Trigger quality enhancement workflow
 */
async function triggerQualityEnhancement(analysisResult) {
    try {
        log('INFO', 'Triggering quality enhancement workflow');
        
        // Check if quality enhancement is needed
        const educationalValue = analysisResult.context_analysis?.review_quality?.educational_score || 0;
        const overallScore = analysisResult.context_analysis?.combined_recommendation?.overall_score || 0;
        
        if (educationalValue < 7 || overallScore < 7) {
            log('INFO', 'Quality enhancement recommended');
            
            // Execute quality enhancement script
            const enhancementScript = path.join(CONFIG.projectRoot, 'automation_workflows', 'review_quality_enhancer.py');
            
            if (fs.existsSync(enhancementScript)) {
                const enhancement = spawn('python3', [enhancementScript, JSON.stringify(analysisResult)]);
                
                enhancement.on('close', (code) => {
                    if (code === 0) {
                        log('INFO', 'Quality enhancement completed');
                    } else {
                        log('WARN', `Quality enhancement failed with code ${code}`);
                    }
                });
            }
        } else {
            log('INFO', 'Quality enhancement not needed (scores sufficient)');
        }
        
    } catch (error) {
        log('WARN', `Quality enhancement trigger failed: ${error.message}`);
    }
}

/**
 * Send processing completion notification
 */
async function notifyProcessingComplete(analysisResult) {
    try {
        // Play completion sound
        await playNotificationSound('/Users/michaelmote/Desktop/vr-game-review-studio/sounds/review-ready.wav');
        
        // Log completion summary
        const summary = {
            status: 'complete',
            game: analysisResult.game_info?.name || 'Unknown',
            overall_score: analysisResult.context_analysis?.combined_recommendation?.overall_score || 0,
            educational_value: analysisResult.context_analysis?.review_quality?.educational_score || 0,
            recommended_action: analysisResult.context_analysis?.combined_recommendation?.action || 'review_manually'
        };
        
        log('INFO', `Processing complete: ${JSON.stringify(summary)}`);
        
        // Create notification file for web interface
        const notificationFile = path.join(CONFIG.projectRoot, 'web_interface', 'notifications', 'latest.json');
        const notificationDir = path.dirname(notificationFile);
        
        if (!fs.existsSync(notificationDir)) {
            fs.mkdirSync(notificationDir, { recursive: true });
        }
        
        fs.writeFileSync(notificationFile, JSON.stringify({
            type: 'processing_complete',
            timestamp: new Date().toISOString(),
            message: `Review analysis complete for ${analysisResult.game_info?.name || 'Unknown Game'}`,
            summary: summary
        }));
        
    } catch (error) {
        log('WARN', `Notification failed: ${error.message}`);
    }
}

/**
 * Play notification sound
 */
async function playNotificationSound(soundPath) {
    return new Promise((resolve) => {
        if (!fs.existsSync(soundPath)) {
            // Create basic notification sound path if it doesn't exist
            resolve();
            return;
        }
        
        // Try to play sound using system tools
        const player = spawn('afplay', [soundPath]); // macOS
        
        player.on('close', () => resolve());
        player.on('error', () => resolve()); // Fail silently
        
        // Timeout after 5 seconds
        setTimeout(() => {
            player.kill();
            resolve();
        }, 5000);
    });
}

/**
 * Handle processing errors
 */
async function notifyProcessingError(error) {
    try {
        log('ERROR', `Processing error: ${error.message}`);
        
        // Create error notification
        const notificationFile = path.join(CONFIG.projectRoot, 'web_interface', 'notifications', 'error.json');
        const notificationDir = path.dirname(notificationFile);
        
        if (!fs.existsSync(notificationDir)) {
            fs.mkdirSync(notificationDir, { recursive: true });
        }
        
        fs.writeFileSync(notificationFile, JSON.stringify({
            type: 'processing_error',
            timestamp: new Date().toISOString(),
            error: error.message,
            message: 'Review processing failed - manual review recommended'
        }));
        
    } catch (e) {
        log('ERROR', `Error notification failed: ${e.message}`);
    }
}

/**
 * Handle validation failures
 */
async function notifyValidationFailure(errorMessage) {
    try {
        log('WARN', `Validation failed: ${errorMessage}`);
        
        const notificationFile = path.join(CONFIG.projectRoot, 'web_interface', 'notifications', 'validation_error.json');
        const notificationDir = path.dirname(notificationFile);
        
        if (!fs.existsSync(notificationDir)) {
            fs.mkdirSync(notificationDir, { recursive: true });
        }
        
        fs.writeFileSync(notificationFile, JSON.stringify({
            type: 'validation_error',
            timestamp: new Date().toISOString(),
            error: errorMessage,
            message: 'Upload validation failed - please check file and try again'
        }));
        
    } catch (e) {
        log('ERROR', `Validation notification failed: ${e.message}`);
    }
}

/**
 * Logging utility
 */
function log(level, message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${level}: ${message}`;
    
    console.log(logMessage);
    
    // Also write to log file
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
    executePostUploadHook().catch((error) => {
        log('ERROR', `Hook execution failed: ${error.message}`);
        process.exit(1);
    });
}

module.exports = {
    executePostUploadHook,
    validateUpload,
    processReviewWithContextIsolation,
    log
};