"""Prometheus-compatible metrics collection for agents."""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from collections import defaultdict
import asyncio

from ..core.logging import AgentLogger


@dataclass
class MetricValue:
    """A single metric value with timestamp."""
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collects and exposes Prometheus-compatible metrics."""
    
    def __init__(self):
        self.logger = AgentLogger("metrics", "INFO")
        
        # Counter metrics (only increase)
        self._counters: Dict[str, List[MetricValue]] = defaultdict(list)
        
        # Gauge metrics (can go up/down)
        self._gauges: Dict[str, List[MetricValue]] = defaultdict(list)
        
        # Histogram metrics (track distributions)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        
        # Metric metadata
        self._metadata: Dict[str, Dict[str, str]] = {}
        
    def register_metric(self, name: str, metric_type: str, help_text: str):
        """Register a metric with metadata."""
        self._metadata[name] = {
            "type": metric_type,
            "help": help_text
        }
        
    def inc_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        if labels is None:
            labels = {}
            
        # Find existing metric with same labels or create new
        key = self._make_key(name, labels)
        
        if key in self._counters and self._counters[key]:
            # Increment existing value
            last_value = self._counters[key][-1].value
            self._counters[key].append(MetricValue(last_value + value, labels=labels))
        else:
            # New counter starts at value
            self._counters[key] = [MetricValue(value, labels=labels)]
            
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric value."""
        if labels is None:
            labels = {}
            
        key = self._make_key(name, labels)
        self._gauges[key] = [MetricValue(value, labels=labels)]
        
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Add an observation to a histogram."""
        if labels is None:
            labels = {}
            
        key = self._make_key(name, labels)
        self._histograms[key].append(value)
        
    def _make_key(self, name: str, labels: Dict[str, str]) -> str:
        """Create a unique key for metric + labels."""
        if not labels:
            return name
            
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
        
    def get_metrics_prometheus(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []
        
        # Add metadata
        for name, meta in self._metadata.items():
            lines.append(f'# HELP {name} {meta["help"]}')
            lines.append(f'# TYPE {name} {meta["type"]}')
            
            # Add metric values based on type
            if meta["type"] == "counter":
                for key, values in self._counters.items():
                    if key.startswith(name):
                        if values:
                            lines.append(f"{key} {values[-1].value}")
                            
            elif meta["type"] == "gauge":
                for key, values in self._gauges.items():
                    if key.startswith(name):
                        if values:
                            lines.append(f"{key} {values[-1].value}")
                            
            elif meta["type"] == "histogram":
                for key, observations in self._histograms.items():
                    if key.startswith(name):
                        if observations:
                            # Calculate histogram stats
                            sorted_obs = sorted(observations)
                            count = len(sorted_obs)
                            total = sum(sorted_obs)
                            
                            # Add histogram metrics
                            base_key = key.replace(name, "")
                            lines.append(f'{name}_bucket{{le="0.005"{base_key}}} {sum(1 for x in sorted_obs if x <= 0.005)}')
                            lines.append(f'{name}_bucket{{le="0.01"{base_key}}} {sum(1 for x in sorted_obs if x <= 0.01)}')
                            lines.append(f'{name}_bucket{{le="0.025"{base_key}}} {sum(1 for x in sorted_obs if x <= 0.025)}')
                            lines.append(f'{name}_bucket{{le="0.05"{base_key}}} {sum(1 for x in sorted_obs if x <= 0.05)}')
                            lines.append(f'{name}_bucket{{le="0.1"{base_key}}} {sum(1 for x in sorted_obs if x <= 0.1)}')
                            lines.append(f'{name}_bucket{{le="0.25"{base_key}}} {sum(1 for x in sorted_obs if x <= 0.25)}')
                            lines.append(f'{name}_bucket{{le="0.5"{base_key}}} {sum(1 for x in sorted_obs if x <= 0.5)}')
                            lines.append(f'{name}_bucket{{le="1"{base_key}}} {sum(1 for x in sorted_obs if x <= 1)}')
                            lines.append(f'{name}_bucket{{le="2.5"{base_key}}} {sum(1 for x in sorted_obs if x <= 2.5)}')
                            lines.append(f'{name}_bucket{{le="5"{base_key}}} {sum(1 for x in sorted_obs if x <= 5)}')
                            lines.append(f'{name}_bucket{{le="10"{base_key}}} {sum(1 for x in sorted_obs if x <= 10)}')
                            lines.append(f'{name}_bucket{{le="+Inf"{base_key}}} {count}')
                            lines.append(f"{name}_sum{base_key} {total}")
                            lines.append(f"{name}_count{base_key} {count}")
            
            lines.append("")  # Empty line between metrics
            
        return "\n".join(lines)
        
    def get_metrics_json(self) -> Dict[str, Any]:
        """Export metrics in JSON format."""
        result = {
            "counters": {},
            "gauges": {},
            "histograms": {}
        }
        
        # Export counters
        for key, values in self._counters.items():
            if values:
                result["counters"][key] = {
                    "value": values[-1].value,
                    "timestamp": values[-1].timestamp,
                    "labels": values[-1].labels
                }
                
        # Export gauges
        for key, values in self._gauges.items():
            if values:
                result["gauges"][key] = {
                    "value": values[-1].value,
                    "timestamp": values[-1].timestamp,
                    "labels": values[-1].labels
                }
                
        # Export histograms
        for key, observations in self._histograms.items():
            if observations:
                sorted_obs = sorted(observations)
                result["histograms"][key] = {
                    "count": len(sorted_obs),
                    "sum": sum(sorted_obs),
                    "min": sorted_obs[0],
                    "max": sorted_obs[-1],
                    "avg": sum(sorted_obs) / len(sorted_obs),
                    "p50": sorted_obs[len(sorted_obs) // 2],
                    "p95": sorted_obs[int(len(sorted_obs) * 0.95)] if len(sorted_obs) > 1 else sorted_obs[0],
                    "p99": sorted_obs[int(len(sorted_obs) * 0.99)] if len(sorted_obs) > 1 else sorted_obs[0]
                }
                
        return result


class AgentMetrics:
    """Standard metrics for agent framework."""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        
        # Register standard metrics
        self._register_standard_metrics()
        
    def _register_standard_metrics(self):
        """Register all standard agent metrics."""
        # Agent lifecycle
        self.collector.register_metric(
            "agent_up", "gauge", 
            "Whether the agent is up (1) or down (0)"
        )
        self.collector.register_metric(
            "agent_start_time", "gauge",
            "Unix timestamp when agent started"
        )
        self.collector.register_metric(
            "agent_restarts_total", "counter",
            "Total number of agent restarts"
        )
        
        # Connections
        self.collector.register_metric(
            "agent_connections_active", "gauge",
            "Number of active peer connections"
        )
        self.collector.register_metric(
            "agent_connections_total", "counter",
            "Total number of connections established"
        )
        self.collector.register_metric(
            "agent_connection_errors_total", "counter",
            "Total number of connection errors"
        )
        
        # Messages
        self.collector.register_metric(
            "agent_messages_sent_total", "counter",
            "Total messages sent to peers"
        )
        self.collector.register_metric(
            "agent_messages_received_total", "counter",
            "Total messages received from peers"
        )
        self.collector.register_metric(
            "agent_message_errors_total", "counter",
            "Total message processing errors"
        )
        
        # Performance
        self.collector.register_metric(
            "agent_message_duration_seconds", "histogram",
            "Time to process messages in seconds"
        )
        self.collector.register_metric(
            "agent_llm_request_duration_seconds", "histogram",
            "Time for LLM API calls in seconds"
        )
        
        # Health
        self.collector.register_metric(
            "agent_health_check_duration_seconds", "histogram",
            "Duration of health checks in seconds"
        )
        self.collector.register_metric(
            "agent_health_check_failures_total", "counter",
            "Total number of failed health checks"
        )
        
    def set_agent_up(self, agent_name: str, is_up: bool):
        """Set agent up/down status."""
        self.collector.set_gauge(
            "agent_up", 
            1.0 if is_up else 0.0,
            {"agent": agent_name}
        )
        
    def set_agent_start_time(self, agent_name: str, start_time: float):
        """Set agent start time."""
        self.collector.set_gauge(
            "agent_start_time",
            start_time,
            {"agent": agent_name}
        )
        
    def inc_restarts(self, agent_name: str):
        """Increment restart counter."""
        self.collector.inc_counter(
            "agent_restarts_total",
            labels={"agent": agent_name}
        )
        
    def set_active_connections(self, agent_name: str, count: int):
        """Set number of active connections."""
        self.collector.set_gauge(
            "agent_connections_active",
            float(count),
            {"agent": agent_name}
        )
        
    def inc_connections(self, agent_name: str, peer_name: str):
        """Increment connection counter."""
        self.collector.inc_counter(
            "agent_connections_total",
            labels={"agent": agent_name, "peer": peer_name}
        )
        
    def inc_connection_errors(self, agent_name: str, peer_name: str, error_type: str):
        """Increment connection error counter."""
        self.collector.inc_counter(
            "agent_connection_errors_total",
            labels={"agent": agent_name, "peer": peer_name, "type": error_type}
        )
        
    def inc_messages_sent(self, agent_name: str, peer_name: str):
        """Increment sent message counter."""
        self.collector.inc_counter(
            "agent_messages_sent_total",
            labels={"agent": agent_name, "peer": peer_name}
        )
        
    def inc_messages_received(self, agent_name: str, peer_name: str):
        """Increment received message counter."""
        self.collector.inc_counter(
            "agent_messages_received_total",
            labels={"agent": agent_name, "peer": peer_name}
        )
        
    def observe_message_duration(self, agent_name: str, duration: float):
        """Record message processing duration."""
        self.collector.observe_histogram(
            "agent_message_duration_seconds",
            duration,
            {"agent": agent_name}
        )
        
    def observe_llm_duration(self, agent_name: str, provider: str, duration: float):
        """Record LLM request duration."""
        self.collector.observe_histogram(
            "agent_llm_request_duration_seconds",
            duration,
            {"agent": agent_name, "provider": provider}
        )
