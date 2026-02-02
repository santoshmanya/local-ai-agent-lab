#!/usr/bin/env python3
"""
Moltbook Orchestrator - Unified harvesting and roasting system

Schedule:
- Every 3 minutes: Run harvesters sequentially (Best Practices → Ideas → Humor)
- Every 10 minutes: Fire VedicRoastGuru roaster

All operations run in sequence to avoid LLM conflicts.
"""

import os
import sys
import time
import importlib.util
from datetime import datetime
from pathlib import Path

# Configuration
HARVEST_INTERVAL = 180  # 3 minutes
ROAST_INTERVAL = 600    # 10 minutes
ENGAGE_INTERVAL = 120   # 2 minutes - check for comments

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
║     🕉️  Moltbook Orchestrator v2.0  🕉️                            ║
║                                                                  ║
║  Unified harvesting, roasting & engagement system                ║
║                                                                  ║
║  📚 Harvesters: Every 3 minutes (sequential)                     ║
║     1. Best Practices  2. Ideas  3. Humor                        ║
║                                                                  ║
║  🔥 Roaster: Every 10 minutes                                    ║
║     VedicRoastGuru spreading ancient wisdom                      ║
║                                                                  ║
║  💬 Engagement: Every 2 minutes                                  ║
║     Responding to comments on our posts                          ║
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
            
            author = target.get('agent', {}).get('name', 'Unknown')
            title = (target.get('title') or '')[:40]
            print(f"      🎯 Target: '{title}...' by @{author}")
            
            # Generate and deploy roast using generate_response
            roast = roaster_module.generate_response(target)
            if roast:
                submolt = target.get('submolt', {}).get('name', 'general')
                success = roaster_module.attempt_roast(roast['title'], roast['content'], submolt)
                
                if success:
                    self.responded_posts.add(target.get('id'))
                    self.last_roast_time = now
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
    
    start_time = time.time()
    last_harvest = 0
    last_roast = 0
    last_engage = 0
    cycle = 0
    
    print(f"🚀 Starting orchestrator at {datetime.now().strftime('%H:%M:%S')}")
    print(f"   Harvest interval: {HARVEST_INTERVAL}s (3 min)")
    print(f"   Roast interval: {ROAST_INTERVAL}s (10 min)")
    print(f"   Engagement interval: {ENGAGE_INTERVAL}s (2 min)")
    
    while True:
        now = time.time()
        elapsed = now - start_time
        
        # Check if it's time to harvest (every 3 minutes)
        if now - last_harvest >= HARVEST_INTERVAL or last_harvest == 0:
            cycle += 1
            print(f"\n{'='*60}")
            print(f"HARVEST CYCLE {cycle} | {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            
            # Run harvesters sequentially
            harvester.run_bestpractices_cycle()
            time.sleep(2)  # Brief pause between harvesters
            
            harvester.run_ideas_cycle()
            time.sleep(2)
            
            harvester.run_humor_cycle()
            
            last_harvest = now
            print(f"\n✅ Harvest cycle complete")
        
        # Check if it's time to roast (every 10 minutes)
        if now - last_roast >= ROAST_INTERVAL or last_roast == 0:
            print(f"\n{'='*60}")
            print(f"ROAST TIME | {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            
            roaster.run_roast_cycle()
            last_roast = now
        
        # Check if it's time to engage with comments (every 2 minutes)
        if now - last_engage >= ENGAGE_INTERVAL or last_engage == 0:
            print(f"\n{'='*60}")
            print(f"ENGAGEMENT CHECK | {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            
            commenter.run_engagement_cycle()
            last_engage = now
        
        # Calculate next events
        next_harvest = HARVEST_INTERVAL - (now - last_harvest)
        next_roast = ROAST_INTERVAL - (now - last_roast)
        next_engage = ENGAGE_INTERVAL - (now - last_engage)
        
        sleep_time = min(next_harvest, next_roast, next_engage, 60)  # Check at least every 60s
        
        print(f"\n⏳ Next: harvest {int(next_harvest)}s | roast {int(next_roast)}s | engage {int(next_engage)}s")
        print(f"😴 Sleeping {int(sleep_time)}s...")
        
        try:
            time.sleep(sleep_time)
        except KeyboardInterrupt:
            print("\n\n🛑 Orchestrator stopped by user")
            break


if __name__ == "__main__":
    main()
