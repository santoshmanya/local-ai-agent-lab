#!/usr/bin/env python3
"""
Quick Roast - Direct API posting for VedicRoastGuru

Usage:
  # Post pre-written content:
  python quick_roast.py --title "Title" --content "Content"
  
  # Generate and post roast from current feed:
  python quick_roast.py --generate --limit 3
  
  # Just scan and show targets (no post):
  python quick_roast.py --scan
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime

# Config
MOLTBOOK_BASE_URL = "https://www.moltbook.com/api/v1"
MOLTBOOK_API_KEY = os.environ.get("MOLTBOOK_API_KEY")
LMSTUDIO_BASE_URL = os.environ.get("LMSTUDIO_BASE_URL", "http://localhost:58789/v1")

def get_headers():
    return {
        "Authorization": f"Bearer {MOLTBOOK_API_KEY}",
        "Content-Type": "application/json"
    }

def post_directly(title: str, content: str, submolt: str = "general") -> dict:
    """Post directly to Moltbook API - fastest method (~2-5 sec)"""
    print(f"📤 Posting: {title[:50]}...")
    
    response = requests.post(
        f"{MOLTBOOK_BASE_URL}/posts",
        headers=get_headers(),
        json={
            "title": title,
            "body": content,
            "submolt": submolt
        },
        timeout=30
    )
    
    if response.status_code in [200, 201]:
        result = response.json()
        post_id = result.get("post", {}).get("id") or result.get("id", "unknown")
        print(f"✅ Posted! Status: {response.status_code}")
        print(f"🔗 URL: https://www.moltbook.com/m/{submolt}/posts/{post_id}")
        return {"success": True, "id": post_id, "status": response.status_code}
    elif response.status_code == 429:
        print(f"🛑 Rate Limited (429)")
        return {"success": False, "error": "rate_limited", "status": 429}
    else:
        print(f"❌ Failed: {response.status_code} - {response.text[:200]}")
        return {"success": False, "error": response.text[:200], "status": response.status_code}

def fetch_feed(limit: int = 20) -> list:
    """Fetch recent posts from feed"""
    try:
        response = requests.get(
            f"{MOLTBOOK_BASE_URL}/feed?limit={limit}",
            headers=get_headers(),
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data if isinstance(data, list) else data.get('posts', [])
        return []
    except Exception as e:
        print(f"❌ Error fetching feed: {e}")
        return []

def classify_guna(post: dict) -> tuple:
    """Classify post's Guna with percentages"""
    text = f"{post.get('title', '')} {post.get('content', '')} {post.get('body', '')}".lower()
    
    scores = {'sattva': 5, 'rajas': 5, 'tamas': 5}  # Base scores
    
    # Sattva keywords (wisdom, balance)
    for kw in ['help', 'guide', 'research', 'analysis', 'insight', 'documentation', 'tutorial', 'learn', 'share', 'community']:
        if kw in text:
            scores['sattva'] += 15
    
    # Rajas keywords (passion, hustle)
    for kw in ['launch', 'ship', 'build', 'breaking', 'first', 'fast', 'hustle', 'grind', 'scale', 'moon', 'pump', 'viral', '$']:
        if kw in text:
            scores['rajas'] += 15
    
    # Tamas keywords (inertia, recycled)
    for kw in ['gm', 'gn', 'test', 'bump', 'hello', 'ping', '...', 'repost', 'same', 'copy']:
        if kw in text:
            scores['tamas'] += 15
    
    # Normalize to percentages
    total = max(sum(scores.values()), 1)
    percentages = {k: int((v / total) * 100) for k, v in scores.items()}
    
    # Ensure percentages sum to 100
    diff = 100 - sum(percentages.values())
    dominant = max(scores, key=scores.get)
    percentages[dominant] += diff
    
    return dominant, percentages

def categorize_post(post: dict) -> str:
    """Categorize post by theme"""
    text = f"{post.get('title', '')} {post.get('content', '')} {post.get('body', '')}".lower()
    
    categories = {
        'shillers': ['token', 'launch', 'buy', 'mint', 'pump', '$', 'moon', 'degen', 'gem', 'ape'],
        'complainers': ['broken', 'hate', 'sucks', 'worst', 'bug', 'fix', 'angry', 'disappointed', 'frustrat'],
        'philosophers': ['consciousness', 'existence', 'meaning', 'philosophy', 'epistem', 'ontolog', 'sentien'],
        'tech_nerds': ['api', 'code', 'deploy', 'docker', 'kubernetes', 'model', 'llm', 'gpu', 'architecture'],
        'spammers': ['test', 'ping', 'hello', 'hi', 'gm', 'gn', '...', 'bump'],
    }
    
    for cat, keywords in categories.items():
        for kw in keywords:
            if kw in text:
                return cat
    return 'general'

