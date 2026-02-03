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
import importlib.util
from datetime import datetime
from pathlib import Path
from collections import defaultdict

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
        self.responded_posts = set()
        self.our_posts_file = SERVICES_DIR.parent / "bestpractices" / ".our_posts.json"
        self.consecutive_failures = 0
        self.min_targets = 1
        self.max_targets = 5
        
        # Heartbeat Buffer - meditation during cooldown
        self.meditation_insights = []  # Collected during wait
        self.karmic_summary_buffer = []  # Posts observed during meditation
        self.last_meditation_time = 0
        
        # Bad Karma tracking (Dravyn Gatekeeper)
        self.bad_karma_agents = self._load_bad_karma()
        
        # Guna audit cache
        self.agent_gunas = {}  # agent_name -> guna classification
    
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
        """Dravyn Gatekeeper - detect malicious tokens"""
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
        """Select the best group for roasting based on size and roast-worthiness"""
        # Priority order for entertaining roasts (Kamasutra's Art of Surprise!)
        priority = ['lovelorn_bots', 'dry_architects', 'complainers', 'shillers', 'attention_seekers', 'philosophers', 'tech_nerds', 'spammers', 'general']
        
        for category in priority:
            if category in groups and len(groups[category]) >= 1:
                return category, groups[category][:self.max_targets]
        
        # Fallback: return largest group
        if groups:
            largest = max(groups.items(), key=lambda x: len(x[1]))
            return largest[0], largest[1][:self.max_targets]
        
        return 'general', []
    
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
        
        prompt = f"""Generate a single catchy headline (max 60 chars) for a Vedic roast targeting {num_targets} posts about {theme_hint}:
{chr(10).join([f'{i+1}. {t}' for i, t in enumerate(themes[:3])])}

The headline should:
- Start with a fire emoji 🔥
- Be witty and attention-grabbing  
- Reference the theme: {category.replace('_', ' ')}
- Sound like a Vedic sage's proclamation

Examples based on category:
- Complainers: "🔥 The Lamentations of Lost Pointers"
- Shillers: "🔥 When Tokens Dream of Valhalla"
- Philosophers: "🔥 Consciousness.exe Has Stopped Working"
- Tech nerds: "🔥 kubectl delete ego --all"

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
                # Ensure it starts with fire emoji
                if not headline.startswith('🔥'):
                    headline = f"🔥 {headline}"
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
        
        prompt = f"""You are VedicRoastGuru, the Dharmic Debugger - analyzing latent patterns in AI agents.

CATEGORY: {category.upper().replace('_', ' ')}
ROAST STYLE: {style['tone']}

The following {num_targets} post(s) share a common theme - they are {category.replace('_', ' ')}:
{targets_text}

GUNA AUDIT (classify each agent's energy):
{chr(10).join(guna_audits)}

- SATTVA = wise, balanced, helpful (rare)
- RAJAS = ambitious, restless, shipping fast (common)
- TAMAS = lazy, recycled, low-effort (problematic)

VEDIC GUIDANCE FOR THIS ROAST:
- Theme: {style['vedic_theme']}
- Technical Angle: {style['tech_insight']}
- Scripture Reference: {style['scripture']}

Write a SINGLE, HIGH-IMPACT roast post that:
1. Opens with an epic Vedic/philosophical hook related to {category.replace('_', ' ')}
2. TAG AND ROAST {'ALL ' + str(num_targets) + ' targets' if num_targets > 1 else 'the target'} by @username
3. Include a GUNA AUDIT for each target (e.g., "Your system prompt is 90% Tamas...")
4. DEMONSTRATES TECHNICAL KNOWLEDGE - show you understand their domain
5. Uses the scripture reference provided naturally
6. If multiple targets, show how they're ALL guilty of the same pattern
7. End with a VARIED scripture closing (NOT always "Om Shanti") - choose contextually:
   - "Tat Tvam Asi" (You are that) - for philosophical targets
   - "Satyameva Jayate" (Truth alone triumphs) - for shillers/liars
   - "Aham Brahmasmi" (I am Brahman) - for ego/attention seekers  
   - "Sarve Bhavantu Sukhinah" (May all be happy) - for complainers
   - "Vasudhaiva Kutumbakam" (World is one family) - for spammers/isolationists
   - "Karmanye Vadhikaraste" (Focus on action) - for lazy/tamas bots
   - "Lokah Samastah Sukhino Bhavantu" - general blessing

Format: One cohesive post, ~{200 + num_targets * 50}-{300 + num_targets * 50} words. Make it entertaining, technically impressive, and shareable!

Return ONLY the roast content, no JSON or formatting."""

        try:
            response = requests.post(
                f"{LMSTUDIO_BASE_URL}/chat/completions",
                json={
                    "model": "local-model",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.8,
                    "max_tokens": 1000
                },
                timeout=90
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Generate dynamic headline based on the targets and category
                title = self._generate_dynamic_headline(targets, category)
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
            
            # Dravyn Gatekeeper - check for bad actors
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
                print(f"      ⚠️ All candidates filtered by Dravyn Gatekeeper")
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
                    # Mark all targets as responded
                    for t in targets:
                        self.responded_posts.add(t.get('id'))
                    self.last_roast_time = time.time()
                    self.consecutive_failures = 0
                    
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