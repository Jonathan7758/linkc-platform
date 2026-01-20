# 模块开发规格书：G6 数据查询API

## 文档信息
| 项目 | 内容 |
|-----|------|
| 模块ID | G6 |
| 模块名称 | 数据查询API |
| 版本 | 1.0 |
| 日期 | 2026年1月 |
| 状态 | 待开发 |
| 前置依赖 | F1数据模型, F4认证授权, D3数据查询服务 |

---

## 1. 模块概述

### 1.1 职责描述
数据查询API提供统一的数据查询和统计分析接口，支持KPI指标、效率分析、趋势分析、报表数据等查询，为运营控制台和战略驾驶舱提供数据支撑。

### 1.2 在系统中的位置
```
运营控制台 / 战略驾驶舱
         │
         ▼
┌─────────────────────────────────────┐
│         G6 数据查询API              │  ← 本模块
│   /api/v1/data/*                    │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│       D3 数据查询服务               │
└─────────────────────────────────────┘
```

### 1.3 输入/输出概述
| 方向 | 内容 |
|-----|------|
| 输入 | HTTP请求（查询参数、时间范围、聚合方式） |
| 输出 | JSON响应（统计数据、时序数据、报表数据） |
| 依赖 | D3数据查询服务、Redis缓存 |

---

## 2. API定义

### 2.1 KPI概览
```yaml
GET /api/v1/data/kpi/overview
描述: 获取关键KPI指标概览
权限: data:read

查询参数:
  - tenant_id: string (required)
  - building_id: string (optional) - 筛选楼宇
  - date: date (optional, default: today) - 统计日期

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "date": "2026-01-20",
      "cleaning": {
        "tasks_completed": 45,
        "tasks_total": 48,
        "completion_rate": 93.75,
        "total_area_cleaned": 12500.5,
        "average_efficiency": 145.8,
        "vs_yesterday": {
          "tasks_completed": 2,
          "completion_rate": 1.5,
          "efficiency": -2.3
        }
      },
      "robots": {
        "total": 15,
        "active": 12,
        "idle": 2,
        "charging": 1,
        "error": 0,
        "average_utilization": 78.5,
        "average_battery": 72.3
      },
      "alerts": {
        "critical": 0,
        "warning": 2,
        "info": 5
      },
      "agent": {
        "decisions_today": 156,
        "escalations_today": 3,
        "auto_resolution_rate": 94.5,
        "average_feedback_score": 4.2
      }
    }
  }
```

### 2.2 效率趋势
```yaml
GET /api/v1/data/efficiency/trend
描述: 获取清洁效率趋势数据
权限: data:read

查询参数:
  - tenant_id: string (required)
  - building_id: string (optional)
  - start_date: date (required)
  - end_date: date (required)
  - granularity: string (default: day) - hour/day/week/month
  - robot_id: string (optional) - 筛选单个机器人

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "granularity": "day",
      "series": [
        {
          "date": "2026-01-15",
          "efficiency": 142.5,
          "area_cleaned": 11200.0,
          "tasks_completed": 42,
          "working_hours": 78.6
        },
        {
          "date": "2026-01-16",
          "efficiency": 145.2,
          "area_cleaned": 11800.5,
          "tasks_completed": 44,
          "working_hours": 81.3
        }
      ],
      "summary": {
        "average_efficiency": 143.8,
        "total_area": 58500.5,
        "total_tasks": 215,
        "trend": "up",
        "trend_percent": 2.1
      }
    }
  }
```

### 2.3 机器人利用率
```yaml
GET /api/v1/data/robots/utilization
描述: 获取机器人利用率数据
权限: data:read

查询参数:
  - tenant_id: string (required)
  - building_id: string (optional)
  - start_date: date (required)
  - end_date: date (required)
  - granularity: string (default: day)

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "by_robot": [
        {
          "robot_id": "robot_001",
          "robot_name": "清洁机器人1号",
          "utilization_rate": 82.5,
          "working_hours": 156.3,
          "idle_hours": 33.2,
          "charging_hours": 20.5,
          "tasks_completed": 68
        }
      ],
      "overall": {
        "average_utilization": 78.5,
        "total_working_hours": 1250.5,
        "peak_hour": 10,
        "low_hour": 3
      },
      "by_hour": [
        {"hour": 0, "utilization": 15.2},
        {"hour": 1, "utilization": 12.5},
        {"hour": 8, "utilization": 85.3},
        {"hour": 10, "utilization": 92.1}
      ]
    }
  }
```

