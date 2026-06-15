# D3-3 Dockerfile 与镜像扫描报告

**产出编号**：D3-3  
**产出名称**：Dockerfile 与镜像扫描报告  
**所属实验**：实验三 DevOps 流水线与容器化部署  
**案例项目**：NekoCafé 猫咪主题餐饮预约平台  
**班级 / 学号 / 姓名**：计算机23-2 / 230502209 / 潘美儒  

---

## 1 Reservation Service Dockerfile

见 `services/reservation-service/Dockerfile`

### 1.1 多阶段说明

| 阶段 | 基础镜像 | 作用 |
|------|----------|------|
| Builder | python:3.11-slim | 安装 pip 依赖到 `/root/.local` |
| Runtime | python:3.11-slim | 仅复制依赖 + 源码，非 root 用户运行 |

### 1.2 优化措施

- 使用 `python:3.11-slim`（非 alpine，避免 C 扩展编译问题）
- pip install `--no-cache-dir` 减少层大小
- 创建 appuser 非 root 用户
- HEALTHCHECK 内置健康探针

### 1.3 镜像大小

（构建后填写）

```
REPOSITORY              TAG       SIZE
nekocafe-reservation    latest    ___ MB
```

目标：≤ 200MB

## 2 Member Service Dockerfile

见 `services/member-service/Dockerfile`（结构同上）

### 2.1 镜像大小

（构建后填写）

```
REPOSITORY              TAG       SIZE
nekocafe-member         latest    ___ MB
```

目标：≤ 200MB

## 3 Trivy 安全扫描报告

### 3.1 扫描命令

```bash
trivy image --severity HIGH,CRITICAL --ignore-unfixed \
  nekocafe-reservation:latest
trivy image --severity HIGH,CRITICAL --ignore-unfixed \
  nekocafe-member:latest
```

### 3.2 Reservation Service 扫描结果

（粘贴 Trivy 输出）

```
[构建后粘贴扫描结果]
```

### 3.3 Member Service 扫描结果

（粘贴 Trivy 输出）

```
[构建后粘贴扫描结果]
```

### 3.4 漏洞处置

| 漏洞 ID | 严重级别 | 组件 | 修复方案 | 状态 |
|----------|----------|------|----------|------|
| | | | | |
