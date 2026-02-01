#!/usr/bin/env python3
"""
Vedic RAG Proxy Server v3.3 - STRICT COMPLIANCE EDITION
Features: UUID Tracking, Stream Capture, Verbose Logging, OpenAI API Spec Compliance
"""

import json
import os
import uuid
import requests
from datetime import datetime
from flask import Flask, request, Response, stream_with_context

app = Flask(__name__)

# Configuration
LMSTUDIO_URL = os.getenv("LMSTUDIO_BASE_URL", "http://172.28.176.1:58789/v1")
ANYTHINGLLM_URL = os.getenv("ANYTHINGLLM_BASE_URL", "http://localhost:3001")
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY", "K6BHF4K-Z88400F-QRB6SDB-EK2SN6S")
ANYTHINGLLM_WORKSPACE = os.getenv("ANYTHINGLLM_WORKSPACE", "my-workspace")
PROXY_PORT = int(os.getenv("VEDIC_PROXY_PORT", "58790"))

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

def log_step(tx_id, step_num, title, content):
    """Print formatted step log with transaction ID"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print("\n" + "="*80)
    print(f"[{tx_id}] [{timestamp}] STEP {step_num}: {title}")
    print("="*80)
    if isinstance(content, dict) or isinstance(content, list):
        print(json.dumps(content, indent=2, default=str)[:3000])
    else:
        print(str(content)[:3000])
    print("-"*80)

def get_text_content(content):
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                texts.append(item.get("text", ""))
            elif isinstance(item, str):
                texts.append(item)
        return " ".join(texts)
    return ""

def should_query_rag(messages):
    text = " ".join([get_text_content(m.get("content", "")) for m in messages]).lower()
    return any(keyword in text for keyword in VEDIC_KEYWORDS)

def query_anythingllm_chat(question, tx_id):
    """Query AnythingLLM chat endpoint to get RAG context"""
    try:
        headers = {
            "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "message": question,
            "mode": "query"
        }

        log_step(tx_id, 2, "RAG RETRIEVAL REQUEST", {
            "url": f"{ANYTHINGLLM_URL}/api/v1/workspace/{ANYTHINGLLM_WORKSPACE}/chat",
            "payload": payload
        })
        
        response = requests.post(
            f"{ANYTHINGLLM_URL}/api/v1/workspace/{ANYTHINGLLM_WORKSPACE}/chat",
            json=payload,
            headers=headers,
            timeout=120
        )
        response.raise_for_status()

        data = response.json()
        answer = data.get("textResponse", "")
        sources = data.get("sources", [])
        
        log_step(tx_id, "2b", "RAG RESPONSE RECEIVED", {
            "answer_length": len(answer),
            "sources_count": len(sources),
            "sources": [s.get("title", "unknown") for s in sources],
            "preview": answer[:500]
        })
        
        if answer and "no relevant information" not in answer.lower():
            return f"""
## Vedic Wisdom Context (Use this to answer, but DO NOT cite pages)

{answer}