### 2.4 区域覆盖分析
```yaml
GET /api/v1/data/coverage/analysis
描述: 获取区域清洁覆盖分析
权限: data:read

查询参数:
  - tenant_id: string (required)
  - building_id: string (required)
  - floor_id: string (optional)
  - date: date (required)

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "building_id": "building_001",
      "date": "2026-01-20",
      "floors": [
        {
          "floor_id": "floor_001",
          "floor_name": "1F",
          "total_area": 2500.0,
          "cleaned_area": 2350.5,
          "coverage_rate": 94.02,
          "zones": [
            {
              "zone_id": "zone_001",
              "zone_name": "大堂",
              "area": 500.0,
              "cleaned_area": 500.0,
              "coverage_rate": 100.0,
              "clean_count": 3,
              "last_cleaned_at": "2026-01-20T14:30:00Z"
            },
            {
              "zone_id": "zone_002",
              "zone_name": "走廊A",
              "area": 200.0,
              "cleaned_area": 180.5,
              "coverage_rate": 90.25,
              "clean_count": 2,
              "last_cleaned_at": "2026-01-20T12:15:00Z"
            }
          ]
        }
      ],
      "summary": {
        "total_area": 12500.0,
        "cleaned_area": 11850.5,
        "overall_coverage": 94.8,
        "uncovered_zones": 3
      }
    }
  }
```

### 2.5 任务统计
```yaml
GET /api/v1/data/tasks/statistics
描述: 获取任务执行统计
权限: data:read

查询参数:
  - tenant_id: string (required)
  - building_id: string (optional)
  - start_date: date (required)
  - end_date: date (required)

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "summary": {
        "total_tasks": 215,
        "completed": 198,
        "failed": 8,
        "cancelled": 9,
        "completion_rate": 92.1,
        "average_duration": 42.5,
        "total_area": 58500.5
      },
      "by_status": {
        "completed": 198,
        "failed": 8,
        "cancelled": 9
      },
      "by_failure_reason": {
        "robot_error": 3,
        "battery_low": 2,
        "obstacle": 2,
        "timeout": 1
      },
      "by_zone_type": {
        "lobby": {"count": 45, "area": 12500.0},
        "corridor": {"count": 80, "area": 20000.0},
        "office": {"count": 60, "area": 18000.0},
        "restroom": {"count": 30, "area": 8000.5}
      },
      "performance_distribution": {
        "excellent": 85,
        "good": 78,
        "average": 30,
        "poor": 5
      }
    }
  }
```

### 2.6 告警统计
```yaml
GET /api/v1/data/alerts/statistics
描述: 获取告警统计数据
权限: data:read

查询参数:
  - tenant_id: string (required)
  - start_date: date (required)
  - end_date: date (required)

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "summary": {
        "total": 45,
        "resolved": 40,
        "pending": 5,
        "average_resolution_time": 15.3
      },
      "by_level": {
        "critical": 2,
        "warning": 18,
        "info": 25
      },
      "by_type": {
        "battery_anomaly": 8,
        "task_timeout": 12,
        "robot_error": 5,
        "coverage_low": 10,
        "schedule_conflict": 10
      },
      "trend": [
        {"date": "2026-01-15", "count": 8},
        {"date": "2026-01-16", "count": 6},
        {"date": "2026-01-17", "count": 10}
      ],
      "top_robots": [
        {"robot_id": "robot_003", "robot_name": "3号", "alert_count": 8},
        {"robot_id": "robot_007", "robot_name": "7号", "alert_count": 6}
      ]
    }
  }
```

