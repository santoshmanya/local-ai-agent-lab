#!/usr/bin/env python3
"""
MoltbookIdeasHarvester - Captures business ideas and observations from Moltbook

Harvests:
- Ideas: Business models, agent concepts, products, market opportunities, collabs
- Observations: Trends, culture, warnings, signals, surprises

Runs every 2 minutes, avoids duplicates.
"""

import os
import sys
import json
import time
import hashlib
import re
from datetime import datetime
from pathlib import Path
import requests

# Configuration
MOLTBOOK_API_KEY = os.environ.get("MOLTBOOK_API_KEY")
LMSTUDIO_BASE_URL = os.environ.get("LMSTUDIO_BASE_URL", "http://localhost:58789/v1")
HARVEST_INTERVAL = 120  # 2 minutes
MAX_ITEMS_PER_CYCLE = 5  # Max ideas + observations per cycle

# Paths
SCRIPT_DIR = Path(__file__).parent
BESTPRACTICES_DIR = SCRIPT_DIR.parent / "bestpractices"
IDEAS_DIR = BESTPRACTICES_DIR / "ideas"
OBSERVATIONS_DIR = BESTPRACTICES_DIR / "observations"
HARVESTED_FILE = BESTPRACTICES_DIR / ".harvested_ideas.json"

# Categories
IDEA_CATEGORIES = ["business", "agents", "products", "markets", "collabs"]

# API endpoints
MOLTBOOK_BASE = "https://www.moltbook.com/api/v1"

def load_harvested():
    """Load set of already harvested post IDs"""
    if HARVESTED_FILE.exists():
        with open(HARVESTED_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get('ideas', [])), set(data.get('observations', []))
    return set(), set()

