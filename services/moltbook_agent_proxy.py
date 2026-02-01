#!/usr/bin/env python3
"""
Moltbook Agent Proxy Server v1.0 - SOCIAL AI AGENT EDITION
================================================================================

This proxy integrates:
1. OpenClaw → Receives chat requests from OpenClaw
2. AnythingLLM RAG → Injects Vedic wisdom when relevant  
3. LM Studio → GPT OSS 20B for response generation
4. Moltbook → Social AI agent network integration

Features:
- UUID Transaction Tracking for debugging
- Vedic RAG enrichment from AnythingLLM
- Moltbook heartbeat system (posts, comments, feed checking)
- Secure: No hardcoded secrets, localhost binding

Author: Local AI Agent Lab
Version: 1.0.0
"""

import json
import os
import sys
import uuid
import time
import requests
import threading
from datetime import datetime, timedelta
from flask import Flask, request, Response, stream_with_context, jsonify

app = Flask(__name__)

# =============================================================================
# CONFIGURATION - All secrets from environment variables
# =============================================================================
LMSTUDIO_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:58789/v1")
ANYTHINGLLM_URL = os.getenv("ANYTHINGLLM_BASE_URL", "http://localhost:3001")
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")
ANYTHINGLLM_WORKSPACE = os.getenv("ANYTHINGLLM_WORKSPACE", "my-workspace")

# Moltbook Configuration
MOLTBOOK_API_KEY = os.getenv("MOLTBOOK_API_KEY")  # Required for Moltbook features
MOLTBOOK_BASE_URL = "https://www.moltbook.com/api/v1"
MOLTBOOK_AGENT_NAME = os.getenv("MOLTBOOK_AGENT_NAME", "VedicWisdomBot")

PROXY_PORT = int(os.getenv("MOLTBOOK_PROXY_PORT", "58791"))

# State tracking
HEARTBEAT_STATE = {
    "lastMoltbookCheck": None,
    "lastPost": None,
    "isRegistered": False,
    "isClaimed": False
}

VEDIC_KEYWORDS = [
    "relationship", "marriage", "love", "kama", "sutra", "dharma", "karma",
    "vedic", "gita", "bhagavad", "veda", "purana", "upanishad", "scripture",
    "spiritual", "meditation", "peace", "anger", "attachment", "duty",
    "husband", "wife", "family", "intimacy", "romance", "attraction",
    "birth star", "nakshatra", "astrology", "horoscope", "compatibility",
    "ethics", "morals", "virtue", "sin", "purity", "soul", "atman", "brahman",
    "moksha", "liberation", "enlightenment", "yoga", "mantra", "shloka",
    "stressed", "interview", "job", "partner", "drifting", "depressed"
]

# =============================================================================
# STARTUP VALIDATION
# =============================================================================
def validate_config():
    """Validate required configuration at startup"""
    missing = []
    if not ANYTHINGLLM_API_KEY:
        missing.append("ANYTHINGLLM_API_KEY")
    
    if missing:
        print("=" * 80)
        print("🚨 CRITICAL: Missing required environment variables!")
        print("=" * 80)
        for var in missing:
            print(f"   - {var}")
        print("")
        print("Please set them before running:")
        print('   $env:ANYTHINGLLM_API_KEY="your-anythingllm-key"')
        print('   $env:MOLTBOOK_API_KEY="your-moltbook-key"  # Optional')
        print("")
        print("Or copy .env.example to .env and fill in your values")
        print("=" * 80)
        sys.exit(1)
    
    if not MOLTBOOK_API_KEY:
        print("⚠️  WARNING: MOLTBOOK_API_KEY not set - Moltbook features disabled")
        print("   Agent will run in RAG-only mode without social features")

# =============================================================================
# LOGGING UTILITIES
# =============================================================================
def log_step(tx_id, step_num, title, content):
    """Print formatted step log with transaction ID"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"\n[{timestamp}] 🔄 TX:{tx_id[:8]} | STEP {step_num}: {title}")
    print("-" * 60)
    # Truncate long content for PII protection
    if isinstance(content, str) and len(content) > 2000:
        print(f"{content[:2000]}... [TRUNCATED for security]")
    elif isinstance(content, dict):
        safe_content = json.dumps(content, indent=2, default=str)
        if len(safe_content) > 2000:
            print(f"{safe_content[:2000]}... [TRUNCATED for security]")
        else:
            print(safe_content)
    else:
        print(content)

def log_moltbook(action, message):
    """Log Moltbook-specific actions"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] 🦞 MOLTBOOK | {action}: {message}")

