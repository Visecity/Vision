"""
Base agent class for Vision pixel art generation system.

This module provides the abstract base class that all specialized agents
inherit from, ensuring consistent interfaces and behavior.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from src.core.models import (
    AgentContext,
    AgentMessage,
    AgentRole,
    MessageType,
    ValidationResult,
)

# Type variables for generic input/output typing
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class AgentCapability:
    """Defines a capability that an agent possesses."""

    def __init__(
        self,
        name: str,
        description: str,
        required_inputs: list[str] | None = None,
        provided_outputs: list[str] | None = None,
    ) -> None:
        """
        Initialize an agent capability.

        Args:
            name: Capability identifier
            description: Human-readable description
            required_inputs: List of required input fields
            provided_outputs: List of output fields this capability provides
        """
        self.name = name
        self.description = description
        self.required_inputs = required_inputs or []
        self.provided_outputs = provided_outputs or []


class AgentMetadata:
    """Metadata describing an agent's role and capabilities."""

    def __init__(
        self,
        name: str,
        role: AgentRole,
        description: str,
        version: str = "1.0.0",
        capabilities: list[AgentCapability] | None = None,
    ) -> None:
        """
        Initialize agent metadata.

        Args:
            name: Agent display name
            role: Agent role from AgentRole enum
            description: What this agent does
            version: Agent version string
            capabilities: List of agent capabilities
        """
        self.name = name
        self.role = role
        self.description = description
        self.version = version
        self.capabilities = capabilities or []

    def can_handle(self, capability_name: str) -> bool:
        """Check if agent has a specific capability."""
        return any(cap.name == capability_name for cap in self.capabilities)


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """
    Abstract base class for all agents in the Vision system.

    All specialized agents (Design, Palette, Detail, Animation) must inherit
    from this class and implement the required abstract methods.

    Type Parameters:
        InputT: Type of input data this agent accepts
        OutputT: Type of output data this agent produces
    """

    def __init__(self, metadata: AgentMetadata) -> None:
        """
        Initialize the base agent.

        Args:
            metadata: Agent metadata describing its capabilities
        """
        self._metadata = metadata
        self._processing_history: list[AgentMessage] = []

    @property
    def metadata(self) -> AgentMetadata:
        """Get agent metadata."""
        return self._metadata

    @property
    def name(self) -> str:
        """Get agent name."""
        return self._metadata.name

    @property
    def role(self) -> AgentRole:
        """Get agent role."""
        return self._metadata.role

    @abstractmethod
    async def process(self, context: AgentContext) -> OutputT:
        """
        Process input and generate output.

        This is the main method that specialized agents must implement.
        It should contain the agent's core logic.

        Args:
            context: Processing context with request and previous results

        Returns:
            OutputT: Agent-specific output

        Raises:
            ValidationError: If input validation fails
            ProcessingError: If processing encounters an error
        """
        pass

    @abstractmethod
    def validate_input(self, context: AgentContext) -> ValidationResult:
        """
        Validate input before processing.

        Args:
            context: Processing context to validate

        Returns:
            ValidationResult: Validation outcome with errors/warnings
        """
        pass

    @abstractmethod
    def validate_output(self, output: OutputT) -> ValidationResult:
        """
        Validate output after processing.

        Args:
            output: Output data to validate

        Returns:
            ValidationResult: Validation outcome with errors/warnings
        """
        pass

    def _log_message(self, message: AgentMessage) -> None:
        """
        Log an agent message for debugging and audit trail.

        Args:
            message: Message to log
        """
        self._processing_history.append(message)

    def get_processing_history(self) -> list[AgentMessage]:
        """
        Get history of messages processed by this agent.

        Returns:
            list[AgentMessage]: Chronological list of messages
        """
        return self._processing_history.copy()

    def clear_history(self) -> None:
        """Clear processing history (useful for testing)."""
        self._processing_history.clear()

    async def execute(self, context: AgentContext) -> tuple[OutputT, ValidationResult]:
        """
        Execute the agent with full validation pipeline.

        This method wraps the process() call with input/output validation,
        providing a complete execution flow.

        Args:
            context: Processing context

        Returns:
            tuple[OutputT, ValidationResult]: Output and validation result

        Raises:
            ValidationError: If validation fails and is critical
        """
        # Validate input
        input_validation = self.validate_input(context)
        if not input_validation.is_valid:
            raise ValueError(f"Input validation failed: {input_validation.errors}")

        # Process
        output = await self.process(context)

        # Validate output
        output_validation = self.validate_output(output)
        if not output_validation.is_valid:
            raise ValueError(f"Output validation failed: {output_validation.errors}")

        return output, output_validation

    def create_message(
        self,
        to_agent: AgentRole | None,
        message_type: MessageType,
        content: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> AgentMessage:
        """
        Create a message to send to another agent.

        Args:
            to_agent: Recipient agent role (None for broadcast)
            message_type: Type of message
            content: Message payload
            context: Optional additional context

        Returns:
            AgentMessage: Constructed message
        """
        message = AgentMessage(
            from_agent=self.role,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            context=context or {},
        )
        self._log_message(message)
        return message

    def can_process(self, context: AgentContext) -> bool:
        """
        Check if agent can process given context.

        Default implementation checks if required capabilities are available.
        Can be overridden for more complex logic.

        Args:
            context: Processing context

        Returns:
            bool: True if agent can process this context
        """
        validation = self.validate_input(context)
        return validation.is_valid

    def __repr__(self) -> str:
        """String representation of agent."""
        return f"{self.__class__.__name__}(role={self.role.value}, name={self.name})"


class ProcessingError(Exception):
    """
    Exception raised when agent processing fails.

    Attributes:
        agent_role: Role of the agent that failed
        message: Error message
        context: Optional context information
    """

    def __init__(
        self,
        agent_role: AgentRole,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize processing error.

        Args:
            agent_role: Agent that encountered the error
            message: Error description
            context: Optional error context
        """
        self.agent_role = agent_role
        self.context = context or {}
        super().__init__(f"[{agent_role.value}] {message}")


class ValidationError(Exception):
    """
    Exception raised when validation fails critically.

    Attributes:
        validation_result: The validation result that failed
        message: Error message
    """

    def __init__(self, validation_result: ValidationResult, message: str | None = None) -> None:
        """
        Initialize validation error.

        Args:
            validation_result: Validation result with errors
            message: Optional additional message
        """
        self.validation_result = validation_result
        error_msg = message or "Validation failed"
        if validation_result.errors:
            error_msg += f": {', '.join(validation_result.errors)}"
        super().__init__(error_msg)


class RenderingError(Exception):
    """
    Exception raised when PNG rendering fails.

    This error is raised during the automatic rendering phase when
    a manifest cannot be converted to PNG format. It includes context
    about what failed and why.

    Attributes:
        message: Error description
        manifest_path: Optional path to the manifest that failed
        context: Optional additional error context
    """

    def __init__(
        self,
        message: str,
        manifest_path: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize rendering error.

        Args:
            message: Error description
            manifest_path: Optional manifest file path
            context: Optional error context
        """
        self.manifest_path = manifest_path
        self.context = context or {}
        error_msg = f"Rendering failed: {message}"
        if manifest_path:
            error_msg += f" (manifest: {manifest_path})"
        super().__init__(error_msg)


# TODO: Phase 3 - Implement specialized agent classes (Design, Palette, Detail, Animation)
# TODO: Phase 3 - Add middleware/plugin system for agent extensions
# TODO: Phase 3 - Add agent state persistence and recovery
# TODO: Phase 4 - Add distributed agent execution support
# TODO: Phase 4 - Add agent performance metrics and monitoring