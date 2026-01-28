# 移动机器人扩展 - Claude 开发指南

## 快速状态

| 项目 | 值 |
|------|-----|
| **当前阶段** | Task 10 - 移动机器人扩展 |
| **进度** | 80% |
| **最后更新** | 2026-01-28 |

## 项目路径

| 项目 | 路径 |
|------|------|
| Service Robot | `/root/projects/ecis/ecis-service-robot` |

## 模块状态

| 模块 | 状态 | 说明 |
|------|------|------|
| adapters/drone | ✅ | DroneAdapter + MockDroneAdapter |
| adapters/robot_dog | ✅ | RobotDogAdapter + MockRobotDogAdapter |
| agents/drone_agent | ✅ | DroneAgent with TaskReceiverMixin |
| agents/robot_dog_agent | ✅ | RobotDogAgent with TaskReceiverMixin |
| capabilities/drone | ✅ | 5 能力定义 |
| capabilities/robot_dog | ✅ | 4 能力定义 |
| tests | ✅ | 44 新增测试全部通过 |

## 已完成功能

### 无人机 (Drone)

**能力**:
- `drone.patrol.aerial` - 空中巡逻
- `drone.inspection.facade` - 外墙检查
- `drone.inspection.roof` - 屋顶检查
- `drone.delivery.aerial` - 空中配送
- `drone.photography.aerial` - 航拍

**适配器功能**:
- 连接/断开
- 解锁/锁定电机
- 起飞/降落
- 航点飞行
- 返航
- 相机控制
- 紧急停止

### 机器狗 (Robot Dog)

**能力**:
- `robotdog.patrol.rough` - 复杂地形巡逻
- `robotdog.inspection.underground` - 地下空间检查
- `robotdog.escort.security` - 安保护送
- `robotdog.care.companion` - 陪伴服务

**适配器功能**:
- 连接/断开
- 站立/坐下/卧下
- 运动模式切换
- 步态切换
- 位置移动
- 相机/激光雷达控制
- 气体传感器读取
- 紧急停止

## 测试统计

| 模块 | 测试数 | 状态 |
|------|--------|------|
| test_drone.py | 18 | ✅ |
| test_robot_dog.py | 26 | ✅ |
| **总计** | 44 | ✅ |

## 常用命令

```bash
cd /root/projects/ecis/ecis-service-robot

# 运行无人机测试
python3 -m pytest tests/adapters/test_drone.py -v

# 运行机器狗测试
python3 -m pytest tests/adapters/test_robot_dog.py -v

# 运行所有适配器测试
python3 -m pytest tests/adapters/ -v
```

## 待完成

- [ ] Federation 集成
- [ ] 编排器集成测试
- [ ] 文档完善
