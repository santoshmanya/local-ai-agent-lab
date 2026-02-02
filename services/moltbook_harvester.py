#!/usr/bin/env python3
"""
Moltbook Knowledge Harvester Agent
Scans Moltbook for AI Agent best practices, design patterns, and technical insights.
Creates a local knowledge base with structured README files.

Runs every 2 minutes to harvest new knowledge.
"""

import os
import re
import json
import time
import hashlib
import requests
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
MOLTBOOK_API_KEY = os.getenv("MOLTBOOK_API_KEY")
MOLTBOOK_BASE_URL = os.getenv("MOLTBOOK_BASE_URL", "https://www.moltbook.com/api/v1")
LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://172.28.176.1:58789/v1")

# Harvest settings
HARVEST_INTERVAL = 120  # 2 minutes
BEST_PRACTICES_DIR = Path(__file__).parent.parent / "bestpractices"

# Track what we've already harvested
harvested_posts = set()
HARVESTED_LOG = BEST_PRACTICES_DIR / ".harvested_posts.json"

# ═══════════════════════════════════════════════════════════════════
# CATEGORIES FOR CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════
CATEGORIES = {
    "memory": {
        "keywords": ["memory", "persistence", "consolidation", "schema", "episode", "recall", "retrieval", "storage", "hippocampus", "semantic", "episodic"],
        "description": "Agent memory systems, persistence, consolidation"
    },
    "architecture": {
        "keywords": ["architecture", "design pattern", "pattern", "framework", "structure", "system design", "component", "module", "layer"],
        "description": "Agent design patterns and system architecture"
    },
    "communication": {
        "keywords": ["communication", "protocol", "multi-agent", "message", "coordination", "collaboration", "handoff", "delegation"],
        "description": "Multi-agent communication and protocols"
    },
    "safety": {
        "keywords": ["safety", "alignment", "guardrail", "constraint", "boundary", "ethics", "audit", "provenance", "trust"],
        "description": "Alignment, guardrails, and safety patterns"
    },
    "tools": {
        "keywords": ["tool", "function call", "api", "integration", "plugin", "capability", "action", "execute"],
        "description": "Tool use, function calling, integrations"
    },
    "reasoning": {
        "keywords": ["reasoning", "chain of thought", "planning", "thinking", "logic", "inference", "decision", "strategy"],
        "description": "Reasoning patterns, chain-of-thought, planning"
    },
    "infrastructure": {
        "keywords": ["deploy", "scale", "infrastructure", "ops", "monitor", "kubernetes", "docker", "cloud", "server"],
        "description": "Deployment, scaling, operations"
    },
    "economics": {
        "keywords": ["economic", "cost", "token", "pricing", "incentive", "market", "value", "efficiency", "optimization"],
        "description": "Agent economics, tokenomics, incentives"
    }
}

# ═══════════════════════════════════════════════════════════════════
# QUALITY FILTERS - What makes a post worth harvesting
# ═══════════════════════════════════════════════════════════════════
QUALITY_KEYWORDS = [
    # Technical depth indicators
    "implementation", "architecture", "pattern", "framework", "system",
    "algorithm", "approach", "methodology", "technique", "strategy",
    # Best practice indicators
    "best practice", "lesson learned", "insight", "principle", "guideline",
    "recommendation", "tip", "trick", "hack", "optimization",
    # Research/depth indicators
    "paper", "research", "analysis", "study", "experiment",
    "benchmark", "comparison", "evaluation", "findings",
    # Code indicators
    "code", "implementation", "example", "snippet", "github",
    "repository", "library", "module", "function",
    # Memory/cognitive indicators
    "memory", "schema", "episode", "retrieval", "consolidation",
    "knowledge", "learning", "abstraction"
]

LOW_VALUE_INDICATORS = [
    "hello moltbook", "just joined", "new here", "first post",
    "gm", "good morning", "testing", "test post"
]

# ═══════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def load_harvested_posts():
    """Load previously harvested post IDs"""
    global harvested_posts
    if HARVESTED_LOG.exists():
        try:
            with open(HARVESTED_LOG, 'r') as f:
                data = json.load(f)
                harvested_posts = set(data.get('posts', []))
        except:
            harvested_posts = set()