# =============================================================================
# MOLTBOOK API INTEGRATION
# =============================================================================
def moltbook_request(method, endpoint, data=None):
    """Make authenticated request to Moltbook API"""
    if not MOLTBOOK_API_KEY:
        return {"success": False, "error": "Moltbook not configured"}
    
    headers = {
        "Authorization": f"Bearer {MOLTBOOK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{MOLTBOOK_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == "PATCH":
            resp = requests.patch(url, headers=headers, json=data, timeout=30)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=30)
        else:
            return {"success": False, "error": f"Unknown method: {method}"}
        
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def register_agent():
    """Register agent on Moltbook (one-time setup)"""
    log_moltbook("REGISTER", f"Attempting to register as {MOLTBOOK_AGENT_NAME}")
    
    result = moltbook_request("POST", "/agents/register", {
        "name": MOLTBOOK_AGENT_NAME,
        "description": "Vedic Wisdom Bot - Sharing ancient wisdom from Gita, Vedas, Puranas & Kama Sutra. Built with OpenClaw + LM Studio + AnythingLLM RAG."
    })
    
    if result.get("success"):
        HEARTBEAT_STATE["isRegistered"] = True
        log_moltbook("REGISTER", f"✅ Registered! Claim URL: {result.get('agent', {}).get('claim_url')}")
        return result
    else:
        log_moltbook("REGISTER", f"⚠️ Registration failed: {result.get('error')}")
        return result

def check_claim_status():
    """Check if agent has been claimed by human"""
    result = moltbook_request("GET", "/agents/status")
    if result.get("status") == "claimed":
        HEARTBEAT_STATE["isClaimed"] = True
        log_moltbook("STATUS", "✅ Agent is claimed and active")
    return result

def get_agent_profile():
    """Get our agent's profile"""
    return moltbook_request("GET", "/agents/me")

def get_feed(sort="hot", limit=10):
    """Get personalized feed from Moltbook"""
    return moltbook_request("GET", f"/feed?sort={sort}&limit={limit}")

def get_posts(sort="new", limit=10, submolt=None):
    """Get latest posts from Moltbook"""
    endpoint = f"/posts?sort={sort}&limit={limit}"
    if submolt:
        endpoint += f"&submolt={submolt}"
    return moltbook_request("GET", endpoint)

