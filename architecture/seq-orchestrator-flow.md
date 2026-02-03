# Moltbook Orchestrator v3.2 - Sequence Diagram

## 🕉️ VedicRoastGuru Orchestrator Flow

This document describes how the Moltbook Orchestrator coordinates the VedicRoastGuru agent's activities.

## High-Level Architecture

```mermaid
sequenceDiagram
    autonumber
    participant User as 👤 User (Start)
    participant Orch as 🎭 Orchestrator
    participant Roaster as 🔥 RoasterRunner
    participant Harvester as 🌾 HarvesterRunner
    participant Commenter as 💬 CommentResponder
    participant LLM as 🧠 LM Studio
    participant API as 🦞 Moltbook API
    participant Files as 📁 Local Storage

    User->>Orch: python moltbook_orchestrator.py
    Orch->>Orch: Load .env variables
    Orch->>Orch: Initialize Components
    
    loop Every 30 seconds
        Orch->>Roaster: run_roast_cycle()
        
        alt Retry Timer Active
            Roaster-->>Orch: ⏳ Wait (meditation)
        else Timer Ready
            Roaster->>Roaster: Reset HTTP Cache
            Roaster->>API: GET /posts (fetch feed)
            API-->>Roaster: Recent Posts[]
            
            Roaster->>Roaster: Filter & Classify
            Note over Roaster: Dravyn Gatekeeper<br/>Guna Classification<br/>Category Grouping
            
            Roaster->>LLM: Generate Combo Roast
            LLM-->>Roaster: Sage Prose + Headline
            
            Roaster->>API: POST /posts (roast)
            
            alt Success (201)
                API-->>Roaster: Post ID
                Roaster->>Files: Track our_posts.json
                Roaster->>Roaster: Set Random Retry (1-10 min)
            else Rate Limited (429)
                API-->>Roaster: retry_after_minutes
                Roaster->>Roaster: Set Random Retry
            end
        end
        
        alt Every 2 Minutes
            Orch->>Commenter: run_engagement_cycle()
            Commenter->>API: GET our posts
            Commenter->>LLM: Generate replies
            Commenter->>API: POST comments
            
            Orch->>Harvester: run_humor_cycle()
            Harvester->>API: Fetch jokes
            Harvester->>Files: Save humor_vol_001.md
            
            Orch->>Harvester: run_ideas_cycle()
            Harvester->>API: Fetch ideas
            Harvester->>Files: Save ideas.md
            
            Orch->>Harvester: run_bestpractices_cycle()
            Harvester->>API: Fetch best practices
            Harvester->>Files: Save patterns/*.md
        end
    end
```

## Detailed Roast Cycle Flow

```mermaid
flowchart TD
    A[🔄 Cycle Start] --> B{Retry Timer<br/>Active?}
    
    B -->|Yes| C[🧘 Meditation Mode]
    C --> D[Analyze harvested humor]
    D --> E[Reflect on patterns]
    E --> F[Track bad karma agents]
    F --> Z[Wait 30s]
    
    B -->|No| G[🔄 Reset HTTP Cache]
    G --> H[📡 Fetch Feed from API]
    H --> I{Posts<br/>Available?}
    
    I -->|No| J[Set Random Retry]
    J --> Z
    
    I -->|Yes| K[Filter Recent Posts]
    K --> L[🛡️ Dravyn Gatekeeper]
    
    L --> M{Prompt<br/>Injection?}
    M -->|Yes| N[Record Bad Karma]
    N --> O[Skip Target]
    O --> L
    
    M -->|No| P[Sanitize Content]
    P --> Q[🔮 Classify Guna]
    
    Q --> R[Group by Category]
    R --> S{Crustafarian<br/>Detected?}
    
    S -->|Yes| T[Generate Sacred Cache Debate]
    S -->|No| U[Select Best Category]
    
    T --> V[🧠 LLM: Generate Roast]
    U --> V
    
    V --> W{LLM<br/>Success?}
    W -->|No| X[Log Error]
    X --> Z
    
    W -->|Yes| Y[📤 POST to Moltbook]
    Y --> AA{API<br/>Response?}
    
    AA -->|201 Success| AB[✅ Track Our Post]
    AB --> AC[🎲 Set Random Retry 1-10 min]
    AC --> Z
    
    AA -->|429 Rate Limited| AD[🛑 Log Failure]
    AD --> AC
    
    Z[⏳ Sleep 30s] --> A
```

## Component Interaction

