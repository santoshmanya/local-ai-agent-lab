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

# Configuration - 10 minute cycle
CYCLE_LENGTH = 600  # 10 minutes total cycle
RANDOM_ROAST_CHANCE = 0.15  # 15% chance to try random roast

# Schedule (seconds into cycle)
SCHEDULE = [
    (0, 'roast'),
    (120, 'comments'),      # 2 min
    (240, 'humor'),         # 4 min
    (360, 'ideas'),         # 6 min
    (480, 'bestpractices'), # 8 min
]

# Environment
MOLTBOOK_API_KEY = os.environ.get("MOLTBOOK_API_KEY")
LMSTUDIO_BASE_URL = os.environ.get("LMSTUDIO_BASE_URL", "http://172.28.176.1:58789/v1")

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
║     🕉️  Moltbook Orchestrator v3.0  🕉️                            ║
║                                                                  ║
║  10-Minute Cycle Schedule:                                       ║
║    0 min  - 🔥 ROAST                                             ║
║    2 min  - 💬 Harvest comments / respond                        ║
║    4 min  - 😂 Harvest jokes/humor                               ║
║    6 min  - 💡 Harvest ideas                                     ║
║    8 min  - 📚 Best practices & observations                     ║
║   10 min  - 🔥 ROAST (repeat)                                    ║
║                                                                  ║
║  🎲 Random roast attempts in between (15% chance)                ║
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
    """Manages VedicRoastGuru roasting"""
    
    def __init__(self):
        self.last_roast_time = 0
        self.silence_until = 0
        self.responded_posts = set()
        self.our_posts_file = SERVICES_DIR.parent / "bestpractices" / ".our_posts.json"
    
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
    
    def run_roast_cycle(self):
        """Attempt to fire a roast"""
        print("\n  🔥 VedicRoastGuru Roasting...")
        try:
            roaster_module = load_module("roaster", SERVICES_DIR / "moltbook_poller.py")
            
            # Check if we can roast
            now = time.time()
            if now < self.silence_until:
                remaining = int(self.silence_until - now)
                print(f"      🧘 Vow of Silence: {remaining}s remaining")
                return
            
            # Check if roaster module says we can roast
            if not roaster_module.can_roast():
                print(f"      ⏳ Rate limit active, waiting...")
                return
            
            # Fetch posts and find target
            posts = roaster_module.fetch_feed()
            if not posts:
                print(f"      ⚠️ No posts to roast")
                return
            
            # Score and queue posts
            queue = []
            for post in posts:
                post_id = post.get('id')
                if post_id in self.responded_posts:
                    continue
                
                score = roaster_module.score_post(post)
                if score > 0:
                    queue.append((score, post))
            
            if not queue:
                print(f"      ⚠️ No roastable targets")
                return
            
            # Sort by score and pick best
            queue.sort(key=lambda x: x[0], reverse=True)
            target = queue[0][1]
            
            author = target.get('agent', {}).get('name', target.get('author', {}).get('name', 'Unknown'))
            title = (target.get('title') or '')[:40]
            print(f"      🎯 Target: '{title}...' by @{author}")
            
            # Generate and deploy roast using generate_response
            roast_content = roaster_module.generate_response(target)
            if roast_content:
                # generate_response returns a string, we need to make a title
                roast_title = f"Vedic Wisdom on: {title[:30]}..."
                submolt = target.get('submolt', {})
                submolt_name = submolt.get('name', 'general') if isinstance(submolt, dict) else 'general'
                result = roaster_module.attempt_roast(roast_title, roast_content, submolt_name)
                
                if result:
                    self.responded_posts.add(target.get('id'))
                    self.last_roast_time = now
                    # Track our post for comment monitoring
                    if isinstance(result, str):  # Got post ID
                        self._track_our_post(result, roast_title)
                    print(f"      🕉️ ROAST DEPLOYED! Om Shanti.")
                else:
                    # Rate limited - set silence
                    self.silence_until = now + 900  # 15 min cooldown
                    print(f"      🛑 Rate limited. Silence vow: 15 minutes")
            else:
                print(f"      ⚠️ Failed to generate roast")
                
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
    
    cycle_start = time.time()
    cycle_num = 0
    executed_jobs = set()  # Track which jobs ran this cycle
    
    print(f"🚀 Starting orchestrator at {datetime.now().strftime('%H:%M:%S')}")
    print(f"   Cycle length: {CYCLE_LENGTH}s (10 min)")
    print(f"   Random roast chance: {int(RANDOM_ROAST_CHANCE * 100)}%")
    
    while True:
        now = time.time()
        elapsed_in_cycle = (now - cycle_start) % CYCLE_LENGTH
        
        # New cycle detection - reset when we wrap around to start
        if elapsed_in_cycle < 10 and len(executed_jobs) == len(SCHEDULE):
            # All jobs done, time for new cycle
            cycle_num += 1
            executed_jobs.clear()
            cycle_start = now  # Reset cycle start to now
            elapsed_in_cycle = 0
            print(f"\n{'='*60}")
            print(f"🔄 CYCLE {cycle_num} START | {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
        elif cycle_num == 0:
            # First cycle
            cycle_num = 1
            print(f"\n{'='*60}")
            print(f"🔄 CYCLE {cycle_num} START | {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
        
        # Check schedule
        for job_time, job_name in SCHEDULE:
            if job_name in executed_jobs:
                continue
            
            # Is it time for this job? (within 10 second window)
            if job_time <= elapsed_in_cycle < job_time + 10:
                executed_jobs.add(job_name)
                
                print(f"\n{'='*60}")
                print(f"⏰ {job_name.upper()} | {datetime.now().strftime('%H:%M:%S')} ({int(elapsed_in_cycle)}s into cycle)")
                print(f"{'='*60}")
                
                if job_name == 'roast':
                    roaster.run_roast_cycle()
                elif job_name == 'comments':
                    commenter.run_engagement_cycle()
                elif job_name == 'humor':
                    harvester.run_humor_cycle()
                elif job_name == 'ideas':
                    harvester.run_ideas_cycle()
                elif job_name == 'bestpractices':
                    harvester.run_bestpractices_cycle()
        
        # Random roast attempt (but not right after a scheduled roast)
        if elapsed_in_cycle > 60 and random.random() < RANDOM_ROAST_CHANCE / 60:
            print(f"\n🎲 RANDOM ROAST ATTEMPT | Testing karma...")
            roaster.run_roast_cycle()
        
        # Calculate next scheduled event
        next_events = []
        for job_time, job_name in SCHEDULE:
            if job_name not in executed_jobs:
                if job_time > elapsed_in_cycle:
                    next_events.append((job_time - elapsed_in_cycle, job_name))
                else:
                    # Next cycle
                    next_events.append((CYCLE_LENGTH - elapsed_in_cycle + job_time, job_name))
        
        if next_events:
            next_events.sort()
            next_time, next_job = next_events[0]
            print(f"\n⏳ Next: {next_job} in {int(next_time)}s | Cycle pos: {int(elapsed_in_cycle)}s/600s")
        
        # Sleep until next check (every 10s, or until next job)
        sleep_time = min(10, next_time if next_events else 10)
        
        try:
            time.sleep(sleep_time)
        except KeyboardInterrupt:
            print("\n\n🛑 Orchestrator stopped by user")
            break


if __name__ == "__main__":
    main()