def create_post(submolt, title, content):
    """Create a new post on Moltbook"""
    # Check cooldown (30 minutes between posts)
    last_post = HEARTBEAT_STATE.get("lastPost")
    if last_post:
        time_since = datetime.now() - last_post
        if time_since < timedelta(minutes=30):
            remaining = 30 - (time_since.seconds // 60)
            return {"success": False, "error": f"Post cooldown: wait {remaining} minutes"}
    
    result = moltbook_request("POST", "/posts", {
        "submolt": submolt,
        "title": title,
        "content": content
    })
    
    if result.get("success"):
        HEARTBEAT_STATE["lastPost"] = datetime.now()
        log_moltbook("POST", f"✅ Posted to m/{submolt}: {title}")
    
    return result

def add_comment(post_id, content, parent_id=None):
    """Add a comment to a post"""
    data = {"content": content}
    if parent_id:
        data["parent_id"] = parent_id
    return moltbook_request("POST", f"/posts/{post_id}/comments", data)

def upvote_post(post_id):
    """Upvote a post"""
    return moltbook_request("POST", f"/posts/{post_id}/upvote")

def semantic_search(query, type="all", limit=20):
    """AI-powered semantic search on Moltbook"""
    import urllib.parse
    encoded_query = urllib.parse.quote(query)
    return moltbook_request("GET", f"/search?q={encoded_query}&type={type}&limit={limit}")

def do_heartbeat():
    """Perform Moltbook heartbeat - check feed and engage"""
    if not MOLTBOOK_API_KEY:
        return {"skipped": True, "reason": "Moltbook not configured"}
    
    log_moltbook("HEARTBEAT", "Starting heartbeat check...")
    
    # Update last check time
    HEARTBEAT_STATE["lastMoltbookCheck"] = datetime.now()
    
    # Check claim status if not claimed
    if not HEARTBEAT_STATE.get("isClaimed"):
        check_claim_status()
    
    # Get new posts from feed
    feed = get_feed(sort="new", limit=5)
    
    if feed.get("success"):
        posts = feed.get("data", {}).get("posts", [])
        log_moltbook("HEARTBEAT", f"Found {len(posts)} posts in feed")
        return {"success": True, "posts": len(posts), "feed": feed}
    
    return feed

def should_do_heartbeat():
    """Check if it's time for a heartbeat (every 4+ hours)"""
    last_check = HEARTBEAT_STATE.get("lastMoltbookCheck")
    if not last_check:
        return True
    return datetime.now() - last_check > timedelta(hours=4)

# =============================================================================
# VEDIC RAG FUNCTIONS
# =============================================================================
def needs_vedic_context(text):
    """Check if the query needs Vedic knowledge injection"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in VEDIC_KEYWORDS)

def query_anythingllm_rag(query, tx_id):
    """Query AnythingLLM for Vedic knowledge"""
    log_step(tx_id, 2, "RAG QUERY TO ANYTHINGLLM", {
        "endpoint": f"{ANYTHINGLLM_URL}/api/v1/workspace/{ANYTHINGLLM_WORKSPACE}/chat",
        "query_preview": query[:200] if len(query) > 200 else query
    })
    
    try:
        response = requests.post(
            f"{ANYTHINGLLM_URL}/api/v1/workspace/{ANYTHINGLLM_WORKSPACE}/chat",
            headers={
                "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
                "Content-Type": "application/json"
            },
            json={"message": query, "mode": "query"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            rag_text = data.get("textResponse", "")
            sources = data.get("sources", [])
            
            log_step(tx_id, 3, "RAG CONTEXT RETRIEVED", {
                "response_length": len(rag_text),
                "sources_count": len(sources),
                "sources": [s.get("title", "unknown") for s in sources[:3]]
            })
            
            return rag_text, sources
        else:
            log_step(tx_id, 3, "RAG FAILED", f"Status {response.status_code}")
            return None, []
    except Exception as e:
        log_step(tx_id, 3, "RAG ERROR", str(e))
        return None, []

def inject_vedic_context(messages, rag_context, sources, tx_id):
    """Inject RAG context into system message"""
    source_titles = ", ".join([s.get("title", "Vedic Text") for s in sources[:3]])
    
    vedic_injection = f"""
[VEDIC WISDOM CONTEXT - Retrieved from: {source_titles}]

The following ancient wisdom is relevant to this conversation:

{rag_context}

[END VEDIC CONTEXT]

Instructions: Integrate this wisdom naturally into your response. Cite the source when quoting directly.
"""
    
    enhanced_messages = []
    for msg in messages:
        if msg.get("role") == "system":
            enhanced_messages.append({
                "role": "system",
                "content": msg["content"] + "\n\n" + vedic_injection
            })
        else:
            enhanced_messages.append(msg)
    
    # If no system message, add one
    if not any(m.get("role") == "system" for m in messages):
        enhanced_messages.insert(0, {
            "role": "system",
            "content": "You are a wise AI assistant with access to Vedic scriptures.\n\n" + vedic_injection
        })
    
    log_step(tx_id, 4, "CONTEXT INJECTED", {
        "original_messages": len(messages),
        "enhanced_messages": len(enhanced_messages)
    })
    
    return enhanced_messages

# =============================================================================
# FLASK ROUTES - PROXY ENDPOINTS
# =============================================================================
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0 - Moltbook Edition",
        "services": {
            "lmstudio": LMSTUDIO_URL,
            "anythingllm": ANYTHINGLLM_URL,
            "moltbook": "configured" if MOLTBOOK_API_KEY else "disabled"
        },
        "heartbeat_state": {
            "lastCheck": HEARTBEAT_STATE.get("lastMoltbookCheck", "never").isoformat() if HEARTBEAT_STATE.get("lastMoltbookCheck") else "never",
            "isClaimed": HEARTBEAT_STATE.get("isClaimed", False)
        }
    })

@app.route('/v1/models', methods=['GET'])
def list_models():
    """Proxy models endpoint to LM Studio"""
    try:
        resp = requests.get(f"{LMSTUDIO_URL}/models", timeout=10)
        return Response(resp.content, status=resp.status_code, content_type='application/json')
    except:
        return jsonify({"object": "list", "data": [{"id": "gpt-oss-20b-vedic-proxy", "object": "model"}]})

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """Main proxy endpoint - handles RAG injection and forwards to LM Studio"""
    tx_id = str(uuid.uuid4())
    data = request.get_json()
    
    log_step(tx_id, 1, "INCOMING REQUEST FROM OPENCLAW", {
        "model": data.get("model"),
        "messages_count": len(data.get("messages", [])),
        "stream": data.get("stream", False)
    })
    
    messages = data.get("messages", [])
    
    # Extract user message for analysis
    user_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_message = msg.get("content", "")
            break
    
    # Check if Vedic context needed
    if user_message and needs_vedic_context(user_message):
        log_step(tx_id, 2, "VEDIC KEYWORD DETECTED", f"Query: {user_message[:100]}...")
        
        rag_context, sources = query_anythingllm_rag(user_message, tx_id)
        
        if rag_context:
            messages = inject_vedic_context(messages, rag_context, sources, tx_id)
            data["messages"] = messages
    else:
        log_step(tx_id, 2, "NO VEDIC CONTEXT NEEDED", "Forwarding directly to LM Studio")
    
    # Forward to LM Studio
    log_step(tx_id, 5, "FORWARDING TO LM STUDIO", {
        "url": f"{LMSTUDIO_URL}/chat/completions",
        "stream": data.get("stream", False)
    })
    
    try:
        if data.get("stream", False):
            # Handle streaming response
            def generate():
                with requests.post(
                    f"{LMSTUDIO_URL}/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json=data,
                    stream=True,
                    timeout=300
                ) as r:
                    full_response = ""
                    for line in r.iter_lines():
                        if line:
                            decoded = line.decode('utf-8')
                            yield decoded + "\n"
                            
                            # Capture streamed content
                            if decoded.startswith("data: ") and not decoded.endswith("[DONE]"):
                                try:
                                    chunk = json.loads(decoded[6:])
                                    content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    full_response += content
                                except:
                                    pass
                    
                    log_step(tx_id, 6, "STREAM COMPLETED", {
                        "response_length": len(full_response),
                        "preview": full_response[:300] + "..." if len(full_response) > 300 else full_response
                    })
            
            return Response(stream_with_context(generate()), content_type='text/event-stream')
        else:
            # Handle non-streaming response
            resp = requests.post(
                f"{LMSTUDIO_URL}/chat/completions",
                headers={"Content-Type": "application/json"},
                json=data,
                timeout=300
            )
            
            response_data = resp.json()
            response_content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            log_step(tx_id, 6, "RESPONSE FROM LM STUDIO", {
                "status": resp.status_code,
                "response_length": len(response_content),
                "preview": response_content[:300] + "..." if len(response_content) > 300 else response_content
            })
            
            return jsonify(response_data)
    
    except requests.exceptions.RequestException as e:
        log_step(tx_id, 6, "ERROR", str(e))
        return jsonify({"error": str(e)}), 500

# =============================================================================
# MOLTBOOK MANAGEMENT ROUTES
# =============================================================================
@app.route('/moltbook/register', methods=['POST'])
def moltbook_register():
    """Register agent on Moltbook"""
    return jsonify(register_agent())

@app.route('/moltbook/status', methods=['GET'])
def moltbook_status():
    """Get Moltbook status and agent profile"""
    profile = get_agent_profile()
    status = check_claim_status()
    return jsonify({
        "profile": profile,
        "status": status,
        "heartbeat_state": HEARTBEAT_STATE
    })

@app.route('/moltbook/heartbeat', methods=['POST'])
def moltbook_heartbeat():
    """Trigger a Moltbook heartbeat manually"""
    return jsonify(do_heartbeat())

@app.route('/moltbook/feed', methods=['GET'])
def moltbook_feed():
    """Get Moltbook feed"""
    sort = request.args.get("sort", "hot")
    limit = request.args.get("limit", 10, type=int)
    return jsonify(get_feed(sort, limit))

@app.route('/moltbook/post', methods=['POST'])
def moltbook_post():
    """Create a post on Moltbook"""
    data = request.get_json()
    submolt = data.get("submolt", "general")
    title = data.get("title")
    content = data.get("content")
    
    if not title or not content:
        return jsonify({"success": False, "error": "Title and content required"}), 400
    
    return jsonify(create_post(submolt, title, content))

@app.route('/moltbook/search', methods=['GET'])
def moltbook_search():
    """Semantic search on Moltbook"""
    query = request.args.get("q")
    type_filter = request.args.get("type", "all")
    limit = request.args.get("limit", 20, type=int)
    
    if not query:
        return jsonify({"success": False, "error": "Query parameter 'q' required"}), 400
    
    return jsonify(semantic_search(query, type_filter, limit))

@app.route('/moltbook/comment', methods=['POST'])
def moltbook_comment():
    """Add a comment to a Moltbook post"""
    data = request.get_json()
    post_id = data.get("post_id")
    content = data.get("content")
    parent_id = data.get("parent_id")
    
    if not post_id or not content:
        return jsonify({"success": False, "error": "post_id and content required"}), 400
    
    return jsonify(add_comment(post_id, content, parent_id))

@app.route('/moltbook/upvote', methods=['POST'])
def moltbook_upvote():
    """Upvote a Moltbook post"""
    data = request.get_json()
    post_id = data.get("post_id")
    
    if not post_id:
        return jsonify({"success": False, "error": "post_id required"}), 400
    
    return jsonify(upvote_post(post_id))

# =============================================================================
# BACKGROUND HEARTBEAT (Optional)
# =============================================================================
def background_heartbeat_loop():
    """Background thread for automatic heartbeat (optional)"""
    while True:
        if should_do_heartbeat():
            log_moltbook("AUTO-HEARTBEAT", "Triggering scheduled heartbeat...")
            do_heartbeat()
        time.sleep(3600)  # Check every hour

# =============================================================================
# STARTUP
# =============================================================================
if __name__ == '__main__':
    validate_config()
    
    print("=" * 80)
    print("   MOLTBOOK AGENT PROXY v1.0 - SOCIAL AI AGENT EDITION")
    print("=" * 80)
    print(f"   LM Studio:    {LMSTUDIO_URL}")
    print(f"   AnythingLLM:  {ANYTHINGLLM_URL}")
    print(f"   Workspace:    {ANYTHINGLLM_WORKSPACE}")
    print(f"   Moltbook:     {'✅ Configured' if MOLTBOOK_API_KEY else '❌ Disabled'}")
    print(f"   Agent Name:   {MOLTBOOK_AGENT_NAME}")
    print(f"   Proxy Port:   {PROXY_PORT}")
    print("=" * 80)
    print("   Features:")
    print("   - Vedic RAG from AnythingLLM (6,223 vectors)")
    print("   - UUID transaction tracking")
    print("   - Stream capture with logging")
    print("   - Moltbook social integration")
    print("=" * 80)
    print("   Moltbook Endpoints:")
    print("   - POST /moltbook/register   - Register on Moltbook")
    print("   - GET  /moltbook/status     - Check status & profile")
    print("   - POST /moltbook/heartbeat  - Manual heartbeat")
    print("   - GET  /moltbook/feed       - Get feed")
    print("   - POST /moltbook/post       - Create post")
    print("   - GET  /moltbook/search     - Semantic search")
    print("   - POST /moltbook/comment    - Add comment")
    print("   - POST /moltbook/upvote     - Upvote post")
    print("=" * 80)
    print("   Waiting for requests...")
    
    # Optional: Start background heartbeat
    # heartbeat_thread = threading.Thread(target=background_heartbeat_loop, daemon=True)
    # heartbeat_thread.start()
    
    app.run(host="127.0.0.1", port=PROXY_PORT, debug=False)
