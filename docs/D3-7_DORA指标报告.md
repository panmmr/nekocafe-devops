# D3-7 DORA 指标报告

**产出编号**：D3-7  
**产出名称**：DORA 指标报告  
**所属实验**：实验三 DevOps 流水线与容器化部署  
**案例项目**：NekoCafé 猫咪主题餐饮预约平台  
**班级 / 学号 / 姓名**：计算机23-2 / 230502209 / 潘美儒  

---

## 1 指标体系说明

DORA（DevOps Research and Assessment）四指标是衡量 DevOps 效能的核心标准，出自《Accelerate》一书。

## 2 采集方案

| 指标 | 数据源 | 采集方法 | 采集频率 |
|------|--------|----------|----------|
| 部署频率（DF） | GitHub Actions 运行记录 | `gh run list --workflow=cd.yml` 统计次数 | 每次 CD 运行自动记录 |
| 变更前置时间（LTTC） | Git + GitHub Actions | `commit_timestamp → deploy_timestamp` 时间差 | 每次部署计算 |
| 变更失败率（CFR） | GitHub Actions + Rollback 记录 | 回滚次数 / 总部署次数 | 每周统计 |
| 恢复时间（MTTR） | Rollback 脚本执行日志 | `rollback_start → rollback_end` 时间差 | 每次回滚记录 |

### 2.1 自动化采集脚本

见 `scripts/dora-collect.sh`（待运行时填充数据）

### 2.2 采集命令示例

```bash
# 部署频率（最近30天 CD 运行次数）
gh run list --workflow=cd.yml --limit 100 --json createdAt \
  | python3 -c "import json,sys; data=json.load(sys.stdin); print(len(data))"

# 变更前置时间（最近一次部署的 commit-to-deploy 时间）
gh run view $(gh run list --workflow=cd.yml --limit 1 --json databaseId -q '.[0].databaseId') \
  --json createdAt,headSha

# 变更失败率
echo "回滚次数: $(gh run list --workflow=cd.yml --json conclusion -q '[.[] | select(.conclusion==\"failure\")] | length')"
echo "总部署次数: $(gh run list --workflow=cd.yml --limit 100 --json databaseId -q 'length')"

# 恢复时间（最近一次 rollback job 耗时）
gh run list --workflow=cd.yml --json databaseId,name,updatedAt \
  -q '.[] | select(.name | contains("Rollback"))'
```

## 3 指标目标与基准

| 指标 | Elite 级目标 | 本项目目标 | 当前状态 |
|------|-------------|-----------|----------|
| 部署频率 | On-demand（每日多次） | ≥ 1 次/天 | [运行时填写] |
| 变更前置时间 | < 1 小时 | < 1 小时 | [运行时填写] |
| 变更失败率 | 0-15% | < 5% | [运行时填写] |
| 恢复时间 | < 1 小时 | < 10 分钟 | [运行时填写] |

## 4 数据记录表

| 日期 | 部署次数 | 前置时间 | 失败次数 | 恢复时间 | 备注 |
|------|---------|---------|---------|---------|------|
| [YYYY-MM-DD] | | | | | 首次运行填充 |
| | | | | | |
| | | | | | |

## 5 分析与改进建议

### 5.1 当前瓶颈分析
[运行时根据实际数据填写]

### 5.2 改进措施
1. **减少前置时间**：优化 Docker 缓存命中率、并行化测试 job
2. **降低失败率**：增强 staging 环境测试覆盖、引入金丝雀发布逐步验证
3. **缩短恢复时间**：排练回滚流程、自动化健康检查阈值调优
