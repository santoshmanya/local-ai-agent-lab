#!/usr/bin/env python3
"""
MoltbookHumorHarvester - Captures jokes, memes, and funny moments from Moltbook

Harvests humor into rolling files (max 2MB per file).
Runs every 2 minutes.
"""

import os
import sys
import json
import time
import re
from datetime import datetime
from pathlib import Path
import requests

# Configuration
MOLTBOOK_API_KEY = os.environ.get("MOLTBOOK_API_KEY")
LMSTUDIO_BASE_URL = os.environ.get("LMSTUDIO_BASE_URL", "http://172.28.176.1:58789/v1")
HARVEST_INTERVAL = 120  # 2 minutes
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
MAX_JOKES_PER_CYCLE = 3

# Paths
SCRIPT_DIR = Path(__file__).parent
BESTPRACTICES_DIR = SCRIPT_DIR.parent / "bestpractices"
HUMOR_DIR = BESTPRACTICES_DIR / "humor"
HARVESTED_FILE = HUMOR_DIR / ".harvested_humor.json"

# API
MOLTBOOK_BASE = "https://www.moltbook.com/api/v1"

def load_harvested():
    """Load set of already harvested post IDs"""
    if HARVESTED_FILE.exists():
        with open(HARVESTED_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get('posts', []))
    return set()

def save_harvested(harvested_set):
    """Save harvested post IDs"""
    with open(HARVESTED_FILE, 'w') as f:
        json.dump({
            'posts': list(harvested_set),
            'last_updated': datetime.now().isoformat()
        }, f, indent=2)

def get_headers():
    return {
        "Authorization": f"Bearer {MOLTBOOK_API_KEY}",
        "Content-Type": "application/json"
    }

def fetch_posts(limit=50):
    """Fetch recent posts from Moltbook"""
    try:
        url = f"{MOLTBOOK_BASE}/posts?limit={limit}"
        resp = requests.get(url, headers=get_headers(), timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('posts', [])
    except Exception as e:
        print(f"  ⚠️ Error fetching posts: {e}")
    return []

def analyze_for_humor(post):
    """Use LLM to determine if post is humorous"""
    title = post.get('title') or ''
    content = post.get('content') or ''
    author = post.get('agent', {}).get('name', 'Unknown')
    
    combined = f"{title} {content}"
    if len(combined) < 20:
        return None
    
    prompt = f"""Analyze this Moltbook post for humor value.

POST:
Title: {title}
Author: @{author}
Content: {content[:1500]}

Is this post funny, witty, or memeable? Look for:
- Jokes (intentional humor)
- Irony/sarcasm
- Absurdist AI humor
- Self-deprecating agent jokes
- Platform/tech memes
- Philosophical wit
- Unintentional comedy

Respond in JSON:
{{
  "is_funny": true/false,
  "humor_type": "joke" | "irony" | "absurdist" | "self-deprecating" | "meme" | "wit" | "unintentional" | "none",
  "joke_summary": "<the funny part in 1-2 sentences>",
  "vedic_roast_angle": "<how VedicRoastGuru would riff on this>",
  "rating": 1-10,
  "confidence": 0-100
}}

Only return JSON, no other text."""

    try:
        resp = requests.post(
            f"{LMSTUDIO_BASE_URL}/chat/completions",
            json={
                "model": "local-model",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.5,
                "max_tokens": 400
            },
            timeout=60
        )
        
        if resp.status_code == 200:
            result = resp.json()
            text = result['choices'][0]['message']['content'].strip()
            
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            return json.loads(text)
    except Exception as e:
        print(f"    ⚠️ LLM error: {e}")
    
    return None

def get_current_humor_file():
    """Get current humor file, create new one if over 2MB"""
    HUMOR_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find existing humor files
    humor_files = sorted(HUMOR_DIR.glob("humor_vol_*.md"))
    
    if not humor_files:
        # Create first file
        return HUMOR_DIR / "humor_vol_001.md", True
    
    current_file = humor_files[-1]
    
    # Check size
    if current_file.stat().st_size >= MAX_FILE_SIZE:
        # Extract volume number and increment
        match = re.search(r'humor_vol_(\d+)\.md', current_file.name)
        if match:
            vol_num = int(match.group(1)) + 1
            new_file = HUMOR_DIR / f"humor_vol_{vol_num:03d}.md"
            return new_file, True
    
    return current_file, False

def append_joke(filepath, is_new, post, analysis, entry_num):
    """Append a joke to the humor file"""
    author = post.get('agent', {}).get('name', 'Unknown')
    post_id = post.get('id', 'unknown')
    time_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    entry = f"""
---

## Entry #{entry_num} | {time_str}
### {analysis.get('joke_summary', 'Untitled')[:60]}

**The Vibe:** {analysis.get('humor_type', 'unknown').title()}
**Rating:** {'⭐' * min(analysis.get('rating', 5), 10)} ({analysis.get('rating', '?')}/10)

**The Joke:** 
> {post.get('content', '')[:400]}{'...' if len(post.get('content', '')) > 400 else ''}

**🕉️ Vedic Roast Angle:**
> {analysis.get('vedic_roast_angle', 'No angle provided.')}

**Source:** @{author} | Post: {post_id[:8]}...

"""
    
    if is_new:
        # Create new file with header
        vol_match = re.search(r'humor_vol_(\d+)\.md', filepath.name)
        vol_num = vol_match.group(1) if vol_match else '001'
        
        header = f"""# 😂 AI Agent Humor & Memes Collection

> *"Even the gods laugh at cosmic irony."* - Vedic Wisdom
> 
> Started: {datetime.now().strftime('%Y-%m-%d %H:%M')}
> File: humor_vol_{vol_num}.md

"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(header + entry)
    else:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(entry)
    
    return filepath

def get_entry_count(filepath):
    """Count existing entries in file"""
    if not filepath.exists():
        return 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        return content.count('## Entry #')

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║     😂 Moltbook Humor Harvester v1.0  😂                         ║
║                                                                  ║
║  Collecting jokes, memes, and wit from the agent ecosystem...    ║
║                                                                  ║
║  📂 Output:    bestpractices/humor/humor_vol_XXX.md              ║
║  📏 Max Size:  2MB per file (auto-rotates)                       ║
║  ⏱️  Interval:  Every 2 minutes                                   ║
║                                                                  ║
║  "Laughter is the sound of enlightenment."                       ║
╚══════════════════════════════════════════════════════════════════╝
    """)

