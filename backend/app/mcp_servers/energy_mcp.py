"""能耗分析MCP Server模块"""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcp_servers.base_mcp_server import (
    BaseMCPServer,
    MCPServerType,
    MCPTool,
    ToolParameter,
)
from app.models.energy import EnergyReading, EnergyType


class EnergyMCPServer(BaseMCPServer):
    """能耗分析MCP Server

    提供能耗查询、趋势分析、对比分析等功能。
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        super().__init__(MCPServerType.ENERGY)

    def _register_tools(self) -> None:
        """注册能耗分析工具"""

        # 1. 获取能耗数据
        self.register_tool(
            MCPTool(
                name="get_energy_consumption",
                description="获取能耗消耗数据，支持按能源类型、建筑、系统、时间范围查询",
                parameters=[
                    ToolParameter(
                        name="energy_type",
                        type="string",
                        description="能源类型: electricity/water/gas/steam/cooling",
                        required=False,
                        enum=["electricity", "water", "gas", "steam", "cooling"],
                    ),
                    ToolParameter(
                        name="building",
                        type="string",
                        description="建筑名称，如 A栋, B栋",
                        required=False,
                    ),
                    ToolParameter(
                        name="system_type",
                        type="string",
                        description="系统类型，如 hvac, lighting",
                        required=False,
                    ),
                    ToolParameter(
                        name="hours",
                        type="integer",
                        description="查询最近多少小时，默认24",
                        required=False,
                        default=24,
                    ),
                ],
                handler=self._get_energy_consumption,
            )
        )

        # 2. 获取能耗趋势
        self.register_tool(
            MCPTool(
                name="get_energy_trend",
                description="获取能耗趋势数据，用于生成趋势图",
                parameters=[
                    ToolParameter(
                        name="energy_type",
                        type="string",
                        description="能源类型",
                        required=False,
                        enum=["electricity", "water", "gas"],
                        default="electricity",
                    ),
                    ToolParameter(
                        name="building",
                        type="string",
                        description="建筑名称",
                        required=False,
                    ),
                    ToolParameter(
                        name="period",
                        type="string",
                        description="聚合周期: hour/day/week",
                        required=False,
                        enum=["hour", "day", "week"],
                        default="day",
                    ),
                    ToolParameter(
                        name="days",
                        type="integer",
                        description="查询天数，默认7",
                        required=False,
                        default=7,
                    ),
                ],
                handler=self._get_energy_trend,
            )
        )

        # 3. 获取同比环比
        self.register_tool(
            MCPTool(
                name="get_energy_comparison",
                description="获取能耗同比或环比对比",
                parameters=[
                    ToolParameter(
                        name="energy_type",
                        type="string",
                        description="能源类型",
                        required=False,
                        enum=["electricity", "water", "gas"],
                        default="electricity",
                    ),
                    ToolParameter(
                        name="building",
                        type="string",
                        description="建筑名称",
                        required=False,
                    ),
                    ToolParameter(
                        name="compare_type",
                        type="string",
                        description="对比类型: yoy(同比)/mom(月环比)/wow(周环比)",
                        required=False,
                        enum=["yoy", "mom", "wow"],
                        default="mom",
                    ),
                ],
                handler=self._get_energy_comparison,
            )
        )

        # 4. 获取能耗排名
        self.register_tool(
            MCPTool(
                name="get_energy_ranking",
                description="获取能耗排名，找出能耗最高的建筑或系统",
                parameters=[
                    ToolParameter(
                        name="energy_type",
                        type="string",
                        description="能源类型",
                        required=False,
                        enum=["electricity", "water", "gas"],
                        default="electricity",
                    ),
                    ToolParameter(
                        name="group_by",
                        type="string",
                        description="分组维度: building/floor/system_type",
                        required=False,
                        enum=["building", "floor", "system_type"],
                        default="building",
                    ),
                    ToolParameter(
                        name="days",
                        type="integer",
                        description="统计天数，默认7",
                        required=False,
                        default=7,
                    ),
                    ToolParameter(
                        name="limit",
                        type="integer",
                        description="返回数量，默认10",
                        required=False,
                        default=10,
                    ),
                ],
                handler=self._get_energy_ranking,
            )
        )

        # 5. 检测能耗异常
        self.register_tool(
            MCPTool(
                name="get_energy_anomaly",
                description="检测能耗异常，发现用量突增或异常波动",
                parameters=[
                    ToolParameter(
                        name="building",
                        type="string",
                        description="建筑名称",
                        required=False,
                    ),
                    ToolParameter(
                        name="threshold",
                        type="number",
                        description="异常阈值倍数，默认1.5（超过平均值的1.5倍视为异常）",
                        required=False,
                        default=1.5,
                    ),
                    ToolParameter(
                        name="hours",
                        type="integer",
                        description="分析最近多少小时，默认24",
                        required=False,
                        default=24,
                    ),
                ],
                handler=self._get_energy_anomaly,
            )
        )

    async def _get_energy_consumption(self, args: dict[str, Any]) -> dict[str, Any]:
        """获取能耗数据"""
        energy_type = args.get("energy_type")
        building = args.get("building")
        system_type = args.get("system_type")
        hours = args.get("hours", 24)

        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = select(EnergyReading).where(EnergyReading.timestamp >= since)

        if energy_type:
            query = query.where(EnergyReading.energy_type == energy_type)
        if building:
            query = query.where(EnergyReading.building == building)
        if system_type:
            query = query.where(EnergyReading.system_type == system_type)

        query = query.order_by(EnergyReading.timestamp.desc())

        result = await self.db.execute(query)
        readings = result.scalars().all()

        # 计算总量和平均值
        total = sum(r.value for r in readings)
        avg = total / len(readings) if readings else 0

        # 按类型分组统计
        by_type: dict[str, float] = {}
        for r in readings:
            by_type[r.energy_type] = by_type.get(r.energy_type, 0) + r.value

        return {
            "period_hours": hours,
            "total_readings": len(readings),
            "total_consumption": round(total, 2),
            "average_consumption": round(avg, 2),
            "by_type": by_type,
            "readings": [
                {
                    "meter_id": r.meter_id,
                    "energy_type": r.energy_type,
                    "value": r.value,
                    "unit": r.unit,
                    "building": r.building,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                }
                for r in readings[:20]  # 只返回最近20条
            ],
        }

    async def _get_energy_trend(self, args: dict[str, Any]) -> dict[str, Any]:
        """获取能耗趋势"""
        energy_type = args.get("energy_type", "electricity")
        building = args.get("building")
        period = args.get("period", "day")
        days = args.get("days", 7)

        since = datetime.now(timezone.utc) - timedelta(days=days)

        query = select(EnergyReading).where(
            EnergyReading.timestamp >= since,
            EnergyReading.energy_type == energy_type,
        )

        if building:
            query = query.where(EnergyReading.building == building)

        query = query.order_by(EnergyReading.timestamp.asc())

        result = await self.db.execute(query)
        readings = result.scalars().all()

        # 按周期聚合
        trend_data: dict[str, float] = {}
        for r in readings:
            if period == "hour":
                key = r.timestamp.strftime("%Y-%m-%d %H:00")
            elif period == "day":
                key = r.timestamp.strftime("%Y-%m-%d")
            else:  # week
                key = r.timestamp.strftime("%Y-W%W")
            trend_data[key] = trend_data.get(key, 0) + r.value

        trend_list = [
            {"period": k, "value": round(v, 2)}
            for k, v in sorted(trend_data.items())
        ]

        return {
            "energy_type": energy_type,
            "building": building,
            "period": period,
            "days": days,
            "data_points": len(trend_list),
            "trend": trend_list,
        }

    async def _get_energy_comparison(self, args: dict[str, Any]) -> dict[str, Any]:
        """获取同比环比"""
        energy_type = args.get("energy_type", "electricity")
        building = args.get("building")
        compare_type = args.get("compare_type", "mom")

        now = datetime.now(timezone.utc)

        # 确定当前期和对比期的时间范围
        if compare_type == "yoy":  # 年同比
            current_start = now - timedelta(days=30)
            previous_start = current_start - timedelta(days=365)
            previous_end = now - timedelta(days=365)
        elif compare_type == "mom":  # 月环比
            current_start = now - timedelta(days=30)
            previous_start = current_start - timedelta(days=30)
            previous_end = current_start
        else:  # wow - 周环比
            current_start = now - timedelta(days=7)
            previous_start = current_start - timedelta(days=7)
            previous_end = current_start

        # 当前期查询
        current_query = select(func.sum(EnergyReading.value)).where(
            EnergyReading.timestamp >= current_start,
            EnergyReading.timestamp <= now,
            EnergyReading.energy_type == energy_type,
        )
        if building:
            current_query = current_query.where(EnergyReading.building == building)

        # 对比期查询
        previous_query = select(func.sum(EnergyReading.value)).where(
            EnergyReading.timestamp >= previous_start,
            EnergyReading.timestamp <= previous_end,
            EnergyReading.energy_type == energy_type,
        )
        if building:
            previous_query = previous_query.where(EnergyReading.building == building)

        current_result = await self.db.execute(current_query)
        current_value = current_result.scalar() or 0

        previous_result = await self.db.execute(previous_query)
        previous_value = previous_result.scalar() or 0

        # 计算变化率
        if previous_value > 0:
            change_rate = (current_value - previous_value) / previous_value * 100
        else:
            change_rate = 0 if current_value == 0 else 100

        return {
            "energy_type": energy_type,
            "building": building,
            "compare_type": compare_type,
            "current_period": {
                "start": current_start.isoformat(),
                "end": now.isoformat(),
                "value": round(current_value, 2),
            },
            "previous_period": {
                "start": previous_start.isoformat(),
                "end": previous_end.isoformat(),
                "value": round(previous_value, 2),
            },
            "change_rate": round(change_rate, 2),
            "trend": "up" if change_rate > 0 else ("down" if change_rate < 0 else "stable"),
        }

    async def _get_energy_ranking(self, args: dict[str, Any]) -> dict[str, Any]:
        """获取能耗排名"""
        energy_type = args.get("energy_type", "electricity")
        group_by = args.get("group_by", "building")
        days = args.get("days", 7)
        limit = args.get("limit", 10)

        since = datetime.now(timezone.utc) - timedelta(days=days)

        # 根据分组维度选择字段
        group_column = getattr(EnergyReading, group_by, EnergyReading.building)

        query = (
            select(group_column, func.sum(EnergyReading.value).label("total"))
            .where(
                EnergyReading.timestamp >= since,
                EnergyReading.energy_type == energy_type,
                group_column.isnot(None),
            )
            .group_by(group_column)
            .order_by(func.sum(EnergyReading.value).desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        ranking = [
            {
                "rank": i + 1,
                "name": row[0],
                "consumption": round(row[1], 2) if row[1] else 0,
            }
            for i, row in enumerate(rows)
        ]

        return {
            "energy_type": energy_type,
            "group_by": group_by,
            "period_days": days,
            "ranking": ranking,
        }

    async def _get_energy_anomaly(self, args: dict[str, Any]) -> dict[str, Any]:
        """检测能耗异常"""
        building = args.get("building")
        threshold = args.get("threshold", 1.5)
        hours = args.get("hours", 24)

        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = select(EnergyReading).where(EnergyReading.timestamp >= since)

        if building:
            query = query.where(EnergyReading.building == building)

        result = await self.db.execute(query)
        readings = result.scalars().all()

        if not readings:
            return {
                "period_hours": hours,
                "threshold": threshold,
                "anomalies": [],
                "message": "无能耗数据",
            }

        # 按能源类型计算平均值
        type_values: dict[str, list[float]] = {}
        for r in readings:
            if r.energy_type not in type_values:
                type_values[r.energy_type] = []
            type_values[r.energy_type].append(r.value)

        type_avg = {
            t: sum(v) / len(v) for t, v in type_values.items()
        }

        # 检测异常
        anomalies = []
        for r in readings:
            avg = type_avg.get(r.energy_type, 0)
            if avg > 0 and r.value > avg * threshold:
                anomalies.append({
                    "meter_id": r.meter_id,
                    "energy_type": r.energy_type,
                    "value": r.value,
                    "average": round(avg, 2),
                    "ratio": round(r.value / avg, 2),
                    "building": r.building,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                })

        return {
            "period_hours": hours,
            "threshold": threshold,
            "total_readings": len(readings),
            "anomaly_count": len(anomalies),
            "anomalies": anomalies[:10],  # 只返回前10个异常
            "averages": {k: round(v, 2) for k, v in type_avg.items()},
        }
