"""模型单元测试"""

from app.models import (
    DeviceType,
    SystemType,
    DeviceStatus,
    AlarmSeverity,
    AlarmStatus,
    EnergyType,
    KnowledgeCategory,
    TicketType,
    TicketPriority,
    TicketStatus,
    MessageRole,
)


class TestDeviceModel:
    """设备模型测试"""

    def test_device_type_enum(self):
        """测试设备类型枚举"""
        assert DeviceType.CHILLER.value == "chiller"
        assert DeviceType.AHU.value == "ahu"
        assert DeviceType.FCU.value == "fcu"
        assert DeviceType.PUMP.value == "pump"

    def test_system_type_enum(self):
        """测试系统类型枚举"""
        assert SystemType.HVAC.value == "hvac"
        assert SystemType.ELECTRICAL.value == "electrical"
        assert SystemType.PLUMBING.value == "plumbing"

    def test_device_status_enum(self):
        """测试设备状态枚举"""
        assert DeviceStatus.RUNNING.value == "running"
        assert DeviceStatus.STOPPED.value == "stopped"
        assert DeviceStatus.FAULT.value == "fault"


class TestAlarmModel:
    """告警模型测试"""

    def test_alarm_severity_enum(self):
        """测试告警级别枚举"""
        assert AlarmSeverity.CRITICAL.value == "critical"
        assert AlarmSeverity.MAJOR.value == "major"
        assert AlarmSeverity.MINOR.value == "minor"
        assert AlarmSeverity.WARNING.value == "warning"

    def test_alarm_status_enum(self):
        """测试告警状态枚举"""
        assert AlarmStatus.ACTIVE.value == "active"
        assert AlarmStatus.ACKNOWLEDGED.value == "acknowledged"
        assert AlarmStatus.RESOLVED.value == "resolved"


class TestEnergyModel:
    """能耗模型测试"""

    def test_energy_type_enum(self):
        """测试能源类型枚举"""
        assert EnergyType.ELECTRICITY.value == "electricity"
        assert EnergyType.WATER.value == "water"
        assert EnergyType.GAS.value == "gas"


class TestKnowledgeModel:
    """知识库模型测试"""

    def test_knowledge_category_enum(self):
        """测试知识分类枚举"""
        assert KnowledgeCategory.TROUBLESHOOTING.value == "troubleshooting"
        assert KnowledgeCategory.MAINTENANCE.value == "maintenance"
        assert KnowledgeCategory.OPERATION.value == "operation"


class TestTicketModel:
    """工单模型测试"""

    def test_ticket_type_enum(self):
        """测试工单类型枚举"""
        assert TicketType.REPAIR.value == "repair"
        assert TicketType.MAINTENANCE.value == "maintenance"

    def test_ticket_priority_enum(self):
        """测试工单优先级枚举"""
        assert TicketPriority.URGENT.value == "urgent"
        assert TicketPriority.HIGH.value == "high"

    def test_ticket_status_enum(self):
        """测试工单状态枚举"""
        assert TicketStatus.PENDING.value == "pending"
        assert TicketStatus.COMPLETED.value == "completed"


class TestConversationModel:
    """对话模型测试"""

    def test_message_role_enum(self):
        """测试消息角色枚举"""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.TOOL.value == "tool"
        assert MessageRole.SYSTEM.value == "system"
