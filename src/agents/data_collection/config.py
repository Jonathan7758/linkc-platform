"""
A4: 数据采集Agent - 配置模型
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CollectionStrategy(str, Enum):
    """采集策略"""
    POLLING = "polling"
    EVENT_DRIVEN = "event"
    HYBRID = "hybrid"


class DataType(str, Enum):
    """数据类型"""
    STATUS = "status"
    POSITION = "position"
    TASK_PROGRESS = "task"
    CONSUMABLES = "consumables"
    ERRORS = "errors"


class CollectionConfig(BaseModel):
    """单项数据采集配置"""
    data_type: DataType
    enabled: bool = True
    interval_seconds: int = Field(default=30, ge=1, le=3600)
    strategy: CollectionStrategy = CollectionStrategy.POLLING
    batch_size: int = Field(default=10, ge=1, le=100)
    timeout_seconds: int = Field(default=30, ge=5, le=120)
    retry_count: int = Field(default=3, ge=0, le=5)


class DataCollectionAgentConfig(BaseModel):
    """数据采集Agent配置"""
    agent_id: str = "data-collection-agent"
    tenant_id: str
    
    # 采集配置
    collections: List[CollectionConfig] = Field(default_factory=lambda: [
        CollectionConfig(data_type=DataType.STATUS, interval_seconds=30),
        CollectionConfig(data_type=DataType.POSITION, interval_seconds=5),
        CollectionConfig(data_type=DataType.TASK_PROGRESS, interval_seconds=10),
        CollectionConfig(data_type=DataType.CONSUMABLES, interval_seconds=3600),
        CollectionConfig(data_type=DataType.ERRORS, interval_seconds=60, strategy=CollectionStrategy.EVENT_DRIVEN),
    ])
    
    # 健康监控配置
    health_check_interval_seconds: int = 60
    max_collection_delay_seconds: int = 300

    class Config:
        use_enum_values = True


class CollectionResult(BaseModel):
    """采集结果"""
    data_type: DataType
    timestamp: datetime
    robot_count: int
    success_count: int
    failed_count: int
    duration_ms: int
    errors: List[str] = Field(default_factory=list)


class CollectionStats(BaseModel):
    """采集统计"""
    total_collections: int = 0
    successful: int = 0
    failed: int = 0
    avg_duration_ms: float = 0.0
    last_collection: Optional[datetime] = None
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def record_success(self, duration_ms: int):
        self.total_collections += 1
        self.successful += 1
        self.last_collection = datetime.utcnow()
        # Update rolling average
        if self.avg_duration_ms == 0:
            self.avg_duration_ms = duration_ms
        else:
            self.avg_duration_ms = (self.avg_duration_ms * 0.9) + (duration_ms * 0.1)

    def record_failure(self, error: str):
        self.total_collections += 1
        self.failed += 1
        self.last_error = error
        self.last_error_time = datetime.utcnow()


class HealthStatus(BaseModel):
    """健康状态"""
    healthy: bool = True
    checks: Dict[str, bool] = Field(default_factory=dict)
    issues: List[str] = Field(default_factory=list)
