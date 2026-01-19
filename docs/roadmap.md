# Agent Builder Roadmap

## v0.0.1 - Email Assistant (Complete)
Hardcoded email assistant with Gmail/Calendar tools, HITL approval, and canvas UI.

## v0.0.2 - Generic Agent Builder (Complete)
Transform into a platform that can generate any agent a user needs.

**Reference:** [LangSmith Agent Builder](https://www.blog.langchain.com/langsmith-agent-builder-generally-available/)

**Design:** [v0.0.2 Design Document](./archive/v0.0.2-agent-builder/design.md)

### Implemented
- [x] Clone template to create agents
- [x] Agent chat with streaming responses
- [x] HITL approval flow (Approve/Edit/Reject)
- [x] Tool execution (list_emails, draft_reply, get_email, search_emails)
- [x] Agent editor UI (toolbox, triggers panel, instructions, subagents)
- [x] SQLite persistence for agents and conversations
- [x] Templates system (Email Assistant)
- [x] Builder wizard WebSocket connectivity
- [x] Error feedback via react-hot-toast
- [x] Sidebar navigation

### Known Issues (defer to v0.0.3)
- [ ] Save Changes button lacks visual feedback (deferred to v0.0.4)
- [x] Raw JSON displayed alongside formatted tool results - fixed with collapsible ToolResultBubble
- [x] Example suggestions not clickable in builder wizard - verified working

## v0.0.3 - Agent Learning (Current)

**Reference:** [LangChain Agent Builder Memory](https://www.langchain.com/conceptual-guides/how-we-built-agent-builders-memory)

**Competitive Analysis:** [LangSmith Agent Builder Analysis](./product-research/insights.md)

**PRD:** [v0.0.3 Product Requirements](./v0.0.3-agent-learning/prd.md)

**Design:** [v0.0.3 Design Document](./v0.0.3-agent-learning/design.md)

**Review:** [v0.0.3 Review Plan](./v0.0.3-agent-learning/review-plan.md)

**Key Insight:** Agent quality is instruction-driven, not model-driven. See [analysis](./product-research/insights.md#quality-is-instruction-driven-not-model-driven).

### Phase 1: Infrastructure (P0)
- [x] Add `langgraph-checkpoint-sqlite` dependency
- [x] Implement `AsyncSqliteSaver` checkpointer via FastAPI lifespan
- [x] Remove agent caching from `RunAgentUseCase`
- [x] Add new SQLAlchemy models (via create_all, no Alembic)
- [x] Enable SQLite WAL mode

### Phase 2: Memory System (P0)
- [x] Implement `MemoryFileSystem` service with path validation
- [x] Create memory tools (`write_memory`, `read_memory`, `list_memory`)
- [x] Wire memory tools to HITL flow
- [x] Add suspicious pattern detection
- [x] Security fixes: TOCTOU, agent ID auth, size validation
- [ ] Implement 1-level undo for memory changes (deferred to v0.0.4)

### Phase 3: Skills (P1) - Anthropic Agent Skills Spec
- [x] Implement `SkillRepository` with YAML frontmatter parsing
- [x] Add Skills panel to agent editor UI (frontend) - verified existing
- [x] Inject active skills into agent context
- [x] Add skill visibility indicator instruction (`[Using skill: X]`)
- [x] Implement Agent Skills spec compliance:
  - Name auto-normalization ("PDF Processing" → "pdf-processing")
  - Name validation (lowercase, hyphens, max 64 chars)
  - Optional fields (license, compatibility, metadata, allowed_tools)
  - Progressive disclosure (metadata-only in prompt, full via memory tools)
- [x] Add Skill domain entity with Pydantic validators
- [x] Add SkillLoader service for progressive disclosure orchestration
- [x] Add domain validation module (`domain/validation/skill_validator.py`)

### Phase 4: Slack (P1)
- [x] Implement `list_slack_channels` tool
- [x] Implement `send_slack_message` tool with HITL
- [x] Add Slack token input UI (frontend) - verified existing in CredentialsPanel
- [x] Wire to `CredentialStore` for encrypted storage

### Phase 5: Bug Fixes (P0)
- [x] Remove fake tools from builder wizard
- [x] Fix Create button visibility (frontend) - verified visible (purple button top-right)
- [x] Persist wizard conversation state
- [x] Fix Research Assistant description - created proper template with correct description

### Phase 6: Testing (P0)
- [x] Path traversal attack tests
- [x] Content size validation tests
- [x] Suspicious pattern detection tests
- [x] v0.0.2 regression tests - all 46 tests passing
- [x] E2E tests for core workflow (templates, memory, skills)
- [ ] Concurrent memory write tests (deferred to v0.0.4)
- [ ] Server restart recovery tests (deferred to v0.0.4)

### Phase 7: Agent Quality Patterns (P1)
- [x] Add instruction patterns to wizard-generated agents (transparency ✅/⚠️, A/B/C options, workflows)
- [x] Update Email Assistant template with quality patterns
- [x] Document recommended system prompt patterns (in product-research/insights.md)

### Out of Scope (deferred to v0.0.4+)
- Global skill library (agent-specific only for MVP)
- Cross-agent memory sharing
- Memory versioning (git-like history)
- Subagent orchestration
- Slack OAuth (v0.0.3 requires users to create their own Slack app)
- Skill file attachments (scripts/, references/, assets/ directories)

## v0.0.4 - Triggers & Orchestration

**Key Features:**
- Working trigger system (schedule, webhooks, email polling)
- Full subagent orchestration
- Global skill library and sharing
- Slack OAuth flow (managed app, one-click install)
- More MCP tool integrations (Notion, Google Drive)
- Memory View Panel (read-only UI)
- Save Changes button feedback
- 1-level undo for memory changes

**Self-Introspection (from LangSmith analysis):**
- `read_agent_config` tool - agent can read its own system prompt
- `list_agent_tools` tool - agent can discover its available tools
- Collapsible tool call UI chips (better UX)
- Canvas with connected node visualization

## Known Simplifications

Current architectural shortcuts that will need addressing for production:

- No platform/tenant separation - platform infrastructure and tenant workloads run in the same environment
- No tenant isolation - all agents share the same database, memory filesystem, and resources without boundaries
- Single-user assumption (no auth, no RBAC)
- SQLite for persistence (not horizontally scalable)

## Future
- Multi-user support (requires tenant isolation)
- Cloud deployment
- Agent marketplace
- Agent sharing/export
- Memory compaction and optimization

### Phase 8: UI/UX Improvements (P2)
- [x] Collapsible tool result display with summary
- [x] Research Assistant template with correct description

---
*Last updated: January 18, 2026*
