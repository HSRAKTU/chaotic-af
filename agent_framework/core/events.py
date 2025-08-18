"""Event streaming system for agent observability.

Requirements:
- Emit structured events for all significant agent actions
- Support UI subscriptions via WebSocket (future)
- Keep event history for debugging
- Minimal overhead
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from collections import deque
import asyncio
from enum import Enum


class EventType(str, Enum):
    """Types of events emitted by agents."""
    # Agent lifecycle
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    
    # Communication events
    TOOL_CALL_RECEIVED = "tool_call_received"
    TOOL_CALL_MAKING = "tool_call_making"
    TOOL_CALL_RESPONSE = "tool_call_response"
    
    # LLM events
    LLM_REASONING = "llm_reasoning"
    LLM_COMPLETION = "llm_completion"
    
    # User interaction
    USER_MESSAGE = "user_message"
    USER_RESPONSE = "user_response"
    
    # Inter-agent communication
    AGENT_MESSAGE_SENT = "agent_message_sent"
    AGENT_MESSAGE_RECEIVED = "agent_message_received"
    
    # Errors
    ERROR = "error"


@dataclass
class AgentEvent:
    """Structured event emitted by an agent."""
    timestamp: datetime
    agent_id: str
    event_type: EventType
    data: Dict[str, Any]
    correlation_id: Optional[str] = None  # For tracking related events
    
    def to_json(self) -> str:
        """Convert event to JSON for streaming."""
        event_dict = asdict(self)
        event_dict['timestamp'] = self.timestamp.isoformat()
        event_dict['event_type'] = self.event_type.value
        return json.dumps(event_dict)


class EventStream:
    """Manages event emission and subscription for an agent.
    
    This enables future UI connections to observe agent behavior in real-time.
    """
    
    def __init__(self, agent_id: str, history_size: int = 1000):
        self.agent_id = agent_id
        self.history = deque(maxlen=history_size)
        self.subscribers: List[Callable[[AgentEvent], None]] = []
        self._lock = asyncio.Lock()
    
    async def emit(self, event_type: EventType, data: Dict[str, Any], 
                   correlation_id: Optional[str] = None) -> None:
        """Emit an event to all subscribers.
        
        This is the core method called throughout the agent to report activity.
        """
        event = AgentEvent(
            timestamp=datetime.now(timezone.utc),
            agent_id=self.agent_id,
            event_type=event_type,
            data=data,
            correlation_id=correlation_id
        )
        
        async with self._lock:
            # Store in history
            self.history.append(event)
            
            # Notify all subscribers
            for subscriber in self.subscribers:
                try:
                    # Call subscriber in background to avoid blocking
                    asyncio.create_task(self._notify_subscriber(subscriber, event))
                except Exception as e:
                    # Log error but don't crash on subscriber failure
                    print(f"Error notifying subscriber: {e}")
    
    async def _notify_subscriber(self, subscriber: Callable, event: AgentEvent) -> None:
        """Notify a single subscriber, handling async/sync callbacks."""
        if asyncio.iscoroutinefunction(subscriber):
            await subscriber(event)
        else:
            subscriber(event)
    
    def subscribe(self, callback: Callable[[AgentEvent], None]) -> Callable[[], None]:
        """Subscribe to events. Returns unsubscribe function."""
        self.subscribers.append(callback)
        
        def unsubscribe():
            self.subscribers.remove(callback)
        
        return unsubscribe
    
    def get_history(self, limit: Optional[int] = None) -> List[AgentEvent]:
        """Get recent event history."""
        if limit:
            return list(self.history)[-limit:]
        return list(self.history)
    
    def clear_history(self) -> None:
        """Clear event history."""
        self.history.clear()
