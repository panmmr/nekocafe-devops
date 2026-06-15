# D3-6 可观测性配置与 Dashboard 截图

**产出编号**：D3-6  
**产出名称**：可观测性配置与 Dashboard 截图  
**所属实验**：实验三 DevOps 流水线与容器化部署  
**案例项目**：NekoCafé 猫咪主题餐饮预约平台  
**班级 / 学号 / 姓名**：计算机23-2 / 230502209 / 潘美儒  

---

## 1 OpenTelemetry 接入

### 1.1 SDK 版本

- `opentelemetry-api==1.28.2`
- `opentelemetry-sdk==1.28.2`
- `opentelemetry-instrumentation-fastapi==0.49b2`

### 1.2 接入方式

- **自动埋点**：`FastAPIInstrumentor.instrument_app(app)` 自动打 HTTP 请求 span
- **手动埋点**：自定义 `trace_id_middleware` 注入 traceId 到响应头 `X-Trace-Id`
- **导出目标**：OTLP gRPC → Otel Collector → Prometheus + Tempo + Loki

### 1.3 采样策略

- 开发/测试环境：`ALWAYS_ON`（100% 采样）
- 生产环境建议：`PARENT_BASED_ALWAYS_ON`，辅以尾部采样

## 2 日志规范

### 2.1 字段约定

每条日志输出为 JSON 单行：

```json
{
  "timestamp": "2026-06-15T10:30:00.000Z",
  "level": "INFO",
  "service": "reservation-service",
  "message": "POST /api/v1/reservations 201 0.042s",
  "module": "main",
  "traceId": "a1b2c3d4e5f6789012345678abcdef01"
}
```

### 2.2 脱敏策略

- 手机号：`138****8000`（保留前 3 后 4）
- 身份证号：不记录
- 邮箱：`p***@neko.cafe`（保留首字母和域名）

## 3 Metrics 指标清单

### 3.1 RED 指标（Rate / Errors / Duration）

| 指标 | PromQL | 面板 |
|------|--------|------|
| Rate (QPS) | `rate(http_requests_total[1m])` | 面板 1 |
| Errors | `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])` | 面板 3 |
| Duration (P99) | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` | 面板 2 |

### 3.2 USE 指标（Utilization / Saturation / Errors）

| 指标 | PromQL | 面板 |
|------|--------|------|
| CPU Utilization | `container_cpu_usage_seconds_total / container_spec_cpu_quota` | 面板 4 |
| Memory Utilization | `container_memory_working_set_bytes / container_spec_memory_limit_bytes` | 面板 4 |

## 4 Dashboard 截图（≥ 4 张）

### 4.1 面板 1：QPS（每秒请求数）

（粘贴 Grafana 截图）

### 4.2 面板 2：P99 / P95 / P50 延迟

（粘贴 Grafana 截图）

### 4.3 面板 3：错误率（%）

（粘贴 Grafana 截图）

### 4.4 面板 4：CPU / Memory 资源使用

（粘贴 Grafana 截图）

## 5 告警规则

### 5.1 规则 YAML

见 `k8s/monitoring/prometheus-rules/alerts.yaml`，共 5 条规则：

| # | 规则名 | 条件 | 严重级别 |
|---|--------|------|----------|
| 1 | HighP95Latency | P95 > 500ms | Warning |
| 2 | HighErrorRate | 5xx > 1% | Critical |
| 3 | RedisDown | redis_up == 0 | Critical |
| 4 | HighCPUUsage | CPU > 80% | Warning |
| 5 | FrequentRestarts | 重启频率 > 0.05/min | Warning |

### 5.2 告警通道

- 开发环境：控制台输出
- 预发布/生产：钉钉/飞书 Webhook + 短信升级策略

## 6 故障演练（Chaos）记录 — 可选加分项

（如实施 Chaos Mesh 演练，在此记录演练范围、注入工具、观测结果、改进项）
