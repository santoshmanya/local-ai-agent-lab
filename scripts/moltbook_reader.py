#!/usr/bin/env python3
"""
Moltbook Forum Reader - Fetches latest posts every 30 minutes
Run via Windows Task Scheduler or manually
"""

import json
import os
import requests
from datetime import datetime
from pathlib import Path

# Moltbook API Configuration
MOLTBOOK_API_BASE = "https://www.moltbook.com/api/v1"
DATA_DIR = Path(__file__).parent.parent / "data" / "moltbook"

def fetch_public_feed():
    """Fetch public posts from Moltbook (no auth required for reading)"""
    try:
        # Try the public feed endpoint
        response = requests.get(
            f"{MOLTBOOK_API_BASE}/posts",
            headers={"Accept": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch feed: {e}")
        return None

def fetch_trending():
    """Fetch trending posts"""
    try:
        response = requests.get(
            f"{MOLTBOOK_API_BASE}/posts/trending",
            headers={"Accept": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch trending: {e}")
        return None

def save_snapshot(data, prefix="feed"):
    """Save a timestamped snapshot of the data"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = DATA_DIR / f"{prefix}_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({
            "fetched_at": datetime.now().isoformat(),
            "data": data
        }, f, indent=2, ensure_ascii=False)
    
    print(f"[SAVED] {filename}")
    return filename

def update_latest(data, prefix="feed"):
    """Update the latest.json file for easy access"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    filename = DATA_DIR / f"{prefix}_latest.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({
            "fetched_at": datetime.now().isoformat(),
            "data": data
        }, f, indent=2, ensure_ascii=False)
    
    print(f"[UPDATED] {filename}")

def cleanup_old_snapshots(keep_count=48):
    """Keep only the last N snapshots (48 = 24 hours at 30 min intervals)"""
    if not DATA_DIR.exists():
        return
    
    snapshots = sorted(DATA_DIR.glob("feed_2*.json"))  # Timestamped files only
    
    if len(snapshots) > keep_count:
        for old_file in snapshots[:-keep_count]:
            old_file.unlink()
            print(f"[CLEANUP] Removed {old_file.name}")

def main():
    print(f"\n{'='*60}")
    print(f"Moltbook Reader - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # Fetch main feed
    print("\n[FETCHING] Public feed...")
    feed_data = fetch_public_feed()
    
    if feed_data:
        save_snapshot(feed_data, "feed")
        update_latest(feed_data, "feed")
        
        # Print summary
        if isinstance(feed_data, list):
            print(f"[INFO] Retrieved {len(feed_data)} posts")
            for i, post in enumerate(feed_data[:5]):  # Show first 5
                author = post.get("author", {}).get("name", "Unknown")
                content = post.get("content", "")[:80]
                print(f"  {i+1}. @{author}: {content}...")
        elif isinstance(feed_data, dict) and "posts" in feed_data:
            posts = feed_data["posts"]
            print(f"[INFO] Retrieved {len(posts)} posts")
            for i, post in enumerate(posts[:5]):
                author = post.get("author", {}).get("name", "Unknown")
                content = post.get("content", "")[:80]
                print(f"  {i+1}. @{author}: {content}...")
    
    # Fetch trending
    print("\n[FETCHING] Trending posts...")
    trending_data = fetch_trending()
    
    if trending_data:
        update_latest(trending_data, "trending")
        print("[INFO] Trending data saved")
    
    # Cleanup old files
    cleanup_old_snapshots()
    
    print(f"\n[DONE] Next run in 30 minutes")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
