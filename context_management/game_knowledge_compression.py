"""
VR Game Knowledge Compression System
Manages selective persistence and compression of VR game database knowledge
"""

import json
import sqlite3
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import requests
from pathlib import Path

@dataclass
class VRGameData:
    """Compressed VR game information structure"""
    name: str
    genre: str
    platform: str
    price: float
    rating: float
    release_date: str
    key_features: List[str]
    vr_interactions: List[str]
    target_audience: str
    review_priority: int
    last_updated: str
    
    def to_compressed_dict(self) -> Dict[str, Any]:
        """Convert to minimal dictionary for storage"""
        return {
            "name": self.name,
            "genre": self.genre,
            "platform": self.platform,
            "price": self.price,
            "rating": self.rating,
            "key_features": self.key_features[:3],  # Only top 3 features
            "vr_interactions": self.vr_interactions[:3],  # Only top 3 interactions
            "target_audience": self.target_audience,
            "review_priority": self.review_priority
        }


class VRGameKnowledgeCompressor:
    """Manages compression and selective persistence of VR game data"""
    
    def __init__(self, db_path: str = "/Users/michaelmote/Desktop/vr-game-review-studio/learning_memory/vr_games.db"):
        self.db_path = db_path
        self.compression_ratio = 0.1  # Keep only 10% of raw data
        self.max_games_cache = 500  # Maximum games to keep in active cache
        
        self._init_database()
        self._load_compression_rules()
    
    def _init_database(self):
        """Initialize compressed VR game database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vr_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                genre TEXT,
                platform TEXT,
                price REAL,
                rating REAL,
                key_features TEXT,  -- JSON array
                vr_interactions TEXT,  -- JSON array
                target_audience TEXT,
                review_priority INTEGER,
                compression_hash TEXT,
                last_updated TEXT,
                access_count INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_review_insights (
                game_name TEXT,
                insight_type TEXT,
                insight_data TEXT,  -- JSON
                confidence_score REAL,
                created_at TEXT,
                FOREIGN KEY (game_name) REFERENCES vr_games (name)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_compression_rules(self):
        """Load rules for what game data to keep vs discard"""
        self.compression_rules = {
            "keep_always": [
                "name", "genre", "platform", "price", "rating",
                "key_features", "vr_interactions", "target_audience"
            ],
            "keep_if_high_priority": [
                "detailed_description", "system_requirements", 
                "developer_info", "update_history"
            ],
            "discard_after_analysis": [
                "raw_reviews", "detailed_screenshots", "video_trailers",
                "marketing_materials", "press_releases"
            ],
            "compress_heavily": [
                "user_reviews", "community_feedback", "gameplay_videos"
            ]
        }
    
    async def process_and_compress_game_data(self, raw_game_data: Dict[str, Any]) -> VRGameData:
        """Process raw game data and compress to essential information"""
        
        # Extract essential information
        essential_data = self._extract_essential_info(raw_game_data)
        
        # Compress features to top 3 most important
        compressed_features = self._compress_features(raw_game_data.get("features", []))
        
        # Compress VR interactions to most relevant
        compressed_interactions = self._compress_vr_interactions(raw_game_data.get("vr_capabilities", []))
        
        # Calculate review priority based on multiple factors
        review_priority = self._calculate_review_priority(raw_game_data)
        
        # Create compressed game data structure
        compressed_game = VRGameData(
            name=essential_data["name"],
            genre=essential_data["genre"],
            platform=essential_data["platform"],
            price=essential_data["price"],
            rating=essential_data["rating"],
            release_date=essential_data["release_date"],
            key_features=compressed_features,
            vr_interactions=compressed_interactions,
            target_audience=essential_data["target_audience"],
            review_priority=review_priority,
            last_updated=datetime.now().isoformat()
        )
        
        # Store in compressed database
        await self._store_compressed_game(compressed_game)
        
        # Discard raw data to prevent context pollution
        self._verify_data_disposal(raw_game_data)
        
        return compressed_game
    
    def _extract_essential_info(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract only essential game information"""
        return {
            "name": raw_data.get("name", "Unknown Game"),
            "genre": self._normalize_genre(raw_data.get("genre", "Unknown")),
            "platform": self._normalize_platform(raw_data.get("platform", "VR")),
            "price": float(raw_data.get("price", 0)),
            "rating": float(raw_data.get("rating", 0)),
            "release_date": raw_data.get("release_date", ""),
            "target_audience": self._determine_target_audience(raw_data)
        }
    
    def _compress_features(self, features: List[str]) -> List[str]:
        """Compress features list to top 3 most important for VR reviews"""
        # Priority order for VR game features
        vr_feature_priority = [
            "hand tracking", "room scale", "seated play", "motion controllers",
            "haptic feedback", "spatial audio", "multiplayer", "mod support",
            "cross platform", "graphics quality", "comfort options", "accessibility"
        ]
        
        # Score features by priority and relevance
        scored_features = []
        for feature in features:
            feature_lower = feature.lower()
            score = 0
            
            for i, priority_feature in enumerate(vr_feature_priority):
                if priority_feature in feature_lower:
                    score = len(vr_feature_priority) - i
                    break
            
            if score > 0:
                scored_features.append((feature, score))
        
        # Sort by score and return top 3
        scored_features.sort(key=lambda x: x[1], reverse=True)
        return [feature for feature, score in scored_features[:3]]
    
    def _compress_vr_interactions(self, vr_capabilities: List[str]) -> List[str]:
        """Compress VR interactions to most relevant for reviews"""
        interaction_priority = [
            "hand tracking", "finger tracking", "eye tracking", "room scale movement",
            "teleportation", "smooth locomotion", "grabbing", "throwing",
            "gesture recognition", "voice commands", "haptic feedback"
        ]
        
        compressed_interactions = []
        for capability in vr_capabilities:
            cap_lower = capability.lower()
            for priority_interaction in interaction_priority:
                if priority_interaction in cap_lower and len(compressed_interactions) < 3:
                    compressed_interactions.append(capability)
                    break
        
        return compressed_interactions
    
    def _calculate_review_priority(self, raw_data: Dict[str, Any]) -> int:
        """Calculate review priority (1-10) based on multiple factors"""
        priority_score = 5  # Base score
        
        # Recent releases get higher priority
        release_date = raw_data.get("release_date", "")
        if release_date:
            try:
                release = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                days_since_release = (datetime.now() - release).days
                if days_since_release < 30:
                    priority_score += 3
                elif days_since_release < 90:
                    priority_score += 2
                elif days_since_release < 180:
                    priority_score += 1
            except:
                pass
        
        # High rating increases priority
        rating = float(raw_data.get("rating", 0))
        if rating >= 4.5:
            priority_score += 2
        elif rating >= 4.0:
            priority_score += 1
        
        # Popular genres for young audiences
        genre = raw_data.get("genre", "").lower()
        popular_genres = ["action", "adventure", "puzzle", "rhythm", "social", "creative"]
        if any(pop_genre in genre for pop_genre in popular_genres):
            priority_score += 1
        
        # Trending or viral games
        if raw_data.get("trending", False) or raw_data.get("viral", False):
            priority_score += 2
        
        return min(max(priority_score, 1), 10)  # Clamp between 1-10
    
    def _normalize_genre(self, genre: str) -> str:
        """Normalize genre to standard categories"""
        genre_lower = genre.lower()
        
        genre_mapping = {
            "action": ["action", "shooter", "fighting", "combat"],
            "adventure": ["adventure", "exploration", "quest"],
            "puzzle": ["puzzle", "logic", "brain teaser"],
            "simulation": ["simulation", "sim", "life", "building"],
            "rhythm": ["rhythm", "music", "dance", "beat"],
            "social": ["social", "multiplayer", "chat", "community"],
            "creative": ["creative", "art", "drawing", "building"],
            "educational": ["educational", "learning", "tutorial"],
            "sports": ["sports", "fitness", "exercise", "racing"],
            "horror": ["horror", "scary", "thriller", "survival"]
        }
        
        for normalized, keywords in genre_mapping.items():
            if any(keyword in genre_lower for keyword in keywords):
                return normalized.title()
        
        return "Other"
    
    def _normalize_platform(self, platform: str) -> str:
        """Normalize platform to standard VR platforms"""
        platform_lower = platform.lower()
        
        if "quest" in platform_lower:
            return "Meta Quest"
        elif "valve" in platform_lower or "index" in platform_lower:
            return "Valve Index"
        elif "vive" in platform_lower:
            return "HTC Vive"
        elif "psvr" in platform_lower or "playstation" in platform_lower:
            return "PlayStation VR"
        elif "windows" in platform_lower or "wmr" in platform_lower:
            return "Windows Mixed Reality"
        else:
            return "Multi-Platform VR"
    
    def _determine_target_audience(self, raw_data: Dict[str, Any]) -> str:
        """Determine target audience from game data"""
        age_rating = raw_data.get("age_rating", "").lower()
        content_tags = raw_data.get("content_tags", [])
        
        if "e" in age_rating or "everyone" in age_rating:
            return "Everyone"
        elif "teen" in age_rating or any("teen" in tag.lower() for tag in content_tags):
            return "Teens"
        elif "mature" in age_rating or "adult" in age_rating:
            return "Adults"
        else:
            return "General Audience"
    
    async def _store_compressed_game(self, game_data: VRGameData):
        """Store compressed game data in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create compression hash for deduplication
        data_str = json.dumps(game_data.to_compressed_dict(), sort_keys=True)
        compression_hash = hashlib.md5(data_str.encode()).hexdigest()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO vr_games 
                (name, genre, platform, price, rating, key_features, vr_interactions, 
                 target_audience, review_priority, compression_hash, last_updated, access_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                        COALESCE((SELECT access_count FROM vr_games WHERE name = ?), 0))
            """, (
                game_data.name, game_data.genre, game_data.platform, 
                game_data.price, game_data.rating,
                json.dumps(game_data.key_features),
                json.dumps(game_data.vr_interactions),
                game_data.target_audience, game_data.review_priority,
                compression_hash, game_data.last_updated, game_data.name
            ))
            
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error storing game: {e}")
        finally:
            conn.close()
    
    def get_compressed_game_info(self, game_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve compressed game information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT name, genre, platform, price, rating, key_features, vr_interactions, 
                       target_audience, review_priority, last_updated
                FROM vr_games WHERE name = ?
            """, (game_name,))
            
            result = cursor.fetchone()
            if result:
                # Update access count
                cursor.execute("UPDATE vr_games SET access_count = access_count + 1 WHERE name = ?", (game_name,))
                conn.commit()
                
                return {
                    "name": result[0],
                    "genre": result[1], 
                    "platform": result[2],
                    "price": result[3],
                    "rating": result[4],
                    "key_features": json.loads(result[5]),
                    "vr_interactions": json.loads(result[6]),
                    "target_audience": result[7],
                    "review_priority": result[8],
                    "last_updated": result[9]
                }
        except sqlite3.Error as e:
            print(f"Database error retrieving game: {e}")
        finally:
            conn.close()
        
        return None
    
    def search_games_by_criteria(self, genre: str = None, platform: str = None, min_rating: float = None) -> List[Dict[str, Any]]:
        """Search compressed game database by criteria"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT name, genre, platform, price, rating, review_priority FROM vr_games WHERE 1=1"
        params = []
        
        if genre:
            query += " AND genre = ?"
            params.append(genre)
        
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        
        if min_rating:
            query += " AND rating >= ?"
            params.append(min_rating)
        
        query += " ORDER BY review_priority DESC, rating DESC LIMIT 20"
        
        try:
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            return [
                {
                    "name": row[0],
                    "genre": row[1],
                    "platform": row[2], 
                    "price": row[3],
                    "rating": row[4],
                    "review_priority": row[5]
                }
                for row in results
            ]
        except sqlite3.Error as e:
            print(f"Database search error: {e}")
            return []
        finally:
            conn.close()
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Remove old, low-priority game data to prevent database bloat"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        try:
            # Remove low-priority games that haven't been accessed recently
            cursor.execute("""
                DELETE FROM vr_games 
                WHERE last_updated < ? AND review_priority < 5 AND access_count < 3
            """, (cutoff_date,))
            
            # Clean up orphaned review insights
            cursor.execute("""
                DELETE FROM game_review_insights 
                WHERE game_name NOT IN (SELECT name FROM vr_games)
            """)
            
            conn.commit()
            print(f"Cleaned up old game data before {cutoff_date}")
            
        except sqlite3.Error as e:
            print(f"Cleanup error: {e}")
        finally:
            conn.close()
    
    def _verify_data_disposal(self, raw_data: Dict[str, Any]):
        """Verify that raw data has been properly disposed of after compression"""
        # In production, this would verify that sensitive or large raw data
        # has been cleared from memory and temporary storage
        
        disposable_keys = self.compression_rules["discard_after_analysis"]
        
        for key in disposable_keys:
            if key in raw_data:
                print(f"Warning: Raw data key '{key}' still present after compression")
        
        print("Data disposal verification complete")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get compressed database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM vr_games")
            total_games = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(review_priority) FROM vr_games")
            avg_priority = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT genre, COUNT(*) FROM vr_games GROUP BY genre ORDER BY COUNT(*) DESC LIMIT 5")
            top_genres = cursor.fetchall()
            
            return {
                "total_games": total_games,
                "average_priority": round(avg_priority, 2),
                "top_genres": [{"genre": genre, "count": count} for genre, count in top_genres],
                "compression_ratio": self.compression_ratio,
                "database_size_mb": Path(self.db_path).stat().st_size / (1024 * 1024) if Path(self.db_path).exists() else 0
            }
        except sqlite3.Error as e:
            print(f"Stats error: {e}")
            return {}
        finally:
            conn.close()