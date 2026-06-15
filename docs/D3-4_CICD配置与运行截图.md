# D3-4 CI/CD 配置与运行截图

**产出编号**：D3-4  
**产出名称**：CI/CD 配置与运行截图  
**所属实验**：实验三 DevOps 流水线与容器化部署  
**班级 / 学号 / 姓名**：计算机23-2 / 230502209 / 潘美儒  

---

## 1 CI 流水线

### 1.1 完整 YAML

见 `.github/workflows/ci.yml`

### 1.2 阶段说明

| 阶段 | Job | 超时 | 依赖 |
|------|-----|------|------|
| Lint | ruff + hadolint + yamllint | 3 min | - |
| Test | pytest + coverage | 5 min | Lint |
| Security Scan | Trivy (HIGH/CRITICAL) | 5 min | Test |
| Build & Push | Docker Build + Push GHCR | 8 min | Security Scan |
| PR Comment | 自动评论指标 | 2 min | All above (PR only) |

### 1.3 关键运行截图

#### 成功运行

（粘贴 GitHub Actions 全部 Job 绿色的截图）

#### 失败案例

（粘贴某个 Job 失败的截图 + 错误日志）

---

## 2 CD 流水线

### 2.1 完整 YAML

见 `.github/workflows/cd.yml`

### 2.2 审批节点

使用 GitHub Environments 的 required reviewers 功能：
- **dev**：无需审批
- **staging**：1 位 reviewer
- **prod**：2 位 reviewers

### 2.3 蓝绿部署演示截图

（粘贴以下 4 张截图）

1. Deploy Green — 新版部署中
2. Health Check — 健康检查通过
3. Switch Traffic — Service selector 切换
4. Clean Blue — 旧版清理完成

---

## 3 缓存策略

### 3.1 缓存配置

- **pip 缓存**：`actions/setup-python` 的 `cache: pip`
- **Docker 层缓存**：`docker/build-push-action` 的 `cache-from: type=gha`

### 3.2 缓存命中率截图

（粘贴 actions/cache 命中率截图）

---

## 4 常见失败与处置手册

| 失败类型 | 原因 | 处置步骤 |
|----------|------|----------|
| Lint 失败 | 代码格式不合规 | 运行 `ruff check --fix && ruff format` |
| Test 失败 | 用例不通过 | 查看 pytest 输出，修复后重新提交 |
| Trivy Block | 发现 HIGH/CRITICAL 漏洞 | 升级依赖版本或添加 `--ignore-unfixed` |
| Build 失败 | Dockerfile 语法错误 | 本地 `docker build` 验证 |
| Push 失败 | GHCR 权限不足 | 检查 GITHUB_TOKEN 权限 |
| Deploy 超时 | Pod 无法启动 | `kubectl describe pod` 查看事件 |
