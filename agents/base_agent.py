"""
Abstract base agent class for the multi-agent design system.

This module provides the foundation for all agents in the system,
ensuring consistent interfaces and behavior patterns.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from uuid import UUID

from models.task_models import Task, TaskStatus, AgentType, AgentStatus, AgentMessage


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the multi-agent system.
    
    This class provides common functionality and defines the interface
    that all agents must implement.
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        capabilities: List[str],
        max_concurrent_tasks: int = 1
    ):
        """
        Initialize the base agent.
        
        Args:
            agent_id: Unique identifier for this agent
            agent_type: Type of agent (design, effects, etc.)
            capabilities: List of capabilities this agent provides
            max_concurrent_tasks: Maximum number of tasks this agent can handle simultaneously
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # State management
        self._current_tasks: Dict[UUID, Task] = {}
        self._status = "offline"
        self._last_heartbeat = datetime.utcnow()
        self._performance_metrics: Dict[str, Any] = {}
        
        # Communication
        self._message_handlers: Dict[str, Callable] = {}
        self._coordinator_connection: Optional[Any] = None
        
        # Logging
        self.logger = logging.getLogger(f"agent.{agent_id}")
        
        # Register default message handlers
        self._register_default_handlers()
    
    @abstractmethod
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """
        Process a task assigned to this agent.
        
        This method must be implemented by concrete agent classes.
        
        Args:
            task: The task to process
            
        Returns:
            Dictionary containing the result of task processing
            
        Raises:
            Exception: If task processing fails
        """
        pass
    
    @abstractmethod
    async def validate_task(self, task: Task) -> bool:
        """
        Validate if this agent can handle the given task.
        
        Args:
            task: The task to validate
            
        Returns:
            True if the agent can handle the task, False otherwise
        """
        pass
    
    async def start(self) -> None:
        """Start the agent and register with coordinator."""
        self._status = "online"
        self._last_heartbeat = datetime.utcnow()
        self.logger.info(f"Agent {self.agent_id} started")
        
        # Register with coordinator
        if self._coordinator_connection:
            await self._register_with_coordinator()
        
        # Start heartbeat
        asyncio.create_task(self._heartbeat_loop())
    
    async def stop(self) -> None:
        """Stop the agent gracefully."""
        self._status = "offline"
        
        # Cancel all current tasks
        for task_id in list(self._current_tasks.keys()):
            await self._cancel_task(task_id)
        
        self.logger.info(f"Agent {self.agent_id} stopped")
    
    async def assign_task(self, task: Task) -> bool:
        """
        Assign a task to this agent.
        
        Args:
            task: The task to assign
            
        Returns:
            True if task was accepted, False otherwise
        """
        if len(self._current_tasks) >= self.max_concurrent_tasks:
            self.logger.warning(f"Agent {self.agent_id} at capacity, rejecting task {task.id}")
            return False
        
        if not await self.validate_task(task):
            self.logger.warning(f"Agent {self.agent_id} cannot handle task {task.id}")
            return False
        
        self._current_tasks[task.id] = task
        task.update_status(TaskStatus.IN_PROGRESS)
        
        self.logger.info(f"Agent {self.agent_id} accepted task {task.id}")
        
        # Process task asynchronously
        asyncio.create_task(self._process_task_wrapper(task))
        
        return True
    
    async def _process_task_wrapper(self, task: Task) -> None:
        """Wrapper for task processing with error handling."""
        try:
            start_time = datetime.utcnow()
            result = await self.process_task(task)
            end_time = datetime.utcnow()
            
            # Update task with result
            task.result = result
            task.update_status(TaskStatus.COMPLETED)
            
            # Update performance metrics
            processing_time = (end_time - start_time).total_seconds()
            self._update_performance_metrics(task.id, processing_time, True)
            
            self.logger.info(f"Task {task.id} completed successfully")
            
        except Exception as e:
            self.logger.error(f"Task {task.id} failed: {str(e)}")
            task.update_status(TaskStatus.FAILED, str(e))
            self._update_performance_metrics(task.id, 0, False)
        
        finally:
            # Remove task from current tasks
            self._current_tasks.pop(task.id, None)
            
            # Notify coordinator of completion
            if self._coordinator_connection:
                await self._notify_task_completion(task)
    
    async def _cancel_task(self, task_id: UUID) -> None:
        """Cancel a task."""
        if task_id in self._current_tasks:
            task = self._current_tasks[task_id]
            task.update_status(TaskStatus.CANCELLED)
            self._current_tasks.pop(task_id)
            self.logger.info(f"Task {task_id} cancelled")
    
    def get_status(self) -> AgentStatus:
        """Get current agent status."""
        return AgentStatus(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=self._status,
            last_heartbeat=self._last_heartbeat,
            current_tasks=list(self._current_tasks.keys()),
            capabilities=self.capabilities,
            performance_metrics=self._performance_metrics.copy()
        )
    
    def _update_performance_metrics(self, task_id: UUID, processing_time: float, success: bool) -> None:
        """Update performance metrics."""
        if "task_count" not in self._performance_metrics:
            self._performance_metrics["task_count"] = 0
        if "success_count" not in self._performance_metrics:
            self._performance_metrics["success_count"] = 0
        if "total_processing_time" not in self._performance_metrics:
            self._performance_metrics["total_processing_time"] = 0.0
        
        self._performance_metrics["task_count"] += 1
        self._performance_metrics["total_processing_time"] += processing_time
        
        if success:
            self._performance_metrics["success_count"] += 1
        
        # Calculate success rate
        success_rate = (
            self._performance_metrics["success_count"] / 
            self._performance_metrics["task_count"]
        )
        self._performance_metrics["success_rate"] = success_rate
        
        # Calculate average processing time
        avg_time = (
            self._performance_metrics["total_processing_time"] / 
            self._performance_metrics["task_count"]
        )
        self._performance_metrics["average_processing_time"] = avg_time
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats to coordinator."""
        while self._status == "online":
            try:
                self._last_heartbeat = datetime.utcnow()
                if self._coordinator_connection:
                    await self._send_heartbeat()
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
            except Exception as e:
                self.logger.error(f"Heartbeat failed: {str(e)}")
                await asyncio.sleep(5)  # Retry in 5 seconds on error
    
    def _register_default_handlers(self) -> None:
        """Register default message handlers."""
        self._message_handlers["heartbeat"] = self._handle_heartbeat
        self._message_handlers["task_assignment"] = self._handle_task_assignment
        self._message_handlers["task_cancellation"] = self._handle_task_cancellation
        self._message_handlers["status_request"] = self._handle_status_request
    
    async def _handle_heartbeat(self, message: AgentMessage) -> None:
        """Handle heartbeat message."""
        self._last_heartbeat = datetime.utcnow()
    
    async def _handle_task_assignment(self, message: AgentMessage) -> None:
        """Handle task assignment message."""
        # This would be implemented by the coordinator
        pass
    
    async def _handle_task_cancellation(self, message: AgentMessage) -> None:
        """Handle task cancellation message."""
        if message.task_id:
            await self._cancel_task(message.task_id)
    
    async def _handle_status_request(self, message: AgentMessage) -> None:
        """Handle status request message."""
        # Send status back to coordinator
        if self._coordinator_connection:
            status = self.get_status()
            await self._send_message("coordinator", "status_response", {"status": status.dict()})
    
    async def _register_with_coordinator(self) -> None:
        """Register this agent with the coordinator."""
        # This would be implemented by the coordinator
        pass
    
    async def _notify_task_completion(self, task: Task) -> None:
        """Notify coordinator of task completion."""
        if self._coordinator_connection:
            await self._send_message(
                "coordinator",
                "task_completion",
                {"task": task.dict()},
                task.id
            )
    
    async def _send_heartbeat(self) -> None:
        """Send heartbeat to coordinator."""
        await self._send_message("coordinator", "heartbeat", {})
    
    async def _send_message(
        self,
        recipient: str,
        message_type: str,
        payload: Dict[str, Any],
        task_id: Optional[UUID] = None
    ) -> None:
        """Send a message to another agent or coordinator."""
        if self._coordinator_connection:
            message = AgentMessage(
                sender=self.agent_id,
                recipient=recipient,
                message_type=message_type,
                payload=payload,
                task_id=task_id
            )
            await self._coordinator_connection.send_message(message)
    
    def set_coordinator_connection(self, connection: Any) -> None:
        """Set the coordinator connection."""
        self._coordinator_connection = connection
    
    def add_capability(self, capability: str) -> None:
        """Add a new capability to this agent."""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
            self.logger.info(f"Added capability: {capability}")
    
    def remove_capability(self, capability: str) -> None:
        """Remove a capability from this agent."""
        if capability in self.capabilities:
            self.capabilities.remove(capability)
            self.logger.info(f"Removed capability: {capability}")
    
    @property
    def is_available(self) -> bool:
        """Check if agent is available for new tasks."""
        return (
            self._status == "online" and 
            len(self._current_tasks) < self.max_concurrent_tasks
        )
    
    @property
    def current_task_count(self) -> int:
        """Get current number of active tasks."""
        return len(self._current_tasks)