### 2.7 对比分析
```yaml
POST /api/v1/data/comparison
描述: 多维度对比分析
权限: data:read

请求体:
  {
    "tenant_id": "tenant_001",
    "comparison_type": "robot",  # robot/floor/period
    "subjects": ["robot_001", "robot_002", "robot_003"],
    "metrics": ["efficiency", "utilization", "task_count", "error_rate"],
    "start_date": "2026-01-01",
    "end_date": "2026-01-20"
  }

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "comparison_type": "robot",
      "period": {
        "start": "2026-01-01",
        "end": "2026-01-20"
      },
      "results": [
        {
          "subject_id": "robot_001",
          "subject_name": "清洁机器人1号",
          "metrics": {
            "efficiency": 148.5,
            "utilization": 82.3,
            "task_count": 68,
            "error_rate": 1.5
          },
          "rank": 1
        },
        {
          "subject_id": "robot_002",
          "subject_name": "清洁机器人2号",
          "metrics": {
            "efficiency": 142.3,
            "utilization": 78.5,
            "task_count": 62,
            "error_rate": 2.1
          },
          "rank": 2
        }
      ],
      "best_performer": {
        "efficiency": "robot_001",
        "utilization": "robot_001",
        "task_count": "robot_001",
        "error_rate": "robot_001"
      }
    }
  }
```

### 2.8 导出报表
```yaml
POST /api/v1/data/export
描述: 导出数据报表
权限: data:export

请求体:
  {
    "tenant_id": "tenant_001",
    "report_type": "daily_summary",  # daily_summary/weekly_report/monthly_report/custom
    "format": "xlsx",  # xlsx/csv/pdf
    "date_range": {
      "start": "2026-01-01",
      "end": "2026-01-20"
    },
    "include_sections": ["kpi", "efficiency", "robots", "tasks", "alerts"],
    "filters": {
      "building_id": "building_001"
    }
  }

响应 200:
  {
    "code": 0,
    "message": "Report generation started",
    "data": {
      "export_id": "export_001",
      "status": "processing",
      "estimated_time": 30
    }
  }
```

### 2.9 获取导出状态
```yaml
GET /api/v1/data/export/{export_id}
描述: 获取导出任务状态
权限: data:export

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "export_id": "export_001",
      "status": "completed",  # processing/completed/failed
      "download_url": "https://storage.linkc.com/exports/report_001.xlsx",
      "expires_at": "2026-01-21T10:30:00Z",
      "file_size": 256000
    }
  }
```

### 2.10 实时仪表板数据
```yaml
GET /api/v1/data/dashboard/realtime
描述: 获取实时仪表板数据（用于自动刷新）
权限: data:read

查询参数:
  - tenant_id: string (required)
  - building_id: string (optional)

响应 200:
  {
    "code": 0,
    "message": "success",
    "data": {
      "timestamp": "2026-01-20T10:30:00Z",
      "robots": {
        "working": 8,
        "idle": 4,
        "charging": 2,
        "error": 1
      },
      "current_tasks": {
        "in_progress": 8,
        "queued": 3,
        "completed_today": 32
      },
      "efficiency_now": 147.5,
      "coverage_today": 68.5,
      "active_alerts": 2,
      "pending_items": 1
    }
  }
```

---

## 3. 数据模型

### 3.1 请求/响应模型
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum

