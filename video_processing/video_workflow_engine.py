"""
Video Workflow Engine
Orchestrates the complete video editing and publishing workflow
"""

import os
import json
import asyncio
from datetime import datetime
import shutil
from .ai_video_editor import AIVideoEditor
from .social_media_optimizer import SocialMediaOptimizer


class VideoWorkflowEngine:
    """Manages the complete video creation workflow"""
    
    def __init__(self):
        self.video_editor = AIVideoEditor()
        self.social_optimizer = SocialMediaOptimizer()
        self.workflow_presets = {
            'quick_tiktok': {
                'name': 'Quick TikTok Edit',
                'description': 'Fast 60-second highlight reel for TikTok',
                'steps': ['analyze', 'extract_highlights', 'create_tiktok', 'add_captions', 'optimize'],
                'platforms': ['tiktok'],
                'duration': 60
            },
            'multi_platform_short': {
                'name': 'Multi-Platform Shorts',
                'description': 'Create shorts for TikTok, YouTube, and Instagram',
                'steps': ['analyze', 'extract_highlights', 'create_vertical', 'add_captions', 'optimize_all'],
                'platforms': ['tiktok', 'youtube_shorts', 'instagram_reels'],
                'duration': 60
            },
            'youtube_highlights': {
                'name': 'YouTube Highlight Video',
                'description': 'Full highlight compilation for YouTube',
                'steps': ['analyze', 'extract_all_highlights', 'create_compilation', 'add_intro_outro', 'add_chapters', 'optimize'],
                'platforms': ['youtube'],
                'duration': 300
            },
            'social_media_package': {
                'name': 'Complete Social Package',
                'description': 'Create content for all platforms',
                'steps': ['analyze', 'create_multiple_edits', 'optimize_all', 'generate_thumbnails'],
                'platforms': ['youtube', 'tiktok', 'youtube_shorts', 'instagram_reels', 'twitter'],
                'duration': 'various'
            }
        }
        
    async def process_gameplay_video(self, video_path, workflow_preset, output_dir):
        """Process gameplay video using selected workflow"""
        print(f"🎬 Starting video workflow: {workflow_preset}")
        
        if workflow_preset not in self.workflow_presets:
            raise ValueError(f"Unknown workflow preset: {workflow_preset}")
        
        preset = self.workflow_presets[workflow_preset]
        workflow_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create workflow directory
        workflow_dir = os.path.join(output_dir, f'workflow_{workflow_id}')
        os.makedirs(workflow_dir, exist_ok=True)
        
        # Initialize workflow state
        workflow_state = {
            'id': workflow_id,
            'preset': workflow_preset,
            'input_video': video_path,
            'output_dir': workflow_dir,
            'started_at': datetime.now().isoformat(),
            'status': 'processing',
            'steps_completed': [],
            'outputs': {},
            'analysis': None
        }
        
        try:
            # Execute workflow steps
            for step in preset['steps']:
                print(f"📋 Executing step: {step}")
                await self.execute_workflow_step(step, workflow_state, preset)
                workflow_state['steps_completed'].append(step)
                self.save_workflow_state(workflow_state)
            
            workflow_state['status'] = 'completed'
            workflow_state['completed_at'] = datetime.now().isoformat()
            
        except Exception as e:
            workflow_state['status'] = 'failed'
            workflow_state['error'] = str(e)
            print(f"❌ Workflow failed: {e}")
        
        # Save final state
        self.save_workflow_state(workflow_state)
        
        # Cleanup
        self.video_editor.cleanup()
        
        return workflow_state
    
    async def execute_workflow_step(self, step, state, preset):
        """Execute individual workflow step"""
        if step == 'analyze':
            # Analyze gameplay footage
            analysis = self.video_editor.analyze_gameplay_footage(state['input_video'])
            state['analysis'] = analysis
            
        elif step == 'extract_highlights':
            # Extract top highlights
            if not state['analysis']:
                raise ValueError("Analysis required before extracting highlights")
            
            moments = state['analysis']['action_moments'][:10]
            state['top_moments'] = moments
            
        elif step == 'extract_all_highlights':
            # Extract all highlights for longer video
            if not state['analysis']:
                raise ValueError("Analysis required before extracting highlights")
            
            state['all_moments'] = state['analysis']['action_moments']
            
        elif step == 'create_tiktok':
            # Create TikTok-specific edit
            output_path = os.path.join(state['output_dir'], 'tiktok_edit.mp4')
            self.video_editor.create_highlight_reel(
                state['input_video'],
                state['top_moments'],
                output_path,
                style='tiktok'
            )
            state['outputs']['tiktok_raw'] = output_path
            
        elif step == 'create_vertical':
            # Create vertical video for multiple platforms
            for platform in ['tiktok', 'youtube_shorts', 'instagram_reels']:
                if platform in preset['platforms']:
                    output_path = os.path.join(state['output_dir'], f'{platform}_edit.mp4')
                    self.video_editor.create_highlight_reel(
                        state['input_video'],
                        state['top_moments'],
                        output_path,
                        style=platform
                    )
                    state['outputs'][f'{platform}_raw'] = output_path
            
        elif step == 'create_compilation':
            # Create full compilation for YouTube
            output_path = os.path.join(state['output_dir'], 'youtube_compilation.mp4')
            self.video_editor.create_highlight_reel(
                state['input_video'],
                state.get('all_moments', state.get('top_moments', [])),
                output_path,
                style='youtube'
            )
            state['outputs']['youtube_raw'] = output_path
            
        elif step == 'add_captions':
            # Add captions to all outputs
            for key, video_path in state['outputs'].items():
                if 'raw' in key and os.path.exists(video_path):
                    captioned_path = video_path.replace('.mp4', '_captioned.mp4')
                    self.video_editor.generate_auto_captions(video_path, captioned_path)
                    state['outputs'][key.replace('raw', 'captioned')] = captioned_path
            
        elif step == 'optimize_all':
            # Optimize for each platform
            for platform in preset['platforms']:
                if f'{platform}_captioned' in state['outputs']:
                    input_video = state['outputs'][f'{platform}_captioned']
                elif f'{platform}_raw' in state['outputs']:
                    input_video = state['outputs'][f'{platform}_raw']
                else:
                    continue
                
                result = self.social_optimizer.optimize_for_platform(
                    input_video,
                    platform,
                    state['output_dir']
                )
                state['outputs'][f'{platform}_final'] = result
            
        elif step == 'create_multiple_edits':
            # Create different edits for each platform
            await self.create_platform_specific_edits(state, preset)
            
        elif step == 'generate_thumbnails':
            # Generate thumbnail suggestions
            await self.generate_video_thumbnails(state)
    
    async def create_platform_specific_edits(self, state, preset):
        """Create platform-specific edits in parallel"""
        tasks = []
        
        for platform in preset['platforms']:
            if platform in ['tiktok', 'youtube_shorts', 'instagram_reels']:
                # Short form content
                duration = 60
                style = platform
            elif platform == 'youtube':
                # Long form content
                duration = 300
                style = 'youtube'
            elif platform == 'twitter':
                # Medium form content
                duration = 140
                style = 'youtube'  # Use horizontal format
            else:
                continue
            
            output_path = os.path.join(state['output_dir'], f'{platform}_edit.mp4')
            
            # Select moments based on duration
            if duration <= 60:
                moments = state['analysis']['action_moments'][:12]
            else:
                moments = state['analysis']['action_moments']
            
            # Create edit
            self.video_editor.create_highlight_reel(
                state['input_video'],
                moments,
                output_path,
                style=style
            )
            
            # Optimize for platform
            result = self.social_optimizer.optimize_for_platform(
                output_path,
                platform,
                state['output_dir']
            )
            
            state['outputs'][f'{platform}_final'] = result
    
    async def generate_video_thumbnails(self, state):
        """Generate thumbnail options for videos"""
        import cv2
        
        thumbnails_dir = os.path.join(state['output_dir'], 'thumbnails')
        os.makedirs(thumbnails_dir, exist_ok=True)
        
        # Extract frames from key moments
        cap = cv2.VideoCapture(state['input_video'])
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        for i, moment in enumerate(state.get('top_moments', [])[:5]):
            timestamp = moment['timestamp']
            frame_number = int(timestamp * fps)
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            
            if ret:
                # Save original frame
                thumbnail_path = os.path.join(thumbnails_dir, f'thumbnail_{i}_original.jpg')
                cv2.imwrite(thumbnail_path, frame)
                
                # Create enhanced version with text overlay
                # In production, you'd add dynamic text, effects, etc.
                enhanced_path = os.path.join(thumbnails_dir, f'thumbnail_{i}_enhanced.jpg')
                cv2.imwrite(enhanced_path, frame)
                
                if 'thumbnails' not in state['outputs']:
                    state['outputs']['thumbnails'] = []
                
                state['outputs']['thumbnails'].append({
                    'original': thumbnail_path,
                    'enhanced': enhanced_path,
                    'moment_type': moment.get('type', 'highlight'),
                    'timestamp': timestamp
                })
        
        cap.release()
    
    def save_workflow_state(self, state):
        """Save workflow state to JSON"""
        state_file = os.path.join(state['output_dir'], 'workflow_state.json')
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def get_workflow_presets(self):
        """Get available workflow presets"""
        return self.workflow_presets
    
    def estimate_processing_time(self, video_duration, workflow_preset):
        """Estimate how long the workflow will take"""
        base_time = video_duration * 0.1  # 10% of video duration for analysis
        
        preset_multipliers = {
            'quick_tiktok': 1.5,
            'multi_platform_short': 2.5,
            'youtube_highlights': 3.0,
            'social_media_package': 5.0
        }
        
        multiplier = preset_multipliers.get(workflow_preset, 2.0)
        return base_time * multiplier
    
    def get_workflow_status(self, workflow_id, output_dir):
        """Get status of a workflow"""
        workflow_dir = os.path.join(output_dir, f'workflow_{workflow_id}')
        state_file = os.path.join(workflow_dir, 'workflow_state.json')
        
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                return json.load(f)
        
        return None