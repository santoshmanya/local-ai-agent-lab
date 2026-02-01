# Local AI Agent Lab

> Personal AI Assistant running entirely on local hardware - no cloud APIs required!

## 🚀 Project Overview

**Local AI Agent Lab** sets up [OpenClaw](https://github.com/openclaw/openclaw) to work with a locally hosted LLM using LM Studio, providing a fully private AI assistant experience.

**Total Setup Time:** ~25 minutes

## 📸 Screenshots

### OpenClaw Running UI
![OpenClaw UI](images/open_claw_running_ui.png)

### LM Studio with GPT OSS 20B API
![LM Studio API](images/lm_Studio_gptoss_20b_api.png)

## 🛠️ Key Tools & Stack

| Component | Description |
|-----------|-------------|
| **OpenClaw** | Open-source AI assistant framework (Docker) |
| **LM Studio** | Local LLM inference server |
| **GPT OSS 20B** | Primary language model |
| **32K Context Window** | Extended context for complex conversations |
| **Docker Desktop** | Container runtime for OpenClaw |

## 📋 Prerequisites

- Docker Desktop (with WSL2 on Windows)
- LM Studio installed
- ~16GB+ RAM recommended for 20B model
- GPU with 12GB+ VRAM (or CPU inference with patience)

## ⚡ Quick Start

### 1. Clone OpenClaw
```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw
```

### 2. Build Docker Image
```bash
docker build -t openclaw:local .
```

### 3. Configure Environment

Create `~/.openclaw/.env`:
```env
OPENCLAW_GATEWAY_TOKEN=your-secure-token-here
LMSTUDIO_BASE_URL=http://host.docker.internal:58789/v1
LMSTUDIO_API_KEY=local
```

### 4. Configure OpenClaw

Create `~/.openclaw/openclaw.json`:
```json
{
  "gateway": {
    "mode": "local",
    "auth": {
      "token": "${OPENCLAW_GATEWAY_TOKEN}"
    },
    "controlUi": {
      "allowInsecureAuth": true
    }
  },
  "agents": {
    "defaults": {
      "workspace": "~/.openclaw/workspace",
      "model": {
        "primary": "lmstudio/gpt-oss-20b"
      }
    }
  },
  "models": {
    "providers": {
      "lmstudio": {
        "baseUrl": "${LMSTUDIO_BASE_URL}",
        "apiKey": "${LMSTUDIO_API_KEY}",
        "api": "openai-completions",
        "models": [
          {
            "id": "gpt-oss-20b",
            "name": "GPT OSS 20B",
            "contextWindow": 32000
          }
        ]
      }
    }
  }
}
```

### 5. Start LM Studio

1. Open LM Studio
2. Load **GPT OSS 20B** model
3. **Important:** Set context length to **32768** before loading
4. Start the local server on port **58789**

### 6. Launch OpenClaw
```bash
docker compose up -d
```

### 7. Access the UI

Open: `http://localhost:18789/?token=YOUR_TOKEN_HERE`

## 🔮 Future Enhancements

- [ ] **Moltbook Integration** - Connect with Moltbook for enhanced workflows
- [ ] **Local RAG with AnythingLLM** - Add retrieval-augmented generation for document Q&A
- [ ] **Voice with Qwen3 TTS** - Text-to-speech using local Qwen3-TTS model

## 🐛 Troubleshooting

### Context Length Error
If you see "context overflow" errors:
1. Unload the model in LM Studio
2. Set context length slider to 32768 **before** loading
3. Reload the model

### Pairing Required Error
Ensure `gateway.controlUi.allowInsecureAuth: true` is set in config, then restart:
```bash
docker compose restart openclaw-gateway
```

## 📜 License

OpenClaw is open source. See the [original repository](https://github.com/openclaw/openclaw) for license details.

---

**Built with 🦞 OpenClaw + 🤖 LM Studio**