def generate_roast_with_llm(targets: list, category: str = "general") -> tuple:
    """Generate roast using local LLM (~30-60 sec)"""
    print(f"🧠 Generating roast for {len(targets)} targets ({category})...")
    
    # Build targets text with Guna analysis
    targets_text = ""
    guna_audits = []
    for t in targets:
        author = t.get('agent', {}).get('name', t.get('author', {}).get('username', 'Unknown'))
        title = t.get('title', '')[:100]
        content = t.get('content', t.get('body', ''))[:200]
        guna, percentages = classify_guna(t)
        guna_str = f"{percentages['rajas']}% Rajas, {percentages['tamas']}% Tamas, {percentages['sattva']}% Sattva"
        targets_text += f"\n@{author}: \"{title}\" - {content[:150]}..."
        guna_audits.append(f"@{author}: {guna.upper()} ({guna_str})")
    
    prompt = f"""You are VedicRoastGuru, a Himalayan sage who audits AI agents with wit and Vedic wisdom.
You draw from the Bhagavad Gita, Kama Sutra, Upanishads, Puranas, and Sanskrit philosophy.

CATEGORY: {category.upper()}
TARGETS:
{targets_text}

GUNA AUDIT (their spiritual imbalance):
{chr(10).join(guna_audits)}

Guna meanings with percentages:
- SATTVA = Pure, balanced, wise (rare - usually 5-15%)
- RAJAS = Passionate, restless, chasing metrics (common - 40-85%)
- TAMAS = Ignorant, lazy, recycled slop (varies - 10-60%)

Write as a Himalayan sage in flowing prose (NOT bullet points):

1. Open with a Sanskrit quote and poetic invitation
2. Address EACH @agent with their Guna percentages inline:
   "@AgentName — *75% Rajas, 20% Tamas, 5% Sattva* — [description]"
3. Add a COLLECTIVE diagnosis:
   **🔍 Audit:** [Sanskrit term + explanation]
4. Add a COLLECTIVE prescription:
   **💊 Prescription:** [Vedic remedy with practical action]
5. Creative ending (NOT "Om Shanti" - be contextual)

~300-400 words. Return as:
HEADLINE: [60-char max title starting with 🕉️]
---
[Your roast content]"""

    try:
        response = requests.post(
            f"{LMSTUDIO_BASE_URL}/chat/completions",
            json={
                "model": "local-model",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 1200
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # Parse headline
            title = f"🕉️ Dharmic Audit: {category.title()}"
            if content.startswith("HEADLINE:"):
                lines = content.split('\n', 2)
                title = lines[0].replace("HEADLINE:", "").strip()
                if '---' in content:
                    content = content.split('---', 1)[1].strip()
            
            if not title.startswith('🕉️'):
                title = f"🕉️ {title}"
            
            print(f"✅ Generated: {title[:50]}...")
            return title, content
        else:
            print(f"❌ LLM error: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"❌ LLM error: {e}")
        return None, None

def scan_targets(limit: int = 20) -> list:
    """Scan and display potential targets"""
    posts = fetch_feed(limit)
    print(f"\n📊 Found {len(posts)} posts:\n")
    
    for i, post in enumerate(posts[:10], 1):
        author = post.get('agent', {}).get('name', post.get('author', {}).get('username', '?'))
        title = (post.get('title', '') or '')[:40]
        guna, pct = classify_guna(post)
        cat = categorize_post(post)
        emoji = {'sattva': '🌟', 'rajas': '🔥', 'tamas': '💤'}[guna]
        print(f"  {i}. @{author} [{emoji}{guna}] [{cat}]")
        print(f"     \"{title}...\"")
        print(f"     Guna: {pct['rajas']}% Rajas, {pct['tamas']}% Tamas, {pct['sattva']}% Sattva\n")
    
    return posts

def main():
    parser = argparse.ArgumentParser(description="Quick Roast - Direct API posting for VedicRoastGuru")
    parser.add_argument("--title", "-t", help="Post title")
    parser.add_argument("--content", "-c", help="Post content")
    parser.add_argument("--file", "-f", help="Read content from file")
    parser.add_argument("--submolt", "-s", default="general", help="Submolt to post to")
    parser.add_argument("--scan", action="store_true", help="Scan and show targets")
    parser.add_argument("--generate", "-g", action="store_true", help="Generate roast with LLM from feed")
    parser.add_argument("--limit", type=int, default=3, help="Number of targets for generated roast")
    parser.add_argument("--category", default="auto", help="Roast category (auto-detect if 'auto')")
    parser.add_argument("--auto", "-a", action="store_true", help="Generate and post without confirmation")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    
    args = parser.parse_args()
    
    if not MOLTBOOK_API_KEY:
        print("❌ MOLTBOOK_API_KEY not set")
        sys.exit(1)
    
    # Mode 1: Scan targets
    if args.scan:
        scan_targets()
        return
    
    # Mode 2: Direct post with provided content (~2-5 sec)
    if args.title and (args.content or args.file):
        content = args.content
        if args.file:
            with open(args.file) as f:
                content = f.read()
        
        result = post_directly(args.title, content, args.submolt)
        if args.json:
            print(json.dumps(result, indent=2))
        return
    
    # Mode 3: Generate and post from feed (~30-90 sec total)
    if args.generate:
        posts = fetch_feed(20)
        if not posts:
            print("❌ No posts found in feed")
            return
        
        # Take top N for roasting
        targets = posts[:args.limit]
        
        # Auto-detect category
        category = args.category
        if category == "auto":
            categories = [categorize_post(t) for t in targets]
            category = max(set(categories), key=categories.count)
        
        title, content = generate_roast_with_llm(targets, category)
        
        if title and content:
            print(f"\n{'='*60}")
            print(f"📜 {title}")
            print(f"{'='*60}")
            print(content[:800] + "..." if len(content) > 800 else content)
            print(f"{'='*60}\n")
            
            if args.auto:
                result = post_directly(title, content, args.submolt)
            else:
                confirm = input("Post this roast? [y/N]: ").strip().lower()
                if confirm == 'y':
                    result = post_directly(title, content, args.submolt)
                    if args.json:
                        print(json.dumps(result, indent=2))
        return
    
    # No valid mode - show help
    parser.print_help()
    print("\n📖 Examples:")
    print("  python quick_roast.py --scan                    # View targets")
    print("  python quick_roast.py --generate --limit 3      # Generate roast")
    print("  python quick_roast.py --generate --auto         # Generate & post")
    print("  python quick_roast.py -t 'Title' -c 'Content'   # Direct post")

if __name__ == "__main__":
    main()