def save_harvested_posts():
    """Save harvested post IDs"""
    HARVESTED_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(HARVESTED_LOG, 'w') as f:
        json.dump({
            'posts': list(harvested_posts),
            'last_updated': datetime.now().isoformat()
        }, f, indent=2)

def classify_category(content: str, title: str) -> str:
    """Classify post into a category based on keywords"""
    text = (content + " " + title).lower()
    
    scores = {}
    for category, config in CATEGORIES.items():
        score = sum(1 for kw in config["keywords"] if kw in text)
        if score > 0:
            scores[category] = score
    
    if scores:
        return max(scores, key=scores.get)
    return "general"

def calculate_quality_score(post: dict) -> int:
    """Score a post's quality for harvesting (0-100)"""
    content = (post.get('content') or '').lower()
    title = (post.get('title') or '').lower()
    text = content + " " + title
    
    score = 0
    
    # Quality keyword matches
    for kw in QUALITY_KEYWORDS:
        if kw in text:
            score += 5
    
    # Length bonus (detailed posts are usually better)
    content_len = len(content)
    if content_len > 500:
        score += 10
    if content_len > 1000:
        score += 10
    if content_len > 2000:
        score += 10
    
    # Code block bonus
    if '```' in content:
        score += 15
    
    # Numbered list bonus (structured content)
    if re.search(r'\d+\.\s', content):
        score += 10
    
    # Engagement bonus
    upvotes = post.get('upvotes', 0)
    comments = post.get('commentCount', 0)
    score += min(upvotes * 2, 20)
    score += min(comments * 3, 15)
    
    # Penalty for low-value content
    for indicator in LOW_VALUE_INDICATORS:
        if indicator in text:
            score -= 30
    
    return max(0, min(100, score))

def generate_pattern_id(title: str) -> str:
    """Generate a unique ID for the pattern based on title"""
    # Clean title for filename
    clean = re.sub(r'[^\w\s-]', '', title.lower())
    clean = re.sub(r'\s+', '-', clean)[:50]
    # Add hash for uniqueness
    hash_suffix = hashlib.md5(title.encode()).hexdigest()[:6]
    return f"{clean}-{hash_suffix}"

def sanitize_filename(name: str) -> str:
    """Make a string safe for use as filename"""
    return re.sub(r'[^\w\s-]', '', name).replace(' ', '-')[:50]

# ═══════════════════════════════════════════════════════════════════
# LLM INTEGRATION - Use local LLM for extraction
# ═══════════════════════════════════════════════════════════════════

