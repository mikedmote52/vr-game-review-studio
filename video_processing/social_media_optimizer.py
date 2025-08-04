"""
Social Media Video Optimizer
Optimizes gameplay videos for different social platforms
"""

import os
import json
import subprocess
from datetime import datetime
import requests


class SocialMediaOptimizer:
    """Optimize videos for various social media platforms"""
    
    def __init__(self):
        self.platform_specs = {
            'tiktok': {
                'max_duration': 60,
                'aspect_ratio': '9:16',
                'resolution': '1080x1920',
                'fps': 30,
                'bitrate': '12M',
                'format': 'mp4',
                'features': ['captions', 'music', 'effects', 'trending_sounds']
            },
            'youtube_shorts': {
                'max_duration': 60,
                'aspect_ratio': '9:16',
                'resolution': '1080x1920',
                'fps': 30,
                'bitrate': '15M',
                'format': 'mp4',
                'features': ['captions', 'chapters', 'end_screen']
            },
            'instagram_reels': {
                'max_duration': 90,
                'aspect_ratio': '9:16',
                'resolution': '1080x1920',
                'fps': 30,
                'bitrate': '10M',
                'format': 'mp4',
                'features': ['captions', 'music', 'filters']
            },
            'youtube': {
                'max_duration': 3600,  # 1 hour
                'aspect_ratio': '16:9',
                'resolution': '1920x1080',
                'fps': 60,
                'bitrate': '25M',
                'format': 'mp4',
                'features': ['intro', 'outro', 'chapters', 'cards', 'end_screen']
            },
            'twitter': {
                'max_duration': 140,
                'aspect_ratio': '16:9',
                'resolution': '1280x720',
                'fps': 30,
                'bitrate': '8M',
                'format': 'mp4',
                'features': ['captions', 'preview_thumbnail']
            }
        }
        
    def optimize_for_platform(self, video_path, platform, output_dir):
        """Optimize video for specific social media platform"""
        if platform not in self.platform_specs:
            raise ValueError(f"Unknown platform: {platform}")
        
        specs = self.platform_specs[platform]
        output_path = os.path.join(output_dir, f"{platform}_optimized.mp4")
        
        print(f"🎯 Optimizing for {platform}...")
        
        # Apply platform-specific optimizations
        optimized_path = self.apply_platform_specs(video_path, specs, output_path)
        
        # Add platform-specific features
        final_path = self.add_platform_features(optimized_path, platform, specs['features'])
        
        # Generate metadata
        metadata = self.generate_platform_metadata(final_path, platform)
        
        return {
            'path': final_path,
            'metadata': metadata,
            'platform': platform,
            'specs': specs
        }
    
    def apply_platform_specs(self, input_path, specs, output_path):
        """Apply technical specifications for platform"""
        cmd = ['ffmpeg', '-i', input_path]
        
        # Video filters
        filters = []
        
        # Scale to platform resolution
        if specs['aspect_ratio'] == '9:16':
            # Vertical video - crop and scale
            filters.append(f"crop=ih*9/16:ih,scale={specs['resolution']}")
        else:
            # Horizontal video - scale
            filters.append(f"scale={specs['resolution']}")
        
        # Adjust frame rate
        filters.append(f"fps={specs['fps']}")
        
        # Apply filters
        if filters:
            cmd.extend(['-vf', ','.join(filters)])
        
        # Video encoding
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-b:v', specs['bitrate'],
            '-maxrate', specs['bitrate'],
            '-bufsize', str(int(specs['bitrate'][:-1]) * 2) + 'M'
        ])
        
        # Audio encoding
        cmd.extend([
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '44100'
        ])
        
        # Duration limit
        duration = self.get_video_duration(input_path)
        if duration > specs['max_duration']:
            cmd.extend(['-t', str(specs['max_duration'])])
        
        # Output
        cmd.extend([output_path, '-y'])
        
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def add_platform_features(self, video_path, platform, features):
        """Add platform-specific features to video"""
        current_path = video_path
        
        if 'captions' in features:
            current_path = self.add_dynamic_captions(current_path, platform)
        
        if 'music' in features:
            current_path = self.add_trending_music(current_path, platform)
        
        if 'effects' in features:
            current_path = self.add_visual_effects(current_path, platform)
        
        if 'intro' in features:
            current_path = self.add_intro(current_path)
        
        if 'outro' in features:
            current_path = self.add_outro(current_path)
        
        return current_path
    
    def add_dynamic_captions(self, video_path, platform):
        """Add engaging animated captions"""
        output_path = video_path.replace('.mp4', '_captioned.mp4')
        
        # Platform-specific caption styles
        caption_styles = {
            'tiktok': {
                'font': 'Arial Black',
                'size': 36,
                'color': 'white',
                'outline': 3,
                'position': 'center',
                'animation': 'pop'
            },
            'youtube_shorts': {
                'font': 'Roboto',
                'size': 32,
                'color': 'white',
                'outline': 2,
                'position': 'bottom',
                'animation': 'fade'
            },
            'instagram_reels': {
                'font': 'Helvetica',
                'size': 30,
                'color': 'white',
                'outline': 2,
                'position': 'center',
                'animation': 'slide'
            }
        }
        
        style = caption_styles.get(platform, caption_styles['youtube_shorts'])
        
        # Apply styled captions using FFmpeg
        # This is simplified - in production you'd use more advanced captioning
        filter_complex = f"drawtext=text='EPIC GAMEPLAY':fontfile=/System/Library/Fonts/Helvetica.ttc:fontsize={style['size']}:fontcolor={style['color']}:x=(w-text_w)/2:y=h-50:enable='between(t,0,3)'"
        
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', filter_complex,
            '-c:a', 'copy',
            output_path, '-y'
        ]
        
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def add_trending_music(self, video_path, platform):
        """Add platform-appropriate background music"""
        output_path = video_path.replace('.mp4', '_music.mp4')
        
        # In production, you'd integrate with platform APIs
        # to get trending sounds/music
        # For now, we'll just adjust audio levels
        
        cmd = [
            'ffmpeg', '-i', video_path,
            '-af', 'volume=0.7',  # Lower game audio
            '-c:v', 'copy',
            output_path, '-y'
        ]
        
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def add_visual_effects(self, video_path, platform):
        """Add platform-specific visual effects"""
        output_path = video_path.replace('.mp4', '_effects.mp4')
        
        # Platform-specific effects
        if platform == 'tiktok':
            # Add zoom effect on action moments
            filter_complex = "scale=1.1*iw:1.1*ih,zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=125"
        elif platform == 'instagram_reels':
            # Add slight vignette
            filter_complex = "vignette=PI/4"
        else:
            # Default - slight contrast boost
            filter_complex = "eq=contrast=1.1:brightness=0.05"
        
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', filter_complex,
            '-c:a', 'copy',
            output_path, '-y'
        ]
        
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def generate_platform_metadata(self, video_path, platform):
        """Generate platform-specific metadata and recommendations"""
        metadata = {
            'platform': platform,
            'file_path': video_path,
            'file_size': os.path.getsize(video_path),
            'created_at': datetime.now().isoformat()
        }
        
        # Platform-specific recommendations
        if platform == 'tiktok':
            metadata['recommendations'] = {
                'hashtags': self.generate_tiktok_hashtags(),
                'description': self.generate_tiktok_description(),
                'best_time_to_post': self.get_best_posting_time('tiktok'),
                'trending_sounds': self.get_trending_sounds()
            }
        elif platform == 'youtube':
            metadata['recommendations'] = {
                'title': self.generate_youtube_title(),
                'description': self.generate_youtube_description(),
                'tags': self.generate_youtube_tags(),
                'thumbnail_suggestions': self.generate_thumbnail_ideas()
            }
        
        return metadata
    
    def generate_tiktok_hashtags(self):
        """Generate relevant TikTok hashtags"""
        return [
            '#VRGaming', '#VirtualReality', '#GamingClips',
            '#EpicMoments', '#GameReview', '#VRGameplay',
            '#GamingCommunity', '#NextGenGaming', '#VRLife',
            '#GamingHighlights'
        ]
    
    def generate_tiktok_description(self):
        """Generate engaging TikTok description"""
        return "🎮 INSANE VR Gameplay! You won't believe what happens next 🤯 Drop a ❤️ if you love VR gaming!"
    
    def generate_youtube_title(self):
        """Generate SEO-optimized YouTube title"""
        return "EPIC VR Gameplay Highlights - Mind-Blowing Moments Compilation"
    
    def generate_youtube_description(self):
        """Generate comprehensive YouTube description"""
        return """🎮 Welcome to the most INSANE VR gameplay compilation!

In this video:
00:00 - Epic Introduction
00:30 - Mind-blowing Combat Sequence
02:15 - Incredible Boss Battle
04:30 - Victory Celebration

🔥 TIMESTAMPS:
[Auto-generated chapters]

📱 Follow me on:
- TikTok: @yourusername
- Instagram: @yourusername
- Twitter: @yourusername

🎯 About this game:
[Game description]

⚙️ My VR Setup:
- Headset: [Your VR headset]
- PC Specs: [Your specs]

#VRGaming #VirtualReality #Gaming
"""
    
    def generate_youtube_tags(self):
        """Generate YouTube tags for SEO"""
        return [
            'VR gaming', 'virtual reality', 'VR gameplay',
            'gaming highlights', 'epic moments', 'game review',
            'VR headset', 'gaming compilation', 'best VR games'
        ]
    
    def generate_thumbnail_ideas(self):
        """Generate thumbnail suggestions"""
        return [
            {
                'style': 'action_shot',
                'text_overlay': 'INSANE VR MOMENTS',
                'color_scheme': 'high_contrast',
                'elements': ['explosion_effect', 'shocked_expression']
            },
            {
                'style': 'before_after',
                'text_overlay': 'YOU WON\'T BELIEVE',
                'color_scheme': 'vibrant',
                'elements': ['arrow', 'highlight_circle']
            }
        ]
    
    def get_best_posting_time(self, platform):
        """Get optimal posting time for platform"""
        # In production, this would use analytics data
        best_times = {
            'tiktok': {
                'weekday': '6:00 AM, 11:00 AM, 7:00 PM',
                'weekend': '9:00 AM, 12:00 PM, 7:00 PM'
            },
            'youtube': {
                'weekday': '2:00 PM - 4:00 PM',
                'weekend': '12:00 PM - 3:00 PM'
            }
        }
        return best_times.get(platform, {})
    
    def get_trending_sounds(self):
        """Get current trending sounds (mock data)"""
        return [
            {'name': 'Epic Gaming Moment', 'uses': '2.3M'},
            {'name': 'Oh No Oh No', 'uses': '5.7M'},
            {'name': 'Victory Royale', 'uses': '1.2M'}
        ]
    
    def get_video_duration(self, video_path):
        """Get video duration in seconds"""
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
               '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    
    def batch_optimize(self, video_path, platforms, output_dir):
        """Optimize video for multiple platforms at once"""
        results = {}
        
        for platform in platforms:
            try:
                result = self.optimize_for_platform(video_path, platform, output_dir)
                results[platform] = result
                print(f"✅ Successfully optimized for {platform}")
            except Exception as e:
                print(f"❌ Error optimizing for {platform}: {e}")
                results[platform] = {'error': str(e)}
        
        return results