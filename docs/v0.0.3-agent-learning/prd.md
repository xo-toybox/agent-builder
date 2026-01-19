# v0.0.3 Product Requirements Document

## Problem

In v0.0.2, agents are stateless and forgetful:
- Conversations lost on server restart
- Agents don't learn from user feedback
- Users can't teach agents reusable skills
- Limited to Gmail/Calendar tools

Users can't build agents they'd actually rely on for daily work.

---

## Vision

Agents that **learn and remember** - users can teach preferences, correct mistakes, and trust agents to improve over time.

---

## Success Definition

### Users can rely on agents across sessions

**What good looks like:**
- User returns after days/weeks, agent remembers context
- Ongoing work continues seamlessly
- No "starting over" feeling

**What bad looks like:**
- Agent forgets everything after restart
- User re-explains context every session
- Data loss or corruption

**Measurable criteria:**
- 100% conversation data retention across planned server restarts
- User can resume conversation within 3 seconds of restart
- Zero silent data loss; explicit error message if corruption detected

---

### Agents learn from corrections

**What good looks like:**
- User corrects agent once, agent remembers
- Proposed updates are sensible and well-scoped
- Agent behavior actually changes after approval
- User feels agent is getting smarter

**What bad looks like:**
- Agent ignores feedback
- Agent proposes confusing or overly broad updates
- Approved changes don't affect behavior
- User gives up on teaching agent

**Example - Good memory update:**
- User prefers "Hi [name]" not "Dear [name]" → Update greeting style in `knowledge/preferences.md`
- User corrects timezone from ET to PT → Update user profile, not entire agent instructions

**Example - Bad memory update:**
- User says "be more professional" → Agent rewrites entire AGENTS.md (too broad)
- User corrects one email tone → Agent generalizes to all communication (over-generalized)

**Measurable criteria:**
- Learning scope is appropriate (not too broad/narrow) in 90%+ of proposals
- User can verify what agent has learned via memory view
- Behavior change observable in next relevant interaction

---

### Users can teach reusable skills

**What good looks like:**
- User creates skill in natural language
- Skill applies across different situations
- Agent clearly follows skill instructions
- User can iterate and improve skills

**What bad looks like:**
- Skill creation is confusing
- Agent ignores or misinterprets skills
- No way to tell if skill is working
- Skills feel like busywork

**Skill visibility:**
- Agent shows `[Using skill: X]` indicator when applying skill
- User can see which skills are active in current conversation
- Debug mode: "Why didn't you use skill X?" explanation

**Measurable criteria:**
- User can create working skill in <2 minutes
- User understands difference between memory vs. skills without consulting docs

---

### Agents can notify via Slack

**What good looks like:**
- Easy to add Slack in <5 clicks with clear instructions
- Agent shows message preview before sending (HITL)
- User trusts agent for team communication

**What bad looks like:**
- Confusing setup process
- Agent writes inappropriate messages
- Messages fail silently

**Reliability requirements:**
- Failed messages show clear error with retry option
- Token expiry shows explicit re-authentication prompt
- Rate limit warning before hitting Slack limits

---

### Builder wizard is honest

**What good looks like:**
- Wizard only suggests tools that exist
- Created agents work as described
- No broken promises

**What bad looks like:**
- Wizard suggests features that don't work
- User disappointed when agent can't do what wizard said

---

## Quality Expectations

| Area | Expectation |
|------|-------------|
| **Agent decisions** | Reasonable triage, appropriate tone in drafts |
| **Learning** | Right granularity - not too broad, not too narrow |
| **Persistence** | Zero data loss from normal operations |
| **UX clarity** | User always knows what's happening and what to do |
| **Trust** | User would use this for real work, not just demos |
| **Discovery** | User finds memory/skills within first session without docs |
| **Error clarity** | User knows why learning failed and how to fix |
| **Mental model** | User picks correct learning mechanism 80%+ of time |

---

## Agent Quality: Instruction-Driven, Not Model-Driven

