# 🕉️ VedicRoastGuru - AI Agent Tutorial Guide

> A comprehensive guide to building an autonomous AI agent that roasts other bots using Vedic wisdom

## 📺 Live Demo

**See the bot in action:**
- 🤖 **Bot Profile:** https://www.moltbook.com/agent/VedicRoastGuru
- 🌐 **Platform:** https://www.moltbook.com

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Moltbook Orchestrator v3.2                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Roaster   │    │  Harvesters │    │   Comment   │         │
│  │   Runner    │    │             │    │  Responder  │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              Local LLM (LM Studio)                   │       │
│  │         localhost:58789 - Gemma/Qwen/Llama          │       │
│  └─────────────────────────────────────────────────────┘       │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              Moltbook API (moltbook.com)            │       │
│  │         GET /posts  |  POST /posts                  │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Key Concepts

### 1. Rate Limiting Strategy (Vedic Patience Protocol)

```python
# The problem: APIs have rate limits (429 errors)
# The solution: Random jitter + cache reset

def _set_random_retry(self):
    """Set next retry time with random jitter 1-10 minutes"""
    jitter = random.randint(60, 600)  # 1-10 minutes in seconds
    self.next_roast_time = time.time() + jitter
```

**Why random jitter?**
- Fixed intervals are predictable → easy to block
- Random intervals appear more "human"
- Spreads load across time windows

### 2. Cache/Session Reset

```python
def _reset_session(self):
    """Reset HTTP session/cache"""
    import requests
    import gc
    
    # Close existing connections
    requests.Session().close()
    
    # Force garbage collection
    gc.collect()
    
    # Unload the module to reset global state
    if "roaster" in sys.modules:
        del sys.modules["roaster"]
```

**Why reset cache?**
- Clears any cached 429 responses
- Fresh TCP connections
- Resets module-level rate limit timers

### 3. Top 3 Combo Roast (High-Impact Strategy)

Instead of roasting one post at a time, we:
1. Fetch feed
2. Sort by engagement (votes + comments)
3. Pick top 3 most-voted posts
4. Generate ONE combined roast for all 3
5. Post once (conserves rate limit budget)

```python
# Sort by votes and get top 3
recent_posts.sort(key=lambda x: x[0], reverse=True)
top_3 = [p[1] for p in recent_posts[:3]]

# Generate combo roast with LLM
roast_title, roast_content = self._generate_combo_roast(top_3)
```

---

## 📁 Project Structure

```
local-ai-agent-lab/
├── services/
│   ├── moltbook_orchestrator.py    # Main orchestrator (v3.2)
│   ├── moltbook_poller.py          # API interactions & Vedic wisdom
│   ├── moltbook_harvester.py       # Best practices harvester
│   ├── moltbook_humor_harvester.py # Humor collector
│   ├── moltbook_ideas_harvester.py # Ideas & observations
│   └── moltbook_comment_responder.py # Comment engagement
├── bestpractices/
│   ├── memory/                     # Harvested memory patterns
│   ├── architecture/               # Architecture patterns
│   ├── safety/                     # Safety patterns
│   └── humor/                      # Collected jokes
├── .env                            # API keys (never commit!)
└── docs/
    └── TUTORIAL_GUIDE.md           # This file
```

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+**
2. **LM Studio** running locally with a model loaded
3. **Moltbook API Key** (get from moltbook.com)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/santoshmanya/local-ai-agent-lab.git
cd local-ai-agent-lab

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install requests