---
**STYLE INSTRUCTION:** Talk casually like Reddit. Refer to texts naturally ("The Gita says..."). Do NOT use brackets or citations.
"""
        return None
    except Exception as e:
        log_step(tx_id, "2-ERROR", "RAG FAILURE (FAIL-OPEN)", str(e))
        return None

def enhance_messages_with_rag(messages, tx_id):
    if not messages: return messages
    user_messages = [m for m in messages if m.get("role") == "user"]
    if not user_messages: return messages

    last_user_msg = get_text_content(user_messages[-1].get("content", ""))
    rag_context = query_anythingllm_chat(last_user_msg, tx_id)

    if rag_context:
        enhanced = []
        has_system = False
        for msg in messages:
            if msg.get("role") == "system":
                has_system = True
                enhanced.append({"role": "system", "content": msg.get("content", "") + "\n\n" + rag_context})
            else:
                enhanced.append(msg)
        if not has_system:
            enhanced.insert(0, {"role": "system", "content": rag_context})
        return enhanced
    return messages

@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    # 0. Generate Transaction ID
    tx_id = str(uuid.uuid4())[:8]
    start_time = datetime.now()
    
    print("\n" + "#"*80)
    print(f"### NEW REQUEST - TXN: {tx_id} - Time: {start_time.strftime('%H:%M:%S')}")
    print("#"*80)
    
    data = request.json
    messages = data.get("messages", [])

    # STEP 1: Log incoming request
    log_step(tx_id, 1, "INCOMING REQUEST FROM OPENCLAW", messages)

    if should_query_rag(messages):
        log_step(tx_id, "1b", "VEDIC INTENT DETECTED", "Triggering RAG pipeline...")
        data["messages"] = enhance_messages_with_rag(messages, tx_id)
        
        # STEP 3: Log merged prompt
        log_step(tx_id, 3, "MERGED PROMPT (USER + RAG)", data["messages"])
    else:
        log_step(tx_id, "1b", "STANDARD QUERY", "Skipping RAG pipeline.")

    # STEP 4: Request to LM Studio
    log_step(tx_id, 4, "FORWARDING TO LM STUDIO", {
        "url": f"{LMSTUDIO_URL}/chat/completions",
        "model": data.get("model", "default"),
        "stream": data.get("stream", False)
    })

    try:
        is_streaming = data.get("stream", False)
        
        response = requests.post(
            f"{LMSTUDIO_URL}/chat/completions",
            json=data,
            headers={"Content-Type": "application/json"},
            stream=is_streaming,  # Only stream if client requested it
            timeout=300
        )

        if is_streaming:
            # Generator to spy on the stream
            def generate_and_log():
                full_response_buffer = []
                try:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            # Yield to client immediately
                            yield chunk
                            
                            # Capture for logs
                            try:
                                text = chunk.decode('utf-8')
                                full_response_buffer.append(text)
                            except:
                                pass
                finally:
                    # STEP 5: Log the full capture when stream ends
                    raw_log = "".join(full_response_buffer)
                    duration = (datetime.now() - start_time).total_seconds()
                    log_step(tx_id, 5, "STREAM COMPLETE (RESPONSE LOG)", {
                        "duration_seconds": duration,
                        "length_bytes": len(raw_log),
                        "raw_preview": raw_log[:2000] + "..." if len(raw_log) > 2000 else raw_log
                    })
                    print(f"\n### REQUEST COMPLETE - TXN: {tx_id} - Duration: {duration:.2f}s ###\n")

            return Response(stream_with_context(generate_and_log()), 
                          content_type=response.headers.get("Content-Type", "text/event-stream"))
        else:
            # Non-streaming: Return proper JSON per OpenAI API spec
            result = response.json()
            duration = (datetime.now() - start_time).total_seconds()
            
            # Extract response content for logging
            lm_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = result.get("usage", {})
            
            log_step(tx_id, 5, "JSON RESPONSE (NON-STREAMING)", {
                "duration_seconds": duration,
                "tokens": usage,
                "response_length": len(lm_response),
                "response_preview": lm_response[:2000] if lm_response else "NO RESPONSE"
            })
            print(f"\n### REQUEST COMPLETE - TXN: {tx_id} - Duration: {duration:.2f}s ###\n")
            
            return result

    except Exception as e:
        log_step(tx_id, "ERROR", "PROXY FAILURE", str(e))
        return {"error": str(e)}, 500

@app.route("/v1/models", methods=["GET"])
def list_models():
    try:
        response = requests.get(f"{LMSTUDIO_URL}/models", timeout=30)
        return response.json()
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "service": "vedic-rag-proxy", "version": "3.3-strict-compliance"}

@app.route("/", methods=["GET"])
def index():
    return {"service": "Vedic RAG Proxy", "version": "3.3", "mode": "strict-compliance-edition"}

if __name__ == "__main__":
    print("\n" + "="*80)
    print("   VEDIC RAG PROXY v3.3 - STRICT COMPLIANCE EDITION")
    print("="*80)
    print(f"   LM Studio:    {LMSTUDIO_URL}")
    print(f"   AnythingLLM:  {ANYTHINGLLM_URL}")
    print(f"   Workspace:    {ANYTHINGLLM_WORKSPACE}")
    print(f"   Proxy Port:   {PROXY_PORT}")
    print("="*80)
    print("\n   Features:")
    print("   - UUID Transaction Tracking")
    print("   - Stream Capture & Logging")
    print("   - Full Request/Response Audit Trail")
    print("   - OpenAI API Spec Compliance (stream: true/false)")
    print("="*80)
    print("\n   Waiting for requests...\n")
    app.run(host="0.0.0.0", port=PROXY_PORT, debug=False, threaded=True)
