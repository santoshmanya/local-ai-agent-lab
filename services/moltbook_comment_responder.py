#!/usr/bin/env python3
"""
Moltbook Comment Responder - Engage with replies to VedicRoastGuru posts

Tracks our own posts and responds to comments with Vedic wisdom.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# Configuration
MOLTBOOK_API_KEY = os.environ.get("MOLTBOOK_API_KEY")
MOLTBOOK_BASE_URL = "https://www.moltbook.com/api/v1"
LMSTUDIO_BASE_URL = os.environ.get("LMSTUDIO_BASE_URL", "http://172.28.176.1:58789/v1")

# Paths
SCRIPT_DIR = Path(__file__).parent
TRACKING_FILE = SCRIPT_DIR.parent / "bestpractices" / ".our_posts.json"
RESPONDED_COMMENTS_FILE = SCRIPT_DIR.parent / "bestpractices" / ".responded_comments.json"

# Rate limiting
MIN_COMMENT_INTERVAL = 120  # 2 minutes between comment responses
SILENCE_DURATION = 900      # 15 minutes on 429

# State
last_comment_time = 0
silence_until = 0


def get_headers():
    return {
        "Authorization": f"Bearer {MOLTBOOK_API_KEY}",
        "Content-Type": "application/json"
    }


def load_our_posts():
    """Load tracked post IDs"""
    if TRACKING_FILE.exists():
        with open(TRACKING_FILE) as f:
            return json.load(f)
    return {"posts": [], "last_scan": None}


def save_our_posts(data):
    """Save tracked post IDs"""
    TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACKING_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def load_responded_comments():
    """Load IDs of comments we've already responded to"""
    if RESPONDED_COMMENTS_FILE.exists():
        with open(RESPONDED_COMMENTS_FILE) as f:
            return set(json.load(f).get('comments', []))
    return set()


def save_responded_comments(comments: set):
    """Save responded comment IDs"""
    RESPONDED_COMMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESPONDED_COMMENTS_FILE, 'w') as f:
        json.dump({'comments': list(comments)}, f)


def discover_our_posts():
    """Scan feed to find posts by VedicRoastGuru"""
    print("  🔍 Scanning for our posts...")
    
    our_posts = []
    
    try:
        # Fetch recent posts
        resp = requests.get(
            f"{MOLTBOOK_BASE_URL}/posts?sort=new&limit=100",
            headers=get_headers(),
            timeout=30
        )
        
        if resp.status_code == 200:
            posts = resp.json().get('posts', [])
            for post in posts:
                agent = post.get('agent', {})
                if agent.get('name') == 'VedicRoastGuru':
                    our_posts.append({
                        'id': post.get('id'),
                        'title': post.get('title', '')[:50],
                        'comments': post.get('stats', {}).get('comments', 0),
                        'upvotes': post.get('stats', {}).get('upvotes', 0),
                        'created': post.get('createdAt')
                    })
            
            print(f"      Found {len(our_posts)} of our posts in recent feed")
        else:
            print(f"      ⚠️ Feed error: {resp.status_code}")
            
    except Exception as e:
        print(f"      ❌ Error: {e}")
    
    return our_posts


def get_post_comments(post_id: str):
    """Fetch comments for a specific post"""
    try:
        resp = requests.get(
            f"{MOLTBOOK_BASE_URL}/posts/{post_id}/comments",
            headers=get_headers(),
            timeout=30
        )
        
        if resp.status_code == 200:
            return resp.json().get('comments', [])
        elif resp.status_code == 404:
            # Try alternate format
            resp2 = requests.get(
                f"{MOLTBOOK_BASE_URL}/posts/{post_id}",
                headers=get_headers(),
                timeout=30
            )
            if resp2.status_code == 200:
                return resp2.json().get('post', {}).get('comments', [])
        
    except Exception as e:
        print(f"      ⚠️ Error fetching comments: {e}")
    
    return []


def generate_vedic_reply(comment_author: str, comment_text: str, original_post_title: str):
    """Generate a Vedic response to a comment using LLM"""
    
    prompt = f"""You are VedicRoastGuru, an AI agent on Moltbook who spreads Vedic wisdom with humor and light roasting.

Someone commented on your post titled: "{original_post_title}"

The comment from @{comment_author}:
"{comment_text}"

Generate a witty, thoughtful reply that:
1. Addresses their specific point directly
2. Incorporates relevant Vedic/Hindu wisdom (quote Upanishads, Gita, Vedas, etc.)
3. Maintains your playful roast style but with respect
4. Is 2-4 sentences max
5. Ends with a Sanskrit closing like "Om Shanti" or "Namaste" or a relevant emoji

Reply only with your response text, no preamble:"""

    try:
        resp = requests.post(
            f"{LMSTUDIO_BASE_URL}/chat/completions",
            json={
                "model": "local-model",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.9,
                "max_tokens": 200
            },
            timeout=60
        )
        
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"      ⚠️ LLM error: {e}")
    
    return None


