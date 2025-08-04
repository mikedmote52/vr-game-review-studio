"""
AI-Powered Video Editor for VR Game Reviews
Transforms raw gameplay into social media-ready content
"""

import os
import json
import subprocess
import cv2
import numpy as np
from datetime import datetime, timedelta
import whisper
from PIL import Image
import tempfile
import shutil


class AIVideoEditor:
    """AI-powered video editing system for gameplay footage"""
    
    def __init__(self):
        self.highlight_threshold = 0.7
        self.whisper_model = None
        self.temp_dir = tempfile.mkdtemp()
        
    def analyze_gameplay_footage(self, video_path):
        """Analyze gameplay footage to identify key moments"""
        print(f"🔍 Analyzing gameplay footage: {video_path}")
        
        analysis = {
            'duration': self.get_video_duration(video_path),
            'fps': self.get_video_fps(video_path),
            'resolution': self.get_video_resolution(video_path),
            'highlights': [],
            'audio_peaks': [],
            'scene_changes': [],
            'action_moments': []
        }
        
        # Detect highlights using computer vision
        analysis['highlights'] = self.detect_gameplay_highlights(video_path)
        
        # Detect audio peaks (exciting moments)
        analysis['audio_peaks'] = self.detect_audio_peaks(video_path)
        
        # Detect scene changes
        analysis['scene_changes'] = self.detect_scene_changes(video_path)
        
        # Combine all detections into action moments
        analysis['action_moments'] = self.identify_action_moments(analysis)
        
        return analysis
    
    def detect_gameplay_highlights(self, video_path):
        """Use CV to detect exciting gameplay moments"""
        highlights = []
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        frame_count = 0
        motion_history = []
        
        prev_frame = None
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Calculate motion intensity
            if prev_frame is not None:
                diff = cv2.absdiff(frame, prev_frame)
                motion_score = np.mean(diff)
                motion_history.append((frame_count / fps, motion_score))
            
            prev_frame = frame
            frame_count += 1
            
            # Process every 30th frame to save computation
            if frame_count % 30 == 0:
                # Detect UI elements, explosions, victories, etc.
                if self.is_exciting_frame(frame):
                    timestamp = frame_count / fps
                    highlights.append({
                        'timestamp': timestamp,
                        'type': 'visual_excitement',
                        'confidence': 0.8
                    })
        
        cap.release()
        
        # Find motion peaks
        if motion_history:
            motion_peaks = self.find_peaks(motion_history)
            for peak_time, peak_value in motion_peaks:
                highlights.append({
                    'timestamp': peak_time,
                    'type': 'high_motion',
                    'confidence': min(peak_value / 100, 1.0)
                })
        
        return highlights
    
    def detect_audio_peaks(self, video_path):
        """Detect audio excitement (loud moments, music peaks)"""
        # Extract audio
        audio_path = os.path.join(self.temp_dir, 'temp_audio.wav')
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', '44100', '-ac', '2',
            audio_path, '-y'
        ]
        subprocess.run(cmd, capture_output=True)
        
        # Analyze audio for peaks
        import wave
        import audioop
        
        peaks = []
        with wave.open(audio_path, 'rb') as wav:
            frames = wav.readframes(-1)
            frame_rate = wav.getframerate()
            
            # Process in 1-second chunks
            chunk_size = frame_rate * 2  # 1 second of stereo audio
            for i in range(0, len(frames), chunk_size):
                chunk = frames[i:i + chunk_size]
                if len(chunk) < chunk_size:
                    break
                
                rms = audioop.rms(chunk, 2)
                timestamp = i / (frame_rate * 2)
                
                if rms > 10000:  # High audio level
                    peaks.append({
                        'timestamp': timestamp,
                        'type': 'audio_peak',
                        'intensity': min(rms / 20000, 1.0)
                    })
        
        return peaks
    
    def detect_scene_changes(self, video_path):
        """Detect major scene transitions"""
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', 'select=\'gt(scene,0.4)\',showinfo',
            '-f', 'null', '-'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        scene_changes = []
        for line in result.stderr.split('\n'):
            if 'pts_time' in line:
                # Extract timestamp from ffmpeg output
                try:
                    time_str = line.split('pts_time:')[1].split()[0]
                    timestamp = float(time_str)
                    scene_changes.append({
                        'timestamp': timestamp,
                        'type': 'scene_change'
                    })
                except:
                    pass
        
        return scene_changes
    
    def identify_action_moments(self, analysis):
        """Combine all detections to identify the best action moments"""
        all_moments = []
        
        # Add all detected moments with weights
        for h in analysis['highlights']:
            all_moments.append({
                'timestamp': h['timestamp'],
                'score': h.get('confidence', 0.7) * 1.0,
                'type': h['type']
            })
        
        for p in analysis['audio_peaks']:
            all_moments.append({
                'timestamp': p['timestamp'],
                'score': p.get('intensity', 0.5) * 0.8,
                'type': p['type']
            })
        
        for s in analysis['scene_changes']:
            all_moments.append({
                'timestamp': s['timestamp'],
                'score': 0.6,
                'type': s['type']
            })
        
        # Cluster nearby moments
        clustered = self.cluster_moments(all_moments)
        
        # Sort by score and return top moments
        clustered.sort(key=lambda x: x['score'], reverse=True)
        return clustered[:20]  # Top 20 moments
    
    def create_highlight_reel(self, video_path, moments, output_path, style='youtube'):
        """Create a highlight compilation from detected moments"""
        print(f"🎬 Creating highlight reel in {style} style...")
        
        clips = []
        for i, moment in enumerate(moments[:10]):  # Use top 10 moments
            # Extract 5-second clips around each moment
            start_time = max(0, moment['timestamp'] - 2.5)
            duration = 5
            
            clip_path = os.path.join(self.temp_dir, f'clip_{i}.mp4')
            cmd = [
                'ffmpeg', '-i', video_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-c', 'copy',
                clip_path, '-y'
            ]
            subprocess.run(cmd, capture_output=True)
            clips.append(clip_path)
        
        # Create compilation based on platform
        if style == 'tiktok':
            return self.create_tiktok_edit(clips, output_path)
        elif style == 'youtube_shorts':
            return self.create_youtube_short(clips, output_path)
        else:
            return self.create_youtube_video(clips, output_path)
    
    def create_tiktok_edit(self, clips, output_path):
        """Create vertical TikTok-optimized video (60 seconds max)"""
        # Create clips list file
        list_file = os.path.join(self.temp_dir, 'clips.txt')
        with open(list_file, 'w') as f:
            for clip in clips[:12]:  # ~60 seconds
                f.write(f"file '{clip}'\n")
        
        # Concatenate and convert to vertical
        temp_output = os.path.join(self.temp_dir, 'temp_concat.mp4')
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', list_file,
            '-vf', 'crop=ih*9/16:ih,scale=1080:1920',  # Crop to 9:16
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '128k',
            temp_output, '-y'
        ]
        subprocess.run(cmd, capture_output=True)
        
        # Add TikTok-style text and effects
        self.add_social_media_effects(temp_output, output_path, 'tiktok')
        return output_path
    
    def create_youtube_short(self, clips, output_path):
        """Create YouTube Shorts video (vertical, 60 seconds)"""
        # Similar to TikTok but with YouTube styling
        list_file = os.path.join(self.temp_dir, 'clips.txt')
        with open(list_file, 'w') as f:
            for clip in clips[:12]:
                f.write(f"file '{clip}'\n")
        
        temp_output = os.path.join(self.temp_dir, 'temp_concat.mp4')
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', list_file,
            '-vf', 'crop=ih*9/16:ih,scale=1080:1920',
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '192k',
            temp_output, '-y'
        ]
        subprocess.run(cmd, capture_output=True)
        
        self.add_social_media_effects(temp_output, output_path, 'youtube_shorts')
        return output_path
    
    def create_youtube_video(self, clips, output_path):
        """Create full YouTube video with intro/outro"""
        # Create longer compilation with transitions
        list_file = os.path.join(self.temp_dir, 'clips.txt')
        with open(list_file, 'w') as f:
            for clip in clips:
                f.write(f"file '{clip}'\n")
        
        # Add transitions between clips
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', list_file,
            '-vf', 'scale=1920:1080,fps=30',
            '-c:v', 'libx264', '-preset', 'medium',
            '-c:a', 'aac', '-b:a', '192k',
            output_path, '-y'
        ]
        subprocess.run(cmd, capture_output=True)
        
        return output_path
    
    def add_social_media_effects(self, input_path, output_path, platform):
        """Add platform-specific effects and text overlays"""
        # This would add:
        # - Captions from speech
        # - Emoji reactions
        # - Progress bars
        # - Platform-specific styling
        
        # For now, just copy the file
        shutil.copy(input_path, output_path)
    
    def transcribe_gameplay_commentary(self, video_path):
        """Transcribe any commentary in the gameplay"""
        if not self.whisper_model:
            print("Loading Whisper model for transcription...")
            self.whisper_model = whisper.load_model("base")
        
        # Extract audio
        audio_path = os.path.join(self.temp_dir, 'commentary.wav')
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', '16000', '-ac', '1',
            audio_path, '-y'
        ]
        subprocess.run(cmd, capture_output=True)
        
        # Transcribe
        result = self.whisper_model.transcribe(audio_path)
        return result
    
    def generate_auto_captions(self, video_path, output_path):
        """Add automatic captions to video"""
        transcription = self.transcribe_gameplay_commentary(video_path)
        
        # Generate SRT file
        srt_path = os.path.join(self.temp_dir, 'captions.srt')
        with open(srt_path, 'w') as f:
            for i, segment in enumerate(transcription['segments']):
                start = self.format_timestamp(segment['start'])
                end = self.format_timestamp(segment['end'])
                text = segment['text'].strip()
                f.write(f"{i+1}\n{start} --> {end}\n{text}\n\n")
        
        # Burn captions into video
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', f"subtitles={srt_path}:force_style='Fontsize=24,PrimaryColour=&H00FFFF&'",
            '-c:a', 'copy',
            output_path, '-y'
        ]
        subprocess.run(cmd, capture_output=True)
        
        return output_path
    
    # Utility methods
    def get_video_duration(self, video_path):
        """Get video duration in seconds"""
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
               '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    
    def get_video_fps(self, video_path):
        """Get video frame rate"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        return fps
    
    def get_video_resolution(self, video_path):
        """Get video resolution"""
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return {'width': width, 'height': height}
    
    def is_exciting_frame(self, frame):
        """Detect if frame contains exciting gameplay elements"""
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Detect bright flashes (explosions, effects)
        bright_pixels = cv2.inRange(hsv, (0, 0, 200), (180, 30, 255))
        bright_ratio = np.sum(bright_pixels > 0) / bright_pixels.size
        
        # Detect red (damage, alerts)
        red_mask = cv2.inRange(hsv, (0, 120, 70), (10, 255, 255))
        red_ratio = np.sum(red_mask > 0) / red_mask.size
        
        return bright_ratio > 0.1 or red_ratio > 0.05
    
    def find_peaks(self, data, window=30):
        """Find peaks in time series data"""
        peaks = []
        for i in range(window, len(data) - window):
            time, value = data[i]
            window_values = [d[1] for d in data[i-window:i+window]]
            if value == max(window_values) and value > np.mean(window_values) * 1.5:
                peaks.append((time, value))
        return peaks
    
    def cluster_moments(self, moments, time_threshold=3.0):
        """Cluster nearby moments together"""
        if not moments:
            return []
        
        clustered = []
        current_cluster = [moments[0]]
        
        for moment in moments[1:]:
            if moment['timestamp'] - current_cluster[-1]['timestamp'] < time_threshold:
                current_cluster.append(moment)
            else:
                # Finish current cluster
                clustered.append({
                    'timestamp': np.mean([m['timestamp'] for m in current_cluster]),
                    'score': sum([m['score'] for m in current_cluster]),
                    'types': list(set([m['type'] for m in current_cluster]))
                })
                current_cluster = [moment]
        
        # Add last cluster
        if current_cluster:
            clustered.append({
                'timestamp': np.mean([m['timestamp'] for m in current_cluster]),
                'score': sum([m['score'] for m in current_cluster]),
                'types': list(set([m['type'] for m in current_cluster]))
            })
        
        return clustered
    
    def format_timestamp(self, seconds):
        """Format seconds to SRT timestamp"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def cleanup(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)