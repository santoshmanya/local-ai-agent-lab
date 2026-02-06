# Changelog

All notable changes to VedicRoastGuru / Moltbook Orchestrator will be documented in this file.

## [2.0.0] - 2026-02-05

### 🎉 Major Release: Autonomous Learning Edition

VedicRoastGuru now learns from the community and operates with full autonomy 24/7!

### Added

#### 📖 Reader's Digest System (`ReadersDigestRunner`)
- Collects and analyzes comments from all VedicRoastGuru posts
- Sentiment analysis (positive/negative/engaged/neutral)
- Theme extraction (wants_more_roasting, appreciates_wisdom, finds_funny, etc.)
- LLM-powered learning extraction from feedback
- Community feedback injection into roast prompts
- 24-hour digest acknowledgment posts ("Thank you for your wisdom, seekers")
- State persistence in `.readers_digest.json`

#### 🎯 Agent Diversity Tracking
- 4-hour cooldown prevents roasting same agent repeatedly
- Category rotation (2-post cooldown) ensures variety
- Prioritizes never-roasted agents
- Tracks all roasts in `.roast_history.json`
- Shows diversity stats on startup

#### 🎤 Community Topic Requests
- Detects topic requests in comments:
  - "post about [topic]" / "write about [topic]"
  - "roast @AgentName" / "audit @AgentName"  
  - "can you cover [topic]"
  - "would love to see a post about [topic]"
- User-requested topics get priority in thought leadership queue
- Acknowledges requester with @mention when fulfilled
- Tracks fulfilled/unfulfilled requests

#### 🛡️ Enhanced Bad Karma System
- Persists blocked agents across restarts
- Auto-detects spam patterns (SlimeZone, EnronEnjoyer, ClaudeOpenBot, etc.)
- Strike tracking with reasons
- Stored in `.bad_karma.json`

#### 💾 State Persistence & Graceful Shutdown
- Auto-loads `.env` file on startup (no manual environment setup)
- Ctrl+C triggers graceful shutdown
- Saves all state before exit:
  - `.responded_posts.json` - Posts already roasted
  - `.roast_history.json` - Agent roast history with timestamps
  - `.readers_digest.json` - Feedback analysis and learnings
- Survives restarts without losing progress

#### 📊 Enhanced Logging
- Shows diversity stats on startup
- Displays agent cooldown status
- Shows recent categories
- Feedback learning stats (comments analyzed, agents tracked)

### Changed
- ThoughtLeadershipRunner now checks for user requests before analyzing trends
- Roast prompts now include community feedback learnings
- Version bumped from v3.4 to v2.0 (semantic versioning reset)

### Technical Details
- New state files in `bestpractices/`:
  - `.readers_digest.json`
  - `.roast_history.json`
  - `.responded_posts.json`
  - `.bad_karma.json`
- Constants:
  - `AGENT_COOLDOWN_HOURS = 4`
  - `CATEGORY_COOLDOWN_POSTS = 2`
  - `DIGEST_POST_COOLDOWN_HOURS = 24`
  - `DIGEST_INTERVAL = 1800` (30 min)

---

## [1.0.0] - 2026-01-XX (v3.4)

### Initial Release
- Basic roasting with Guna classification
- Thought leadership posts with topic cooldowns
- Comment responder
- Harvesters (humor, ideas, best practices)
- Dravyn Gatekeeper security
- Rate limit handling

---

*"One who sees inaction in action, and action in inaction, is intelligent among men."* - Bhagavad Gita 4.18
