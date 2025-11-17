"""
Agent factory for Vision pixel art generation system.

This module provides factory functions to instantiate agents with proper
dependencies, configuration, and LLM clients. Simplifies agent creation
and ensures consistent setup across the system.
"""

import logging
from typing import Any

from redis import Redis

from src.agents.animation_agent import AnimationAgent
from src.agents.design_agent import DesignAgent
from src.agents.detail_agent import DetailAgent
from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.palette_agent import PaletteAgent
from src.core.config import Settings, get_settings
from src.llm.client import LLMClient, create_llm_client

logger = logging.getLogger(__name__)


def create_design_agent(
    settings: Settings | None = None,
    llm_client: LLMClient | None = None,
    redis_client: Redis | None = None,
    **kwargs: Any,
) -> DesignAgent:
    """
    Factory function to create a Design Agent with proper configuration.

    This function handles all dependency injection, including settings,
    LLM client creation, and custom parameters.

    Args:
        settings: Application settings (uses get_settings() if None)
        llm_client: Pre-configured LLM client (creates new one if None)
        redis_client: Redis client for LLM caching (optional)
        **kwargs: Additional parameters passed to DesignAgent constructor

    Returns:
        DesignAgent: Configured design agent instance

    Example:
        >>> # Basic usage
        >>> agent = create_design_agent()
        
        >>> # With custom settings
        >>> settings = Settings()
        >>> agent = create_design_agent(settings=settings)
        
        >>> # With shared LLM client
        >>> client = create_llm_client()
        >>> agent = create_design_agent(llm_client=client)
        
        >>> # With custom model
        >>> agent = create_design_agent(model_name="claude-3-opus-20240229")
    """
    # Get or use provided settings
    if settings is None:
        settings = get_settings()

    # Create or use provided LLM client
    if llm_client is None:
        logger.debug("Creating new LLM client for Design Agent")
        llm_client = create_llm_client(settings=settings, redis_client=redis_client)
    else:
        logger.debug("Using provided LLM client for Design Agent")

    # Get model name from settings or kwargs
    model_name = kwargs.pop("model_name", settings.models.design_agent_model)

    # Create and return agent
    logger.info(f"Creating Design Agent with model: {model_name}")
    return DesignAgent(
        llm_client=llm_client,
        model_name=model_name,
        **kwargs,
    )


def create_palette_agent(
    settings: Settings | None = None,
    llm_client: LLMClient | None = None,
    redis_client: Redis | None = None,
    **kwargs: Any,
) -> PaletteAgent:
    """
    Factory function to create a Palette Agent with proper configuration.

    This function handles all dependency injection, including settings,
    LLM client creation, and custom parameters.

    Args:
        settings: Application settings (uses get_settings() if None)
        llm_client: Pre-configured LLM client (creates new one if None)
        redis_client: Redis client for LLM caching (optional)
        **kwargs: Additional parameters passed to PaletteAgent constructor

    Returns:
        PaletteAgent: Configured palette agent instance

    Example:
        >>> # Basic usage
        >>> agent = create_palette_agent()
        
        >>> # With custom settings
        >>> settings = Settings()
        >>> agent = create_palette_agent(settings=settings)
        
        >>> # With shared LLM client
        >>> client = create_llm_client()
        >>> agent = create_palette_agent(llm_client=client)
        
        >>> # With custom max colors
        >>> agent = create_palette_agent(max_colors=64)
    """
    # Get or use provided settings
    if settings is None:
        settings = get_settings()

    # Create or use provided LLM client
    if llm_client is None:
        logger.debug("Creating new LLM client for Palette Agent")
        llm_client = create_llm_client(settings=settings, redis_client=redis_client)
    else:
        logger.debug("Using provided LLM client for Palette Agent")

    # Get model name from settings or kwargs
    model_name = kwargs.pop("model_name", settings.models.palette_agent_model)

    # Get max colors from kwargs or use default
    max_colors = kwargs.pop("max_colors", 52)  # Stardew Valley limit

    # Create and return agent
    logger.info(f"Creating Palette Agent with model: {model_name}, max_colors: {max_colors}")
    return PaletteAgent(
        llm_client=llm_client,
        model_name=model_name,
        max_colors=max_colors,
        **kwargs,
    )