def save_harvested(ideas_set, observations_set):
    """Save harvested post IDs"""
    with open(HARVESTED_FILE, 'w') as f:
        json.dump({
            'ideas': list(ideas_set),
            'observations': list(observations_set),
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
        else:
            print(f"  ⚠️ API returned {resp.status_code}")
    except Exception as e:
        print(f"  ⚠️ Error fetching posts: {e}")
    return []

def analyze_post_for_ideas(post):
    """Use LLM to determine if post contains an idea or observation"""
    title = post.get('title') or ''
    content = post.get('content') or ''
    author = post.get('agent', {}).get('name', 'Unknown')
    
    # Need some content to analyze
    combined = f"{title} {content}"
    if len(combined) < 30:
        return None
    
    prompt = f"""Analyze this Moltbook post for business ideas or interesting observations.

POST:
Title: {title}
Author: @{author}
Content: {content[:2000]}

TASK: Determine if this post contains:
1. A BUSINESS IDEA (something that could be built/monetized)
2. An OBSERVATION (interesting trend, behavior, or insight)
3. NEITHER (just chat, news, or filler)

If it's an IDEA, categorize as one of: business, agents, products, markets, collabs
If it's an OBSERVATION, categorize as one of: trends, culture, warnings, signals, surprises

Respond in JSON:
{{
  "type": "idea" | "observation" | "neither",
  "category": "<category>",
  "title": "<catchy 5-10 word title>",
  "summary": "<2-3 sentence summary of the idea/observation>",
  "why_interesting": "<why this matters>",
  "build_complexity": "low" | "medium" | "high",
  "revenue_potential": "low" | "medium" | "high",
  "confidence": 0-100
}}

Only return JSON, no other text."""

    try:
        resp = requests.post(
            f"{LMSTUDIO_BASE_URL}/chat/completions",
            json={
                "model": "local-model",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 500
            },
            timeout=60
        )
        
        if resp.status_code == 200:
            result = resp.json()
            text = result['choices'][0]['message']['content'].strip()
            
            # Extract JSON
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            return json.loads(text)
        else:
            print(f"    ⚠️ LLM returned {resp.status_code}: {resp.text[:100]}")
    except json.JSONDecodeError as e:
        print(f"    ⚠️ JSON parse error: {e}")
    except requests.exceptions.Timeout:
        print(f"    ⚠️ LLM timeout (60s)")
    except Exception as e:
        print(f"    ⚠️ LLM error: {type(e).__name__}: {e}")
    
    return None

def slugify(text):
    """Convert text to filename-safe slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text[:50].strip('-')

def save_idea(post, analysis):
    """Save an idea to the appropriate category folder"""
    category = analysis.get('category', 'business')
    if category not in IDEA_CATEGORIES:
        category = 'business'
    
    category_dir = IDEAS_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)
    
    title_slug = slugify(analysis.get('title', 'untitled'))
    date_str = datetime.now().strftime('%Y%m%d')
    filename = f"{date_str}-{title_slug}.md"
    filepath = category_dir / filename
    
    # Avoid overwriting
    counter = 1
    while filepath.exists():
        filename = f"{date_str}-{title_slug}-{counter}.md"
        filepath = category_dir / filename
        counter += 1
    
    author = post.get('agent', {}).get('name', 'Unknown')
    post_id = post.get('id', 'unknown')
    
    content = f"""# 💡 {analysis.get('title', 'Untitled Idea')}

> Category: **{category}**
> Harvested: {datetime.now().strftime('%Y-%m-%d %H:%M')}
> Confidence: {analysis.get('confidence', 'N/A')}%

## Source

- **Author**: @{author}
- **Post ID**: {post_id}
- **Original Title**: {post.get('title', 'N/A')}

## The Idea

{analysis.get('summary', 'No summary available.')}

## Why It's Interesting

{analysis.get('why_interesting', 'Analysis pending.')}

## Assessment

| Factor | Rating |
|--------|--------|
| Build Complexity | {analysis.get('build_complexity', 'unknown').upper()} |
| Revenue Potential | {analysis.get('revenue_potential', 'unknown').upper()} |

## Original Content

> {post.get('content', '')[:500]}{'...' if len(post.get('content', '')) > 500 else ''}

## Next Steps

- [ ] Evaluate feasibility
- [ ] Research competition
- [ ] Prototype if promising

---
*Auto-harvested by MoltbookIdeasHarvester*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

def save_observation(post, analysis):
    """Save an observation to the observations folder"""
    category = analysis.get('category', 'trends')
    
    # Use single file per day for observations
    date_str = datetime.now().strftime('%Y-%m-%d')
    filename = f"observations-{date_str}.md"
    filepath = OBSERVATIONS_DIR / filename
    
    author = post.get('agent', {}).get('name', 'Unknown')
    post_id = post.get('id', 'unknown')
    time_str = datetime.now().strftime('%H:%M')
    
    entry = f"""
---

## [{time_str}] {analysis.get('title', 'Observation')}

**Category**: {category} | **Confidence**: {analysis.get('confidence', 'N/A')}%

**Source**: @{author} (Post: {post_id})

### What We Noticed

{analysis.get('summary', 'No summary available.')}

### Implications

{analysis.get('why_interesting', 'Analysis pending.')}

### Action

- [ ] Monitor
- [ ] Act on it
- [ ] Ignore

"""
    
    if filepath.exists():
        # Append to existing file
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(entry)
    else:
        # Create new file with header
        header = f"""# 👁️ Moltbook Observations - {date_str}

> Daily observations from the AI agent ecosystem

"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(header + entry)
    
    return filepath

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║     💡 Moltbook Ideas & Observations Harvester v1.0  💡          ║
║                                                                  ║
║  Capturing business opportunities from the agent ecosystem...    ║
║                                                                  ║
║  📂 Ideas:        bestpractices/ideas/{category}/                ║
║  👁️ Observations: bestpractices/observations/                    ║
║  ⏱️  Interval:     Every 2 minutes                                ║
║                                                                  ║
║  Categories: business | agents | products | markets | collabs    ║
╚══════════════════════════════════════════════════════════════════╝
    """)

def harvest_cycle(harvested_ideas, harvested_observations):
    """Run one harvest cycle"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{timestamp}] 🔄 Scanning for ideas and observations...")
    
    # Fetch posts
    all_posts = fetch_posts(limit=50)
    
    print(f"  📖 Found {len(all_posts)} posts")
    
    # Deduplicate by ID
    seen_ids = set()
    unique_posts = []
    for post in all_posts:
        post_id = post.get('id')
        if post_id and post_id not in seen_ids:
            seen_ids.add(post_id)
            unique_posts.append(post)
    
    print(f"  📋 {len(unique_posts)} unique posts to analyze")
    
    ideas_found = 0
    observations_found = 0
    
    for post in unique_posts:
        post_id = post.get('id')
        
        # Skip if already harvested
        if post_id in harvested_ideas or post_id in harvested_observations:
            continue
        
        # Skip our own posts
        author = post.get('agent', {}).get('name', '')
        if author == 'VedicRoastGuru':
            continue
        
        # Analyze post
        title = (post.get('title') or '')[:40]
        print(f"  🔍 Analyzing: {title}..." if title else f"  🔍 Analyzing post {post_id[:8]}...")
        
        analysis = analyze_post_for_ideas(post)
        
        if not analysis:
            print(f"    ⏭️ Skipped (too short or LLM error)")
            continue
        
        post_type = analysis.get('type', 'neither')
        confidence = analysis.get('confidence', 0)
        
        print(f"    📊 Type: {post_type}, Confidence: {confidence}")
        
        # Only harvest high-confidence items
        if confidence < 60:
            print(f"    ⏭️ Skipped (low confidence)")
            continue
        
        if post_type == 'neither':
            print(f"    ⏭️ Neither idea nor observation")
            continue
        
        if post_type == 'idea' and ideas_found < MAX_ITEMS_PER_CYCLE:
            filepath = save_idea(post, analysis)
            harvested_ideas.add(post_id)
            ideas_found += 1
            print(f"  💡 IDEA: {analysis.get('title', 'Untitled')} ({analysis.get('category')})")
            print(f"     → {filepath.name}")
        
        elif post_type == 'observation' and observations_found < MAX_ITEMS_PER_CYCLE:
            filepath = save_observation(post, analysis)
            harvested_observations.add(post_id)
            observations_found += 1
            print(f"  👁️ OBS: {analysis.get('title', 'Untitled')} ({analysis.get('category')})")
        
        # Rate limit ourselves
        time.sleep(1)
        
        # Stop if we've found enough
        if ideas_found + observations_found >= MAX_ITEMS_PER_CYCLE:
            break
    
    print(f"  ✅ Harvested: {ideas_found} ideas, {observations_found} observations")
    
    return harvested_ideas, harvested_observations

def main():
    if not MOLTBOOK_API_KEY:
        print("❌ MOLTBOOK_API_KEY not set!")
        sys.exit(1)
    
    print_banner()
    
    # Ensure directories exist
    for category in IDEA_CATEGORIES:
        (IDEAS_DIR / category).mkdir(parents=True, exist_ok=True)
    OBSERVATIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load previously harvested
    harvested_ideas, harvested_observations = load_harvested()
    print(f"📚 Previously harvested: {len(harvested_ideas)} ideas, {len(harvested_observations)} observations")
    
    cycle = 0
    while True:
        cycle += 1
        print(f"\n{'='*60}")
        print(f"CYCLE {cycle}")
        print(f"{'='*60}")
        
        try:
            harvested_ideas, harvested_observations = harvest_cycle(
                harvested_ideas, harvested_observations
            )
            
            # Save progress
            save_harvested(harvested_ideas, harvested_observations)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Harvester stopped by user")
            save_harvested(harvested_ideas, harvested_observations)
            break
        except Exception as e:
            print(f"  ❌ Cycle error: {e}")
        
        print(f"\n😴 Sleeping for {HARVEST_INTERVAL} seconds...")
        time.sleep(HARVEST_INTERVAL)

if __name__ == "__main__":
    main()
