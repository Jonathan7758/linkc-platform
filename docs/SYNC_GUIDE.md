# LinkC 文档同步指南

## 概述

本指南解决以下问题：
- 如何将 Claude.ai 对话中产生的文档同步到服务器
- 如何确保本地电脑、服务器、Git 三方一致
- 如何在后续更新中保持同步

---

## 同步架构

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   Claude.ai 对话                                                             │
│   ┌─────────────────┐                                                        │
│   │ 1. 讨论/生成文档 │                                                        │
│   │ 2. 下载到本地   │                                                        │
│   └────────┬────────┘                                                        │
│            │ 下载                                                             │
│            ▼                                                                  │
│   本地电脑 (Windows)                                                          │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│   │ linkc-platform/ │────►│ sync-to-server  │────►│ 服务器同步      │       │
│   │ (Git仓库)       │     │ .ps1            │     │ + Git推送       │       │
│   └─────────────────┘     └─────────────────┘     └─────────────────┘       │
│            │                                               │                 │
│            │ Claude Code (本地运行)                         │                 │
│            ▼                                               ▼                 │
│   ┌─────────────────┐                           ┌─────────────────┐         │
│   │ 直接编辑项目文件 │                           │ GitHub 仓库     │         │
│   │ 自动读取CLAUDE.md│                           │ (代码+文档)     │         │
│   └─────────────────┘                           └─────────────────┘         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 方法一：直接在本地使用 Claude Code（推荐）

这是最简单且最一致的方法。

### 步骤

1. **克隆仓库到本地**
   ```powershell
   git clone git@github.com:YOUR_ORG/linkc-platform.git
   cd linkc-platform
   ```

2. **使用 Claude Code 开发**
   ```powershell
   # Claude Code 自动读取 CLAUDE.md
   claude "开发M1空间MCP Server"
   ```

3. **更新文档后同步**
   ```powershell
   git add -A
   git commit -m "docs: 更新LESSONS_LEARNED"
   git push
   ```

4. **服务器拉取最新**
   ```bash
   # SSH到服务器
   ssh root@101.47.67.225
   cd /root/linkc-platform
   git pull
   ```

### 优点
- Git 作为单一真相源
- 自动版本控制
- 团队成员都能看到更新

---

## 方法二：从 Claude.ai 下载后同步

当你在 Claude.ai 网页端生成了新文档时使用。

### 步骤

1. **在 Claude.ai 下载文件**
   - 点击文档下方的下载按钮
   - 保存到本地项目对应目录

2. **放到正确位置**
   ```
   linkc-platform/
   ├── CLAUDE.md              ← 项目根目录
   ├── docs/
   │   ├── LESSONS_LEARNED.md ← docs目录
   │   ├── ARCHITECTURE.md
   │   └── specs/
   │       └── M1-space-mcp.md
   └── interfaces/
       ├── data_models.py     ← interfaces目录
       └── ...
   ```

3. **运行同步脚本**
   ```powershell
   cd linkc-platform
   .\scripts\sync-to-server.ps1 -GitPush
   ```

---

## 方法三：Claude.ai Project Knowledge 同步

如果你在 Claude.ai 使用了 Project 功能：

### 当前设置
你的 Project Knowledge 包含以下核心文档：
- LinkC_ECIS商业飞轮战略规划.md
- AI本质与行业影响顺序分析.md
- AI深度应用与组织转型必然性分析.md
- LinkC_MVP开发计划_AI友好模块化设计.md
- Claude_Code_开发最佳实践_团队协作版.md

### 同步到 Git 的方法
1. 这些文档作为"参考资料"保留在 Claude.ai Project
2. 开发相关的可执行文档（CLAUDE.md, 接口定义等）保存在 Git
3. 不需要完全同步 - 战略文档留在 Project，技术文档进 Git

---

## 文件分类指南

| 文件类型 | 存放位置 | 同步方式 |
|---------|---------|---------|
| **战略规划文档** | Claude.ai Project Knowledge | 不需要同步到Git |
| **CLAUDE.md** | Git仓库根目录 | Git管理 |
| **LESSONS_LEARNED.md** | Git仓库 docs/ | Git管理，频繁更新 |
| **接口定义** | Git仓库 interfaces/ | Git管理，严格版本控制 |
| **规格书** | Git仓库 docs/specs/ | Git管理 |
| **源代码** | Git仓库 src/ | Git管理 |

---

## 更新工作流

### 场景1：在 Claude.ai 讨论产生新的 LESSONS_LEARNED 条目

```
1. Claude.ai 输出新条目内容
2. 复制内容
3. 本地打开 docs/LESSONS_LEARNED.md，粘贴
4. Git提交推送
5. 服务器 git pull
```

### 场景2：使用 Claude Code 开发时发现问题

```
1. Claude Code 在服务器开发
2. 发现问题，Claude Code 直接更新 LESSONS_LEARNED.md
3. Git提交推送
4. 本地 git pull 获取更新
5. (可选) 更新 Claude.ai Project Knowledge
```

### 场景3：更新接口定义

```
⚠️ 接口定义是核心契约，需要团队讨论后更新

1. 在 Claude.ai 讨论接口变更
2. 确认后下载新的接口文件
3. 替换本地 interfaces/*.py
4. 运行测试确保兼容
5. Git提交推送
6. 通知团队成员 git pull
```

---

## 常用命令速查

### Windows PowerShell

```powershell
# 同步到服务器
.\scripts\sync-to-server.ps1

# 同步并推送Git
.\scripts\sync-to-server.ps1 -GitPush

# 从服务器拉取
.\scripts\pull-from-server.ps1

# 查看Git状态
git status

# 提交并推送
git add -A
git commit -m "docs: 更新说明"
git push
```

### Linux 服务器

```bash
# 拉取最新
cd /root/linkc-platform
git pull

# 查看文档
cat docs/LESSONS_LEARNED.md

# 使用 Claude Code 开发
claude "继续开发M1模块"
```

---

## 最佳实践

### 1. 单一真相源原则
- **Git 是唯一的代码和技术文档真相源**
- Claude.ai Project 用于战略讨论和参考
- 不要在多个地方维护同一份文档的不同版本

### 2. 频繁小提交
```powershell
# 每完成一个小改动就提交
git add docs/LESSONS_LEARNED.md
git commit -m "LL-007: 添加Redis连接池问题"
git push
```

### 3. 更新 CLAUDE.md 需谨慎
- CLAUDE.md 是所有 Claude Code 会话的基础
- 重大更新需要团队同步
- 更新后通知团队 `git pull`

### 4. 接口变更需评审
- interfaces/*.py 是核心契约
- 变更前在 Claude.ai 或会议讨论
- 变更后更新所有相关实现
- 运行全量测试

---

## 问题排查

### 问题1：同步脚本报错 "scp: Permission denied"
```powershell
# 检查SSH密钥
ssh root@101.47.67.225 "echo 连接成功"

# 如果失败，重新配置密钥
ssh-keygen -t rsa -b 4096
ssh-copy-id root@101.47.67.225
```

### 问题2：Git push 被拒绝
```powershell
# 先拉取合并
git pull --rebase
git push
```

### 问题3：服务器和本地文件冲突
```bash
# 在服务器上
git stash
git pull
git stash pop
# 手动解决冲突
```

---

## 总结

1. **日常开发**：直接用 Git + Claude Code，最简单
2. **Claude.ai 产出**：下载 → 放正确位置 → Git 提交
3. **保持同步**：养成频繁 `git pull/push` 的习惯
4. **团队协作**：重大文档更新通知团队

有问题随时在 Claude.ai 讨论！
