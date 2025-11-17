"""
Vision pixel art generation agents package.

This package contains specialized agents for different aspects of pixel art
generation: design, palette selection, detail rendering, and animation.
"""

from src.agents.animation_agent import AnimationAgent
from src.agents.base import (
    AgentCapability,
    AgentMetadata,
    BaseAgent,
    ProcessingError,
    ValidationError,
)
from src.agents.design_agent import DesignAgent
from src.agents.detail_agent import DetailAgent
from src.agents.factory import (
    create_agent_suite,
    create_animation_agent,
    create_design_agent,
    create_detail_agent,
    create_orchestrator_agent,
    create_palette_agent,
    get_agent,
)
from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.palette_agent import PaletteAgent

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentCapability",
    "AgentMetadata",
    "ProcessingError",
    "ValidationError",
    # Specialized agents
    "DesignAgent",
    "PaletteAgent",
    "DetailAgent",
    "AnimationAgent",
    "OrchestratorAgent",
    # Factory functions
    "create_design_agent",
    "create_palette_agent",
    "create_detail_agent",
    "create_animation_agent",
    "create_orchestrator_agent",
    "create_agent_suite",
    "get_agent",
]