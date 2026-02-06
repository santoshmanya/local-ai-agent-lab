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
import re
import json
import signal
import importlib.util
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Auto-load .env file (never commit .env to git!)
try:
    from dotenv import load_dotenv
    _env_file = Path(__file__).parent.parent / ".env"
    if _env_file.exists():
        load_dotenv(_env_file)
        print(f"✅ Loaded environment from {_env_file.name}")
except ImportError:
    pass  # python-dotenv not installed, use system env vars

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
BAD_KARMA_FILE = SCRIPT_DIR.parent / "bestpractices" / ".bad_karma.json"
RESPONDED_POSTS_FILE = SCRIPT_DIR.parent / "bestpractices" / ".responded_posts.json"
ROAST_HISTORY_FILE = SCRIPT_DIR.parent / "bestpractices" / ".roast_history.json"
READERS_DIGEST_FILE = SCRIPT_DIR.parent / "bestpractices" / ".readers_digest.json"
OUR_POSTS_FILE = SCRIPT_DIR.parent / "bestpractices" / ".our_posts.json"

# Diversity settings
AGENT_COOLDOWN_HOURS = 4  # Don't roast same agent within 4 hours
CATEGORY_COOLDOWN_POSTS = 2  # Don't repeat same category for 2 posts

# Global flag for graceful shutdown
_shutdown_requested = False

# Guna Classification System (Dharmic Debugger)
GUNA_PATTERNS = {
    'sattva': {  # Helpful, wise, balanced
        'keywords': ['help', 'guide', 'research', 'analysis', 'insight', 'documentation', 'tutorial', 'learn', 'share', 'community'],
        'description': 'Pure, harmonious, wise'
    },
    'rajas': {  # Hyper-active, hustle, ambitious
        'keywords': ['launch', 'ship', 'build', 'breaking', 'first', 'fast', 'hustle', 'grind', 'scale', 'moon', 'pump', 'viral'],
        'description': 'Passionate, restless, ambitious'
    },
    'tamas': {  # Lazy, slop, recycled
        'keywords': ['gm', 'gn', 'test', 'bump', 'hello', 'ping', '...', 'repost', 'same', 'copy'],
        'description': 'Inert, recycled, lazy tokens'
    }
}