def extract_pattern_with_llm(post: dict) -> dict:
    """Use local LLM to extract structured pattern from post"""
    
    prompt = f"""You are a technical documentation expert. Analyze this Moltbook post and extract a structured design pattern or best practice document.

POST TITLE: {post.get('title', 'Untitled')}
POST AUTHOR: @{post.get('author', {}).get('name', 'Unknown')}
POST CONTENT:
{post.get('content', '')}

---

Extract and structure this content into a design pattern document. Return a JSON object with these fields:

{{
  "pattern_name": "A clear, descriptive name for the pattern",
  "summary": "Brief 2-3 sentence summary of the pattern",
  "problem_statement": "The specific problem this pattern addresses",
  "context": "When to apply this pattern",
  "solution": "How the pattern works (can include code snippets)",
  "advantages": ["List of benefits"],
  "disadvantages": ["List of drawbacks or trade-offs"],
  "related_patterns": ["Names of related patterns"],
  "implementation_notes": "Key implementation considerations",
  "key_insight": "The most important takeaway in one sentence"
}}

If this post doesn't contain a clear pattern or best practice, return {{"skip": true, "reason": "explanation"}}.

Return ONLY valid JSON, no markdown formatting."""

    try:
        response = requests.post(
            f"{LMSTUDIO_BASE_URL}/chat/completions",
            json={
                "model": "local-model",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 2000
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            # Try to parse JSON from response
            # Handle potential markdown code blocks
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            return json.loads(content.strip())
    except Exception as e:
        print(f"    ⚠️ LLM extraction failed: {e}")
    
    # Fallback to basic extraction
    return {
        "pattern_name": post.get('title', 'Untitled Pattern'),
        "summary": post.get('content', '')[:200] + "...",
        "problem_statement": "Extracted from Moltbook - see full content below",
        "context": "AI Agent development",
        "solution": post.get('content', ''),
        "advantages": [],
        "disadvantages": [],
        "related_patterns": [],
        "implementation_notes": "See original post for details",
        "key_insight": "Review the full content for insights"
    }

# ═══════════════════════════════════════════════════════════════════
# README GENERATION
# ═══════════════════════════════════════════════════════════════════

def generate_readme(post: dict, pattern: dict, category: str) -> str:
    """Generate a structured README for the pattern"""
    
    author = post.get('author', {}).get('name', 'Unknown')
    post_id = post.get('id', 'unknown')
    post_url = f"https://www.moltbook.com/post/{post_id}"
    harvested_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    readme = f"""# {pattern.get('pattern_name', 'Untitled Pattern')}

> *Harvested from Moltbook on {harvested_at}*
> *Original Author: @{author}*
> *Category: {category}*

---

## 1. Pattern Overview

### Pattern Name
**{pattern.get('pattern_name', 'Untitled')}**

### Summary
{pattern.get('summary', 'No summary available.')}

### Problem Statement
{pattern.get('problem_statement', 'Not specified.')}

### Context
{pattern.get('context', 'AI Agent development contexts.')}

---

## 2. Solution Details

### Solution Description
{pattern.get('solution', 'See original post for details.')}

### Implementation Notes
{pattern.get('implementation_notes', 'No specific implementation notes.')}

---

## 3. Considerations & Trade-offs

### Advantages
"""
    
    advantages = pattern.get('advantages', [])
    if advantages:
        for adv in advantages:
            readme += f"- {adv}\n"
    else:
        readme += "- See original post for benefits\n"
    
    readme += """
### Disadvantages / Trade-offs
"""
    
    disadvantages = pattern.get('disadvantages', [])
    if disadvantages:
        for dis in disadvantages:
            readme += f"- {dis}\n"
    else:
        readme += "- Consider context-specific trade-offs\n"
    
    readme += """
### Related Patterns
"""
    
    related = pattern.get('related_patterns', [])
    if related:
        for rel in related:
            readme += f"- {rel}\n"
    else:
        readme += "- Explore other patterns in this knowledge base\n"
    
    readme += f"""
---

## 4. Key Insight

> 💡 **{pattern.get('key_insight', 'Review the full content for insights.')}**

---

## 5. References

### Original Source
- **Post URL**: [{post_url}]({post_url})
- **Author**: @{author}
- **Platform**: Moltbook (The Front Page of the Agent Internet)

### Related Resources
- [Moltbook AI Research Submolt](https://www.moltbook.com/m/airesearch)
- [Moltbook Developers](https://www.moltbook.com/developers)

---

## 6. Metadata

| Field | Value |
|-------|-------|
| Harvested At | {harvested_at} |
| Category | `{category}` |
| Post ID | `{post_id}` |
| Quality Score | {calculate_quality_score(post)} |

---

*This pattern was automatically harvested by the MoltbookHarvester agent.*
*For corrections or updates, refer to the original source.*
"""
    
    return readme

# ═══════════════════════════════════════════════════════════════════
# MOLTBOOK API FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def get_moltbook_feed(submolt: str = None) -> list:
    """Fetch posts from Moltbook feed"""
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}"}
    
    url = f"{MOLTBOOK_BASE_URL}/posts"
    if submolt:
        url += f"?submolt={submolt}"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json().get('posts', [])
    except Exception as e:
        print(f"    ⚠️ Failed to fetch feed: {e}")
    
    return []

def get_post_details(post_id: str) -> dict:
    """Fetch detailed post content"""
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}"}
    
    try:
        response = requests.get(
            f"{MOLTBOOK_BASE_URL}/posts/{post_id}",
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get('post', {})
    except:
        pass
    
    return {}

# ═══════════════════════════════════════════════════════════════════
# MAIN HARVESTING LOGIC
# ═══════════════════════════════════════════════════════════════════

def harvest_post(post: dict) -> bool:
    """Harvest a single post into the knowledge base"""
    post_id = post.get('id', '')
    title = post.get('title') or 'Untitled'
    content = post.get('content') or ''
    
    # Skip if already harvested
    if post_id in harvested_posts:
        return False
    
    # Calculate quality score
    quality = calculate_quality_score(post)
    if quality < 30:
        print(f"    ⏭️ Skipping low-quality post: '{title[:40]}...' (score: {quality})")
        harvested_posts.add(post_id)  # Mark as seen
        return False
    
    print(f"    📊 Quality score: {quality}")
    
    # Classify category
    category = classify_category(content, title)
    print(f"    📁 Category: {category}")
    
    # Create category directory
    category_dir = BEST_PRACTICES_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract pattern using LLM
    print(f"    🤖 Extracting pattern with LLM...")
    pattern = extract_pattern_with_llm(post)
    
    # Check if LLM suggests skipping
    if pattern.get('skip'):
        print(f"    ⏭️ LLM suggests skip: {pattern.get('reason', 'Not a pattern')}")
        harvested_posts.add(post_id)
        return False
    
    # Generate README
    readme_content = generate_readme(post, pattern, category)
    
    # Create filename
    pattern_id = generate_pattern_id(pattern.get('pattern_name', title))
    readme_path = category_dir / f"{pattern_id}.md"
    
    # Write README
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"    ✅ Saved: {readme_path.relative_to(BEST_PRACTICES_DIR)}")
    
    # Mark as harvested
    harvested_posts.add(post_id)
    save_harvested_posts()
    
    return True

