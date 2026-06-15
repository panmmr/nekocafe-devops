# D3-9 答辩 PPT 大纲（≤ 15 页）

**产出编号**：D3-9  
**产出名称**：答辩 PPT 大纲  
**所属实验**：实验三 DevOps 流水线与容器化部署  
**班级 / 学号 / 姓名**：计算机23-2 / 230502209 / 潘美儒  

---

| 页码 | 标题 | 内容要点 |
|------|------|----------|
| 1 | **封面** | NekoCafé DevOps 流水线与容器化部署 / 计算机23-2 / 潘美儒 / 230502209 |
| 2 | **实验目标** | 6 个实验目标（CALMS、GitOps、Dockerfile、K8s、CI/CD、可观测性） |
| 3 | **系统架构总览** | C4 Container 图：Reservation Service / Member Service / Redis / Monitoring Stack |
| 4 | **Monorepo 决策** | Monorepo vs Polyrepo 对比表，取舍理由（2 点），未来演进路径 |
| 5 | **容器化方案** | 多阶段 Dockerfile 示意图 / 镜像大小对比（before vs after ≤200MB）/ Trivy 扫描结果 |
| 6 | **CI 流水线** | 4 阶段流程图（Lint → Test → Scan → Build），各阶段耗时、缓存策略、PR 评论样例 |
| 7 | **CD 蓝绿部署** | 蓝绿部署 4 步动画（Deploy Green → Health → Switch → Clean Blue），流量切分示意 |
| 8 | **自动回滚机制** | 触发条件（P95 > 500ms / ErrorRate > 1%）→ 自动执行 rollback.sh → 通知 |
| 9 | **Helm Chart 多环境** | dev/staging/prod 三套 values 对比表（replicas / resources / HPA） |
| 10 | **可观测性架构** | OpenTelemetry → Collector → Prometheus/Tempo/Loki → Grafana 数据流图 |
| 11 | **Grafana Dashboard** | 4 面板截图（QPS / P99 延迟 / 错误率 / 资源使用） |
| 12 | **DORA 四指标** | 指标定义 + 实际数据表 + 与 Elite 级对比 |
| 13 | **安全合规** | 3 项措施（Secret 管理 / Trivy 扫描 / 非 root 运行） + linter 规范 |
| 14 | **创新点与感悟** | 蓝绿部署选型理由 / OpenTelemetry 埋点体验 / GitOps 理念理解 / Chaos Mesh 展望 |
| 15 | **致谢 & Q&A** | 仓库 URL / 联系方式 / 感谢 |

---

## 每页制作建议

- **第 3 页**：用 draw.io / Excalidraw 画出 C4 Container 图
- **第 5 页**：左右对比 — 左侧单阶段 Dockerfile（~600MB），右侧多阶段（≤200MB）
- **第 7 页**：用 4 张 K8s 部署状态截图拼成动画效果
- **第 10 页**：用 mermaid 渲染数据流图
- **第 11 页**：直接嵌入 Grafana Dashboard 截图（4 面板）
- **第 12 页**：用表格 + 柱状图对比本项目与《Accelerate》Elite 级数据
