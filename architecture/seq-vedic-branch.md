# Vedic Branch - RAG Pipeline

OpenClaw → Vedic RAG Proxy → AnythingLLM (RAG) → LM Studio

Adds Retrieval-Augmented Generation from Vedic scriptures (Gita, Vedas, Puranas, Kama Sutra).

## Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant OpenClaw
    participant Proxy as Vedic RAG Proxy<br/>(Port 58790)
    participant AnythingLLM as AnythingLLM<br/>(6,223 vectors)
    participant LMStudio as LM Studio<br/>(GPT OSS 20B)

    User->>OpenClaw: "What does Gita say about stress?"
    activate OpenClaw
    
    OpenClaw->>Proxy: POST /v1/chat/completions
    activate Proxy
    
    Note over Proxy: Step 1: Parse request<br/>Generate UUID transaction ID
    
    Note over Proxy: Step 2: Detect Vedic keywords<br/>"stress" ✓ "gita" ✓
    
    Proxy->>AnythingLLM: POST /api/v1/workspace/my-workspace/chat<br/>{"message": "stress in Gita", "mode": "query"}
    activate AnythingLLM
    
    Note over AnythingLLM: Search 6,223 vectors<br/>Retrieve relevant passages
    
    AnythingLLM-->>Proxy: RAG Context + Sources<br/>(Bhagavad Gita passages)
    deactivate AnythingLLM
    
    Note over Proxy: Step 4: Inject context<br/>into system message
    
    Proxy->>LMStudio: POST /v1/chat/completions<br/>(Enhanced with Vedic context)
    activate LMStudio
    
    Note over LMStudio: Generate response<br/>with Vedic wisdom
    
    LMStudio-->>Proxy: Stream response
    deactivate LMStudio
    
    Note over Proxy: Step 6: Log response<br/>with transaction ID
    
    Proxy-->>OpenClaw: Stream enhanced response
    deactivate Proxy
    
    OpenClaw-->>User: Vedic wisdom answer<br/>with source citations
    deactivate OpenClaw
```

## Configuration

```yaml
# Environment variables
LMSTUDIO_BASE_URL: http://172.28.176.1:58789/v1
ANYTHINGLLM_BASE_URL: http://localhost:3001
ANYTHINGLLM_API_KEY: <your-api-key>
ANYTHINGLLM_WORKSPACE: my-workspace
VEDIC_PROXY_PORT: 58790
```

## Ports

| Service | Port | URL |
|---------|------|-----|
| OpenClaw | 18789 | http://localhost:18789 |
| Vedic RAG Proxy | 58790 | http://127.0.0.1:58790 |
| AnythingLLM | 3001 | http://localhost:3001 |
| LM Studio | 58789 | http://172.28.176.1:58789/v1 |

## Vedic Keywords (Trigger RAG)

```python
VEDIC_KEYWORDS = [
    "relationship", "marriage", "love", "kama", "sutra", "dharma", "karma",
    "vedic", "gita", "bhagavad", "veda", "purana", "upanishad", "scripture",
    "spiritual", "meditation", "peace", "anger", "attachment", "duty",
    "stressed", "interview", "job", "partner", "drifting", "depressed"
]
```

## Use Case

Perfect for spiritual guidance, life advice, relationship questions, and Vedic philosophy discussions.
