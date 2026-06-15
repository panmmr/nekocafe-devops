# NekoCafé DevOps Pipeline — 实验三

NekoCafé 猫咪主题餐饮预约平台的 DevOps 流水线与容器化部署。

## 架构概览

```
                    ┌─────────────────┐
                    │   GitHub Actions │
                    │  CI/CD Pipeline  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ Reservation │ │   Member    │ │    Redis    │
    │   Service   │ │   Service   │ │   (Cache/   │
    │  :8000      │ │  :8001      │ │   Queue)    │
    └──────┬──────┘ └──────┬──────┘ └─────────────┘
           │               │
           └───────┬───────┘
                   │
    ┌──────────────┼──────────────┐
    │  Prometheus  │   Grafana    │  Loki  │
    │  (Metrics)   │ (Dashboard)  │ (Logs) │
    └──────────────┴──────────────┴────────┘
```

## 仓库结构说明

本项目采用 **Monorepo** 结构。

**取舍理由**：
- 仅有 2 个核心服务，Polyrepo 的独立 CI/CD、独立版本管理优势在此规模下不显著
- Monorepo 降低跨服务变更的协调成本（如共享数据模型、统一依赖版本）
- 一个 `docker-compose.yml` 即可本地起全栈，降低新成员上手门槛

## 30 分钟快速复现指南

### 前置依赖

- Docker ≥ 24.0
- Docker Compose ≥ v2.20
- Python 3.11+（本地开发）
- Git

### 1. 克隆仓库

```bash
git clone <repo-url> && cd nekocafe-devops
```

### 2. 启动全部服务

```bash
docker compose up -d
```

### 3. 验证服务健康

```bash
# Reservation Service
curl http://localhost:8000/health
# 预期: {"status":"healthy","service":"reservation-service"}

# Member Service
curl http://localhost:8001/health
# 预期: {"status":"healthy","service":"member-service"}
```

### 4. 体验 API

```bash
# 查看 API 文档
open http://localhost:8000/docs   # Reservation Service Swagger
open http://localhost:8001/docs   # Member Service Swagger

# 注册会员
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800138000","smsCode":"123456","nickname":"测试用户"}'

# 查询可用桌位
curl "http://localhost:8000/api/v1/stores/1/availability?date=2026-06-15&guestCount=2"
```

### 5. 启动监控栈

```bash
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

- Grafana: http://localhost:3000 （admin/admin）
- Prometheus: http://localhost:9090

## 项目结构

```
nekocafe-devops/
├── .github/workflows/        # CI/CD 流水线定义
├── services/
│   ├── reservation-service/  # 预约服务（FastAPI）
│   └── member-service/       # 会员服务（FastAPI）
├── k8s/
│   ├── helm/nekocafe/        # Helm Chart（dev/staging/prod）
│   └── monitoring/           # 可观测性配置
├── scripts/                  # 运维脚本
├── docker-compose.yml        # 本地一键起栈
└── Makefile                  # 常用命令
```

## 核心指标

| 指标 | 目标值 |
|------|--------|
| 镜像大小 | ≤ 200 MB |
| CI 耗时 | ≤ 10 min |
| 测试覆盖率 | ≥ 80% |
| Trivy 漏洞 | 0 HIGH/CRITICAL |

## DORA 指标采集

参见 `scripts/dora-collect.sh` 和 `D3-7_DORA指标报告.md`。
