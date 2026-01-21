
"""
A4: 数据采集Agent - 数据发布器
"""

from abc import ABC, abstractmethod
from typing import List, Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import json
import logging

logger = logging.getLogger(__name__)


class RobotStatusData(BaseModel):
    robot_id: str
    tenant_id: str
    timestamp: datetime
    state: str
    battery_level: int
    is_charging: bool = False
    current_task_id: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RobotPositionData(BaseModel):
    robot_id: str
    tenant_id: str
    timestamp: datetime
    x: float
    y: float
    floor_id: str
    heading: Optional[float] = None
    speed: Optional[float] = None


class TaskProgressData(BaseModel):
    task_id: str
    robot_id: str
    tenant_id: str
    timestamp: datetime
    progress_percent: int
    cleaned_area_sqm: float = 0.0
    remaining_area_sqm: float = 0.0
    estimated_completion: Optional[datetime] = None


class RobotErrorEvent(BaseModel):
    event_id: str
    robot_id: str
    tenant_id: str
    timestamp: datetime
    error_code: str
    error_message: str
    severity: str = "error"
    resolved: bool = False


class DataPublisher(ABC):
    @abstractmethod
    async def connect(self) -> None:
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        pass
    
    @abstractmethod
    async def publish_robot_status(self, status: RobotStatusData) -> None:
        pass
    
    @abstractmethod
    async def publish_robot_position(self, position: RobotPositionData) -> None:
        pass
    
    @abstractmethod
    async def publish_task_progress(self, progress: TaskProgressData) -> None:
        pass
    
    @abstractmethod
    async def publish_error_event(self, event: RobotErrorEvent) -> None:
        pass
    
    @abstractmethod
    async def publish_batch(self, data_list: List[Any]) -> int:
        pass


class InMemoryDataPublisher(DataPublisher):
    def __init__(self):
        self._connected = False
        self.status_records: List[RobotStatusData] = []
        self.position_records: List[RobotPositionData] = []
        self.progress_records: List[TaskProgressData] = []
        self.error_records: List[RobotErrorEvent] = []
        self._cache: Dict[str, Any] = {}
    
    async def connect(self) -> None:
        self._connected = True
    
    async def disconnect(self) -> None:
        self._connected = False
    
    async def is_connected(self) -> bool:
        return self._connected
    
    async def publish_robot_status(self, status: RobotStatusData) -> None:
        self.status_records.append(status)
        self._cache[f"robot:status:{status.robot_id}"] = status.model_dump()
    
    async def publish_robot_position(self, position: RobotPositionData) -> None:
        self.position_records.append(position)
        self._cache[f"robot:position:{position.robot_id}"] = position.model_dump()
    
    async def publish_task_progress(self, progress: TaskProgressData) -> None:
        self.progress_records.append(progress)
    
    async def publish_error_event(self, event: RobotErrorEvent) -> None:
        self.error_records.append(event)
    
    async def publish_batch(self, data_list: List[Any]) -> int:
        count = 0
        for data in data_list:
            if isinstance(data, RobotStatusData):
                await self.publish_robot_status(data)
                count += 1
            elif isinstance(data, RobotPositionData):
                await self.publish_robot_position(data)
                count += 1
        return count
    
    def get_cached(self, key: str) -> Optional[Dict]:
        return self._cache.get(key)
    
    def clear(self):
        self.status_records.clear()
        self.position_records.clear()
        self.progress_records.clear()
        self.error_records.clear()
        self._cache.clear()
