# D3-5 K8s 部署清单与 Helm Chart

**产出编号**：D3-5  
**产出名称**：K8s 部署清单与 Helm Chart（文件夹结构）  
**所属实验**：实验三 DevOps 流水线与容器化部署  
**班级 / 学号 / 姓名**：计算机23-2 / 230502209 / 潘美儒  

---

## 1 Helm Chart 结构

```
k8s/helm/nekocafe/
├── Chart.yaml
├── values.yaml           # 默认配置
├── values-dev.yaml       # dev 环境覆盖
├── values-staging.yaml   # staging 环境覆盖
├── values-prod.yaml      # prod 环境覆盖
└── templates/
    ├── deployment.yaml    # 2 个服务 Deployment + Redis
    ├── service.yaml       # Service（支持蓝绿 selector）
    ├── ingress.yaml       # Ingress 路由规则
    ├── secrets.yaml       # JWT Secret（K8s Secret）
    ├── hpa.yaml           # HPA 自动扩缩容
    └── servicemonitor.yaml # Prometheus ServiceMonitor
```

## 2 三环境配置对比

| 参数 | dev | staging | prod |
|------|-----|---------|------|
| replicas | 1 | 2 | 4 |
| CPU request | 50m | 100m | 200m |
| Memory request | 64Mi | 128Mi | 256Mi |
| HPA | disabled | disabled | enabled (4-20) |
| Ingress | disabled | api-staging.neko.cafe | api.neko.cafe |
| ServiceMonitor | disabled | enabled (30s) | enabled (15s) |
| JWT Secret | dev-secret-... | staging-secret-... | 外部注入 |

## 3 蓝绿部署机制

### 3.1 原理

使用 Service selector 切换实现流量切换：

```yaml
# Green 版本
Deployment: nekocafe-green-reservation (labels: {color: green})
Deployment: nekocafe-blue-reservation (labels: {color: blue})

# 切换前：Service selector → color: blue
# 切换后：Service selector → color: green
```

### 3.2 流程

1. `helm install nekocafe-green` → 新版本部署
2. `kubectl wait deployment` → 等待健康检查通过
3. `helm upgrade nekocafe --set deployment.color=green` → 更新 Service selector
4. 等待 5 分钟回滚窗口
5. `helm uninstall nekocafe-blue` → 清理旧版本

## 4 部署验证命令

```bash
# 部署 dev 环境
helm install nekocafe ./k8s/helm/nekocafe \
  -f ./k8s/helm/nekocafe/values.yaml \
  -f ./k8s/helm/nekocafe/values-dev.yaml \
  --namespace nekocafe-dev --create-namespace

# 查看部署状态
kubectl get pods -n nekocafe-dev
kubectl get svc -n nekocafe-dev
helm list -n nekocafe-dev

# 回滚
helm rollback nekocafe -n nekocafe-dev
# 或使用脚本
./scripts/rollback.sh dev
```

## 5 部署截图

（粘贴 `kubectl get pods,svc,ingress -n nekocafe-dev` 输出截图）
（粘贴 ArgoCD 或 Helm 部署成功截图）