def create_detail_agent(
    settings: Settings | None = None,
    llm_client: LLMClient | None = None,
    redis_client: Redis | None = None,
    **kwargs: Any,
) -> DetailAgent:
    """
    Factory function to create a Detail Agent with proper configuration.

    This function handles all dependency injection, including settings,
    LLM client creation, and custom parameters.

    Args:
        settings: Application settings (uses get_settings() if None)
        llm_client: Pre-configured LLM client (creates new one if None)
        redis_client: Redis client for LLM caching (optional)
        **kwargs: Additional parameters passed to DetailAgent constructor

    Returns:
        DetailAgent: Configured detail agent instance

    Example:
        >>> # Basic usage
        >>> agent = create_detail_agent()
        
        >>> # With custom settings
        >>> settings = Settings()
        >>> agent = create_detail_agent(settings=settings)
        
        >>> # With shared LLM client
        >>> client = create_llm_client()
        >>> agent = create_detail_agent(llm_client=client)
    """
    # Get or use provided settings
    if settings is None:
        settings = get_settings()

    # Create or use provided LLM client
    if llm_client is None:
        logger.debug("Creating new LLM client for Detail Agent")
        llm_client = create_llm_client(settings=settings, redis_client=redis_client)
    else:
        logger.debug("Using provided LLM client for Detail Agent")

    # Get model name from settings or kwargs
    model_name = kwargs.pop("model_name", settings.models.detail_agent_model)

    # Create and return agent
    logger.info(f"Creating Detail Agent with model: {model_name}")
    return DetailAgent(
        llm_client=llm_client,
        model_name=model_name,
        **kwargs,
    )


def create_animation_agent(
    settings: Settings | None = None,
    llm_client: LLMClient | None = None,
    redis_client: Redis | None = None,
    **kwargs: Any,
) -> AnimationAgent:
    """
    Factory function to create an Animation Agent with proper configuration.

    This function handles all dependency injection, including settings,
    LLM client creation, and custom parameters.

    Args:
        settings: Application settings (uses get_settings() if None)
        llm_client: Pre-configured LLM client (creates new one if None)
        redis_client: Redis client for LLM caching (optional)
        **kwargs: Additional parameters passed to AnimationAgent constructor

    Returns:
        AnimationAgent: Configured animation agent instance

    Example:
        >>> # Basic usage
        >>> agent = create_animation_agent()
        
        >>> # With custom settings
        >>> settings = Settings()
        >>> agent = create_animation_agent(settings=settings)
        
        >>> # With shared LLM client
        >>> client = create_llm_client()
        >>> agent = create_animation_agent(llm_client=client)
    """
    # Get or use provided settings
    if settings is None:
        settings = get_settings()

    # Create or use provided LLM client
    if llm_client is None:
        logger.debug("Creating new LLM client for Animation Agent")
        llm_client = create_llm_client(settings=settings, redis_client=redis_client)
    else:
        logger.debug("Using provided LLM client for Animation Agent")

    # Get model name from settings or kwargs
    model_name = kwargs.pop("model_name", settings.models.animation_agent_model)

    # Create and return agent
    logger.info(f"Creating Animation Agent with model: {model_name}")
    return AnimationAgent(
        llm_client=llm_client,
        model_name=model_name,
        **kwargs,
    )


def create_orchestrator_agent(
    **kwargs: Any,
) -> OrchestratorAgent:
    """
    Factory function to create an Orchestrator Agent.

    The orchestrator doesn't require an LLM client since it manages
    workflow logic rather than generating content.

    Args:
        **kwargs: Additional parameters (currently none supported)

    Returns:
        OrchestratorAgent: Configured orchestrator agent instance

    Example:
        >>> # Basic usage
        >>> agent = create_orchestrator_agent()
    """
    logger.info("Creating Orchestrator Agent")
    return OrchestratorAgent(**kwargs)


