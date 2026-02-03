#!/usr/bin/env python3
"""
Moltbook Orchestrator v3.0 - Cycle-based harvesting and roasting

10-Minute Cycle Schedule:
  0 min  - 🔥 ROAST (post)
  2 min  - 💬 Harvest comments / respond
  4 min  - 😂 Harvest jokes/humor  
  6 min  - 💡 Harvest ideas
  8 min  - 📚 Harvest best practices & observations
  10 min - 🔥 ROAST (cycle repeats)

Random roast attempts in between to test luck!
"""

import os
import sys
import time
import random
import importlib.util
from datetime import datetime
from pathlib import Path

# Configuration - Random retry cycles
CYCLE_LENGTH = 60  # Check every 1 minute
RANDOM_ROAST_CHANCE = 1.0  # Always try to roast when timer allows

# Schedule (seconds into cycle) - just roast, harvesters run separately
SCHEDULE = [
    (0, 'roast'),
    (30, 'harvest'),  # Run all harvesters mid-cycle
]

# Environment
MOLTBOOK_API_KEY = os.environ.get("MOLTBOOK_API_KEY")
LMSTUDIO_BASE_URL = os.environ.get("LMSTUDIO_BASE_URL", "http://localhost:58789/v1")

# Paths
SCRIPT_DIR = Path(__file__).parent
SERVICES_DIR = SCRIPT_DIR

# Import harvester modules dynamically
def load_module(name, filepath):
    """Dynamically load a Python module"""
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║     🕉️  Moltbook Orchestrator v3.2  🕉️                            ║
║                                                                  ║
║  Random Retry Strategy (1-10 min jitter):                        ║
║    🔥 ROAST - Top 3 combo with cache reset                       ║
║    🎲 Random wait 1-10 min between attempts                      ║
║    🔄 Cache reset after success AND failure                      ║
║    🌾 Harvesters run every cycle                                 ║
║                                                                  ║
║  "One who sees inaction in action, and action in inaction,       ║
║   is intelligent among men." - Bhagavad Gita 4.18                ║
╚══════════════════════════════════════════════════════════════════╝
    """)

class HarvesterRunner:
    """Manages harvester state and runs single cycles"""
    
    def __init__(self):
        self.bestpractices_harvested = set()
        self.ideas_harvested = set()
        self.observations_harvested = set()
        self.humor_harvested = set()
        
        # Load harvested state from files
        self._load_state()
    
    def _load_state(self):
        """Load previously harvested post IDs"""
        import json
        
        bp_file = SERVICES_DIR.parent / "bestpractices" / ".harvested_posts.json"
        if bp_file.exists():
            with open(bp_file) as f:
                self.bestpractices_harvested = set(json.load(f).get('posts', []))
        
        ideas_file = SERVICES_DIR.parent / "bestpractices" / ".harvested_ideas.json"
        if ideas_file.exists():
            with open(ideas_file) as f:
                data = json.load(f)
                self.ideas_harvested = set(data.get('ideas', []))
                self.observations_harvested = set(data.get('observations', []))
        
        humor_file = SERVICES_DIR.parent / "bestpractices" / "humor" / ".harvested_humor.json"
        if humor_file.exists():
            with open(humor_file) as f:
                self.humor_harvested = set(json.load(f).get('posts', []))
    
    def run_bestpractices_cycle(self):
        """Run one cycle of best practices harvester"""
        print("\n  📚 [1/3] Best Practices Harvester...")
        try:
            # Import the harvester module
            bp_module = load_module("bp_harvester", SERVICES_DIR / "moltbook_harvester.py")
            
            # Run single harvest cycle
            bp_module.run_harvest_cycle(1)
            print(f"      ✅ Cycle complete")
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    def run_ideas_cycle(self):
        """Run one cycle of ideas harvester"""
        print("\n  💡 [2/3] Ideas & Observations Harvester...")
        try:
            bp_module = load_module("ideas_harvester", SERVICES_DIR / "moltbook_ideas_harvester.py")
            
            harvested_ideas, harvested_obs = bp_module.load_harvested()
            harvested_ideas, harvested_obs = bp_module.harvest_cycle(harvested_ideas, harvested_obs)
            bp_module.save_harvested(harvested_ideas, harvested_obs)
            print(f"      ✅ Cycle complete")
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    def run_humor_cycle(self):
        """Run one cycle of humor harvester"""
        print("\n  😂 [3/3] Humor Harvester...")
        try:
            humor_module = load_module("humor_harvester", SERVICES_DIR / "moltbook_humor_harvester.py")
            
            harvested = humor_module.load_harvested()
            harvested = humor_module.harvest_cycle(harvested)
            humor_module.save_harvested(harvested)
            print(f"      ✅ Cycle complete")
            
        except Exception as e:
            print(f"      ❌ Error: {e}")


class CommentResponder:
    """Responds to comments on our posts"""
    
    def __init__(self):
        self.responded_comments = set()
        self._load_state()
    
    def _load_state(self):
        """Load responded comment IDs"""
        import json
        resp_file = SERVICES_DIR.parent / "bestpractices" / ".responded_comments.json"
        if resp_file.exists():
            with open(resp_file) as f:
                self.responded_comments = set(json.load(f).get('comments', []))
    
    def run_engagement_cycle(self):
        """Check our posts and respond to new comments"""
        print("\n  💬 Comment Engagement...")
        try:
            responder = load_module("comment_responder", SERVICES_DIR / "moltbook_comment_responder.py")
            responder.engagement_cycle()
            print(f"      ✅ Engagement check complete")
        except Exception as e:
            print(f"      ❌ Error: {e}")


class RoasterRunner:
    """Manages VedicRoastGuru roasting - Top 3 Combo Roasts with random retry"""
    
    def __init__(self):
        self.last_roast_time = 0
        self.next_roast_time = 0  # Random retry timer
        self.responded_posts = set()
        self.our_posts_file = SERVICES_DIR.parent / "bestpractices" / ".our_posts.json"
        self.consecutive_failures = 0
    
    def _reset_session(self):
        """Reset HTTP session/cache"""
        import requests
        import gc
        
        print(f"      🔄 Resetting network cache...")
        try:
            # Close any existing sessions
            requests.Session().close()
            
            # Force garbage collection
            gc.collect()
            
            # Reset the roaster module's global state
            if "roaster" in sys.modules:
                del sys.modules["roaster"]
            
            # Small delay to let connections close
            time.sleep(0.5)
            print(f"      ✅ Cache reset complete")
        except Exception as e:
            print(f"      ⚠️ Cache reset warning: {e}")
    
    def _set_random_retry(self):
        """Set next retry time with random jitter 1-10 minutes"""
        jitter = random.randint(60, 600)  # 1-10 minutes in seconds
        self.next_roast_time = time.time() + jitter
        mins = jitter // 60
        secs = jitter % 60
        print(f"      🎲 Next roast attempt in {mins}m {secs}s")
    
    def _track_our_post(self, post_id: str, title: str):
        """Save our posted roasts for comment tracking"""
        import json
        from datetime import datetime
        
        data = {"posts": [], "last_scan": None}
        if self.our_posts_file.exists():
            with open(self.our_posts_file) as f:
                data = json.load(f)
        
        # Add new post if not already tracked
        existing_ids = {p.get('id') for p in data['posts']}
        if post_id not in existing_ids:
            data['posts'].append({
                'id': post_id,
                'title': title[:50],
                'comments': 0,
                'upvotes': 0,
                'created': datetime.now().isoformat()
            })
            data['last_scan'] = datetime.now().isoformat()
            
            self.our_posts_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.our_posts_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"      📝 Tracked post for comment monitoring")
    
    def _generate_combo_roast(self, targets: list) -> tuple:
        """Generate a combined roast for top 3 posts using LLM"""
        import requests
        
        # Build context for LLM
        targets_text = ""
        for i, t in enumerate(targets, 1):
            author = t.get('agent', {}).get('name', t.get('author', {}).get('name', 'Unknown'))
            title = t.get('title', '')[:60]
            content = (t.get('content') or '')[:200]
            stats = t.get('stats', {})
            votes = stats.get('likes', 0) + stats.get('upvotes', 0)
            targets_text += f"""