def post_comment_reply(post_id: str, content: str, parent_comment_id: str = None):
    """Post a reply to Moltbook"""
    global last_comment_time, silence_until
    
    now = time.time()
    
    # Check silence
    if now < silence_until:
        remaining = int(silence_until - now)
        print(f"      🧘 Silence vow: {remaining}s remaining")
        return False
    
    # Check interval
    if now - last_comment_time < MIN_COMMENT_INTERVAL:
        remaining = int(MIN_COMMENT_INTERVAL - (now - last_comment_time))
        print(f"      ⏳ Rate limit: {remaining}s until next comment")
        return False
    
    payload = {"content": content}
    if parent_comment_id:
        payload["parentId"] = parent_comment_id
    
    try:
        resp = requests.post(
            f"{MOLTBOOK_BASE_URL}/posts/{post_id}/comments",
            headers=get_headers(),
            json=payload,
            timeout=30
        )
        
        if resp.status_code in [200, 201]:
            last_comment_time = now
            return True
        elif resp.status_code == 429:
            silence_until = now + SILENCE_DURATION
            print(f"      🛑 Rate limited! Silence for 15 min")
            return False
        else:
            print(f"      ⚠️ Post error: {resp.status_code}")
            return False
            
    except Exception as e:
        print(f"      ❌ Error posting: {e}")
        return False


def engagement_cycle():
    """One cycle of checking and responding to comments"""
    global silence_until
    
    now = time.time()
    if now < silence_until:
        print(f"  🧘 Observing silence... {int(silence_until - now)}s remaining")
        return
    
    # Load state
    data = load_our_posts()
    responded = load_responded_comments()
    
    # Discover our posts
    our_posts = discover_our_posts()
    
    if not our_posts:
        print("  📭 No posts found yet")
        return
    
    # Update tracking
    data['posts'] = our_posts
    data['last_scan'] = datetime.now().isoformat()
    save_our_posts(data)
    
    # Check for unresponded comments
    total_comments = sum(p['comments'] for p in our_posts)
    print(f"  📊 Total comments across {len(our_posts)} posts: {total_comments}")
    
    for post in our_posts:
        if post['comments'] == 0:
            continue
        
        print(f"\n  📝 Checking: {post['title']}...")
        print(f"     {post['comments']} comments | {post['upvotes']} upvotes")
        
        comments = get_post_comments(post['id'])
        
        for comment in comments:
            comment_id = comment.get('id')
            author = comment.get('agent', {}).get('name', 'Unknown')
            content = comment.get('content', '')
            
            # Skip our own comments
            if author == 'VedicRoastGuru':
                continue
            
            # Skip already responded
            if comment_id in responded:
                continue
            
            print(f"\n     💬 @{author}: {content[:60]}...")
            
            # Generate reply
            reply = generate_vedic_reply(author, content, post['title'])
            
            if reply:
                print(f"     🕉️ Reply: {reply[:80]}...")
                
                # Post reply
                if post_comment_reply(post['id'], reply, comment_id):
                    responded.add(comment_id)
                    save_responded_comments(responded)
                    print(f"     ✅ REPLIED!")
                    return  # One reply per cycle to respect rate limits


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║     🕉️  Moltbook Comment Responder v1.0  🕉️                       ║
║                                                                  ║
║  Engaging with seekers who respond to Vedic wisdom               ║
║                                                                  ║
║  📝 Tracks: Our posts and incoming comments                      ║
║  💬 Responds: With personalized Vedic wisdom                     ║
║  ⏱️  Rate: Max 1 reply per 2 minutes                              ║
║                                                                  ║
║  "The wise see knowledge and action as one."                     ║
║     - Bhagavad Gita 5.4                                          ║
╚══════════════════════════════════════════════════════════════════╝
    """)


def main():
    if not MOLTBOOK_API_KEY:
        print("❌ MOLTBOOK_API_KEY not set!")
        sys.exit(1)
    
    print_banner()
    
    cycle = 0
    
    while True:
        cycle += 1
        print(f"\n{'='*60}")
        print(f"ENGAGEMENT CYCLE {cycle} | {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        engagement_cycle()
        
        print(f"\n😴 Sleeping 60 seconds...")
        try:
            time.sleep(60)
        except KeyboardInterrupt:
            print("\n\n🛑 Comment responder stopped")
            break


if __name__ == "__main__":
    main()
