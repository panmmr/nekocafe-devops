# D3-1 DevOps 设计方案

**产出编号**：D3-1  
**产出名称**：DevOps 设计方案  
**所属实验**：实验三 DevOps 流水线与容器化部署  
**案例项目**：NekoCafé 猫咪主题餐饮预约平台  
**班级 / 学号 / 姓名**：计算机23-2 / 230502209 / 潘美儒  

---

## 1 DevOps 文化与实践

### 1.1 CALMS 原则在本项目的落地

| 原则 | 实践 |
|------|------|
| **Culture（文化）** | Monorepo 统一代码仓库，开发与运维共享同一视角；PR Review + pre-commit 钩子建立质量文化 |
| **Automation（自动化）** | GitHub Actions CI/CD 全自动流水线：lint → test → scan → build → deploy → monitor |
| **Lean（精益）** | 多阶段 Dockerfile 最小化镜像（≤200MB）；流水线缓存减少重复构建；MVP 两个核心服务先行 |
| **Measurement（度量）** | DORA 四指标采集；Prometheus + Grafana 实时监控 QPS/P99/ErrorRate；PR 评论自动输出覆盖率 |
| **Sharing（分享）** | OpenTelemetry 统一可观测性标准；告警规则团队共享；README 30 分钟复现指南 |

### 1.2 GitOps 工作流

```
Git Push ──► GitHub Actions ──► Lint ──► Test ──► Trivy Scan ──► Build ──► Push GHCR
                                  │         │          │              │           │
                                  └─┬───────┴────┬─────┴──────────────┴───────────┘
                                    │            │
                             PR 评论自动更新  Helm 部署到 K8s
```

- **Git 为单一事实源**：所有配置（Dockerfile、Helm Chart、告警规则）均版本化
- **声明式部署**：Helm Chart 描述期望状态，K8s 调谐至期望状态
- **自动回滚**：Prometheus 监控触发 → GitHub Actions 执行 rollback

## 2 仓库结构决策

### 选择：Monorepo

**理由**：
1. 当前仅 2 个核心服务（reservation + member），Polyrepo 会增加 CI/CD 配置重复和跨仓库版本协调成本
2. 共享 .editorconfig / pre-commit / Makefile / docker-compose 等基础设施文件
3. 一个 `docker-compose up` 即起全栈，降低新成员上手门槛
4. Helm Chart 统一管理两个服务的部署

**未来演进**：当服务数量超过 5 个或团队超过 10 人时，可拆分为 Polyrepo + 独立 Helm Chart

## 3 容器化策略

- **多阶段构建**：Builder 阶段安装依赖 → Runtime 阶段仅复制 `.local`，减少镜像体积
- **非 root 运行**：创建 `appuser` 用户运行服务，最小权限原则
- **健康检查**：`/health` + `/ready` 双探针，支持 K8s liveness/readiness
- **镜像大小目标**：≤ 200MB（Python 3.11-slim base + 依赖 ~150MB）

## 4 CI/CD 流水线设计

### 4.1 CI 流水线（≤10 分钟）

```
Lint (3min) → Test (5min) → Trivy Scan (5min) → Build & Push (8min)
```

- **缓存策略**：pip 缓存（actions/setup-python cache）、Docker layer 缓存（gha cache）
- **安全门禁**：Trivy 扫描发现 HIGH/CRITICAL 漏洞 → 流水线阻断
- **PR 指标**：覆盖率、漏洞数、镜像大小自动评论到 PR

### 4.2 CD 流水线

- **部署策略**：蓝绿部署
  1. 部署 Green 版本（新版本）
  2. 健康检查 Green
  3. 切换 Service selector 指向 Green
  4. 保留 Blue 5 分钟作为回滚窗口
  5. 清理 Blue

- **自动回滚条件**：
  - P95 延迟 > 500ms
  - 5xx 错误率 > 1%
  - Pod 启动失败

## 5 可观测性架构

```
App (OTel SDK) → OTel Collector → Prometheus (Metrics)
                                 → Tempo (Traces)
                                 → Loki (Logs)
                                        ↓
                                   Grafana Dashboard
```

- **Traces**：OpenTelemetry 自动打点，traceId 注入响应头 `X-Trace-Id`
- **Metrics**：RED 指标（Rate/Errors/Duration）+ USE 指标（CPU/Memory）
- **Logs**：结构化 JSON，含 timestamp / level / traceId / service / message
- **Dashboard**：4 面板 — QPS、P99 延迟、错误率、资源使用
- **Alerts**：5 条告警规则 — 高延迟、高错误率、Redis 宕机、CPU 使用、Pod 重启

## 6 安全合规

- **Secret 管理**：JWT_SECRET 通过 K8s Secret 注入，严禁硬编码
- **镜像扫描**：Trivy 阻断 HIGH/CRITICAL 漏洞
- **非 root**：容器以 appuser（非 root）运行
- **依赖锁定**：requirements.lock 锁定所有传递依赖版本

## 7 DORA 指标设计

| 指标 | 采集方式 | 目标 |
|------|----------|------|
| 部署频率 | GitHub Actions 执行次数 | 日部署 ≥ 1 次 |
| 变更前置时间 | 从 commit 到 deploy 的时间差 | < 1 小时 |
| 变更失败率 | 回滚次数 / 总部署次数 | < 5% |
| 恢复时间 | rollback 执行耗时 | < 10 分钟 |
