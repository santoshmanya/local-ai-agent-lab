# Architecture Documentation

This folder contains sequence diagrams for each branch of the Local AI Agent Lab.

## Diagrams

| File | Branch | Description |
|------|--------|-------------|
| [seq-main-branch.md](seq-main-branch.md) | `main` | Direct OpenClaw → LM Studio flow |
| [seq-vedic-branch.md](seq-vedic-branch.md) | `vedic` | RAG-powered flow with AnythingLLM |
| [seq-moltbook-branch.md](seq-moltbook-branch.md) | `moltbook` | Social AI agent with Moltbook |

## How to Generate Images

1. Copy the Mermaid code from each `.md` file
2. Paste into [Mermaid Live Editor](https://mermaid.live/)
3. Export as PNG
4. Save to `images/` folder with matching name:
   - `seq-main-branch.png`
   - `seq-vedic-branch.png`
   - `seq-moltbook-branch.png`

## Branch Comparison

| Branch | Components | Use Case |
|--------|------------|----------|
| `main` | OpenClaw + LM Studio | Basic local LLM |
| `vedic` ⭐ | + AnythingLLM RAG Proxy | Vedic wisdom responses |
| `moltbook` | + Moltbook integration | Social AI agent |
