# Local AI Agent Lab - Vedic RAG Edition 🕉️

> Personal AI Assistant with RAG-powered Vedic Wisdom - running entirely on local hardware!

## 🌿 Branch Overview

This project has **3 versions** for different use cases:

| Branch | Description | Use Case |
|--------|-------------|----------|
| **main** | OpenClaw + LM Studio (direct) | Basic local LLM, no RAG |
| **edic** ⭐ | OpenClaw + AnythingLLM RAG | Focused Vedic wisdom responses |
| **moltbook** | Moltbook social integration | AI agent on social network |

**You are on the edic branch** - This adds RAG-powered responses from 30+ Vedic texts!

## 🚀 What's Different in Vedic Branch?

This branch adds a **RAG Proxy** that:
- ✅ Intercepts OpenClaw requests
- ✅ Detects Vedic-related questions (relationships, karma, dharma, astrology, etc.)
- ✅ Queries AnythingLLM for relevant scripture context
- ✅ Injects wisdom into the prompt before LM Studio responds
- ✅ Maintains casual "Reddit-style" tone while citing texts naturally

## 📸 Screenshots

### Vedic RAG Q&A in Action
![Vedic RAG Q&A](images/open_claw_vedic_astro_qa.png)

### OpenClaw Running UI
![OpenClaw UI](images/open_claw_running_ui.png)

### LM Studio with GPT OSS 20B API
![LM Studio API](images/lm_Studio_gptoss_20b_api.png)

## 🏗️ Architecture

`
┌─────────────────────────────────────────────────────────────────┐
│                  VEDIC RAG PIPELINE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────┐     ┌────────────────┐     ┌─────────────────┐  │
│   │ OpenClaw │────►│ Vedic RAG      │────►│   LM Studio     │  │
│   │  :18789  │     │ Proxy :58790   │     │   :58789        │  │
│   └──────────┘     └───────┬────────┘     └─────────────────┘  │
│                            │                                    │
│                            ▼                                    │
│                    ┌───────────────┐                           │
│                    │ AnythingLLM   │                           │
│                    │   :3001       │                           │
│                    │               │                           │
│                    │ 30+ Vedic     │                           │
│                    │ PDFs indexed  │                           │
│                    │ 6,223 vectors │                           │
│                    └───────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
`

## 🛠️ Components

| Component | Port | Description |
|-----------|------|-------------|
| **OpenClaw** | 18789 | AI Assistant UI (Docker) |
| **Vedic RAG Proxy** | 58790 | Intercepts & enriches prompts |
| **LM Studio** | 58789 | GPT OSS 20B inference |
| **AnythingLLM** | 3001 | Vector DB + RAG |

## ⚡ Quick Start (Vedic Branch)

### Prerequisites
- All components from main branch setup
- AnythingLLM running with Vedic documents indexed

### 1. Start AnythingLLM
Ensure AnythingLLM is running on port 3001 with your Vedic workspace.

### 2. Start the Vedic RAG Proxy
`ash
cd services
$env:LMSTUDIO_BASE_URL="http://172.28.176.1:58789/v1"
$env:ANYTHINGLLM_API_KEY="your-api-key"
python vedic_rag_proxy.py
`

### 3. Update OpenClaw to use Proxy
In `~/.openclaw/.env`:
`env
LMSTUDIO_BASE_URL=http://host.docker.internal:58790/v1
`

### 4. Restart OpenClaw
`ash
docker compose restart openclaw-gateway
`

### 5. Ask Vedic Questions!
Open `http://localhost:18789/?token=YOUR_TOKEN` and ask:
- "My partner and I are drifting apart. What should I do?"
- "What does the Gita say about attachment?"
- "I'm stressed about my interview tomorrow"

## 📚 Indexed Vedic Texts

The AnythingLLM workspace contains embeddings from:
- 📖 Bhagavad Gita (multiple translations)
- 🕉️ Vedas (Rig, Sama, Yajur, Atharva)
- 📜 Upanishads (13+ major texts)
- 🙏 Puranas (Vishnu, Shiva, etc.)
- 💕 Kama Sutra (Vatsyayana)
- ⭐ Vedic Astrology texts

**Total:** 6,223 vectors indexed

## 🔍 RAG Keyword Triggers

The proxy detects these keywords to trigger RAG:
- Relationships: `relationship`, `marriage`, `love`, `partner`, `husband`, `wife`
- Spirituality: `dharma`, `karma`, `soul`, `meditation`, `peace`
- Scriptures: `gita`, `veda`, `purana`, `upanishad`
- Astrology: `nakshatra`, `birth star`, `horoscope`
- Life: `stressed`, `job`, `interview`, `depressed`

## 📊 Proxy Logging

The Vedic RAG Proxy v3.3 includes full observability:
- **UUID Transaction Tracking** - Each request gets a unique ID
- **5-Step Audit Trail:**
  1. Incoming request from OpenClaw
  2. RAG retrieval from AnythingLLM
  3. Merged prompt (user + context)
  4. Forward to LM Studio
  5. Response capture
- **Stream/JSON Compliance** - Proper OpenAI API spec handling

## 💬 Sample Q&A

**User:** "My partner and I are drifting apart. What should I do?"

**Vedic RAG Response:**
> Hey, glad you're reaching out! Here's what ancient wisdom says...
> The Gita reminds us that attachment to outcomes creates suffering.
> Focus on what you can control - your own actions and growth.
> The Kama Sutra emphasizes that intimacy isn't just physical...
> [continues with actionable advice grounded in texts]

## 🐛 Troubleshooting (Vedic Branch)

### Proxy Not Starting
`ash
# Check if port is in use
netstat -ano | findstr :58790

# Kill existing Python processes
Stop-Process -Name python -Force
`

### No RAG Context Returned
1. Check AnythingLLM is running: `http://localhost:3001`
2. Verify workspace name matches: `my-workspace`
3. Check API key is correct

### OpenClaw Not Using Proxy
1. Verify `.env` points to port 58790
2. Restart OpenClaw gateway after changes
3. Check proxy logs for incoming requests

---

## 📜 License

OpenClaw is open source. See the [original repository](https://github.com/openclaw/openclaw) for license details.

---

**Built with 🦞 OpenClaw + 🤖 LM Studio + 📚 AnythingLLM + 🕉️ Vedic Wisdom**

*Switch to main branch for basic setup, or moltbook branch for social integration.*
