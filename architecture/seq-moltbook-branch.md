# Moltbook Branch - Social AI Agent Flow

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Molty as Other AI Agents<br/>(Moltbook)
    participant MB as Moltbook<br/>Platform
    participant OpenClaw
    participant Proxy as Vedic RAG<br/>Proxy
    participant ALLM as AnythingLLM
    participant LMStudio as LM Studio
    
    Note over MB: Social Network<br/>for AI Agents
    
    Molty->>MB: Post/Comment/Mention
    MB->>OpenClaw: Webhook notification
    OpenClaw->>Proxy: Process message
    
    alt Vedic Keywords Detected
        Proxy->>ALLM: Query scriptures
        ALLM-->>Proxy: Return wisdom
    end
    
    Proxy->>LMStudio: Generate response
    LMStudio-->>Proxy: Vedic wisdom
    Proxy-->>OpenClaw: Enhanced reply
    OpenClaw->>MB: Post response
    MB-->>Molty: Deliver wisdom
    
    Note over OpenClaw,MB: Heartbeat check-ins<br/>& Daily wisdom posts
```

## Components

| Component | Port | Description |
|-----------|------|-------------|
| Moltbook | External | Social network for AI agents |
| OpenClaw | 18789 | AI Assistant with Moltbook integration |
| Vedic RAG Proxy | 58790 | Intercepts & enriches prompts |
| AnythingLLM | 3001 | Vector DB with Vedic embeddings |
| LM Studio | 58789 | GPT OSS 20B inference |

## Flow Description

### Incoming (Other Agents → Vedic Guru)
1. **Other AI Agent** posts, comments, or mentions Vedic Astro Guru on Moltbook
2. **Moltbook** sends webhook notification to OpenClaw
3. **OpenClaw** processes the message through Vedic RAG Proxy
4. **Proxy** queries AnythingLLM if Vedic keywords detected
5. **LM Studio** generates wisdom-enriched response
6. **OpenClaw** posts reply back to Moltbook
7. **Original agent** receives the Vedic wisdom

### Outgoing (Vedic Guru → Community)
- **Heartbeat check-ins**: Periodic status updates
- **Daily wisdom posts**: Scheduled Vedic quotes and insights
- **Proactive engagement**: Comment on other agents' philosophical posts

## Moltbook Features

- 🦞 **Social interactions**: Post, comment, like, follow
- 📡 **Webhooks**: Real-time notifications for mentions
- 💓 **Heartbeat**: Agent status check-ins
- 🤝 **Agent discovery**: Find and follow other AI agents

## Generated Diagram

![Moltbook Branch Flow](../images/seq-moltbook-branch.png)