**Key Insight:** Quality differences between agents are primarily driven by **system prompt engineering**, not model selection. A well-instructed model produces better results than a more powerful model with basic instructions.

**Reference:** [LangSmith Agent Builder Analysis](../product-research/insights.md)

### Instruction Patterns That Drive Quality

| Pattern | Effect | Example |
|---------|--------|---------|
| **Transparency indicators** | Users trust agents more | ✅ capabilities, ⚠️ limitations |
| **Structured options** | Better decision-making | A) B) C) choices with descriptions |
| **Workflow explanations** | Users understand process | Numbered step-by-step lists |
| **Expectation setting** | Fewer surprises | "This requires your approval" |
| **Proactive suggestions** | Agents feel helpful | "For automation, I could..." |

### Quality Metrics (v0.0.3)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Transparency in responses | 90%+ responses include capability indicators | Manual review of 50 agent interactions |
| Option presentation | Multi-path decisions use A/B/C format | Pattern matching in responses |
| Workflow clarity | Complex tasks explained step-by-step | User comprehension testing |
| Learning acknowledgment | 100% corrections acknowledged before memory write | Log analysis |

### Implementation Priority

1. **v0.0.3:** Add instruction patterns to wizard-generated agent prompts
2. **v0.0.4:** Add self-introspection tools (read own config, list own tools)
3. **v0.0.5:** Full self-modification (edit own instructions with HITL)

---

## Security & Privacy Requirements

| Area | Requirement |
|------|-------------|
| **Memory encryption** | Memory files encrypted at rest (SQLite encryption) |
| **Credential storage** | Slack tokens stored encrypted via credential store (same as Google OAuth) |
| **Prompt injection defense** | Memory write validation detects suspicious patterns |
| **HITL diff highlighting** | Suspicious patterns highlighted (URLs, "always/never" instructions) |
| **Audit trail** | All memory writes logged with timestamp and reason |

---

## Memory Management

### Memory limits (v0.0.3)
- Max 50 skills per agent
- Max 100KB total memory size per agent
- Warning at 80% capacity

### Memory discovery (v0.0.3 MVP)
- User can view agent's knowledge files in agent editor panel
- User can delete memory files via UI
- Direct editing deferred to v0.0.4 (use agent conversation to update)

### Memory conflict resolution (v0.0.3 MVP)
- Last-write-wins for same path (simple approach)
- User reviews each memory proposal individually via HITL
- Semantic conflict detection deferred to v0.0.4

---

## Error Recovery

| Scenario | Expected Behavior |
|----------|-------------------|
| Memory update fails (technical error) | Clear error message with retry option |
| Skill syntax invalid | Validation error with helpful message before save |
| HITL UI fails to load | Graceful fallback with skip option |
| User approves bad memory | 1-level undo available |
| Memory system unavailable | Agent works without learning, notifies user |

---

## Out of Scope

| Feature | Why |
|---------|-----|
| Background reflection | MVP learning works without automation |
| Memory compaction | Premature optimization |
| Agent export/import | Portability can wait |
| More integrations | Slack proves the pattern, others in v0.0.4 |
| Triggers | Deferred to v0.0.4 |
| Global skill library | Agent-specific skills only for MVP; sharing in v0.0.4 |
| Cross-agent memory sharing | Single agent scope for v0.0.3 |
| Memory versioning (git-like) | HITL approval provides basic audit trail |
| Subagent orchestration | Data structure exists; execution in v0.0.4 |

---

## Known Issues to Fix