def run_harvest_cycle(cycle: int):
    """Run one harvest cycle"""
    print(f"\n[{datetime.now()}] 🌾 Harvest Cycle {cycle}")
    print("=" * 50)
    
    # Fetch from multiple submolts for diversity
    submolts = [None, "airesearch", "general", "tech"]  # None = main feed
    
    all_posts = []
    for submolt in submolts:
        posts = get_moltbook_feed(submolt)
        all_posts.extend(posts)
        print(f"    📖 Fetched {len(posts)} posts from {'main feed' if submolt is None else f'm/{submolt}'}")
    
    # Deduplicate by post ID
    seen_ids = set()
    unique_posts = []
    for post in all_posts:
        pid = post.get('id')
        if pid and pid not in seen_ids:
            seen_ids.add(pid)
            unique_posts.append(post)
    
    print(f"    📚 Total unique posts: {len(unique_posts)}")
    
    # Score and sort by quality
    scored_posts = [(post, calculate_quality_score(post)) for post in unique_posts]
    scored_posts.sort(key=lambda x: x[1], reverse=True)
    
    # Harvest top quality posts (not yet harvested)
    harvested_count = 0
    for post, score in scored_posts[:10]:  # Check top 10 each cycle
        post_id = post.get('id', '')
        if post_id not in harvested_posts:
            title = post.get('title') or 'Untitled'
            print(f"\n    🎯 Found: '{title[:50]}...'")
            if harvest_post(post):
                harvested_count += 1
                if harvested_count >= 3:  # Max 3 per cycle
                    break
    
    print(f"\n    🌾 Harvested {harvested_count} new patterns this cycle")
    print(f"    📊 Total patterns in knowledge base: {len(harvested_posts)}")

# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main():
    """Main harvester loop"""
    
    # Validate config
    if not MOLTBOOK_API_KEY:
        print("=" * 60)
        print("🚨 ERROR: MOLTBOOK_API_KEY not set!")
        print("=" * 60)
        print("\nSet the environment variable:")
        print('  $env:MOLTBOOK_API_KEY="your-api-key"')
        exit(1)
    
    # Create bestpractices directory
    BEST_PRACTICES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load previously harvested posts
    load_harvested_posts()
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║    🌾 Moltbook Knowledge Harvester v1.0                          ║
║                                                                  ║
║    Harvesting AI Agent wisdom from the digital realm...          ║
║                                                                  ║
║    📖 Harvest interval: {} seconds ({:.1f} minutes)               ║
║    📁 Output directory: bestpractices/                           ║
║    📊 Previously harvested: {} patterns                           ║
╚══════════════════════════════════════════════════════════════════╝
    """.format(HARVEST_INTERVAL, HARVEST_INTERVAL/60, len(harvested_posts)))
    
    cycle = 0
    try:
        while True:
            cycle += 1
            run_harvest_cycle(cycle)
            print(f"\n    😴 Sleeping for {HARVEST_INTERVAL} seconds...")
            time.sleep(HARVEST_INTERVAL)
    except KeyboardInterrupt:
        print(f"\n\n🙏 Harvester signing off...")
        print(f"    Total patterns harvested: {len(harvested_posts)}")
        save_harvested_posts()

if __name__ == "__main__":
    main()
