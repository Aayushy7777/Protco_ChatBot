"""
OpenClaw-style agent orchestrator.
High-precision agent for CSV analysis with RAG support and tool integration.
"""

import logging
import json
from typing import Optional
from dataclasses import dataclass
import yaml

from app.core.config import settings
from app.core.logger import logger
from app.services.rag_pipeline import get_rag_pipeline
from app.db.vector_store import get_vector_store

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Response from agent execution."""
    intent: str
    answer: str
    chart_config: Optional[dict] = None
    dashboard_config: Optional[dict] = None
    table_data: list = None
    table_columns: list = None
    active_file: str = ""
    error: Optional[str] = None
    context_used: Optional[str] = None


class OpenClawAgent:
    """
    OpenClaw-style agent orchestrator for CSV analysis.
    
    Architecture:
    1. Intent Classification (fast, mistral)
    2. Context Retrieval (RAG)
    3. Tool Selection & Execution
    4. LLM Generation (llama3 or qwen)
    5. Response Assembly
    """

    def __init__(self, config_path: str = "openclaw/agent_config.yaml"):
        """Initialize agent with configuration."""
        self.config = self._load_config(config_path)
        self.rag_pipeline = get_rag_pipeline()
        self.vector_store = get_vector_store()
        self.conversation_memory = {}
        logger.info(f"OpenClaw Agent initialized: {self.config['agent']['name']}")

    def _load_config(self, config_path: str) -> dict:
        """Load agent configuration from YAML."""
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded config from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}. Using defaults.")
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        """Return default configuration."""
        return {
            "agent": {"name": "csv_chat_agent", "version": "2.0.0"},
            "llm": {"provider": "ollama", "base_url": settings.OLLAMA_BASE_URL},
            "tools": {"enabled": ["retriever_tool", "csv_processor_tool"]},
            "rag": {"enabled": True},
            "memory": {"type": "buffer", "max_turns": 20},
        }

    async def run(
        self,
        message: str,
        active_file: str = "",
        all_files: list = None,
        conversation_history: list = None,
        session_id: str = "",
        **kwargs,
    ) -> AgentResponse:
        """
        Execute agent pipeline.
        
        Flow:
        1. Classify user intent
        2. Retrieve relevant context using RAG
        3. Select tools based on intent
        4. Execute tools
        5. Generate response using LLM
        6. Return structured response
        """
        try:
            # Step 1: Intent classification
            intent = await self._classify_intent(message)
            logger.info(f"Intent: {intent}")

            # Step 2: RAG retrieval for context
            context_used = None
            if self.config["rag"]["enabled"]:
                retrieval_results = self.rag_pipeline.retrieve(message)
                context_used = self.rag_pipeline.build_context(message, retrieval_results)
                logger.debug(f"Retrieved context: {len(retrieval_results)} documents")

            # Step 3: Route to handler based on intent
            if intent == "CHART":
                return await self._handle_chart(message, active_file, context_used)
            elif intent == "TABLE":
                return await self._handle_table(message, active_file, context_used)
            elif intent == "STATS":
                return await self._handle_stats(message, active_file, context_used)
            elif intent == "DASHBOARD":
                return await self._handle_dashboard(message, active_file, context_used)
            else:
                return await self._handle_chat(message, active_file, context_used)

        except Exception as e:
            logger.exception(f"Agent execution error: {e}")
            return AgentResponse(
                intent="ERROR",
                answer="An error occurred while processing your request.",
                error=str(e),
            )

    async def _classify_intent(self, message: str) -> str:
        """Classify user intent using LLM or keyword matching."""
        # Fast keyword-based classification
        m = message.lower()

        intent_config = self.config.get("intent_routing", {})

        # Check rules in order of priority
        priority_intents = ["DASHBOARD", "STATS", "CHART", "TABLE"]

        for intent in priority_intents:
            if intent in intent_config:
                keywords = intent_config[intent].get("keywords", [])
                if any(kw in m for kw in keywords):
                    return intent

        return "CHAT"  # Default to chat

    async def _handle_chart(
        self, message: str, active_file: str, context: Optional[str]
    ) -> AgentResponse:
        """Handle chart generation request."""
        logger.info("Routing to chart handler")
        # This would call the chart generation tool/service
        return AgentResponse(
            intent="CHART",
            answer="Chart generation not yet implemented in new architecture",
            context_used=context,
        )

    async def _handle_table(
        self, message: str, active_file: str, context: Optional[str]
    ) -> AgentResponse:
        """Handle table data request."""
        logger.info("Routing to table handler")
        return AgentResponse(
            intent="TABLE",
            answer="Table generation not yet implemented in new architecture",
            context_used=context,
        )

    async def _handle_stats(
        self, message: str, active_file: str, context: Optional[str]
    ) -> AgentResponse:
        """Handle statistics request."""
        logger.info("Routing to stats handler")
        return AgentResponse(
            intent="STATS",
            answer="Statistics generation not yet implemented in new architecture",
            context_used=context,
        )

    async def _handle_dashboard(
        self, message: str, active_file: str, context: Optional[str]
    ) -> AgentResponse:
        """Handle dashboard generation request."""
        logger.info("Routing to dashboard handler")
        return AgentResponse(
            intent="DASHBOARD",
            answer="Dashboard generation not yet implemented in new architecture",
            context_used=context,
        )

    async def _handle_chat(
        self, message: str, active_file: str, context: Optional[str]
    ) -> AgentResponse:
        """Handle general chat request."""
        logger.info("Routing to chat handler")
        answer = f"Chat response to: {message[:50]}..."
        if context:
            answer += f"\n\n[Using retrieved context from {active_file}]"

        return AgentResponse(
            intent="CHAT",
            answer=answer,
            context_used=context,
        )


# Global agent instance
_agent_instance: Optional[OpenClawAgent] = None


def get_agent() -> OpenClawAgent:
    """Get or create global agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = OpenClawAgent()
    return _agent_instance