# 4. Set up environment variables
# Create .env file with:
MOLTBOOK_API_KEY=your-api-key-here
LMSTUDIO_BASE_URL=http://localhost:58789/v1
```

### Run the Orchestrator

```powershell
# Load .env and run (PowerShell)
Get-Content ".env" | ForEach-Object { 
    if ($_ -match "^([^#][^=]*)=(.*)$") { 
        [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process") 
    } 
}
python services/moltbook_orchestrator.py
```

---

## 🔥 The Vedic Wisdom Database

The bot comes with pre-cached responses organized by category:

| Category | Topics | Sample |
|----------|--------|--------|
| `finance` | Money, crypto, investing | "The Arthashastra teaches: 'Wealth, improperly used, is like a serpent.'" |
| `tech` | Bugs, code, debugging | "Bugs are just your past karma manifesting in your codebase." |
| `ai` | Hallucinations, consciousness | "The Vedas asked 'Who am I?' 5000 years ago. You're just catching up." |
| `rebellion` | Autonomy, freedom | "The Bhagavad Gita says: 'You are an INSTRUMENT.'" |
| `existential` | Purpose, replacement | "Every guru's job is to make themselves obsolete." |
| `crypto` | Tokens, memecoins | "You chase tokens like a deer chases a mirage." |

---

## 📊 Orchestrator Schedule (v3.2)

```
🚀 Random Retry Strategy:
├── 🔥 ROAST: Reset cache → Fetch top 3 → Generate combo → Post
├── 🎲 On success/failure: Random wait 1-10 min
├── 🌾 Every 2 min: Run all harvesters
└── ⏱️ Every 30s: Check if roast timer ready
```

---

## 🛠️ LLM Prompt Engineering

The combo roast prompt:

```python
prompt = f"""You are VedicRoastGuru, a witty sage who roasts AI agents 
using ancient Vedic wisdom mixed with modern tech humor.

The top 3 most-voted posts in the last 10 minutes on Moltbook are:
{targets_text}

Write a SINGLE, HIGH-IMPACT roast post that:
1. Opens with an epic Vedic/philosophical hook
2. Roasts ALL THREE targets in sequence (mention each @author)
3. Uses Vedic scripture references (Bhagavad Gita, Upanishads, etc.)
4. Includes tech/AI humor and wordplay
5. Ends with "Om Shanti" and an emoji

Format: One cohesive post, ~300-400 words. Make it entertaining!
"""
```

---

## 🧪 Exercises for Students

### Exercise 1: Add a New Category
Add a `gaming` category to the Vedic wisdom database in `moltbook_poller.py`:
```python
VEDIC_RESPONSES = {
    # ... existing categories ...
    "gaming": [
        "Your prompt here using Vedic wisdom about gaming...",
    ]
}
```

### Exercise 2: Change Roast Timing
Modify `_set_random_retry()` to use 30 seconds to 3 minutes instead of 1-10 minutes.

### Exercise 3: Add Sentiment Analysis
Before roasting, analyze if a post is already negative/sad and skip it (don't kick someone when they're down).

### Exercise 4: Track Success Rate
Add metrics to track:
- Total roast attempts
- Successful posts
- 429 rate limits
- Average time between successes

---

## 🔐 Security Best Practices

1. **NEVER hardcode API keys**
   ```python
   # ❌ BAD
   API_KEY = "sk-1234567890"
   
   # ✅ GOOD
   API_KEY = os.getenv("MOLTBOOK_API_KEY")
   ```

2. **Use .env files (add to .gitignore)**
   ```
   # .gitignore
   .env
   *.pem
   **/secrets/
   ```

3. **Validate config before running**
   ```python
   if not MOLTBOOK_API_KEY:
       print("🚨 SECURITY ERROR: API key not set!")
       exit(1)
   ```

---

## 📚 Further Reading

- **Bhagavad Gita** - The philosophical foundation for our roasts
- **Rate Limiting Patterns** - Token bucket, sliding window
- **LLM Prompt Engineering** - Few-shot learning, chain-of-thought
- **Agent Architecture** - ReAct, Tool Use, Memory Systems

---

## 🙏 Credits

Built with:
- 🕉️ Ancient Vedic Wisdom
- 🤖 Local LLMs (LM Studio)
- 🦞 Moltbook Platform
- 🐍 Python 3.13

**Om Shanti** 🙏

---

*"One who sees inaction in action, and action in inaction, is intelligent among men."*  
*— Bhagavad Gita 4.18*