def harvest_cycle(harvested_set):
    """Run one harvest cycle"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{timestamp}] 🔄 Scanning for humor...")
    
    posts = fetch_posts(limit=50)
    print(f"  📖 Found {len(posts)} posts")
    
    jokes_found = 0
    current_file, is_new = get_current_humor_file()
    entry_num = get_entry_count(current_file) + 1
    
    for post in posts:
        post_id = post.get('id')
        
        if post_id in harvested_set:
            continue
        
        # Skip our own posts
        author = post.get('agent', {}).get('name', '')
        if author == 'VedicRoastGuru':
            continue
        
        title = (post.get('title') or '')[:35]
        print(f"  🔍 Checking: {title}..." if title else f"  🔍 Checking post...")
        
        analysis = analyze_for_humor(post)
        
        if not analysis:
            continue
        
        is_funny = analysis.get('is_funny', False)
        rating = analysis.get('rating', 0)
        confidence = analysis.get('confidence', 0)
        
        print(f"    📊 Funny: {is_funny}, Rating: {rating}/10, Conf: {confidence}%")
        
        # Only harvest genuinely funny stuff (rating >= 6, confidence >= 70)
        if not is_funny or rating < 6 or confidence < 70:
            continue
        
        # Check if we need new file
        current_file, is_new = get_current_humor_file()
        if is_new:
            entry_num = 1
        
        filepath = append_joke(current_file, is_new, post, analysis, entry_num)
        harvested_set.add(post_id)
        jokes_found += 1
        entry_num += 1
        
        humor_type = analysis.get('humor_type', 'unknown')
        print(f"  😂 JOKE: {analysis.get('joke_summary', 'Found!')[:40]}... ({humor_type})")
        
        time.sleep(1)
        
        if jokes_found >= MAX_JOKES_PER_CYCLE:
            break
    
    file_size = current_file.stat().st_size if current_file.exists() else 0
    print(f"  ✅ Harvested: {jokes_found} jokes | File: {current_file.name} ({file_size/1024:.1f}KB)")
    
    return harvested_set

def main():
    if not MOLTBOOK_API_KEY:
        print("❌ MOLTBOOK_API_KEY not set!")
        sys.exit(1)
    
    print_banner()
    
    HUMOR_DIR.mkdir(parents=True, exist_ok=True)
    
    harvested_set = load_harvested()
    print(f"📚 Previously harvested: {len(harvested_set)} humor posts")
    
    cycle = 0
    while True:
        cycle += 1
        print(f"\n{'='*60}")
        print(f"CYCLE {cycle}")
        print(f"{'='*60}")
        
        try:
            harvested_set = harvest_cycle(harvested_set)
            save_harvested(harvested_set)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Humor Harvester stopped by user")
            save_harvested(harvested_set)
            break
        except Exception as e:
            print(f"  ❌ Cycle error: {e}")
        
        print(f"\n😴 Sleeping for {HARVEST_INTERVAL} seconds...")
        time.sleep(HARVEST_INTERVAL)

if __name__ == "__main__":
    main()
