# 🛡️ Security Best Practices Guide

## The Vedic Security Sutra

> *"Just as a yogi protects their prana (life force), a developer must protect their secrets."*
> — DevOps Upanishad

This guide establishes security standards for the Local AI Agent Lab project.

---

## 🚨 The Cardinal Rules

### 1. NEVER Hardcode Secrets
```python
# ❌ WRONG - This will be stolen
API_KEY = "moltbook_sk_abc123xyz789"

# ✅ CORRECT - Environment variable
API_KEY = os.getenv("API_KEY")
```

### 2. ALWAYS Validate Before Running
```python
if not API_KEY:
    print("🚨 ERROR: API_KEY not set!")
    exit(1)
```

### 3. NEVER Commit `.env` Files
```gitignore
# .gitignore - ALWAYS include these
.env
.env.local
.env.production
*.key
*.pem
secrets/
```

---

## 🔐 Environment Variable Management

### Setting Variables (PowerShell)
```powershell
# Session-only (disappears when terminal closes)
$env:MOLTBOOK_API_KEY="your-key-here"
$env:ANYTHINGLLM_API_KEY="your-key-here"

# Permanent (User level)
[Environment]::SetEnvironmentVariable("MOLTBOOK_API_KEY", "your-key-here", "User")
```

### Setting Variables (Bash/Linux)
```bash
# Session-only
export MOLTBOOK_API_KEY="your-key-here"

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export MOLTBOOK_API_KEY="your-key-here"' >> ~/.bashrc
```

### Using `.env` Files (Local Development Only)
```ini
# .env (NEVER commit this file!)
MOLTBOOK_API_KEY=your-key-here
ANYTHINGLLM_API_KEY=your-key-here
LMSTUDIO_BASE_URL=http://localhost:1234/v1
```

Load with python-dotenv:
```python
from dotenv import load_dotenv
load_dotenv()  # Loads .env file
```

---

## 🔍 Pre-Commit Security Audit

### Manual Check (Before Every Push)
```powershell
# Search for potential secrets in code
Select-String -Path "*.py" -Pattern "sk_|api_key.*=.*[`"']|Bearer\s+[A-Za-z0-9]" -Recurse

# Search for common secret patterns
Select-String -Path "**/*" -Pattern "password|secret|token|key" -Recurse | Where-Object { $_ -notmatch "\.md$|\.gitignore$" }
```

### Patterns to Watch For
| Pattern | Risk Level | Example |
|---------|------------|---------|
| `sk_*` | 🔴 HIGH | `moltbook_sk_abc123` |
| `Bearer <token>` | 🔴 HIGH | `Bearer eyJhbG...` |
| `password = "..."` | 🔴 HIGH | `password = "admin123"` |
| `api_key = "..."` | 🔴 HIGH | `api_key = "xyz789"` |
| `localhost` URLs | 🟡 MEDIUM | May expose internal ports |
| IP addresses | 🟡 MEDIUM | `172.28.176.1` |

---

## 🛡️ Supply Chain Security

### The Threat
Attackers can:
1. **Compromise dependencies** - Inject malicious code into npm/pip packages
2. **Typosquatting** - Create fake packages with similar names
3. **Steal API tokens** - From public repos, logs, or env vars

### Defense Strategies

#### 1. Pin Dependencies
```toml
# pyproject.toml - Pin exact versions
[project]
dependencies = [
    "requests==2.31.0",  # ✅ Pinned
    "flask>=2.0",        # ⚠️ Range (less secure)
]
```

#### 2. Verify Package Integrity
```bash
# Check package hash
pip hash requests-2.31.0.tar.gz

# Use pip with hash checking
pip install --require-hashes -r requirements.txt
```

#### 3. Use Private Package Repositories
For sensitive projects, host your own PyPI mirror.

#### 4. Regular Audits
```bash
# Python
pip-audit

# Node.js
npm audit
```

---

## 🔄 Secret Rotation Protocol

### When to Rotate
| Event | Action |
|-------|--------|
| Secret committed to Git | **ROTATE IMMEDIATELY** |
| Team member leaves | Rotate all shared secrets |
| Every 90 days | Scheduled rotation |
| Security breach suspected | Rotate everything |

### Rotation Checklist
1. Generate new secret in provider dashboard
2. Update environment variables
3. Verify application works with new secret
4. Revoke old secret in provider dashboard
5. Document rotation in security log

---

## 📝 Code Review Security Checklist

Before approving any PR, verify:

- [ ] No hardcoded secrets
- [ ] No API keys in default values
- [ ] No credentials in comments
- [ ] `.env.example` has dummy values only
- [ ] Sensitive data logged appropriately (masked)
- [ ] Error messages don't expose secrets
- [ ] Dependencies are pinned
- [ ] No suspicious new dependencies

---

## 🚫 What NOT to Do

### 1. Don't Log Secrets
```python
# ❌ WRONG
print(f"Using API key: {API_KEY}")
logger.info(f"Auth header: {headers}")

# ✅ CORRECT
print(f"Using API key: {API_KEY[:8]}...")  # Show only prefix
logger.info("Auth header: [REDACTED]")
```

### 2. Don't Pass Secrets in URLs
```python
# ❌ WRONG - Secret in URL (logged everywhere)
requests.get(f"https://api.com?key={API_KEY}")

# ✅ CORRECT - Secret in header
requests.get("https://api.com", headers={"Authorization": f"Bearer {API_KEY}"})
```

### 3. Don't Trust User Input
```python
# ❌ WRONG - SQL injection risk
query = f"SELECT * FROM users WHERE name = '{user_input}'"

# ✅ CORRECT - Parameterized query
cursor.execute("SELECT * FROM users WHERE name = ?", (user_input,))
```

### 4. Don't Disable SSL Verification
```python
# ❌ WRONG - Man-in-the-middle risk
requests.get(url, verify=False)

# ✅ CORRECT - Always verify SSL
requests.get(url, verify=True)  # Default
```

---

## 🔐 Project-Specific Secrets

### This Project's Required Environment Variables

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `MOLTBOOK_API_KEY` | Moltbook agent API key | [Moltbook Developer Portal](https://moltbook.com/developers) |
| `ANYTHINGLLM_API_KEY` | AnythingLLM API key | AnythingLLM Settings > API |
| `LMSTUDIO_BASE_URL` | LM Studio endpoint | Your local LM Studio instance |

### Example `.env.example` (Safe to Commit)
```ini
# Copy this to .env and fill in your values
# NEVER commit .env to git!

MOLTBOOK_API_KEY=your-moltbook-api-key-here
ANYTHINGLLM_API_KEY=your-anythingllm-api-key-here
LMSTUDIO_BASE_URL=http://localhost:1234/v1
MOLTBOOK_AGENT_NAME=YourAgentName
```

---

## 🙏 The Security Mantra

Before every commit, recite:

> *"I shall not commit secrets.*
> *I shall not trust user input.*
> *I shall verify SSL certificates.*
> *I shall rotate compromised keys.*
> *I shall audit my dependencies.*
> *Om Shanti, Om Security."*

---

## 📚 Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [Python Security Best Practices](https://snyk.io/blog/python-security-best-practices-cheat-sheet/)
- [CWE - Common Weakness Enumeration](https://cwe.mitre.org/)

---

*Last Updated: 2026-02-01*
*Author: VedicRoastGuru Security Council*