class Granularity(str, Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

class ComparisonType(str, Enum):
    ROBOT = "robot"
    FLOOR = "floor"
    PERIOD = "period"

class ExportFormat(str, Enum):
    XLSX = "xlsx"
    CSV = "csv"
    PDF = "pdf"

class ReportType(str, Enum):
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_REPORT = "weekly_report"
    MONTHLY_REPORT = "monthly_report"
    CUSTOM = "custom"

# KPI概览
class KPIOverviewResponse(BaseModel):
    date: date
    cleaning: dict
    robots: dict
    alerts: dict
    agent: dict

# 效率趋势
class EfficiencyPoint(BaseModel):
    date: date
    efficiency: float
    area_cleaned: float
    tasks_completed: int
    working_hours: float

class EfficiencyTrendResponse(BaseModel):
    granularity: Granularity
    series: List[EfficiencyPoint]
    summary: dict

# 对比分析
class ComparisonRequest(BaseModel):
    tenant_id: str
    comparison_type: ComparisonType
    subjects: List[str] = Field(min_length=2, max_length=10)
    metrics: List[str]
    start_date: date
    end_date: date

class ComparisonResult(BaseModel):
    subject_id: str
    subject_name: str
    metrics: Dict[str, float]
    rank: int

class ComparisonResponse(BaseModel):
    comparison_type: ComparisonType
    period: dict
    results: List[ComparisonResult]
    best_performer: Dict[str, str]

# 导出
class ExportRequest(BaseModel):
    tenant_id: str
    report_type: ReportType
    format: ExportFormat
    date_range: dict
    include_sections: List[str]
    filters: Optional[dict] = None

class ExportStatusResponse(BaseModel):
    export_id: str
    status: str
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    file_size: Optional[int] = None
```

---

## 4. 实现要求

### 4.1 技术栈
- Python 3.11+
- FastAPI
- Pydantic v2
- Redis (缓存)
- Pandas (数据处理)
- openpyxl/xlsxwriter (Excel导出)

### 4.2 核心实现

#### 路由器结构
```python
from fastapi import APIRouter, Depends, BackgroundTasks

router = APIRouter(prefix="/api/v1/data", tags=["data"])

@router.get("/kpi/overview", response_model=ApiResponse[KPIOverviewResponse])
async def get_kpi_overview(
    tenant_id: str,
    building_id: Optional[str] = None,
    date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    data_service: DataService = Depends(get_data_service)
):
    """获取KPI概览"""
    pass

@router.get("/efficiency/trend", response_model=ApiResponse[EfficiencyTrendResponse])
async def get_efficiency_trend(
    tenant_id: str,
    start_date: date,
    end_date: date,
    building_id: Optional[str] = None,
    granularity: Granularity = Granularity.DAY,
    robot_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    data_service: DataService = Depends(get_data_service)
):
    """获取效率趋势"""
    pass

@router.post("/comparison", response_model=ApiResponse[ComparisonResponse])
async def compare_data(
    request: ComparisonRequest,
    current_user: User = Depends(get_current_user),
    data_service: DataService = Depends(get_data_service)
):
    """多维度对比分析"""
    pass

@router.post("/export", response_model=ApiResponse[dict])
async def export_report(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service)
):
    """导出报表"""
    export_id = await export_service.create_export(request)
    background_tasks.add_task(export_service.generate_report, export_id)
    return {"export_id": export_id, "status": "processing"}
```

#### 数据服务层
```python
class DataService:
    def __init__(
        self,
        query_service: DataQueryService,
        cache: Redis
    ):
        self.query_service = query_service
        self.cache = cache
    
    async def get_kpi_overview(
        self,
        tenant_id: str,
        building_id: Optional[str],
        query_date: date
    ) -> KPIOverviewResponse:
        """获取KPI概览，带缓存"""
        cache_key = f"kpi:overview:{tenant_id}:{building_id}:{query_date}"
        
        cached = await self.cache.get(cache_key)
        if cached:
            return KPIOverviewResponse.model_validate_json(cached)
        
        data = await self._compute_kpi_overview(tenant_id, building_id, query_date)
        
        await self.cache.setex(cache_key, 300, data.model_dump_json())  # 5分钟缓存
        return data
    
    async def get_efficiency_trend(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date,
        granularity: Granularity,
        filters: dict
    ) -> EfficiencyTrendResponse:
        """获取效率趋势"""
        raw_data = await self.query_service.query_efficiency(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity.value,
            **filters
        )
        
        series = [EfficiencyPoint(**row) for row in raw_data]
        summary = self._compute_summary(series)
        
        return EfficiencyTrendResponse(
            granularity=granularity,
            series=series,
            summary=summary
        )
