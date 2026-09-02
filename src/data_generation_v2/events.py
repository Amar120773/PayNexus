"""Event logging for temporal network evolution."""

from __future__ import annotations
import pandas as pd
from typing import Literal

EventType = Literal[
    "MERCHANT_ONBOARDED",
    "DEVICE_ADDED",
    "DEVICE_REMOVED",
    "IP_ADDED",
    "IP_REMOVED",
    "CUSTOMER_ACQUIRED",
    "SETTLEMENT_CHANGED",
    "VOLUME_SHIFT",
    "REFUND_SHIFT",
    "NETWORK_JOINED",
]

class EventLogger:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []
        
    def log(self, timestamp: pd.Timestamp, merchant_id: str, event_type: EventType, related_entity: str | None = None) -> None:
        self.events.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "merchant_id": merchant_id,
            "event_type": event_type,
            "related_entity": related_entity,
        })
        
    def to_dataframe(self) -> pd.DataFrame:
        if not self.events:
            return pd.DataFrame(columns=["timestamp", "merchant_id", "event_type", "related_entity"])
        df = pd.DataFrame(self.events)
        return df.sort_values("timestamp").reset_index(drop=True)

# Global singleton for easy tracking during generation
_global_logger = EventLogger()

def get_event_logger() -> EventLogger:
    return _global_logger
    
def reset_event_logger() -> None:
    global _global_logger
    _global_logger = EventLogger()