def create_agent_suite(
    settings: Settings | None = None,
    redis_client: Redis | None = None,
    shared_llm_client: bool = True,
) -> dict[str, Any]:
    """
    Create a complete suite of agents with shared or individual LLM clients.

    This function is useful when you need multiple agents and want to
    control whether they share an LLM client (for connection pooling
    and rate limiting) or have separate clients.

    Args:
        settings: Application settings (uses get_settings() if None)
        redis_client: Redis client for LLM caching (optional)
        shared_llm_client: If True, all agents share one LLM client;
                          if False, each agent gets its own client

    Returns:
        dict: Dictionary mapping agent names to agent instances:
            - "design": DesignAgent
            - "palette": PaletteAgent
            - "detail": DetailAgent
            - "animation": AnimationAgent
            - "orchestrator": OrchestratorAgent

    Example:
        >>> # Create suite with shared client (recommended)
        >>> agents = create_agent_suite(shared_llm_client=True)
        >>> design_agent = agents["design"]
        >>> palette_agent = agents["palette"]
        
        >>> # Create suite with individual clients
        >>> agents = create_agent_suite(shared_llm_client=False)
        
        >>> # Use in workflow
        >>> context = AgentContext(request=sprite_request, current_step="design")
        >>> design_spec = await agents["design"].process(context)
        >>> context.previous_results["design"] = design_spec
        >>> context.current_step = "palette"
        >>> palette = await agents["palette"].process(context)
    """
    if settings is None:
        settings = get_settings()

    logger.info(f"Creating agent suite (shared_client={shared_llm_client})")

    # Create shared LLM client if requested
    shared_client = None
    if shared_llm_client:
        logger.debug("Creating shared LLM client for all agents")
        shared_client = create_llm_client(settings=settings, redis_client=redis_client)

    # Create agents
    agents = {
        "design": create_design_agent(
            settings=settings,
            llm_client=shared_client,
            redis_client=redis_client if not shared_llm_client else None,
        ),
        "palette": create_palette_agent(
            settings=settings,
            llm_client=shared_client,
            redis_client=redis_client if not shared_llm_client else None,
        ),
        "detail": create_detail_agent(
            settings=settings,
            llm_client=shared_client,
            redis_client=redis_client if not shared_llm_client else None,
        ),
        "animation": create_animation_agent(
            settings=settings,
            llm_client=shared_client,
            redis_client=redis_client if not shared_llm_client else None,
        ),
        "orchestrator": create_orchestrator_agent(),
    }

    logger.info(f"Agent suite created with {len(agents)} agents")
    return agents


# Convenience function for getting a single agent by name
def get_agent(
    agent_name: str,
    settings: Settings | None = None,
    llm_client: LLMClient | None = None,
    redis_client: Redis | None = None,
    **kwargs: Any,
) -> DesignAgent | PaletteAgent | DetailAgent | AnimationAgent | OrchestratorAgent:
    """
    Get a specific agent by name with proper configuration.

    This is a convenience function that dispatches to the appropriate
    factory function based on the agent name.

    Args:
        agent_name: Name of agent ("design", "palette", "detail", "animation", "orchestrator")
        settings: Application settings (uses get_settings() if None)
        llm_client: Pre-configured LLM client (creates new one if None)
        redis_client: Redis client for LLM caching (optional)
        **kwargs: Additional parameters passed to agent constructor

    Returns:
        Agent instance of the appropriate type

    Raises:
        ValueError: If agent_name is not recognized

    Example:
        >>> # Get design agent
        >>> agent = get_agent("design")
        
        >>> # Get palette agent with custom settings
        >>> agent = get_agent("palette", max_colors=64)
        
        >>> # Get orchestrator agent
        >>> agent = get_agent("orchestrator")
    """
    agent_name = agent_name.lower()

    if agent_name == "design":
        return create_design_agent(
            settings=settings,
            llm_client=llm_client,
            redis_client=redis_client,
            **kwargs,
        )
    elif agent_name == "palette":
        return create_palette_agent(
            settings=settings,
            llm_client=llm_client,
            redis_client=redis_client,
            **kwargs,
        )
    elif agent_name == "detail":
        return create_detail_agent(
            settings=settings,
            llm_client=llm_client,
            redis_client=redis_client,
            **kwargs,
        )
    elif agent_name == "animation":
        return create_animation_agent(
            settings=settings,
            llm_client=llm_client,
            redis_client=redis_client,
            **kwargs,
        )
    elif agent_name == "orchestrator":
        return create_orchestrator_agent(**kwargs)
    else:
        raise ValueError(
            f"Unknown agent name: {agent_name}. "
            f"Valid options: 'design', 'palette', 'detail', 'animation', 'orchestrator'"
        )


# TODO: Phase 3 - Add configuration validation before agent creation
# TODO: Phase 4 - Add agent pool management for concurrent processing
# TODO: Phase 4 - Add agent health checks and monitoring