```

#### 导出服务
```python
class ExportService:
    def __init__(
        self,
        data_service: DataService,
        storage: ObjectStorage
    ):
        self.data_service = data_service
        self.storage = storage
    
    async def create_export(self, request: ExportRequest) -> str:
        """创建导出任务"""
        export_id = f"export_{uuid.uuid4().hex[:8]}"
        # 保存任务状态到数据库
        return export_id
    
    async def generate_report(self, export_id: str):
        """后台生成报表"""
        try:
            request = await self._get_export_request(export_id)
            
            # 获取数据
            data = await self._collect_report_data(request)
            
            # 生成文件
            if request.format == ExportFormat.XLSX:
                file_path = await self._generate_xlsx(data, request)
            elif request.format == ExportFormat.CSV:
                file_path = await self._generate_csv(data, request)
            else:
                file_path = await self._generate_pdf(data, request)
            
            # 上传到存储
            download_url = await self.storage.upload(file_path)
            
            # 更新状态
            await self._update_export_status(export_id, "completed", download_url)
            
        except Exception as e:
            await self._update_export_status(export_id, "failed", error=str(e))
    
    async def _generate_xlsx(self, data: dict, request: ExportRequest) -> str:
        """生成Excel文件"""
        import pandas as pd
        from openpyxl import Workbook
        
        wb = Workbook()
        
        if "kpi" in request.include_sections:
            ws = wb.create_sheet("KPI概览")
            # 写入KPI数据
        
        if "efficiency" in request.include_sections:
            ws = wb.create_sheet("效率趋势")
            df = pd.DataFrame(data["efficiency"])
            # 写入效率数据
        
        file_path = f"/tmp/{request.tenant_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        wb.save(file_path)
        return file_path
```

### 4.3 缓存策略
```python
CACHE_CONFIG = {
    "kpi_overview": {"ttl": 300, "key_pattern": "kpi:overview:{tenant}:{building}:{date}"},
    "efficiency_trend": {"ttl": 600, "key_pattern": "efficiency:{tenant}:{start}:{end}:{granularity}"},
    "robot_utilization": {"ttl": 600, "key_pattern": "utilization:{tenant}:{start}:{end}"},
    "coverage_analysis": {"ttl": 300, "key_pattern": "coverage:{building}:{floor}:{date}"},
    "dashboard_realtime": {"ttl": 30, "key_pattern": "dashboard:{tenant}:{building}"}
}
```

---

## 5. 测试要求

### 5.1 单元测试用例
```python
import pytest
from datetime import date

@pytest.mark.asyncio
async def test_get_kpi_overview(client, auth_headers):
    """测试KPI概览"""
    response = await client.get(
        "/api/v1/data/kpi/overview",
        params={"tenant_id": "tenant_001"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "cleaning" in data
    assert "robots" in data
    assert "alerts" in data

@pytest.mark.asyncio
async def test_efficiency_trend(client, auth_headers):
    """测试效率趋势"""
    response = await client.get(
        "/api/v1/data/efficiency/trend",
        params={
            "tenant_id": "tenant_001",
            "start_date": "2026-01-01",
            "end_date": "2026-01-20"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "series" in response.json()["data"]

@pytest.mark.asyncio
async def test_comparison(client, auth_headers):
    """测试对比分析"""
    response = await client.post(
        "/api/v1/data/comparison",
        json={
            "tenant_id": "tenant_001",
            "comparison_type": "robot",
            "subjects": ["robot_001", "robot_002"],
            "metrics": ["efficiency", "utilization"],
            "start_date": "2026-01-01",
            "end_date": "2026-01-20"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    assert len(response.json()["data"]["results"]) == 2

@pytest.mark.asyncio
async def test_export_report(client, auth_headers):
    """测试导出报表"""
    response = await client.post(
        "/api/v1/data/export",
        json={
            "tenant_id": "tenant_001",
            "report_type": "daily_summary",
            "format": "xlsx",
            "date_range": {"start": "2026-01-01", "end": "2026-01-20"},
            "include_sections": ["kpi", "efficiency"]
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "export_id" in response.json()["data"]
```

---

## 6. 验收标准

### 6.1 功能验收
- [ ] KPI概览数据正确
- [ ] 效率趋势计算准确
- [ ] 利用率统计正确
- [ ] 覆盖率分析正确
- [ ] 对比分析功能正常
- [ ] 报表导出正常

### 6.2 性能要求
- KPI概览查询 < 200ms
- 趋势查询 < 500ms
- 缓存命中率 > 80%
- 报表导出 < 30s

### 6.3 代码质量
- 测试覆盖率 > 80%
- 类型注解完整
