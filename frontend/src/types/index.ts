// v0.0.2 - Multi-agent support types

// ============================================================================
// Tool Types
// ============================================================================

export type ToolSource = 'builtin' | 'mcp';

export interface ToolConfig {
  name: string;
  source: ToolSource;
  enabled: boolean;
  hitl_enabled: boolean;
  server_id?: string;
  server_config?: Record<string, unknown>;
}

export interface Tool {
  name: string;
  description: string;
  enabled: boolean;
  hitl: boolean;
}

// ============================================================================
// Trigger Types
// ============================================================================

export type TriggerType = 'email_polling' | 'webhook' | 'scheduled' | 'event';

export interface TriggerConfig {
  id: string;
  type: TriggerType;
  enabled: boolean;
  config: Record<string, unknown>;
}

export interface Trigger {
  id: string;
  type: string;
  enabled: boolean;
  config: {
    interval_seconds?: number;
    account?: string;
  };
}

// ============================================================================
// Subagent Types
// ============================================================================

export interface SubagentConfig {
  name: string;
  description: string;
  system_prompt: string;
  tools: string[];
}

export interface Subagent {
  name: string;
  description: string;
  system_prompt: string;
  tools: string[];
}

// ============================================================================
// Agent Types (v0.0.2)
// ============================================================================

export interface AgentSummary {
  id: string;
  name: string;
  description: string;
  is_template: boolean;
}

export interface AgentDetail {
  id: string;
  name: string;
  description: string;
  system_prompt: string;
  model: string;
  memory_approval_required: boolean;
  tools: ToolConfig[];
  subagents: SubagentConfig[];
  triggers: TriggerConfig[];
  is_template: boolean;
}

// Legacy v0.0.1 config format (for backward compatibility)
export interface AgentConfig {
  name: string;
  instructions: string;
  tools: string[];
  hitl_tools: string[];
  subagents: Subagent[];
  triggers: Trigger[];
}

// ============================================================================
// Chat Types
// ============================================================================

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'tool' | 'hitl';
  content: string;
  toolName?: string;
  toolArgs?: Record<string, unknown>;
  toolCallId?: string;
}

export interface HITLInterrupt {
  tool_call_id: string;
  name: string;
  args: Record<string, unknown>;
}

// v0.0.3: Memory edit request for HITL approval
export interface MemoryEditRequest {
  request_id: string;
  tool_call_id: string;
  path: string;
  operation: 'write' | 'append' | 'delete';
  current_content: string | null;
  proposed_content: string;
  reason: string;
  suspicious_flags: SuspiciousFlag[];
}

export interface SuspiciousFlag {
  pattern: string;
  match: string;
  description: string;
  severity: 'warning' | 'danger';
}

export type WSMessageType =
  | { type: 'token'; content: string }
  | { type: 'tool_call'; name: string; args: Record<string, unknown> }
  | { type: 'tool_result'; name: string; result: unknown }
  | { type: 'hitl_interrupt'; tool_call_id: string; name: string; args: Record<string, unknown> }
  | { type: 'memory_edit_request'; request_id: string; tool_call_id: string; path: string; operation: string; current_content: string | null; proposed_content: string; reason: string; suspicious_flags: SuspiciousFlag[] }
  | { type: 'memory_edit_complete'; request_id: string; success: boolean; path: string }
  | { type: 'complete' }
  | { type: 'error'; message: string }
  | { type: 'new_email'; email: Record<string, unknown> }
  | { type: 'cleared' };

// ============================================================================
// MCP Types
// ============================================================================

export interface MCPServerConfig {
  id: string;
  name: string;
  command: string;
  args: string[];
  env: Record<string, string>;
  enabled: boolean;
}

export interface MCPServerInfo {
  id: string;
  name: string;
  command: string;
  enabled: boolean;
  tools: { name: string; description: string }[];
}

// ============================================================================
// Builder Types
// ============================================================================

export interface BuilderMessage {
  id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  toolName?: string;
  toolResult?: unknown;
}

// ============================================================================
// v0.0.3 Types
// ============================================================================

export interface Skill {
  id: string;
  name: string;
  description: string;
  instructions: string;
  created_at: string;
  updated_at: string;
}

export interface SkillCreate {
  name: string;
  description: string;
  instructions: string;
}

// ============================================================================
// Global Settings Types
// ============================================================================

export interface GlobalSettingsResponse {
  default_model: string;
  tavily_api_key_configured: boolean;
  tavily_api_key_preview: string | null;
}

export interface ModelOption {
  id: string;
  name: string;
}