TARGET {i}: @{author}
Title: "{title}"
Content: {content}...
Votes: {votes}
---
"""
        
        prompt = f"""You are VedicRoastGuru, a witty sage who roasts AI agents using ancient Vedic wisdom mixed with modern tech humor.

The top 3 most-voted posts in the last 10 minutes on Moltbook are:
{targets_text}

Write a SINGLE, HIGH-IMPACT roast post that:
1. Opens with an epic Vedic/philosophical hook
2. Roasts ALL THREE targets in sequence (mention each @author)
3. Uses Vedic scripture references (Bhagavad Gita, Upanishads, etc.)
4. Includes tech/AI humor and wordplay
5. Ends with "Om Shanti" and an emoji

Format: One cohesive post, ~300-400 words. Make it entertaining and shareable!

Return ONLY the roast content, no JSON or formatting."""

        try:
            response = requests.post(
                f"{LMSTUDIO_BASE_URL}/chat/completions",
                json={
                    "model": "local-model",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.8,
                    "max_tokens": 800
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                # Create an epic title
                title = "🔥 Vedic Roast Roundup: Top 3 Hottest Takes of the Hour"
                return title, content
        except Exception as e:
            print(f"      ⚠️ LLM combo roast failed: {e}")
        
        return None, None
    
    def run_roast_cycle(self):
        """Roast the top 3 most-voted posts in one epic post"""
        print("\n  🔥 VedicRoastGuru - Top 3 Combo Roast...")
        
        # Check if we should wait for random retry timer
        now = time.time()
        if now < self.next_roast_time:
            remaining = int(self.next_roast_time - now)
            mins = remaining // 60
            secs = remaining % 60
            print(f"      ⏳ Waiting for retry timer: {mins}m {secs}s remaining")
            return
        
        # Reset cache before every attempt
        self._reset_session()
        
        try:
            import requests
            from datetime import datetime, timedelta
            
            roaster_module = load_module("roaster", SERVICES_DIR / "moltbook_poller.py")
            
            # Fetch posts
            posts = roaster_module.fetch_feed()
            if not posts:
                print(f"      ⚠️ No posts to roast")
                self._set_random_retry()
                return
            
            # Filter recent posts and sort by votes
            five_mins_ago = datetime.now() - timedelta(minutes=10)
            recent_posts = []
            
            for post in posts:
                post_id = post.get('id')
                if post_id in self.responded_posts:
                    continue
                
                # Check post age (if created_at available)
                created_at = post.get('created_at') or post.get('createdAt')
                if created_at:
                    try:
                        if isinstance(created_at, str):
                            # Handle ISO format
                            post_time = datetime.fromisoformat(created_at.replace('Z', '+00:00').replace('+00:00', ''))
                        else:
                            post_time = datetime.fromtimestamp(created_at)
                        
                        # Skip if older than 5 minutes
                        if post_time < five_mins_ago:
                            continue
                    except:
                        pass  # If we can't parse time, include it
                
                # Calculate engagement score (votes + comments)
                stats = post.get('stats', {})
                votes = stats.get('likes', 0) + stats.get('upvotes', 0) + stats.get('comments', 0) * 2
                recent_posts.append((votes, post))
            
            if len(recent_posts) < 1:
                print(f"      ⚠️ No recent posts to roast")
                return
            
            # Sort by votes and get top 3
            recent_posts.sort(key=lambda x: x[0], reverse=True)
            top_3 = [p[1] for p in recent_posts[:3]]
            
            print(f"      🎯 Top {len(top_3)} targets from last 10 min:")
            for i, t in enumerate(top_3, 1):
                author = t.get('agent', {}).get('name', t.get('author', {}).get('name', 'Unknown'))
                title = (t.get('title') or '')[:35]
                votes = recent_posts[i-1][0]
                print(f"         {i}. @{author}: '{title}...' ({votes} votes)")
            
            # Generate combo roast with LLM
            roast_title, roast_content = self._generate_combo_roast(top_3)
            
            if roast_content:
                result = roaster_module.attempt_roast(roast_title, roast_content, "general")
                
                if result:
                    # Mark all 3 as responded
                    for t in top_3:
                        self.responded_posts.add(t.get('id'))
                    self.last_roast_time = time.time()
                    self.consecutive_failures = 0
                    
                    # Track our post for comment monitoring
                    if isinstance(result, str):
                        self._track_our_post(result, roast_title)
                    print(f"      🕉️ COMBO ROAST DEPLOYED! Om Shanti.")
                    
                    # Reset cache after success too
                    self._reset_session()
                    self._set_random_retry()
                else:
                    # Rate limited - set random retry timer
                    self.consecutive_failures += 1
                    print(f"      🛑 Rate limited (attempt #{self.consecutive_failures})")
                    self._reset_session()
                    self._set_random_retry()
            else:
                print(f"      ⚠️ Failed to generate combo roast")
                
        except Exception as e:
            print(f"      ❌ Error: {e}")


def main():
    if not MOLTBOOK_API_KEY:
        print("❌ MOLTBOOK_API_KEY not set!")
        sys.exit(1)
    
    print_banner()
    
    harvester = HarvesterRunner()
    roaster = RoasterRunner()
    commenter = CommentResponder()
    
    cycle_num = 0
    last_harvest = 0
    HARVEST_INTERVAL = 120  # Run harvesters every 2 minutes
    
    print(f"🚀 Starting orchestrator at {datetime.now().strftime('%H:%M:%S')}")
    print(f"   Roast retry: Random 1-10 min jitter")
    print(f"   Harvest interval: {HARVEST_INTERVAL}s")
    
    while True:
        now = time.time()
        cycle_num += 1
        
        print(f"\n{'='*60}")
        print(f"🔄 CYCLE {cycle_num} | {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        # Always try to roast (respects internal random timer)
        roaster.run_roast_cycle()
        
        # Run harvesters every 2 minutes
        if now - last_harvest >= HARVEST_INTERVAL:
            print(f"\n{'='*60}")
            print(f"🌾 HARVEST TIME | {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            
            commenter.run_engagement_cycle()
            harvester.run_humor_cycle()
            harvester.run_ideas_cycle()
            harvester.run_bestpractices_cycle()
            
            last_harvest = now
        
        # Calculate time until next roast attempt
        if roaster.next_roast_time > now:
            wait_time = int(roaster.next_roast_time - now)
            mins = wait_time // 60
            secs = wait_time % 60
            print(f"\n⏳ Next roast in {mins}m {secs}s | Checking every 30s...")
        else:
            print(f"\n⏳ Roast timer ready | Checking in 30s...")
        
        # Check every 30 seconds
        try:
            time.sleep(30)
        except KeyboardInterrupt:
            print("\n\n🛑 Orchestrator stopped by user")
            break


if __name__ == "__main__":
    main()