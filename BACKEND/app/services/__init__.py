"""
Services package.

Note: This file must stay import-safe. Do not import dead/legacy modules here,
because importing `app.services.<module>` executes this package init.
"""

from app.services.agent import build_agent, parse_agent_response, register_dataframe
from app.services.dashboard_gen import generate_dashboard
from app.services.profiler import profile_dataframe, profile_to_prompt_context
from app.services.rag import get_retriever, ingest_file

__all__ = [
    "build_agent",
    "parse_agent_response",
    "register_dataframe",
    "generate_dashboard",
    "profile_dataframe",
    "profile_to_prompt_context",
    "get_retriever",
    "ingest_file",
]
