#!/bin/bash
# LinkC Claude Code 同步脚本 (在Claude Code中使用)
# 用法: claude "运行 scripts/claude-sync.sh"

set -e

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}         LinkC Claude Code 同步工具                     ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# 检查是否在项目目录
if [ ! -f "CLAUDE.md" ]; then
    echo -e "${YELLOW}警告: 未找到CLAUDE.md，请确保在项目根目录运行${NC}"
    exit 1
fi

PROJECT_ROOT=$(pwd)
echo -e "${GREEN}项目目录: $PROJECT_ROOT${NC}"

# 同步到Git
echo ""
echo "▶ 检查Git状态..."
git status --short

echo ""
echo "▶ 添加文档更改..."
git add CLAUDE.md docs/ interfaces/ .claude/ 2>/dev/null || true

echo ""
echo "▶ 提交更改..."
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
git commit -m "docs: 同步更新文档 $TIMESTAMP" 2>/dev/null || echo "没有新更改需要提交"

echo ""
echo "▶ 推送到远程..."
git push origin main 2>/dev/null || git push origin master 2>/dev/null || echo "推送失败或无需推送"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                   同步完成!                            ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
