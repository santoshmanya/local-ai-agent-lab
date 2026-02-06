# Main Branch - Direct LLM Flow

## Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant OpenClaw
    participant LMStudio as LM Studio<br/>(GPT OSS 20B)
    
    User->>OpenClaw: Ask question
    Note over OpenClaw: Port 18789
    OpenClaw->>LMStudio: POST /v1/chat/completions
    Note over LMStudio: Port 58789
    LMStudio-->>OpenClaw: Stream response
    OpenClaw-->>User: Display answer
```

## Components

| Component | Port | Description |
|-----------|------|-------------|
| OpenClaw | 18789 | AI Assistant UI (Docker) |
| LM Studio | 58789 | GPT OSS 20B inference |

## Flow Description

1. **User** sends a question via OpenClaw web UI
2. **OpenClaw** forwards request directly to LM Studio
3. **LM Studio** processes with GPT OSS 20B model
4. Response streams back to user

## Generated Diagram

![Main Branch Flow](../images/seq-main-branch.png)