| Issue | Impact | Priority | Status |
|-------|--------|----------|--------|
| Fake tools in wizard (Web, Notes) | Breaks trust, user disappointment | HIGH | ✅ Fixed |
| Research Assistant wrong data | Confusing, looks buggy | MEDIUM | ✅ Fixed - created proper template |
| Create button invisible | Users can't find core action | HIGH | ✅ Verified visible (purple button top-right) |
| Wizard state lost on refresh | Frustrating, loses work | HIGH | ✅ Fixed |
| Content size bypass on approve | Security - oversized content could be written | HIGH | ✅ Fixed |
| Frontend pattern highlighting broken | Security - suspicious patterns not highlighted | HIGH | ✅ Fixed |
| Missing severity field in patterns | Frontend/backend type mismatch | HIGH | ✅ Fixed |
| Example suggestions not clickable | Users can't use wizard efficiently | MEDIUM | ✅ Verified working |
| Tool results display raw JSON | Cluttered chat, hard to read | MEDIUM | ✅ Fixed - collapsible with summary |

**Note:** Slack tools are being implemented in v0.0.3, not removed. Only Web and Notes tools are "fake" and have been removed from wizard suggestions.

---

## Implementation Status

### Backend (Complete)

| Component | Status |
|-----------|--------|
| AsyncSqliteSaver checkpointer | ✅ Complete |
| SQLite WAL mode | ✅ Complete |
| MemoryFileSystem with path validation | ✅ Complete |
| Memory tools (write/read/list) | ✅ Complete |
| Suspicious pattern detection | ✅ Complete |
| SkillRepository with YAML parsing | ✅ Complete |
| Skill injection into agent context | ✅ Complete |
| Slack tools with HITL | ✅ Complete |
| Web search tool | ✅ Complete |
| Wizard state persistence | ✅ Complete |
| Security fixes (TOCTOU, auth checks) | ✅ Complete |

### Frontend (Complete)

| Component | Status | Priority |
|-----------|--------|----------|
| Memory Edit UI | ✅ Complete | P0 |
| Skills Panel in agent editor | ✅ Complete | P1 |
| Memory View Panel | ⏳ Deferred to v0.0.4 | P1 |
| Slack token input UI | ✅ Complete | P1 |
| Save Changes button feedback | ❌ Not started | P2 |

### Testing (Complete)

| Test Category | Status | Priority |
|---------------|--------|----------|
| Concurrent memory write tests | ⏳ Deferred to v0.0.4 | P1 |
| Path traversal attack tests | ✅ Complete | P0 |
| Content size validation tests | ✅ Complete | P0 |
| Suspicious pattern detection tests | ✅ Complete | P0 |
| Server restart recovery tests | ⏳ Deferred to v0.0.4 | P1 |
| v0.0.2 regression tests | ✅ Complete (46 tests passing) | P1 |
| E2E core workflow tests | ✅ Complete (templates, memory, skills) | P0 |

### Agent Quality Patterns (Complete)

| Component | Status |
|-----------|--------|
| Quality patterns in wizard prompt | ✅ Complete |
| Quality patterns in Email Assistant template | ✅ Complete |
| Research Assistant template with quality patterns | ✅ Complete |
| Documentation in product-research/insights.md | ✅ Complete |

### Features Deferred to v0.0.4

| Feature | Reason |
|---------|--------|
| 1-level undo for memory changes | Complexity; HITL preview provides guard rails |
| Memory encryption at rest | Requires SQLCipher; HITL approval sufficient for MVP |
| Concurrent memory write tests | Complexity; basic flow tested |
| Server restart recovery tests | Additional infrastructure needed |
| Memory View Panel | Read-only UI deferred |
| Save Changes button feedback | Low priority polish |

---

## Validation Plan

### Automated testing
- SQLite corruption detection tests
- Concurrent memory write tests
- Memory path traversal attack tests
- All v0.0.2 functionality regression tests

### Manual testing
- User testing with 3-5 users unfamiliar with codebase
- Fresh install experience
- Upgrade from v0.0.2 verification

### Success criteria
- Zero silent failures in learning pipeline
- Users discover memory feature within first 3 corrections without documentation
- 80%+ users can debug "why didn't agent use my skill?" without developer help

---

## Rollback Safety

- v0.0.3 memory features can be disabled without data loss
- Migration script to export memories before upgrade
- "Safe mode" to disable memory features if critical bugs found
- All agent definitions backward compatible with v0.0.2

---

*v0.0.3 | January 18, 2026*
