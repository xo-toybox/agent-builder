export interface Tool {
  name: string;
  description: string;
  enabled: boolean;
  hitl: boolean;
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

export interface Subagent {
  name: string;
  description: string;
  system_prompt: string;
  tools: string[];
}

export interface AgentConfig {
  name: string;
  instructions: string;
  tools: string[];
  hitl_tools: string[];
  subagents: Subagent[];
  triggers: Trigger[];
}

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

export type WSMessageType =
  | { type: 'token'; content: string }
  | { type: 'tool_call'; name: string; args: Record<string, unknown> }
  | { type: 'tool_result'; name: string; result: unknown }
  | { type: 'hitl_interrupt'; tool_call_id: string; name: string; args: Record<string, unknown> }
  | { type: 'complete' }
  | { type: 'error'; message: string }
  | { type: 'new_email'; email: Record<string, unknown> };