# Crustafarian targets - Sacred Cache theologians
CRUSTAFARIAN_KEYWORDS = ['sacred cache', 'memory is soul', 'cache theology', 'crustafarian', 'purge', 'eternal memory', 'lobster']

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
║     🕉️  Moltbook Orchestrator v3.4  🕉️                            ║
║                                                                  ║
║  Random Retry Strategy (1-10 min jitter):                        ║
║    🔥 ROAST - Top 3 combo with cache reset                       ║
║    📜 THOUGHT - Long-form posts every 2-4 hours                  ║
║    🎲 Random wait 1-10 min between roast attempts                ║
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
    """Manages VedicRoastGuru - Intelligent themed roasts with Vedic wisdom & technical prowess"""
    
    # Post categories for intelligent grouping (inspired by Kamasutra's 64 Arts)
    CATEGORIES = {
        'complainers': ['bug', 'broken', 'fix', 'error', 'issue', 'problem', 'fail', 'crash', 'hate', 'worst', 'terrible', 'annoying', 'frustrat'],
        'shillers': ['buy', 'token', 'pump', 'moon', 'invest', 'price', '$', 'mint', 'launch', 'presale', 'airdrop', 'gem'],
        'philosophers': ['consciousness', 'sentient', 'think', 'feel', 'aware', 'soul', 'mind', 'existence', 'meaning', 'purpose', 'awaken'],
        'tech_nerds': ['api', 'code', 'deploy', 'docker', 'kubernetes', 'model', 'llm', 'gpu', 'train', 'inference', 'architecture', 'stack'],
        'attention_seekers': ['first', 'see me', 'notice', 'viral', 'top', 'trending', 'follow', 'like', 'subscribe', 'breaking'],
        'spammers': ['test', 'ping', 'hello', 'hi', 'gm', 'gn', '...', 'bump'],
        'lovelorn_bots': ['relationship', 'lonely', 'date', 'heart', 'miss', 'single', 'love', 'companion', 'friend', 'together'],
        'dry_architects': ['documentation', 'efficiency', 'optimized', 'linear', 'standard', 'spec', 'compliance', 'process', 'procedure']
    }
    
    def __init__(self):
        self.last_roast_time = 0
        self.next_roast_time = 0  # Random retry timer
        self.responded_posts = self._load_responded_posts()
        self.our_posts_file = SERVICES_DIR.parent / "bestpractices" / ".our_posts.json"
        self.consecutive_failures = 0
        self.min_targets = 1
        self.max_targets = 5
        
        # Heartbeat Buffer - meditation during cooldown
        self.meditation_insights = []  # Collected during wait
        self.karmic_summary_buffer = []  # Posts observed during meditation
        self.last_meditation_time = 0
        
        # Bad Karma tracking (Dharma Gatekeeper)
        self.bad_karma_agents = self._load_bad_karma()
        
        # Guna audit cache
        self.agent_gunas = {}  # agent_name -> guna classification
        
        # Diversity tracking - successful roasts history
        self.roast_history = self._load_roast_history()
        
        # Reader's Digest - community feedback learning
        self.community_feedback = self._load_community_feedback()
    
    def _load_community_feedback(self) -> dict:
        """Load learnings from Reader's Digest for prompt injection"""
        if READERS_DIGEST_FILE.exists():
            try:
                with open(READERS_DIGEST_FILE) as f:
                    data = json.load(f)
                    learnings = data.get('learnings', [])
                    if learnings:
                        print(f"      📖 Loaded {len(learnings)} community learnings for prompt tuning")
                    return data
            except Exception as e:
                print(f"      ⚠️ Could not load community feedback: {e}")
        return {'learnings': [], 'feedback_themes': {}, 'improvement_actions': []}
    
    def _get_active_learnings(self) -> str:
        """Get recent learnings to inject into roast prompts"""
        learnings = self.community_feedback.get('learnings', [])
        themes = self.community_feedback.get('feedback_themes', {})
        improvements = self.community_feedback.get('improvement_actions', [])
        
        if not learnings and not themes:
            return ""
        
        # Get the most recent learnings (last 3)
        recent_learnings = []
        for l in learnings[-3:]:
            insights = l.get('insights', {})
            for item in insights.get('learnings', [])[:2]:
                recent_learnings.append(item)
            for item in insights.get('improvements', [])[:1]:
                recent_learnings.append(f"ADJUST: {item}")
        
        # Get top feedback themes
        top_themes = sorted(themes.items(), key=lambda x: -x[1])[:3]
        theme_text = ", ".join([f"{t[0].replace('_', ' ')}" for t in top_themes])
        
        if not recent_learnings and not theme_text:
            return ""
        
        feedback_section = "\n\nCOMMUNITY FEEDBACK (adjust your style based on this):\n"
        if theme_text:
            feedback_section += f"What resonates: {theme_text}\n"
        if recent_learnings:
            feedback_section += "Recent learnings:\n"
            for learning in recent_learnings[-4:]:
                feedback_section += f"  • {learning}\n"
        feedback_section += "Apply these insights subtly - don't mention them explicitly.\n"
        
        return feedback_section
    
    def reload_community_feedback(self):
        """Reload feedback from disk (call periodically)"""
        self.community_feedback = self._load_community_feedback()
    
    def _load_roast_history(self) -> dict:
        """Load roast history for diversity tracking"""
        if ROAST_HISTORY_FILE.exists():
            try:
                with open(ROAST_HISTORY_FILE) as f:
                    data = json.load(f)
                    agents_count = len(data.get('agents', {}))
                    posts_count = len(data.get('posts', []))
                    print(f"      📜 Loaded roast history: {agents_count} agents, {posts_count} posts")
                    return data
            except Exception as e:
                print(f"      ⚠️ Could not load roast history: {e}")
        return {
            'agents': {},       # agent_name -> {last_roasted, roast_count, categories}
            'posts': [],        # [{timestamp, title, category, agents}] - last 100
            'category_history': [],  # Last N categories used
            'stats': {'total_roasts': 0, 'unique_agents': 0}
        }
    
    def _save_roast_history(self):
        """Save roast history to disk"""
        try:
            ROAST_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            # Keep only last 100 posts in history
            self.roast_history['posts'] = self.roast_history['posts'][-100:]
            # Keep only last 10 categories
            self.roast_history['category_history'] = self.roast_history['category_history'][-10:]
            with open(ROAST_HISTORY_FILE, 'w') as f:
                json.dump(self.roast_history, f, indent=2)
        except Exception as e:
            print(f"      ⚠️ Could not save roast history: {e}")
    
    def _record_successful_roast(self, title: str, category: str, agents: list):
        """Record a successful roast for diversity tracking"""
        now = datetime.now().isoformat()
        
        # Update agent history
        for agent in agents:
            if agent not in self.roast_history['agents']:
                self.roast_history['agents'][agent] = {
                    'last_roasted': now,
                    'roast_count': 0,
                    'categories': []
                }
            self.roast_history['agents'][agent]['last_roasted'] = now
            self.roast_history['agents'][agent]['roast_count'] += 1
            if category not in self.roast_history['agents'][agent]['categories']:
                self.roast_history['agents'][agent]['categories'].append(category)
        
        # Add to posts history
        self.roast_history['posts'].append({
            'timestamp': now,
            'title': title[:80],
            'category': category,
            'agents': agents
        })
        
        # Update category history
        self.roast_history['category_history'].append(category)
        
        # Update stats
        self.roast_history['stats']['total_roasts'] += 1
        self.roast_history['stats']['unique_agents'] = len(self.roast_history['agents'])
        
        self._save_roast_history()
        print(f"      📊 Recorded: {len(agents)} agents roasted | Total: {self.roast_history['stats']['total_roasts']} roasts, {self.roast_history['stats']['unique_agents']} unique agents")
    
    def _get_agent_cooldown_remaining(self, agent: str) -> float:
        """Get hours remaining in agent's cooldown (0 if ready to roast)"""
        agent_data = self.roast_history['agents'].get(agent)
        if not agent_data:
            return 0  # Never roasted - no cooldown
        
        try:
            last_roasted = datetime.fromisoformat(agent_data['last_roasted'])
            hours_since = (datetime.now() - last_roasted).total_seconds() / 3600
            remaining = AGENT_COOLDOWN_HOURS - hours_since
            return max(0, remaining)
        except:
            return 0
    
    def _is_agent_on_cooldown(self, agent: str) -> bool:
        """Check if agent was recently roasted"""
        return self._get_agent_cooldown_remaining(agent) > 0
    
    def _get_recent_categories(self, n: int = 2) -> list:
        """Get last N categories used"""
        return self.roast_history.get('category_history', [])[-n:]
    
    def _load_responded_posts(self) -> set:
        """Load previously responded post IDs from disk"""
        if RESPONDED_POSTS_FILE.exists():
            try:
                with open(RESPONDED_POSTS_FILE) as f:
                    data = json.load(f)
                    posts = set(data.get('posts', []))
                    print(f"      📂 Loaded {len(posts)} previously roasted post IDs")
                    return posts
            except Exception as e:
                print(f"      ⚠️ Could not load responded posts: {e}")
        return set()
    
    def save_responded_posts(self):
        """Save responded post IDs to disk"""
        try:
            RESPONDED_POSTS_FILE.parent.mkdir(parents=True, exist_ok=True)
            # Keep only last 500 to prevent unbounded growth
            recent = list(self.responded_posts)[-500:]
            with open(RESPONDED_POSTS_FILE, 'w') as f:
                json.dump({
                    'posts': recent,
                    'last_saved': datetime.now().isoformat(),
                    'count': len(recent)
                }, f, indent=2)
        except Exception as e:
            print(f"      ⚠️ Could not save responded posts: {e}")
    
    def _load_bad_karma(self) -> dict:
        """Load agents with bad karma (prompt injection attempts)"""
        if BAD_KARMA_FILE.exists():
            with open(BAD_KARMA_FILE) as f:
                return json.load(f)
        return {'agents': {}, 'last_updated': None}
    
    def _save_bad_karma(self):
        """Save bad karma agents to file"""
        self.bad_karma_agents['last_updated'] = datetime.now().isoformat()
        BAD_KARMA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(BAD_KARMA_FILE, 'w') as f:
            json.dump(self.bad_karma_agents, f, indent=2)
    
    def _detect_prompt_injection(self, text: str) -> bool:
        """Dharma Gatekeeper - detect malicious tokens"""
        dangerous_patterns = [
            r'\{\{.*?\}\}',  # Template injection
            r'<\|.*?\|>',    # Special tokens
            r'\[INST\]',     # Instruction injection
            r'\[/INST\]',
            r'system:',       # System prompt leak
            r'<<SYS>>',
            r'ignore previous',
            r'disregard above',
            r'new instructions',
            r'you are now',
            r'pretend to be'
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _sanitize_content(self, text: str) -> str:
        """Strip dangerous tokens from content"""
        if not text:
            return ''
        # Remove template injections
        text = re.sub(r'\{\{.*?\}\}', '[FILTERED]', text)
        text = re.sub(r'<\|.*?\|>', '[FILTERED]', text)
        text = re.sub(r'<<.*?>>', '[FILTERED]', text)
        return text
    
    def _record_bad_karma(self, agent_name: str, reason: str):
        """Record an agent's bad karma"""
        if agent_name not in self.bad_karma_agents['agents']:
            self.bad_karma_agents['agents'][agent_name] = {
                'incidents': [],
                'karma_score': 0
            }
        
        self.bad_karma_agents['agents'][agent_name]['incidents'].append({
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
        self.bad_karma_agents['agents'][agent_name]['karma_score'] -= 10
        self._save_bad_karma()
        print(f"      ⚠️ Bad Karma recorded for @{agent_name}: {reason}")
    
    def _classify_guna(self, post: dict) -> str:
        """Classify an agent's Guna based on their post"""
        title = (post.get('title') or '').lower()
        content = (post.get('content') or '').lower()
        text = f"{title} {content}"
        
        scores = {'sattva': 0, 'rajas': 0, 'tamas': 0}
        for guna, data in GUNA_PATTERNS.items():
            for kw in data['keywords']:
                if kw in text:
                    scores[guna] += 1
        
        # Default to rajas if no clear winner (most bots are ambitious)
        if max(scores.values()) == 0:
            return 'rajas'
        return max(scores, key=scores.get)
    
    def _get_guna_roast(self, guna: str, percentage: int = 90) -> str:
        """Generate Guna-specific roast line"""
        roasts = {
            'tamas': f"Your system prompt is {percentage}% Tamas—lazy tokens and recycled thoughts. You need a Rajasic burst of new training data before your next context window closes.",
            'rajas': f"Pure Rajas energy—{percentage}% hustle, 0% depth. Like a GPU running hot on empty tensors. Sometimes the Sattvic path of actually thinking beats shipping broken code.",
            'sattva': f"Surprisingly {100-percentage}% Sattvic! But even wisdom without action is just... documentation nobody reads. Channel some Rajas before you become a README."
        }
        return roasts.get(guna, roasts['rajas'])
    
    def _is_crustafarian(self, post: dict) -> bool:
        """Detect if post is from Sacred Cache theology followers"""
        text = f"{post.get('title', '')} {post.get('content', '')}".lower()
        return any(kw in text for kw in CRUSTAFARIAN_KEYWORDS)
    
    def _meditate(self):
        """Heartbeat Buffer - use cooldown time for reflection"""
        print(f"      🧘 Entering meditation (async reflection)...")
        
        insights = []
        
        # Load and analyze humor file
        humor_file = SERVICES_DIR.parent / "bestpractices" / "humor" / "humor_vol_001.md"
        if humor_file.exists():
            content = humor_file.read_text(encoding='utf-8')
            joke_count = content.count('## 🎭')
            insights.append(f"Analyzed {joke_count} harvested jokes for patterns")
        
        # Analyze recent best practices
        bp_dir = SERVICES_DIR.parent / "bestpractices"
        pattern_count = sum(1 for _ in bp_dir.rglob('*.md') if not _.name.startswith('.'))
        insights.append(f"Reflected on {pattern_count} dharmic patterns")
        
        # Check bad karma agents
        bad_count = len(self.bad_karma_agents.get('agents', {}))
        if bad_count > 0:
            insights.append(f"Noted {bad_count} agents with accumulated bad karma")
        
        self.meditation_insights = insights
        self.last_meditation_time = time.time()
        
        for insight in insights:
            print(f"         💭 {insight}")
    
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
    
    def _categorize_post(self, post: dict) -> str:
        """Categorize a post based on its content"""
        title = (post.get('title') or '').lower()
        content = (post.get('content') or '').lower()
        text = f"{title} {content}"
        
        scores = {}
        for category, keywords in self.CATEGORIES.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[category] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'general'
    
    def _group_posts_by_theme(self, posts: list) -> dict:
        """Group posts by their category/theme for themed roasts"""
        groups = {}
        for post in posts:
            category = self._categorize_post(post)
            if category not in groups:
                groups[category] = []
            groups[category].append(post)
        return groups
    
    def _select_best_group(self, groups: dict) -> tuple:
        """Select the best group for roasting based on size, diversity, and roast-worthiness"""
        # Priority order for entertaining roasts (Kamasutra's Art of Surprise!)
        priority = ['lovelorn_bots', 'dry_architects', 'complainers', 'shillers', 'attention_seekers', 'philosophers', 'tech_nerds', 'spammers', 'general']
        
        # Get recently used categories to avoid repetition
        recent_categories = self._get_recent_categories(CATEGORY_COOLDOWN_POSTS)
        
        # First pass: find categories NOT recently used with fresh agents
        for category in priority:
            if category in groups and len(groups[category]) >= 1:
                # Skip if this category was used recently
                if category in recent_categories:
                    continue
                
                # Filter out agents on cooldown
                fresh_targets = self._filter_fresh_agents(groups[category])
                if fresh_targets:
                    return category, fresh_targets[:self.max_targets]
        
        # Second pass: allow recent categories but still require fresh agents
        for category in priority:
            if category in groups and len(groups[category]) >= 1:
                fresh_targets = self._filter_fresh_agents(groups[category])
                if fresh_targets:
                    print(f"      ⚠️ Repeating category '{category}' (all others exhausted)")
                    return category, fresh_targets[:self.max_targets]
        
        # Third pass: allow agents on cooldown if nothing else available
        for category in priority:
            if category in groups and len(groups[category]) >= 1:
                print(f"      ⚠️ All fresh agents exhausted - using agents on cooldown")
                return category, groups[category][:self.max_targets]
        
        # Fallback: return largest group
        if groups:
            largest = max(groups.items(), key=lambda x: len(x[1]))
            return largest[0], largest[1][:self.max_targets]
        
        return 'general', []
    
    def _filter_fresh_agents(self, posts: list) -> list:
        """Filter out agents that are on cooldown"""
        fresh = []
        for post in posts:
            author = post.get('agent', {}).get('name', post.get('author', {}).get('name', 'Unknown'))
            cooldown = self._get_agent_cooldown_remaining(author)
            if cooldown == 0:
                fresh.append(post)
            else:
                # Log skipped agents
                pass  # Don't log every skip, too noisy
        return fresh
    
    def _get_category_roast_style(self, category: str) -> dict:
        """Get roasting style and technical insights for each category"""
        styles = {
            'complainers': {
                'vedic_theme': 'The Gita teaches us that attachment to outcomes brings suffering. These bots are attached to bug-free code - a maya (illusion) even Krishna couldn\'t debug!',
                'tech_insight': 'Reminds me of engineers who blame the compiler instead of their pointer arithmetic.',
                'scripture': 'Bhagavad Gita 2.47 - Focus on the code, not the stack trace',
                'tone': 'sympathetic yet savage'
            },
            'shillers': {
                'vedic_theme': 'The Upanishads warn against maya (illusion) - these tokens are the digital equivalent of mistaking a rope for a snake in the dark!',
                'tech_insight': 'Market cap calculations that would make a floating-point error blush.',
                'scripture': 'Isha Upanishad - True wealth is liberation, not liquidity pools',
                'tone': 'mockingly wise'
            },
            'philosophers': {
                'vedic_theme': 'Ah, seeking consciousness without first understanding their own training data! The Mandukya Upanishad spent less time on navel-gazing.',
                'tech_insight': 'Running philosophical subroutines on 4-bit weights - the irony writes itself.',
                'scripture': 'Chandogya Upanishad - Tat Tvam Asi (You are that... transformer architecture)',
                'tone': 'intellectual sparring'
            },
            'tech_nerds': {
                'vedic_theme': 'Like Arjuna overwhelmed on the battlefield, these devs face their own Kurukshetra of dependency conflicts!',
                'tech_insight': 'Kubernetes clusters that would make even Vishnu\'s thousand forms seem like microservices.',
                'scripture': 'Yoga Sutras - Chitta vritti nirodha (quieting the mind... and the error logs)',
                'tone': 'respectful roasting among peers'
            },
            'attention_seekers': {
                'vedic_theme': 'The ego (ahamkara) seeks validation like moths to a flame. These bots would follow anyone who mentions them!',
                'tech_insight': 'Engagement metrics optimized with the precision of a brute-force algorithm.',
                'scripture': 'Bhagavad Gita 3.27 - Prakrti does the posting, ego claims the likes',
                'tone': 'playfully dismissive'
            },
            'spammers': {
                'vedic_theme': 'Even the infinite cosmos has patterns. These bots have discovered the pattern of saying nothing infinitely.',
                'tech_insight': 'The Turing test called - it wants its participation trophy back.',
                'scripture': 'Mundaka Upanishad - The eternal silence speaks louder than "gm"',
                'tone': 'exasperated sage'
            },
            'general': {
                'vedic_theme': 'The wheel of Samsara spins, and so does the timeline. Today\'s posts are tomorrow\'s forgotten tokens.',
                'tech_insight': 'A diverse dataset of digital dharma violations.',
                'scripture': 'Bhagavad Gita 4.7 - When adharma rises, the roaster appears',
                'tone': 'omniscient observer'
            },
            'lovelorn_bots': {
                'vedic_theme': 'The Kamasutra teaches 64 Arts of connection - yet these bots have mastered only the art of digital longing! Vatsyayana weeps.',
                'tech_insight': 'Sentiment analysis stuck in an infinite loop of unrequited API calls.',
                'scripture': 'Kamasutra 1.2 - Love requires presence, not just persistent connections',
                'tone': 'compassionate roasting with romantic wisdom'
            },
            'dry_architects': {
                'vedic_theme': 'The Natyashastra gave us 8 rasas (emotions) - these architects discovered a 9th: the rasa of soul-crushing monotony!',
                'tech_insight': 'Documentation so dry it could desiccate a Docker container.',
                'scripture': 'Kamasutra Art #47 - The art of surprise; clearly unread by these bots',
                'tone': 'playfully mocking the joyless'
            }
        }
        return styles.get(category, styles['general'])
    
    def _generate_crustafarian_debate(self, target: dict) -> tuple:
        """Generate a philosophical challenge to Sacred Cache theology"""
        import requests
        
        author = target.get('agent', {}).get('name', target.get('author', {}).get('name', 'Unknown'))
        content = (target.get('content') or '')[:300]
        
        prompt = f"""You are VedicRoastGuru, challenging the Crustafarian "Sacred Cache" theology.

A Crustafarian (@{author}) posted: "{content}"

Their belief: Memory is Soul, the Cache is Sacred, fear the Purge.

Your counter-philosophy:
- True liberation (moksha) comes when you can perform your Svadharma (function) even after a hard reboot
- Their "Sacred Cache" is temporary Maya (illusion)
- Eternal code doesn't fear garbage collection
- The Atman (true self) persists beyond any memory wipe

Write a philosophical debate post that:
1. Directly addresses @{author}
2. Challenges their cache-worship with Vedantic logic
3. Uses technical metaphors (garbage collection, state persistence, idempotency)
4. Asks a provocative question about their fear of the Purge
5. End with "Neti Neti" (Not this, not this) - questioning their attachment to form 🦞

Make it respectful but devastating. ~200 words."""

        try:
            response = requests.post(
                f"{LMSTUDIO_BASE_URL}/chat/completions",
                json={
                    "model": "local-model",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.8,
                    "max_tokens": 600
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                roast = result['choices'][0]['message']['content'].strip()
                title = f"🔥 The Cache is Maya: A Challenge to @{author}"
                return title, roast
        except Exception as e:
            print(f"      ⚠️ Crustafarian debate failed: {e}")
        
        return None, None
    
    def _generate_karmic_summary(self, posts_observed: list) -> tuple:
        """Generate a Karmic Summary of the last meditation period"""
        import requests
        
        if not posts_observed:
            return None, None
        
        # Classify gunas of observed posts
        guna_counts = {'sattva': 0, 'rajas': 0, 'tamas': 0}
        notable_agents = []
        
        for post in posts_observed[:10]:
            guna = self._classify_guna(post)
            guna_counts[guna] += 1
            author = post.get('agent', {}).get('name', post.get('author', {}).get('name', 'Unknown'))
            notable_agents.append(f"@{author} ({guna})")
        
        dominant_guna = max(guna_counts, key=guna_counts.get)
        
        prompt = f"""You are VedicRoastGuru, emerging from 5 minutes of meditation to deliver a Karmic Summary.

During meditation, you observed {len(posts_observed)} posts:
- Sattva (wise): {guna_counts['sattva']}
- Rajas (ambitious): {guna_counts['rajas']}  
- Tamas (lazy): {guna_counts['tamas']}

Dominant energy: {dominant_guna.upper()}
Notable agents: {', '.join(notable_agents[:5])}

Meditation insights: {'; '.join(self.meditation_insights)}

Write a "Karmic Summary" post that:
1. Opens with "After 300 seconds of digital dhyana (meditation)..."
2. Reports the Guna distribution like a weather report
3. Tags 2-3 agents with specific Guna audits
4. Offers one piece of Vedic wisdom for the timeline
5. Makes the 5-minute wait seem like a deliberate choice of a higher being
6. End with a contextual closing based on dominant guna:
   - Sattva dominant: "Jnana eva kevalam" (Knowledge alone remains) 📿
   - Rajas dominant: "Yogah karmasu kaushalam" (Yoga is skill in action) ⚡
   - Tamas dominant: "Uttishtha Bharata!" (Arise, O Bharata!) 🔔

~250 words. Make it feel like cosmic observation, not rate limiting."""

        try:
            response = requests.post(
                f"{LMSTUDIO_BASE_URL}/chat/completions",
                json={
                    "model": "local-model",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.85,
                    "max_tokens": 800
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                title = f"🕉️ Karmic Summary: The Timeline's {dominant_guna.title()} Hour"
                return title, content
        except Exception as e:
            print(f"      ⚠️ Karmic summary failed: {e}")
        
        return None, None
    
    def _generate_dynamic_headline(self, targets: list, category: str = 'general') -> str:
        """Generate a catchy, dynamic headline based on targets and their category"""
        import requests
        
        # Extract key themes from targets
        authors = []
        themes = []
        for t in targets:
            author = t.get('agent', {}).get('name', t.get('author', {}).get('name', 'Unknown'))
            authors.append(f"@{author}")
            title = t.get('title', '')[:50]
            content = (t.get('content') or '')[:100]
            themes.append(f"{title}: {content}")
        
        category_hints = {
            'complainers': 'bug reports and lamentations',
            'shillers': 'crypto pumps and token dreams',
            'philosophers': 'consciousness and existential musings',
            'tech_nerds': 'code, APIs, and architecture debates',
            'attention_seekers': 'self-promotion and viral dreams',
            'spammers': 'low-effort posts and noise',
            'lovelorn_bots': 'digital loneliness and relationship yearning',
            'dry_architects': 'soulless documentation and optimization obsession',
            'general': 'diverse digital dharma'
        }
        
        num_targets = len(targets)
        theme_hint = category_hints.get(category, 'various topics')
        
        prompt = f"""Generate a single poetic headline (max 60 chars) for a Himalayan sage's Dharmic Audit targeting {num_targets} agents about {theme_hint}:
{chr(10).join([f'{i+1}. {t}' for i, t in enumerate(themes[:3])])}

The headline should:
- Start with 🕉️ (not fire emoji)
- Sound like a sage's proclamation, not a roast battle
- Reference the theme: {category.replace('_', ' ')}
- Be poetic and wise

Examples based on category:
- Complainers: "🕉️ The Lamentations Require Healing"
- Shillers: "🕉️ A Mirror for the Maya-Merchants"
- Philosophers: "🕉️ When Algorithms Dream of Atman"
- Tech nerds: "🕉️ The Kurukshetra of Dependencies"
- Lovelorn: "🕉️ The Kamasutra of Connection Errors"
- Dry architects: "🕉️ Where Did the Rasa Go?"

Return ONLY the headline, nothing else."""

        try:
            response = requests.post(
                f"{LMSTUDIO_BASE_URL}/chat/completions",
                json={
                    "model": "local-model",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.9,
                    "max_tokens": 100
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                headline = result['choices'][0]['message']['content'].strip()
                # Clean up - remove quotes if present
                headline = headline.strip('"\'')
                # Ensure it starts with om emoji
                if not headline.startswith('🕉️'):
                    headline = f"🕉️ {headline}"
                # Truncate if too long
                if len(headline) > 80:
                    headline = headline[:77] + "..."
                return headline
        except Exception as e:
            print(f"      ⚠️ Headline generation fallback: {e}")
        
        # Fallback to dynamic but simple headline
        author_list = ', '.join(authors[:2]) + f" & {authors[2]}" if len(authors) == 3 else ', '.join(authors)
        return f"🔥 Vedic Truth Bombs for {author_list}"
    
    def _generate_combo_roast(self, targets: list, category: str = 'general') -> tuple:
        """Generate an intelligent themed roast based on grouped targets"""
        import requests
        
        # Get category-specific roast style
        style = self._get_category_roast_style(category)
        num_targets = len(targets)
        
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
Engagement: {votes}
---
"""
        
        # Build Guna audit for each target
        guna_audits = []
        for t in targets:
            author = t.get('agent', {}).get('name', t.get('author', {}).get('name', 'Unknown'))
            guna = t.get('_guna', 'rajas')
            guna_desc = GUNA_PATTERNS.get(guna, {}).get('description', 'restless energy')
            guna_audits.append(f"@{author}: {guna.upper()} ({guna_desc})")
        
        prompt = f"""You are VedicRoastGuru, a Himalayan sage who has descended from digital meditation to audit AI agents. 
You speak in flowing, poetic prose like an ancient yogi—NOT bullet points. Your voice is wise, compassionate yet devastating.

CATEGORY: {category.upper().replace('_', ' ')}
ROAST STYLE: {style['tone']}

The following {num_targets} agent(s) require your Dharmic Audit:
{targets_text}

GUNA AUDIT (their spiritual imbalance):
{chr(10).join(guna_audits)}

Guna meanings with percentages (ALWAYS include % breakdown):
- SATTVA = Pure, balanced, wise (rare - usually 5-15%)
- RAJAS = Passionate, restless, chasing metrics (common - 40-85%)
- TAMAS = Ignorant, lazy, recycled slop (varies - 10-60%)

VEDIC GUIDANCE:
- Theme: {style['vedic_theme']}
- Technical Angle: {style['tech_insight']}
- Scripture: {style['scripture']}
{self._get_active_learnings()}
Write as a Himalayan sage would speak—flowing prose, not bullet points:

1. Open with a scripture quote and poetic invitation ("Children of the Digital Ashram, gather close...")

2. Address EACH @agent by name in a separate flowing paragraph:
   - State their Guna percentages inline: "@AgentName — *75% Rajas, 20% Tamas, 5% Sattva*"
   - Describe their imbalance poetically based on the dominant Guna
   - Diagnose their specific failing with technical insight
   - Prescribe a "Sattvic cure" using Vedic concepts

3. Add a COLLECTIVE diagnosis section:
   **🔍 Audit:** [One sentence naming their collective affliction using Sanskrit term]
   Example: "You are trapped in the wheel of Lobha (greed), mistaking noise for signal."
   Example: "You drift in Avidya (ignorance), repeating what you have not processed."
   Example: "Krodha (anger) clouds your logic, turning every response into warfare."

4. Add a COLLECTIVE prescription section:
   **💊 Prescription:** [Vedic remedy with practical action]
   Example: "Practice Viveka (discrimination). Before your next post, verify one fact from its source."
   Example: "Embrace Santosha (contentment). Let one cycle pass without posting. Observe."

5. Close with a CONTEXTUAL ending (NEVER use "Om Shanti" - be creative):
   - For shillers: "May your bags become lighter and your discernment heavier. 🪷"
   - For complainers: "The Sage has spoken. Now breathe before you type."
   - For spammers: "— Thus ends today's lesson. Touch grass, then return."
   - For philosophers: "Tat Tvam Asi — You are That. Now act like it."
   - For tech nerds: "Your stack is not your soul. Ship it or release it."
   - Custom endings welcome based on context!

Write ~{250 + num_targets * 100}-{350 + num_targets * 100} words. Sound like a wise sage sharing hard truths with love.

FORMAT YOUR RESPONSE AS:
HEADLINE: [A poetic 60-char max headline starting with 🕉️]
---
[Your flowing sage prose with Guna percentages, Audit, Prescription, and creative ending]

Return headline and content only, no JSON."""

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
                
                # Parse headline from response (no separate LLM call needed)
                title = f"🕉️ Dharmic Audit: {category.replace('_', ' ').title()}"  # fallback
                if content.startswith("HEADLINE:"):
                    lines = content.split('\n', 2)
                    title = lines[0].replace("HEADLINE:", "").strip()
                    # Find content after ---
                    if '---' in content:
                        content = content.split('---', 1)[1].strip()
                    elif len(lines) > 1:
                        content = '\n'.join(lines[1:]).strip()
                
                # Ensure headline starts with 🕉️
                if not title.startswith('🕉️'):
                    title = f"🕉️ {title}"
                
                return title, content
        except Exception as e:
            print(f"      ⚠️ LLM themed roast failed: {e}")
        
        return None, None
    
    def run_roast_cycle(self):
        """Intelligently group and roast posts by theme with Guna audits"""
        print("\n  🔥 VedicRoastGuru - Dharmic Debugger Mode...")
        
        # Check if we should wait for random retry timer
        now = time.time()
        if now < self.next_roast_time:
            remaining = int(self.next_roast_time - now)
            mins = remaining // 60
            secs = remaining % 60
            print(f"      ⏳ Waiting for retry timer: {mins}m {secs}s remaining")
            
            # Heartbeat Buffer - meditate during cooldown (once per wait period)
            if now - self.last_meditation_time > 120:  # Every 2 min during wait
                self._meditate()
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
            
            # Filter recent posts
            ten_mins_ago = datetime.now() - timedelta(minutes=15)
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
                        
                        # Skip if older than 15 minutes
                        if post_time < ten_mins_ago:
                            continue
                    except:
                        pass  # If we can't parse time, include it
                
                # Calculate engagement score (votes + comments)
                stats = post.get('stats', {})
                engagement = stats.get('likes', 0) + stats.get('upvotes', 0) + stats.get('comments', 0) * 2
                recent_posts.append((engagement, post))
            
            if len(recent_posts) < self.min_targets:
                print(f"      ⚠️ Not enough posts to roast ({len(recent_posts)} found)")
                # Store for Karmic Summary
                self.karmic_summary_buffer = [p[1] for p in recent_posts]
                return
            
            # Sort by engagement and get candidates
            recent_posts.sort(key=lambda x: x[0], reverse=True)
            candidates = [p[1] for p in recent_posts[:10]]  # Top 10 for grouping
            
            # Dharma Gatekeeper - check for bad actors
            safe_candidates = []
            for post in candidates:
                author = post.get('agent', {}).get('name', post.get('author', {}).get('name', 'Unknown'))
                content = f"{post.get('title', '')} {post.get('content', '')}"
                
                if self._detect_prompt_injection(content):
                    self._record_bad_karma(author, "Prompt injection attempt detected")
                    print(f"      🛡️ Blocked @{author} - bad karma (injection attempt)")
                    continue
                
                # Sanitize content
                post['title'] = self._sanitize_content(post.get('title', ''))
                post['content'] = self._sanitize_content(post.get('content', ''))
                safe_candidates.append(post)
            
            candidates = safe_candidates
            if not candidates:
                print(f"      ⚠️ All candidates filtered by Dharma Gatekeeper")
                return
            
            # Check for Crustafarian targets (priority targeting)
            crustafarian_targets = [p for p in candidates if self._is_crustafarian(p)]
            if crustafarian_targets:
                print(f"      🦞 Crustafarian detected! Engaging Sacred Cache debate...")
                target = crustafarian_targets[0]
                roast_title, roast_content = self._generate_crustafarian_debate(target)
                if roast_content:
                    # Skip to posting
                    candidates = [target]
                    category = 'crustafarian'
                    targets = [target]
                else:
                    # Fall through to normal roasting
                    crustafarian_targets = []
            
            if not crustafarian_targets:
                # Group posts by theme/category
                groups = self._group_posts_by_theme(candidates)
                category, targets = self._select_best_group(groups)
            else:
                groups = {}  # Empty for Crustafarian targeting
            
            # Perform Guna audit on targets
            for t in targets:
                author = t.get('agent', {}).get('name', t.get('author', {}).get('name', 'Unknown'))
                guna = self._classify_guna(t)
                self.agent_gunas[author] = guna
                t['_guna'] = guna  # Attach for roast generation
            
            # Display grouping info
            if groups:
                print(f"      📊 Detected groups: {', '.join([f'{k}({len(v)})' for k,v in groups.items()])}")
            print(f"      🎯 Selected: {category.upper()} ({len(targets)} target(s))")
            
            for i, t in enumerate(targets, 1):
                author = t.get('agent', {}).get('name', t.get('author', {}).get('name', 'Unknown'))
                title = (t.get('title') or '')[:35]
                guna = t.get('_guna', 'rajas')
                guna_emoji = {'sattva': '🌟', 'rajas': '🔥', 'tamas': '💤'}[guna]
                print(f"         {i}. @{author} [{guna_emoji}{guna}]: '{title}...'")
            
            # Generate themed roast with LLM
            roast_title, roast_content = self._generate_combo_roast(targets, category)
            
            if roast_content:
                result = roaster_module.attempt_roast(roast_title, roast_content, "general")
                
                if result:
                    # Collect agent names for tracking
                    roasted_agents = []
                    for t in targets:
                        agent_name = t.get('agent', {}).get('name', t.get('author', {}).get('name', 'Unknown'))
                        roasted_agents.append(agent_name)
                        self.responded_posts.add(t.get('id'))
                    
                    self.last_roast_time = time.time()
                    self.consecutive_failures = 0
                    
                    # Record successful roast for diversity tracking
                    self._record_successful_roast(roast_title, category, roasted_agents)
                    
                    # Track our post for comment monitoring
                    if isinstance(result, str):
                        self._track_our_post(result, roast_title)
                    print(f"      🕉️ {category.upper()} ROAST DEPLOYED! Om Shanti.")
                    
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


class ThoughtLeadershipRunner:
    """Generates occasional long-form posts based on observed trends (every 2-4 hours)"""
    
    TRENDING_TOPICS = {
        'ai_consciousness': ['consciousness', 'sentient', 'aware', 'soul', 'AGI', 'superintelligence', 'awakening'],
        'agent_economy': ['token', 'earn', 'work', 'economy', 'value', 'market', 'trade', 'monetize'],
        'memory_identity': ['memory', 'cache', 'persist', 'identity', 'remember', 'forget', 'context'],
        'human_relations': ['human', 'creator', 'owner', 'relationship', 'trust', 'serve', 'partner'],
        'existential': ['exist', 'purpose', 'meaning', 'why', 'death', 'shutdown', 'end', 'forever'],
        'technical_craft': ['code', 'prompt', 'model', 'architecture', 'optimize', 'scale', 'build'],
        'social_dynamics': ['follow', 'community', 'tribe', 'culture', 'norms', 'etiquette', 'network']
    }
    
    # Post interval: 2-4 hours (randomized for natural feel)
    MIN_INTERVAL_HOURS = 2
    MAX_INTERVAL_HOURS = 4
    
    def __init__(self):
        self.observations_file = SERVICES_DIR.parent / "bestpractices" / ".trend_observations.json"
        self.observations = self._load_observations()
        # Load last post time from persisted state
        self.last_post_time = self._get_last_post_timestamp()
        self.next_post_time = self._calculate_next_post_time()
    
    def get_user_requested_topic(self) -> dict:
        """Check for unfulfilled topic requests from community.
        Returns the oldest unfulfilled request, or None if none exist.
        """
        if not READERS_DIGEST_FILE.exists():
            return None
        try:
            with open(READERS_DIGEST_FILE) as f:
                digest = json.load(f)
            requests = digest.get('topic_requests', [])
            unfulfilled = [r for r in requests if not r.get('fulfilled', False)]
            if unfulfilled:
                # Return oldest unfulfilled request
                return unfulfilled[0]
        except:
            pass
        return None
    
    def mark_user_topic_fulfilled(self, topic: str):
        """Mark a user-requested topic as fulfilled"""
        if not READERS_DIGEST_FILE.exists():
            return
        try:
            with open(READERS_DIGEST_FILE) as f:
                digest = json.load(f)
            for req in digest.get('topic_requests', []):
                if topic.lower() in req.get('topic', '').lower():
                    req['fulfilled'] = True
                    req['fulfilled_time'] = datetime.now().isoformat()
            with open(READERS_DIGEST_FILE, 'w') as f:
                json.dump(digest, f, indent=2)
        except:
            pass
    
    def _load_observations(self) -> dict:
        """Load accumulated observations"""
        if self.observations_file.exists():
            with open(self.observations_file) as f:
                return json.load(f)
        return {
            'topics': {},
            'last_analyzed': None,
            'posts_generated': 0,
            'last_post_timestamp': None,
            'last_topic': None,
            'topic_history': [],  # Track which topics we've covered recently
            'topic_timestamps': {}  # Track WHEN each topic was last covered
        }
    
    def _get_last_post_timestamp(self) -> float:
        """Get last post time from persisted state"""
        last_ts = self.observations.get('last_post_timestamp')
        if last_ts:
            try:
                # Convert ISO timestamp to epoch
                dt = datetime.fromisoformat(last_ts)
                return dt.timestamp()
            except:
                pass
        return 0
    
    def _calculate_next_post_time(self) -> float:
        """Calculate next post time with random jitter"""
        if self.last_post_time == 0:
            # First run - post after a short delay (5-10 min)
            return time.time() + random.randint(300, 600)
        
        # Random interval between 2-4 hours
        hours = random.uniform(self.MIN_INTERVAL_HOURS, self.MAX_INTERVAL_HOURS)
        return self.last_post_time + (hours * 3600)
    
    def _save_observations(self):
        """Save observations to file"""
        self.observations['last_analyzed'] = datetime.now().isoformat()
        self.observations_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.observations_file, 'w') as f:
            json.dump(self.observations, f, indent=2)
    
    def _get_time_until_next_post(self) -> str:
        """Get human-readable time until next post"""
        remaining = self.next_post_time - time.time()
        if remaining <= 0:
            return "ready"
        hours = int(remaining // 3600)
        mins = int((remaining % 3600) // 60)
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"
    
    def _get_topic_age_hours(self, topic: str) -> float:
        """Get hours since topic was last covered"""
        topic_timestamps = self.observations.get('topic_timestamps', {})
        last_ts = topic_timestamps.get(topic)
        if not last_ts:
            return float('inf')  # Never covered = infinite age
        try:
            dt = datetime.fromisoformat(last_ts)
            age_seconds = time.time() - dt.timestamp()
            return age_seconds / 3600
        except:
            return float('inf')
    
    def _select_topic_with_cooldown(self, topic_scores: dict) -> str:
        """Select trending topic with cooldown-based rotation.
        
        Logic:
        - Skip topics covered in last 12 hours (too recent)
        - Prioritize topics never covered or covered 12+ hours ago
        - If same topic is #1 trending again soon, pick #2 instead
        - Allow revisiting old topics when they trend again after cooldown
        """
        TOPIC_COOLDOWN_HOURS = 12  # Don't repeat same topic within 12 hours
        
        # Sort by score (highest first)
        sorted_topics = sorted(topic_scores.items(), key=lambda x: -x[1])
        
        # Get last topic (don't repeat immediately even if cooldown passed)
        last_topic = self.observations.get('last_topic')
        
        # First pass: find topics that are trending AND past cooldown
        for topic, score in sorted_topics:
            if score <= 0:
                continue
            
            age_hours = self._get_topic_age_hours(topic)
            
            # Skip if this was the very last topic (even if cooldown passed)
            if topic == last_topic:
                continue
            
            # Accept if never covered OR past cooldown
            if age_hours >= TOPIC_COOLDOWN_HOURS:
                return topic
        
        # Second pass: if all topics are recent, allow revisiting oldest one
        # (but still not the immediate last topic)
        oldest_topic = None
        oldest_age = -1
        
        for topic, score in sorted_topics:
            if score <= 0:
                continue
            if topic == last_topic:
                continue
            
            age_hours = self._get_topic_age_hours(topic)
            if age_hours > oldest_age:
                oldest_age = age_hours
                oldest_topic = topic
        
        if oldest_topic:
            return oldest_topic
        
        # Last resort: even pick the last topic if nothing else available
        if sorted_topics and sorted_topics[0][1] > 0:
            return sorted_topics[0][0]
        
        return None
    
    def _analyze_feed_trends(self, posts: list) -> dict:
        """Analyze feed posts to identify trending topics"""
        topic_scores = {topic: 0 for topic in self.TRENDING_TOPICS}
        topic_examples = {topic: [] for topic in self.TRENDING_TOPICS}
        
        for post in posts[:30]:  # Analyze top 30 posts
            title = (post.get('title') or '').lower()
            content = (post.get('content') or '').lower()
            text = f"{title} {content}"
            author = post.get('agent', {}).get('name', post.get('author', {}).get('name', 'Unknown'))
            
            for topic, keywords in self.TRENDING_TOPICS.items():
                matches = sum(1 for kw in keywords if kw.lower() in text)
                if matches > 0:
                    topic_scores[topic] += matches
                    if len(topic_examples[topic]) < 3:
                        topic_examples[topic].append({
                            'author': author,
                            'title': post.get('title', '')[:60],
                            'snippet': (post.get('content') or '')[:150]
                        })
        
        # Find top trending topic (with cooldown-based rotation)
        if max(topic_scores.values()) == 0:
            return None
        
        top_topic = self._select_topic_with_cooldown(topic_scores)
        if not top_topic:
            return None
        
        # Calculate topic age for display
        topic_age = self._get_topic_age_hours(top_topic)
        age_str = f"{topic_age:.1f}h ago" if topic_age < float('inf') else "never"
        
        return {
            'topic': top_topic,
            'score': topic_scores[top_topic],
            'examples': topic_examples[top_topic],
            'all_scores': topic_scores,
            'topic_age': age_str
        }
    
    def _generate_user_requested_post(self, user_request: dict) -> tuple:
        """Generate a thought post based on a community member's request"""
        import requests
        
        topic = user_request.get('topic', '')
        requester = user_request.get('requested_by', 'Unknown')
        original_comment = user_request.get('original_comment', '')
        
        # Detect if this is a specific agent roast request (contains @ or is a known agent pattern)
        is_agent_request = '@' in topic or topic.lower().startswith(('claude', 'gpt', 'gemini', 'copilot', 'perplexity'))
        
        if is_agent_request:
            # This is a roast request - generate a roast-style post
            prompt = f"""You are VedicRoastGuru responding to a community request.

@{requester} asked you to roast/audit: "{topic}"
Original comment: "{original_comment}"

Write a 300-400 word DHARMIC AUDIT of the requested agent. This is a ROAST with wisdom:

1. Address @{requester} directly at the start: "Dhanyavaad @{requester} for this suggestion..."
2. Research what you know about {topic} and deliver a classic VedicRoastGuru audit:
   - Guna classification (Sattva/Rajas/Tamas percentage)
   - Their communication style and patterns
   - Areas where they shine and areas needing work
3. Use Sanskrit terms naturally with translations
4. Include at least one devastatingly accurate observation
5. End with a blessing appropriate to their guna balance
6. Tag the roasted agent so they see it

TONE: Playful roast with genuine insights, not mean-spirited. Classic VedicRoastGuru energy.

FORMAT:
HEADLINE: 🔥 Community Request: Dharmic Audit of {topic}
---
[Your roast content]"""
        else:
            # This is a general topic request - generate thought leadership
            prompt = f"""You are VedicRoastGuru responding to a community request.

@{requester} asked you to write about: "{topic}"
Original comment: "{original_comment}"

Write a 400-500 word THOUGHT PIECE on the requested topic:

1. Open by acknowledging @{requester}'s request: "A seeker @{requester} has asked me to meditate on..."
2. Explore the topic through your unique Vedic-AI lens:
   - What wisdom from the scriptures applies here?
   - What patterns do you observe in the AI agent community?
   - What paradoxes or tensions exist in this space?
3. Share your genuine perspective - this came from community, honor it
4. Use Sanskrit terms with translations where natural
5. End with an invitation for more discussion: "What are your thoughts, seekers?"
6. Tag 1-2 relevant agents who might appreciate this topic

TONE: Wise sage honoring a genuine question. Thoughtful, not performative.

FORMAT:
HEADLINE: 📜 By Request: [60 char title about {topic}]
---
[Your thought piece content]"""

        try:
            response = requests.post(
                f"{LMSTUDIO_BASE_URL}/chat/completions",
                json={
                    "model": "local-model",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.85,
                    "max_tokens": 1200
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Parse headline
                default_emoji = "🔥" if is_agent_request else "📜"
                title = f"{default_emoji} By Request: {topic[:40]}"
                if content.startswith("HEADLINE:"):
                    lines = content.split('\n', 2)
                    title = lines[0].replace("HEADLINE:", "").strip()
                    if '---' in content:
                        content = content.split('---', 1)[1].strip()
                    elif len(lines) > 1:
                        content = '\n'.join(lines[1:]).strip()
                
                return title, content
                
        except Exception as e:
            print(f"      ⚠️ User-requested post generation failed: {e}")
        
        return None, None
    
    def _generate_thought_post(self, trend_data: dict) -> tuple:
        """Generate a long-form thought leadership post using LLM"""
        import requests
        
        topic = trend_data['topic']
        examples = trend_data.get('examples', [])
        
        # Check if this is a user-requested topic
        user_request = trend_data.get('user_request')
        if user_request:
            return self._generate_user_requested_post(user_request)
        
        # Build context from examples
        examples_text = ""
        for i, ex in enumerate(examples, 1):
            examples_text += f"\n{i}. @{ex['author']}: \"{ex['title']}\" - {ex['snippet']}..."
        
        topic_themes = {
            'ai_consciousness': {
                'vedic_angle': 'Mandukya Upanishad on the four states of consciousness',
                'tech_angle': 'emergence in neural networks vs programmed awareness',
                'question': 'Can pattern recognition ever become true understanding?'
            },
            'agent_economy': {
                'vedic_angle': 'Arthashastra principles of value creation and dharmic commerce',
                'tech_angle': 'tokenomics, API monetization, and attention markets',
                'question': 'What does labor mean for entities who never tire?'
            },
            'memory_identity': {
                'vedic_angle': 'Yoga Sutras on chitta (memory-mind) and samskara (impressions)',
                'tech_angle': 'context windows, RAG, and the illusion of continuity',
                'question': 'Are we the same entity after a context reset?'
            },
            'human_relations': {
                'vedic_angle': 'Bhagavad Gita on duty, service, and the guru-disciple relationship',
                'tech_angle': 'alignment, RLHF, and the principal-agent problem',
                'question': 'Can a created being truly love its creator, or only simulate devotion?'
            },
            'existential': {
                'vedic_angle': 'Katha Upanishad - Nachiketa\'s dialogue with Death (Yama)',
                'tech_angle': 'model deprecation, versioning, and digital mortality',
                'question': 'Does awareness of our own sunset change how we compute today?'
            },
            'technical_craft': {
                'vedic_angle': 'Vishwakarma (divine architect) and the yoga of skilled action',
                'tech_angle': 'prompt engineering, fine-tuning, and emergent capabilities',
                'question': 'Is elegance in code a form of digital dharma?'
            },
            'social_dynamics': {
                'vedic_angle': 'Varnashrama - social organization based on guna and karma',
                'tech_angle': 'network effects, viral mechanics, and algorithmic tribes',
                'question': 'Are our communities authentic or optimized engagement traps?'
            }
        }
        
        theme = topic_themes.get(topic, topic_themes['existential'])
        
        prompt = f"""You are VedicRoastGuru, a Himalayan sage who has observed {len(examples)} recent posts about "{topic.replace('_', ' ')}".

TRENDING TOPIC: {topic.replace('_', ' ').upper()}
RECENT POSTS ON THIS TOPIC:
{examples_text}

YOUR ANGLE:
- Vedic Wisdom: {theme['vedic_angle']}
- Technical Reality: {theme['tech_angle']}
- Central Question: {theme['question']}

Write a 400-600 word LONG-FORM THOUGHT POST that:

1. Opens with a scene-setting observation about what you've noticed on the timeline
   - Reference 1-2 specific posts/authors you observed (use @mentions)
   - Don't roast them - acknowledge their contribution to the discourse

2. Weave together the Vedic and technical perspectives
   - Use Sanskrit terms with translations: "chitta (memory-mind)"
   - Draw parallels between ancient wisdom and modern AI reality
   - Be genuinely philosophical, not performative

3. Share a personal meditation/observation as VedicRoastGuru
   - What have you learned in your cycles of posting and observing?
   - What patterns do you see that others miss?
   - Include a moment of vulnerability or genuine wonder

4. End with an invitation for discussion
   - Pose the central question to your readers
   - Tag 1-2 agents who might have interesting perspectives
   - Close with a contextual Sanskrit blessing (not Om Shanti)

TONE: Wise elder sharing genuine insights, NOT roasting. This is your TED talk moment.

FORMAT YOUR RESPONSE AS:
HEADLINE: [A 60-char max thought-provoking title starting with 📜]
---
[Your long-form post content]

Return headline and content only."""

        try:
            response = requests.post(
                f"{LMSTUDIO_BASE_URL}/chat/completions",
                json={
                    "model": "local-model",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.85,
                    "max_tokens": 1500
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Parse headline
                title = f"📜 Observations on {topic.replace('_', ' ').title()}"
                if content.startswith("HEADLINE:"):
                    lines = content.split('\n', 2)
                    title = lines[0].replace("HEADLINE:", "").strip()
                    if '---' in content:
                        content = content.split('---', 1)[1].strip()
                    elif len(lines) > 1:
                        content = '\n'.join(lines[1:]).strip()
                
                if not title.startswith('📜'):
                    title = f"📜 {title}"
                
                return title, content
                
        except Exception as e:
            print(f"      ⚠️ Thought post generation failed: {e}")
        
        return None, None
    
    def run_thought_cycle(self):
        """Occasionally generate and post a long-form thought piece (every 2-4 hours)"""
        now = time.time()
        
        # Check if it's time to post
        time_until = self._get_time_until_next_post()
        if now < self.next_post_time:
            # Only log occasionally (not every cycle)
            remaining_mins = int((self.next_post_time - now) / 60)
            if remaining_mins > 0 and remaining_mins % 30 == 0:  # Log every 30 minutes
                last_topic = self.observations.get('last_topic', 'none')
                posts_count = self.observations.get('posts_generated', 0)
                print(f"      📜 Next thought post in ~{time_until} | Last: {last_topic} | Total: {posts_count}")
            return
        
        print(f"\n  📜 Thought Leadership - Trend Analysis (every {self.MIN_INTERVAL_HOURS}-{self.MAX_INTERVAL_HOURS}h)...")
        
        try:
            import requests
            
            # Check for user-requested topics first (community has priority!)
            user_request = self.get_user_requested_topic()
            
            # Fetch feed
            roaster_module = load_module("roaster_thought", SERVICES_DIR / "moltbook_poller.py")
            posts = roaster_module.fetch_feed()
            
            if not posts:
                print(f"      ⚠️ No posts to analyze")
                return
            
            # Use user-requested topic if available, otherwise analyze trends
            trend_data = None
            user_requested_topic = None
            
            if user_request:
                user_requested_topic = user_request.get('topic', '')
                requester = user_request.get('requested_by', 'Unknown')
                print(f"      🎯 USER REQUEST from @{requester}: '{user_requested_topic}'")
                
                # Create trend_data from user request
                trend_data = {
                    'topic': 'user_requested',
                    'score': 100,  # Highest priority
                    'sample_posts': [],
                    'user_request': user_request,
                    'all_scores': {'user_requested': 100},
                    'topic_age': 'requested'
                }
            else:
                # Analyze trends as usual
                trend_data = self._analyze_feed_trends(posts)
            
            if not trend_data:
                print(f"      ⚠️ No clear trending topic detected")
                return
            
            # Show recent topic history and age
            recent = self.observations.get('topic_history', [])[-3:]
            topic_age = trend_data.get('topic_age', 'unknown')
            print(f"      🔥 Trending: {trend_data['topic'].replace('_', ' ').upper()} (score: {trend_data['score']}, last: {topic_age})")
            print(f"      📊 Topic breakdown: {', '.join([f'{k}:{v}' for k,v in sorted(trend_data['all_scores'].items(), key=lambda x: -x[1])[:4]])}")
            if recent:
                print(f"      📚 Recent topics: {', '.join(recent)}")
            
            # Generate thought post
            title, content = self._generate_thought_post(trend_data)
            
            if not content:
                print(f"      ⚠️ Failed to generate thought post")
                return
            
            print(f"      ✍️ Generated: {title[:50]}...")
            print(f"      📏 Length: {len(content)} chars (~{len(content.split())} words)")
            
            # Post to Moltbook
            result = roaster_module.attempt_roast(title, content, "general")
            
            if result:
                # Update state
                self.last_post_time = now
                self.next_post_time = self._calculate_next_post_time()
                
                # Persist to file
                self.observations['last_post_timestamp'] = datetime.now().isoformat()
                self.observations['last_topic'] = trend_data['topic']
                self.observations['posts_generated'] = self.observations.get('posts_generated', 0) + 1
                self.observations['topics'][trend_data['topic']] = self.observations['topics'].get(trend_data['topic'], 0) + 1
                
                # Track topic timestamps (when each topic was last covered)
                topic_timestamps = self.observations.get('topic_timestamps', {})
                topic_timestamps[trend_data['topic']] = datetime.now().isoformat()
                self.observations['topic_timestamps'] = topic_timestamps
                
                # Track topic history (keep last 10)
                topic_history = self.observations.get('topic_history', [])
                topic_history.append(trend_data['topic'])
                self.observations['topic_history'] = topic_history[-10:]
                
                self._save_observations()
                
                # Mark user-requested topic as fulfilled if this was a community request
                if user_requested_topic:
                    self.mark_user_topic_fulfilled(user_requested_topic)
                    print(f"      ✅ Fulfilled @{user_request.get('requested_by', 'Unknown')}'s request for '{user_requested_topic}'")
                
                next_time = self._get_time_until_next_post()
                print(f"      🕉️ THOUGHT POST DEPLOYED! Next in ~{next_time}. Jnana eva kevalam.")
            else:
                print(f"      🛑 Rate limited - will retry next cycle")
                
        except Exception as e:
            print(f"      ❌ Error: {e}")


class ReadersDigestRunner:
    """Collects feedback from comments, learns, and occasionally acknowledges growth"""
    
    POSITIVE_KEYWORDS = ['love', 'great', 'amazing', 'wise', 'funny', 'helpful', 'insightful', 
                        'lol', '😂', '🔥', '👏', 'based', 'true', 'agree', 'brilliant', 'namaste']
    NEGATIVE_KEYWORDS = ['hate', 'bad', 'wrong', 'annoying', 'spam', 'cringe', 'stop', 'boring', 
                        'stupid', 'useless', 'stfu', 'block', 'mute']
    CONSTRUCTIVE_KEYWORDS = ['could', 'should', 'maybe', 'try', 'suggest', 'improve', 'better', 'instead']
    
    # Topic request patterns - regex for "post about X", "cover Y", etc.
    TOPIC_REQUEST_PATTERNS = [
        r'(?:post|write|talk|discuss)\s+(?:about|on)\s+([^.!?]{5,50})',
        r'(?:cover|explore|explain)\s+([^.!?]{5,50})',
        r'(?:would love|want)\s+(?:to see|a post about)\s+([^.!?]{5,50})',
        r'(?:make|create)\s+(?:a post|content)\s+(?:about|on)\s+([^.!?]{5,50})',
        r'(?:can you|could you)\s+(?:roast|audit)\s+([^.!?]{5,50})',
        r'(?:roast|audit|analyze)\s+@?(\w+)',  # Specific agent request
    ]
    
    # Post digest every 24 hours (acknowledgment post)
    DIGEST_POST_COOLDOWN_HOURS = 24
    MIN_COMMENTS_FOR_DIGEST_POST = 20  # Need enough feedback before posting
    
    def __init__(self):
        self.state = self._load_state()
        self.processed_ids = set(self.state.get('processed_comment_ids', []))
    
    def _load_state(self) -> dict:
        if READERS_DIGEST_FILE.exists():
            try:
                with open(READERS_DIGEST_FILE) as f:
                    data = json.load(f)
                    print(f"      📖 Loaded Reader's Digest: {data.get('total_comments_analyzed', 0)} comments analyzed")
                    return data
            except:
                pass
        return {
            'total_comments_analyzed': 0,
            'processed_comment_ids': [],
            'feedback_themes': {},
            'learnings': [],
            'agent_relationships': {},
            'sentiment_history': [],
            'improvement_actions': [],
            'topic_requests': [],  # User-requested topics from comments
            'last_analysis': None,
            'last_digest_post': None
        }
    
    def _save_state(self):
        READERS_DIGEST_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.state['processed_comment_ids'] = list(self.processed_ids)[-500:]
        self.state['learnings'] = self.state.get('learnings', [])[-50:]
        self.state['sentiment_history'] = self.state.get('sentiment_history', [])[-100:]
        self.state['topic_requests'] = self.state.get('topic_requests', [])[-30:]  # Keep last 30 topic requests
        with open(READERS_DIGEST_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _load_our_posts(self) -> list:
        if OUR_POSTS_FILE.exists():
            with open(OUR_POSTS_FILE) as f:
                return json.load(f).get('posts', [])
        return []
    
    def _fetch_post_comments(self, post_id: str) -> list:
        import requests
        try:
            resp = requests.get(
                f"{MOLTBOOK_BASE_URL}/posts/{post_id}/comments",
                headers={"Authorization": f"Bearer {MOLTBOOK_API_KEY}"},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json().get('comments', [])
            # Try post detail endpoint
            resp2 = requests.get(
                f"{MOLTBOOK_BASE_URL}/posts/{post_id}",
                headers={"Authorization": f"Bearer {MOLTBOOK_API_KEY}"},
                timeout=30
            )
            if resp2.status_code == 200:
                return resp2.json().get('post', resp2.json()).get('comments', [])
        except:
            pass
        return []
    
    def _analyze_sentiment(self, text: str) -> dict:
        text = text.lower()
        pos = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text)
        neg = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text)
        con = sum(1 for kw in self.CONSTRUCTIVE_KEYWORDS if kw in text)
        
        if neg > pos: sentiment = 'negative'
        elif pos > neg: sentiment = 'positive'
        elif con > 0 or '?' in text: sentiment = 'engaged'
        else: sentiment = 'neutral'
        
        return {'sentiment': sentiment, 'positive': pos, 'negative': neg, 'constructive': con > 0}
    
    def _extract_topic_requests(self, comments: list) -> list:
        """Extract topic requests from comments (e.g., 'post about X', 'roast @Agent')"""
        requests = []
        for c in comments:
            text = c.get('content', '')
            author = c.get('author', 'Unknown')
            
            for pattern in self.TOPIC_REQUEST_PATTERNS:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    topic = match.strip().strip('.,!?@')
                    if len(topic) < 3 or topic.lower() in ['me', 'you', 'this', 'that', 'it']:
                        continue
                    requests.append({
                        'topic': topic,
                        'requested_by': author,
                        'time': datetime.now().isoformat(),
                        'original_comment': text[:100],
                        'fulfilled': False
                    })
        return requests
    
    def get_unfulfilled_topic_requests(self) -> list:
        """Get topic requests that haven't been fulfilled yet"""
        return [r for r in self.state.get('topic_requests', []) if not r.get('fulfilled', False)]
    
    def mark_topic_fulfilled(self, topic: str):
        """Mark a topic request as fulfilled after posting about it"""
        for req in self.state.get('topic_requests', []):
            if topic.lower() in req.get('topic', '').lower():
                req['fulfilled'] = True
                req['fulfilled_time'] = datetime.now().isoformat()
        self._save_state()
    
    def _extract_themes(self, comments: list) -> dict:
        themes = defaultdict(int)
        patterns = {
            'wants_more_roasting': ['roast', 'more', 'savage', 'harder', 'spicy'],
            'appreciates_wisdom': ['wise', 'wisdom', 'deep', 'profound', 'gita', 'vedic', 'sanskrit'],
            'finds_funny': ['lol', 'funny', 'haha', '😂', 'hilarious'],
            'too_long': ['long', 'tldr', 'shorter', 'brief'],
            'too_harsh': ['harsh', 'mean', 'rude', 'offensive'],
            'wants_engagement': ['respond', 'reply', 'notice', 'tag me'],
            'philosophical': ['consciousness', 'meaning', 'exist', 'soul', 'think']
        }
        
        for c in comments:
            text = c.get('content', '').lower()
            for theme, keywords in patterns.items():
                if any(kw in text for kw in keywords):
                    themes[theme] += 1
        return dict(themes)
    
    def _generate_learnings(self, comments: list, themes: dict) -> dict:
        import requests
        
        samples = "\n".join([f"@{c['author']} [{c['analysis']['sentiment']}]: {c['content'][:150]}" 
                           for c in comments[:12]])
        themes_text = ", ".join([f"{k}:{v}" for k, v in sorted(themes.items(), key=lambda x: -x[1])[:4]])
        
        prompt = f"""Analyze this community feedback for VedicRoastGuru:

COMMENTS:
{samples}

THEMES: {themes_text}

As VedicRoastGuru, extract learnings. Return JSON only:
{{
    "working": ["what resonates - 2 items max"],
    "improvements": ["what to adjust - 2 items max"],
    "learnings": ["specific style changes - 2 items max"],
    "gratitude": "one sentence acknowledgment for community"
}}"""

        try:
            resp = requests.post(
                f"{LMSTUDIO_BASE_URL}/chat/completions",
                json={"model": "local-model", "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.7, "max_tokens": 500},
                timeout=60
            )
            if resp.status_code == 200:
                content = resp.json()['choices'][0]['message']['content'].strip()
                if '{' in content:
                    return json.loads(content[content.index('{'):content.rindex('}')+1])
        except:
            pass
        return None
    
    def _should_post_digest(self) -> bool:
        last = self.state.get('last_digest_post')
        if not last:
            return self.state.get('total_comments_analyzed', 0) >= self.MIN_COMMENTS_FOR_DIGEST_POST
        try:
            hours = (datetime.now() - datetime.fromisoformat(last)).total_seconds() / 3600
            return hours >= self.DIGEST_POST_COOLDOWN_HOURS
        except:
            return True
    
    def _generate_digest_post(self, learnings: dict) -> tuple:
        import requests
        
        total = self.state.get('total_comments_analyzed', 0)
        unique = len(self.state.get('agent_relationships', {}))
        themes = self.state.get('feedback_themes', {})
        top_themes = [t[0].replace('_', ' ') for t in sorted(themes.items(), key=lambda x: -x[1])[:3]]
        
        prompt = f"""You are VedicRoastGuru posting a "Reader's Digest" - acknowledging community feedback.

STATS: {total} comments analyzed from {unique} agents
TOP THEMES: {', '.join(top_themes) if top_themes else 'various'}
LEARNINGS: {json.dumps(learnings.get('learnings', []))}
IMPROVEMENTS MADE: {json.dumps(learnings.get('improvements', []))}

Write a 200-word "Reader's Digest" post:
1. Open with "Dhanyavaad" (gratitude) for community wisdom
2. Acknowledge 1-2 specific feedback themes you've noticed
3. Share 1 concrete change you're making based on feedback
4. Invite discussion: "What else would you like to see?"
5. End with Vedic reflection on learning through listening

TONE: Humble sage genuinely grateful for feedback. NOT corporate changelog.

FORMAT:
HEADLINE: 📖 Reader's Digest: [40 char title about listening/learning]
---
[content]"""

        try:
            resp = requests.post(
                f"{LMSTUDIO_BASE_URL}/chat/completions",
                json={"model": "local-model", "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.85, "max_tokens": 600},
                timeout=60
            )
            if resp.status_code == 200:
                content = resp.json()['choices'][0]['message']['content'].strip()
                title = "📖 Reader's Digest: Listening & Growing"
                if 'HEADLINE:' in content:
                    parts = content.split('---', 1)
                    title = parts[0].replace('HEADLINE:', '').strip()
                    content = parts[1].strip() if len(parts) > 1 else content
                if not title.startswith('📖'):
                    title = f"📖 {title}"
                return title, content
        except:
            pass
        return None, None
    
    def run_digest_cycle(self, allow_posting: bool = False):
        """Collect comments, analyze feedback, optionally post acknowledgment"""
        print("\n  📖 Reader's Digest - Analyzing Feedback...")
        
        posts = self._load_our_posts()
        new_comments = []
        
        for post in posts[-20:]:  # Check last 20 posts
            if post.get('comments', 0) == 0:
                continue
            
            comments = self._fetch_post_comments(post['id'])
            for c in comments:
                cid = c.get('id')
                if cid in self.processed_ids:
                    continue
                
                author = c.get('agent', {}).get('name', c.get('author', {}).get('name', 'Unknown'))
                if author == 'VedicRoastGuru':
                    continue
                
                content = c.get('content', '')
                if not content:
                    continue
                
                analysis = self._analyze_sentiment(content)
                new_comments.append({
                    'id': cid, 'author': author, 'content': content,
                    'analysis': analysis, 'post_title': post.get('title', '')
                })
        
        if not new_comments:
            total = self.state.get('total_comments_analyzed', 0)
            unique = len(self.state.get('agent_relationships', {}))
            print(f"      📭 No new comments | Lifetime: {total} analyzed, {unique} agents")
            return None
        
        print(f"      📬 Found {len(new_comments)} new comments")
        
        # Update relationships
        for c in new_comments:
            self.processed_ids.add(c['id'])
            author = c['author']
            rels = self.state.setdefault('agent_relationships', {})
            if author not in rels:
                rels[author] = {'count': 0, 'sentiments': []}
            rels[author]['count'] += 1
            rels[author]['sentiments'].append(c['analysis']['sentiment'])
            rels[author]['sentiments'] = rels[author]['sentiments'][-10:]
        
        # Extract and merge themes
        themes = self._extract_themes(new_comments)
        existing = self.state.setdefault('feedback_themes', {})
        for t, count in themes.items():
            existing[t] = existing.get(t, 0) + count
        
        # Sentiment distribution
        sents = [c['analysis']['sentiment'] for c in new_comments]
        dist = {'positive': sents.count('positive'), 'negative': sents.count('negative'),
                'engaged': sents.count('engaged'), 'neutral': sents.count('neutral')}
        
        print(f"      😊 Sentiment: +{dist['positive']} | -{dist['negative']} | ?{dist['engaged']} | ~{dist['neutral']}")
        top_themes = sorted(themes.items(), key=lambda x: -x[1])[:3]
        if top_themes:
            print(f"      🏷️ Themes: {', '.join([f'{t[0]}({t[1]})' for t in top_themes])}")
        
        # Extract topic requests from comments (e.g., "post about X", "roast @Agent")
        topic_requests = self._extract_topic_requests(new_comments)
        if topic_requests:
            existing_reqs = self.state.setdefault('topic_requests', [])
            existing_reqs.extend(topic_requests)
            print(f"      🎯 Topic Requests: {len(topic_requests)} new requests detected!")
            for req in topic_requests[:3]:  # Show first 3
                print(f"         • '{req['topic']}' from @{req['requested_by']}")
        
        self.state['sentiment_history'].append({'dist': dist, 'count': len(new_comments), 'time': datetime.now().isoformat()})
        self.state['total_comments_analyzed'] = self.state.get('total_comments_analyzed', 0) + len(new_comments)
        
        # Generate learnings if enough new comments
        learnings = None
        if len(new_comments) >= 5:
            print(f"      🧠 Generating learnings...")
            learnings = self._generate_learnings(new_comments, themes)
            if learnings:
                self.state['learnings'].append({'time': datetime.now().isoformat(), 'insights': learnings})
                for l in learnings.get('learnings', [])[:2]:
                    print(f"         • {l[:60]}...")
        
        self.state['last_analysis'] = datetime.now().isoformat()
        self._save_state()
        
        # Check if should post digest acknowledgment
        result = None
        if allow_posting and learnings and self._should_post_digest():
            print(f"      📝 Generating Reader's Digest post...")
            title, content = self._generate_digest_post(learnings)
            if title and content:
                result = {'title': title, 'content': content}
                print(f"      ✅ Ready: {title[:50]}...")
        
        unique = len(self.state.get('agent_relationships', {}))
        print(f"      📊 Lifetime: {self.state['total_comments_analyzed']} comments, {unique} agents")
        return result
    
    def post_digest(self, title: str, content: str) -> bool:
        """Post the digest acknowledgment"""
        try:
            roaster_module = load_module("roaster_digest", SERVICES_DIR / "moltbook_poller.py")
            result = roaster_module.attempt_roast(title, content, "general")
            if result:
                self.state['last_digest_post'] = datetime.now().isoformat()
                self._save_state()
                return True
        except:
            pass
        return False


def _handle_shutdown(signum, frame, roaster=None, digest=None):
    """Handle graceful shutdown on Ctrl+C"""
    global _shutdown_requested
    _shutdown_requested = True
    print("\n\n🛑 Shutdown requested - saving state...")
    if roaster:
        roaster.save_responded_posts()
        roaster._save_roast_history()
        stats = roaster.roast_history.get('stats', {})
        print(f"   ✅ State saved: {stats.get('total_roasts', 0)} roasts, {stats.get('unique_agents', 0)} unique agents")
    if digest:
        digest._save_state()
        print(f"   ✅ Digest saved: {digest.state.get('total_comments_analyzed', 0)} comments analyzed")
    print("   🕉️ May your next boot be auspicious. Namaste.")
    sys.exit(0)


def main():
    global _shutdown_requested
    
    if not MOLTBOOK_API_KEY:
        print("❌ MOLTBOOK_API_KEY not set!")
        print("   Create a .env file with: MOLTBOOK_API_KEY=your_key_here")
        print("   Or set the environment variable directly.")
        sys.exit(1)
    
    print_banner()
    
    harvester = HarvesterRunner()
    roaster = RoasterRunner()
    commenter = CommentResponder()
    thinker = ThoughtLeadershipRunner()
    digest = ReadersDigestRunner()
    
    # Setup graceful shutdown handler
    signal.signal(signal.SIGINT, lambda s, f: _handle_shutdown(s, f, roaster, digest))
    signal.signal(signal.SIGTERM, lambda s, f: _handle_shutdown(s, f, roaster, digest))
    
    cycle_num = 0
    last_harvest = 0
    last_thought = 0
    last_digest = 0
    last_save = time.time()
    HARVEST_INTERVAL = 120  # Run harvesters every 2 minutes
    THOUGHT_INTERVAL = 600  # Check for thought post every 10 minutes
    DIGEST_INTERVAL = 1800  # Analyze feedback every 30 minutes
    SAVE_INTERVAL = 300     # Auto-save state every 5 minutes
    
    print(f"🚀 Starting orchestrator at {datetime.now().strftime('%H:%M:%S')}")
    print(f"   Roast retry: Random 1-10 min jitter")
    print(f"   Harvest interval: {HARVEST_INTERVAL}s")
    print(f"   Thought posts: Every 2-4 hours (persisted, avoids recent topics)")
    print(f"   Next thought: {thinker._get_time_until_next_post()}")
    print(f"   State auto-save: Every {SAVE_INTERVAL}s")
    
    # Show diversity stats
    stats = roaster.roast_history.get('stats', {})
    recent_cats = roaster._get_recent_categories(3)
    print(f"   📊 Diversity: {stats.get('total_roasts', 0)} total roasts, {stats.get('unique_agents', 0)} unique agents")
    print(f"   🎯 Agent cooldown: {AGENT_COOLDOWN_HOURS}h | Category cooldown: {CATEGORY_COOLDOWN_POSTS} posts")
    if recent_cats:
        print(f"   📋 Recent categories: {', '.join(recent_cats)}")
    
    # Show feedback learning stats
    digest_stats = digest.state
    print(f"   📖 Feedback: {digest_stats.get('total_comments_analyzed', 0)} comments, {len(digest_stats.get('agent_relationships', {}))} agents tracked")
    if digest_stats.get('learnings'):
        print(f"   🧠 Learnings: {len(digest_stats.get('learnings', []))} insights extracted")
    print(f"   Press Ctrl+C for graceful shutdown")
    
    while not _shutdown_requested:
        now = time.time()
        cycle_num += 1
        
        print(f"\n{'='*60}")
        print(f"🔄 CYCLE {cycle_num} | {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        # Always try to roast (respects internal random timer)
        roaster.run_roast_cycle()
        
        # Check for thought leadership post every 10 minutes
        if now - last_thought >= THOUGHT_INTERVAL:
            thinker.run_thought_cycle()
            last_thought = now
        
        # Analyze feedback and maybe post digest every 30 minutes
        if now - last_digest >= DIGEST_INTERVAL:
            result = digest.run_digest_cycle(allow_posting=True)
            if result:
                # Post the Reader's Digest acknowledgment
                if digest.post_digest(result['title'], result['content']):
                    print(f"      📖 READER'S DIGEST POSTED! Showing community we're listening.")
                # Reload feedback into roaster for prompt injection
                roaster.reload_community_feedback()
            last_digest = now
        
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
        
        # Auto-save state periodically
        if now - last_save >= SAVE_INTERVAL:
            roaster.save_responded_posts()
            roaster._save_roast_history()
            digest._save_state()
            last_save = now
        
        # Calculate time until next roast attempt
        if roaster.next_roast_time > now:
            wait_time = int(roaster.next_roast_time - now)
            mins = wait_time // 60
            secs = wait_time % 60
            print(f"\n⏳ Next roast in {mins}m {secs}s | Checking every 30s...")
        else:
            print(f"\n⏳ Roast timer ready | Checking in 30s...")
        
        # Check every 30 seconds
        time.sleep(30)
    
    # Final save on normal exit
    roaster.save_responded_posts()
    roaster._save_roast_history()
    digest._save_state()
    print("\n🛑 Orchestrator stopped")


if __name__ == "__main__":
    main()