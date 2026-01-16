"""SQLAlchemy ORM models for Agent Builder."""

from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.infrastructure.persistence.sqlite.database import Base


class AgentModel(Base):
    """SQLAlchemy model for agents."""
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    system_prompt = Column(Text, nullable=False)
    model = Column(String, default="claude-sonnet-4-20250514")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_template = Column(Boolean, default=False)

    tools = relationship("AgentToolModel", back_populates="agent", cascade="all, delete-orphan")
    subagents = relationship("AgentSubagentModel", back_populates="agent", cascade="all, delete-orphan")
    triggers = relationship("AgentTriggerModel", back_populates="agent", cascade="all, delete-orphan")


class AgentToolModel(Base):
    """SQLAlchemy model for agent tools."""
    __tablename__ = "agent_tools"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    name = Column(String, nullable=False)
    source = Column(String, nullable=False)  # "builtin" or "mcp"
    enabled = Column(Boolean, default=True)
    hitl_enabled = Column(Boolean, default=False)
    server_id = Column(String, nullable=True)
    server_config = Column(JSON, default=dict)

    agent = relationship("AgentModel", back_populates="tools")


class AgentSubagentModel(Base):
    """SQLAlchemy model for agent subagents."""
    __tablename__ = "agent_subagents"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=False)
    tools = Column(JSON, nullable=False)  # List of tool names

    agent = relationship("AgentModel", back_populates="subagents")


class AgentTriggerModel(Base):
    """SQLAlchemy model for agent triggers."""
    __tablename__ = "agent_triggers"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    type = Column(String, nullable=False)
    enabled = Column(Boolean, default=False)
    config = Column(JSON, default=dict)

    agent = relationship("AgentModel", back_populates="triggers")


class MCPServerModel(Base):
    """SQLAlchemy model for MCP server configurations."""
    __tablename__ = "mcp_servers"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    command = Column(String, nullable=False)
    args = Column(JSON, default=list)
    env = Column(JSON, default=dict)
    enabled = Column(Boolean, default=True)


class HITLRequestModel(Base):
    """SQLAlchemy model for HITL requests."""
    __tablename__ = "hitl_requests"

    id = Column(String, primary_key=True)
    thread_id = Column(String, nullable=False)
    agent_id = Column(String, nullable=False)
    tool_call_id = Column(String, nullable=False)
    tool_name = Column(String, nullable=False)
    tool_args = Column(JSON, nullable=False)
    status = Column(String, default="pending")
    decision = Column(String, nullable=True)
    edited_args = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class ConversationMessageModel(Base):
    """SQLAlchemy model for conversation messages."""
    __tablename__ = "conversation_messages"

    id = Column(String, primary_key=True)
    thread_id = Column(String, nullable=False, index=True)
    agent_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    extra_data = Column(JSON, default=dict)  # Renamed from metadata (reserved)
    created_at = Column(DateTime, default=datetime.utcnow)


class CredentialModel(Base):
    """SQLAlchemy model for encrypted credentials."""
    __tablename__ = "credentials"

    provider = Column(String, primary_key=True)
    encrypted_data = Column(Text, nullable=False)  # Fernet encrypted JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
