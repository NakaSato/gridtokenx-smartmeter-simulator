import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)

class ADREventType(Enum):
    LOAD_SHED = "LOAD_SHED"     # Direct Load Control (DLC)
    PRICE_SPIKE = "PRICE_SPIKE" # Critical Peak Pricing (CPP)

@dataclass
class ADREvent:
    event_id: str
    event_type: ADREventType
    start_time: datetime
    duration_minutes: int
    payload: float # MW to shed (for LOAD_SHED) or Price Multiplier (for PRICE_SPIKE)
    status: str # "SCHEDULED", "ACTIVE", "COMPLETED"
    
    @property
    def end_time(self) -> datetime:
        return self.start_time + timedelta(minutes=self.duration_minutes)

class ADRManager:
    """
    Manages Automated Demand Response (ADR) events.
    Simulates OpenADR logic where the utility publishes events and devices respond.
    """
    
    def __init__(self):
        self.events: List[ADREvent] = []
        
    def trigger_event(self, 
                     event_type: ADREventType, 
                     start_time: datetime, 
                     duration_minutes: int, 
                     payload: float) -> str:
        """
        Create and schedule a new ADR event.
        """
        event_id = str(uuid.uuid4())[:8]
        event = ADREvent(
            event_id=event_id,
            event_type=event_type,
            start_time=start_time,
            duration_minutes=duration_minutes,
            payload=payload,
            status="SCHEDULED"
        )
        self.events.append(event)
        logger.info(f"ADR Event Scheduled: {event_type.value} starting {start_time}")
        return event_id
        
    def get_active_event(self, current_time: datetime) -> Optional[ADREvent]:
        """
        Get the currently active event, if any.
        Updates statuses of events based on time.
        """
        active_event = None
        
        for event in self.events:
            if event.status == "COMPLETED":
                continue
                
            if event.start_time <= current_time < event.end_time:
                if event.status != "ACTIVE":
                    event.status = "ACTIVE"
                    logger.info(f"ADR Event STARTED: {event.event_id}")
                active_event = event
                
            elif current_time >= event.end_time and event.status != "COMPLETED":
                event.status = "COMPLETED"
                logger.info(f"ADR Event COMPLETED: {event.event_id}")
                
        return active_event

    def get_tariff_modifier(self, current_time: datetime) -> float:
        """
        Returns a price multiplier if a PRICE_SPIKE event is active.
        Returns 1.0 otherwise.
        """
        event = self.get_active_event(current_time)
        if event and event.event_type == ADREventType.PRICE_SPIKE:
            return event.payload
        return 1.0
        
    def get_load_shed_target(self, current_time: datetime) -> float:
        """
        Returns MW amount to shed if LOAD_SHED event is active.
        Returns 0.0 otherwise.
        """
        event = self.get_active_event(current_time)
        if event and event.event_type == ADREventType.LOAD_SHED:
            return event.payload
        return 0.0