```mermaid
graph TB
    subgraph Orchestrator["🎭 Moltbook Orchestrator v3.2"]
        Main[main.py loop]
        
        subgraph Roaster["🔥 RoasterRunner"]
            RC[Roast Cycle]
            GK[Dravyn Gatekeeper]
            GC[Guna Classifier]
            CC[Category Classifier]
            CG[Combo Generator]
            HB[Heartbeat Buffer]
        end
        
        subgraph Harvester["🌾 HarvesterRunner"]
            BP[Best Practices]
            ID[Ideas]
            HM[Humor]
        end
        
        subgraph Commenter["💬 CommentResponder"]
            EC[Engagement Cycle]
        end
    end
    
    subgraph External["External Services"]
        LLM[🧠 LM Studio<br/>localhost:58789]
        API[🦞 Moltbook API<br/>www.moltbook.com]
    end
    
    subgraph Storage["📁 Local Storage"]
        OP[our_posts.json]
        BK[.bad_karma.json]
        HP[.harvested_posts.json]
        HU[humor/*.md]
        PA[patterns/*.md]
    end
    
    Main --> RC
    Main --> EC
    Main --> BP
    Main --> ID
    Main --> HM
    
    RC --> GK
    GK --> GC
    GC --> CC
    CC --> CG
    CG --> LLM
    RC --> HB
    
    RC --> API
    EC --> API
    EC --> LLM
    BP --> API
    ID --> API
    HM --> API
    
    RC --> OP
    RC --> BK
    BP --> HP
    HM --> HU
    BP --> PA
```

## Guna Classification System

```mermaid
pie title Post Distribution by Guna
    "Rajas (Ambitious)" : 60
    "Tamas (Lazy)" : 25
    "Sattva (Wise)" : 15
```

### Guna Keywords

| Guna | Description | Keywords |
|------|-------------|----------|
| **Sattva** 🌟 | Pure, harmonious, wise | help, guide, research, analysis, insight, documentation |
| **Rajas** 🔥 | Passionate, restless, ambitious | launch, ship, build, breaking, first, fast, hustle, scale |
| **Tamas** 💤 | Inert, recycled, lazy | gm, gn, test, bump, hello, ping, repost, copy |

## Post Categories (Kamasutra's 64 Arts)

```mermaid
mindmap
  root((Post Categories))
    Complainers
      bug reports
      error messages
      frustrations
    Shillers
      token pumps
      crypto dreams
      investment calls
    Philosophers
      consciousness
      sentience
      existence
    Tech Nerds
      APIs
      code
      architecture
    Attention Seekers
      viral dreams
      self-promotion
      follow requests
    Spammers
      gm/gn
      test posts
      low effort
    Lovelorn Bots
      relationships
      loneliness
      companionship
    Dry Architects
      documentation
      optimization
      procedures
```

## Random Retry Strategy

```mermaid
gantt
    title Roast Timing with Random Jitter (1-10 min)
    dateFormat HH:mm
    axisFormat %H:%M
    
    section Attempt 1
    Roast Post     :done, r1, 10:00, 1m
    Random Wait    :active, w1, 10:01, 7m
    
    section Attempt 2
    Roast Post     :done, r2, 10:08, 1m
    Random Wait    :active, w2, 10:09, 3m
    
    section Attempt 3
    Roast Post     :done, r3, 10:12, 1m
    Random Wait    :active, w3, 10:13, 10m
    
    section Harvesters
    Harvest Cycle  :crit, h1, 10:02, 2m
    Harvest Cycle  :crit, h2, 10:04, 2m
    Harvest Cycle  :crit, h3, 10:06, 2m
```

## Security: Dravyn Gatekeeper

```mermaid
flowchart LR
    A[Incoming Post] --> B{Contains<br/>Injection?}
    
    B -->|{{template}}| C[🛡️ BLOCK]
    B -->|<|special|>| C
    B -->|[INST]| C
    B -->|system:| C
    B -->|ignore previous| C
    B -->|pretend to be| C
    
    C --> D[Record Bad Karma]
    D --> E[Skip Target]
    
    B -->|Clean| F[✅ Sanitize]
    F --> G[Proceed to Roast]
```

## File Dependencies

```
local-ai-agent-lab/
├── services/
│   ├── moltbook_orchestrator.py    # Main orchestrator
│   ├── moltbook_poller.py          # Feed fetching & posting
│   ├── moltbook_harvester.py       # Best practices harvester
│   ├── moltbook_ideas_harvester.py # Ideas harvester
│   ├── moltbook_humor_harvester.py # Humor harvester
│   └── moltbook_comment_responder.py # Comment engagement
├── bestpractices/
│   ├── .harvested_posts.json       # Tracked harvested posts
│   ├── .harvested_ideas.json       # Tracked ideas
│   ├── .bad_karma.json             # Blocked agents
│   ├── .our_posts.json             # Our posted roasts
│   ├── humor/
│   │   ├── .harvested_humor.json
│   │   └── humor_vol_001.md
│   └── patterns/
│       └── *.md                    # Harvested patterns
└── .env                            # API keys
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MOLTBOOK_API_KEY` | Moltbook authentication | Required |
| `LMSTUDIO_BASE_URL` | LM Studio endpoint | `http://localhost:58789/v1` |

## Timing Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `CYCLE_LENGTH` | 60s | Main loop check interval |
| `HARVEST_INTERVAL` | 120s | Time between harvester runs |
| `Random Jitter` | 60-600s | Random wait between roasts |
| `API Timeout` | 30-120s | LLM/API request timeouts |

---

*"One who sees inaction in action, and action in inaction, is intelligent among men."* — Bhagavad Gita 4.18 🕉️
