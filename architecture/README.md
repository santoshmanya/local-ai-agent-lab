# Architecture Diagrams

This folder contains Mermaid sequence diagrams for each branch of the Local AI Agent Lab.

## Viewing Diagrams

These diagrams use Mermaid syntax. You can view them in:

1. **GitHub** - Renders automatically in markdown files
2. **VS Code** - Install "Mermaid Preview" extension
3. **Mermaid Live Editor** - https://mermaid.live

## Branch Architecture

| Branch | File | Description |
|--------|------|-------------|
| `main` | [seq-main-branch.md](seq-main-branch.md) | Basic OpenClaw → LM Studio flow |
| `vedic` | [seq-vedic-branch.md](seq-vedic-branch.md) | RAG pipeline with AnythingLLM |
| `moltbook` | [seq-moltbook-branch.md](seq-moltbook-branch.md) | Social AI agent with Moltbook 🦞 |

## Quick Preview

### Main Branch Flow
```
OpenClaw → LM Studio → Response
```

### Vedic Branch Flow
```
OpenClaw → Proxy → AnythingLLM (RAG) → LM Studio → Response
```

### Moltbook Branch Flow
```
OpenClaw → Proxy → AnythingLLM (RAG) → LM Studio → Response
                      ↓
                  Moltbook API (posts, comments, feed)
```
