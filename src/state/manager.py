"""
State management for Vision workflows using Redis.

This module provides the StateManager class for persisting and retrieving
workflow state across the distributed agent system.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import redis.asyncio as aioredis
from redis.asyncio import Redis

from src.core.config import get_settings
from src.state.models import StateSnapshot, WorkflowState, WorkflowStep

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages workflow state persistence using Redis.

    This class provides async methods for storing, retrieving, and managing
    workflow states with TTL-based cleanup and session management.
    """

    def __init__(self, redis_client: Redis | None = None) -> None:
        """
        Initialize state manager.

        Args:
            redis_client: Optional Redis client. If not provided, creates one from settings.
        """
        self._redis: Redis | None = redis_client
        self._settings = get_settings()
        self._default_ttl = 86400  # 24 hours

    async def _get_redis(self) -> Redis:
        """Get or create Redis client."""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self._settings.redis.url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    def _get_workflow_key(self, workflow_id: UUID) -> str:
        """Generate Redis key for workflow state."""
        return f"workflow:{workflow_id}"

    def _get_session_key(self, session_id: str) -> str:
        """Generate Redis key for session workflow list."""
        return f"session:{session_id}:workflows"

    async def save_state(
        self,
        state: WorkflowState,
        ttl: int | None = None,
    ) -> None:
        """
        Save workflow state to Redis.

        Args:
            state: Workflow state to save
            ttl: Time-to-live in seconds (default: 24 hours)

        Raises:
            redis.RedisError: If Redis operation fails
        """
        redis = await self._get_redis()
        workflow_key = self._get_workflow_key(state.workflow_id)
        session_key = self._get_session_key(state.session_id)

        # Update timestamp
        state.updated_at = datetime.utcnow()

        # Serialize state to JSON
        state_json = state.model_dump_json()

        # Save to Redis with TTL
        ttl_seconds = ttl or self._default_ttl
        await redis.setex(workflow_key, ttl_seconds, state_json)

        # Add to session's workflow set
        await redis.sadd(session_key, str(state.workflow_id))
        await redis.expire(session_key, ttl_seconds)

        logger.info(
            f"Saved workflow state {state.workflow_id} for session {state.session_id}"
        )

    async def load_state(self, workflow_id: UUID) -> WorkflowState | None:
        """
        Load workflow state from Redis.

        Args:
            workflow_id: Unique workflow identifier

        Returns:
            WorkflowState if found, None otherwise

        Raises:
            redis.RedisError: If Redis operation fails
        """
        redis = await self._get_redis()
        workflow_key = self._get_workflow_key(workflow_id)

        # Retrieve from Redis
        state_json = await redis.get(workflow_key)

        if state_json is None:
            logger.warning(f"Workflow state {workflow_id} not found")
            return None

        # Deserialize from JSON
        state = WorkflowState.model_validate_json(state_json)
        logger.info(f"Loaded workflow state {workflow_id}")
        return state

    async def delete_state(self, workflow_id: UUID) -> bool:
        """
        Delete workflow state from Redis.

        Args:
            workflow_id: Unique workflow identifier

        Returns:
            True if state was deleted, False if not found

        Raises:
            redis.RedisError: If Redis operation fails
        """
        redis = await self._get_redis()
        workflow_key = self._get_workflow_key(workflow_id)

        # Load state first to get session_id
        state = await self.load_state(workflow_id)
        if state is None:
            return False

        # Remove from Redis
        deleted = await redis.delete(workflow_key)

        # Remove from session set
        session_key = self._get_session_key(state.session_id)
        await redis.srem(session_key, str(workflow_id))

        logger.info(f"Deleted workflow state {workflow_id}")
        return deleted > 0

    async def list_states(
        self,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[StateSnapshot]:
        """
        List workflow states, optionally filtered by session.

        Args:
            session_id: Optional session ID to filter by
            limit: Maximum number of states to return

        Returns:
            List of state snapshots

        Raises:
            redis.RedisError: If Redis operation fails
        """
        redis = await self._get_redis()
        snapshots: list[StateSnapshot] = []

        if session_id:
            # Get workflows for specific session
            session_key = self._get_session_key(session_id)
            workflow_ids = await redis.smembers(session_key)

            for workflow_id_str in list(workflow_ids)[:limit]:
                try:
                    workflow_id = UUID(workflow_id_str)
                    state = await self.load_state(workflow_id)
                    if state:
                        snapshots.append(StateSnapshot.from_workflow_state(state))
                except (ValueError, Exception) as e:
                    logger.warning(
                        f"Failed to load workflow {workflow_id_str}: {e}"
                    )
        else:
            # Get all workflow keys
            cursor = 0
            while len(snapshots) < limit:
                cursor, keys = await redis.scan(
                    cursor, match="workflow:*", count=100
                )

                for key in keys:
                    if len(snapshots) >= limit:
                        break

                    # Extract workflow_id from key
                    workflow_id_str = key.split(":", 1)[1]
                    try:
                        workflow_id = UUID(workflow_id_str)
                        state = await self.load_state(workflow_id)
                        if state:
                            snapshots.append(StateSnapshot.from_workflow_state(state))
                    except (ValueError, Exception) as e:
                        logger.warning(
                            f"Failed to load workflow {workflow_id_str}: {e}"
                        )

                if cursor == 0:
                    break

        return snapshots

    async def update_step(
        self,
        workflow_id: UUID,
        step: WorkflowStep,
        output: dict[str, Any] | None = None,
    ) -> WorkflowState | None:
        """
        Update workflow state with completed step.

        Args:
            workflow_id: Workflow identifier
            step: Completed workflow step
            output: Optional output data from the step

        Returns:
            Updated workflow state, or None if not found

        Raises:
            redis.RedisError: If Redis operation fails
        """
        state = await self.load_state(workflow_id)
        if state is None:
            return None

        # Mark step as complete
        state.mark_step_complete(step)

        # Store output data
        if output is not None:
            if step == WorkflowStep.DESIGN:
                state.design_output = output
            elif step == WorkflowStep.PALETTE:
                from src.core.models import ColorPalette

                state.palette_output = ColorPalette.model_validate(output)
            elif step == WorkflowStep.DETAIL:
                state.detail_output = output
            elif step == WorkflowStep.ANIMATION:
                state.animation_output = output if isinstance(output, list) else [output]

        # Update current step
        next_step = state.get_next_step()
        if next_step == WorkflowStep.COMPLETE:
            state.status = "completed"
            state.completed_at = datetime.utcnow()
        else:
            state.current_step = next_step

        # Save updated state
        await self.save_state(state)
        return state

    async def cleanup_expired(self, older_than_hours: int = 24) -> int:
        """
        Cleanup workflow states older than specified hours.

        Note: Redis TTL handles automatic expiration, but this provides
        manual cleanup for states that may have had TTL extended.

        Args:
            older_than_hours: Delete states older than this many hours

        Returns:
            Number of states deleted

        Raises:
            redis.RedisError: If Redis operation fails
        """
        redis = await self._get_redis()
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        deleted_count = 0

        # Scan all workflow keys
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, match="workflow:*", count=100)

            for key in keys:
                workflow_id_str = key.split(":", 1)[1]
                try:
                    workflow_id = UUID(workflow_id_str)
                    state = await self.load_state(workflow_id)

                    if state and state.updated_at < cutoff_time:
                        await self.delete_state(workflow_id)
                        deleted_count += 1

                except (ValueError, Exception) as e:
                    logger.warning(
                        f"Failed to cleanup workflow {workflow_id_str}: {e}"
                    )

            if cursor == 0:
                break

        logger.info(f"Cleaned up {deleted_count} expired workflow states")
        return deleted_count

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.aclose()
            self._redis = None
            logger.info("Closed Redis connection")

    async def __aenter__(self) -> "StateManager":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()