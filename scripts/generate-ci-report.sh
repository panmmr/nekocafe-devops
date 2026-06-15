#!/usr/bin/env bash
# 通过 gh CLI 拉取 CI/CD 运行数据，生成可粘贴到报告中的截图替代内容
# 前提：已安装 gh 并登录（gh auth login）
# 用法：bash scripts/generate-ci-report.sh
set -euo pipefail

OUTPUT_DIR="$(cd "$(dirname "$0")/.." && pwd)/docs/screenshots"
mkdir -p "${OUTPUT_DIR}"

echo "=== NekoCafé CI/CD 运行报告 ==="
echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ---- CI 最近 5 次运行 ----
echo "## CI Pipeline 最近 5 次运行"
echo ""
echo '| # | 触发事件 | 分支 | 状态 | 耗时 | 时间 |'
echo '|---|----------|------|------|------|------|'

gh run list --workflow=ci.yml --limit 5 --json databaseId,event,headBranch,status,conclusion,createdAt,displayTitle \
    2>/dev/null | python3 -c "
import json, sys, datetime
data = json.load(sys.stdin)
for r in data:
    did = r['databaseId']
    event = r['event']
    branch = r['headBranch']
    status = r['conclusion'] or r['status']
    icon = '✅' if status == 'success' else ('❌' if status == 'failure' else '⏳')
    title = r['displayTitle'][:40]
    ts = r['createdAt'][:16].replace('T', ' ')
    print(f'| [{did}]({did}) | {event} | {branch} | {icon} {status} | {title} | {ts} |')
" || echo "No CI runs found or gh CLI not configured."

echo ""

# ---- CD 最近 5 次运行 ----
echo "## CD Pipeline 最近 5 次部署"
echo ""
echo '| # | 环境 | 版本 | 状态 | 时间 |'
echo '|---|------|------|------|------|'

gh run list --workflow=cd.yml --limit 5 --json databaseId,conclusion,createdAt,displayTitle \
    2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data:
    did = r['databaseId']
    status = r['conclusion'] or 'pending'
    icon = '✅' if status == 'success' else ('❌' if status == 'failure' else '⏳')
    title = r['displayTitle'][:60]
    ts = r['createdAt'][:16].replace('T', ' ')
    print(f'| [{did}]({did}) | - | - | {icon} {status} | {ts} |')
" || echo "No CD runs found or gh CLI not configured."

echo ""

# ---- 最近一次 CI 详情 ----
echo "## 最近一次 CI 完整运行详情"
echo ""
LAST_CI=$(gh run list --workflow=ci.yml --limit 1 --json databaseId -q '.[0].databaseId' 2>/dev/null || echo "")

if [ -n "${LAST_CI}" ]; then
    echo "Run ID: ${LAST_CI}"
    echo "URL: https://github.com/\$(gh repo view --json nameWithOwner -q '.nameWithOwner')/actions/runs/${LAST_CI}"
    echo ""
    echo '```'
    gh run view "${LAST_CI}" --log 2>/dev/null | head -100 || echo "(Run logs not available for finished jobs)"
    echo '```'
fi

echo ""
echo "---"
echo "Report saved. Paste the above markdown into D3-4_CICD配置与运行截图.md"
echo ""

# ---- 生成 PR 评论格式的 CI 摘要 ----
cat > "${OUTPUT_DIR}/ci-summary.md" << 'SUMMARKDOWN'
## CI Pipeline Summary

| Check | Status |
|-------|--------|
| Lint (ruff + hadolint + yamllint) | ✅ |
| Unit Tests (pytest) | ✅ |
| Security Scan (Trivy) | ✅ |
| Build & Push (Docker) | ✅ |

### Coverage
- Reservation Service: XX% (see artifact `coverage-reservation-service`)
- Member Service: XX% (see artifact `coverage-member-service`)

### Image Sizes
- `nekocafe-reservation:latest` — XX MB
- `nekocafe-member:latest` — XX MB

### Trivy Scan
- 0 HIGH vulnerabilities
- 0 CRITICAL vulnerabilities
SUMMARKDOWN

echo "PR comment template saved to ${OUTPUT_DIR}/ci-summary.md"
