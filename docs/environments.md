# 环境事实

<!-- project-governance:managed:start -->
## 环境变量名

- `ASTRO_TELEMETRY_DISABLED`：构建子进程强制为 `1`，禁用 Astro 遥测；`.env.example` 记录安全值。

## 服务

- 本地预览：Python 静态 HTTP 服务，绑定 127.0.0.1
- 正式阅读站点：notes.zzzping.top，Nginx + TLS；部署步骤见 deploy/README.md
- Ubuntu reading-notes-build.service（构建主机）与 reading-notes-deploy.service/.timer（发布主机）：模板交付，本次未安装到生产

## 端口与端点

- 本地预览默认 8000，仅 127.0.0.1；可用 --port 指定
- 生产 Nginx 80 / 443（模板约定；本次没有更改服务器）

本文件严禁写入凭据或生产数据。`.env.example` 必须与环境变量名清单同步。
<!-- project-governance:managed:end -->

## 项目专属环境说明

本地阅读使用离线 HTML 或环回 HTTP；临时 HTTPS 验收单独创建测试证书和 Nginx 配置，验证后停止测试进程。生产域名、目录、证书和切换步骤以 [部署说明](../deploy/README.md) 为准，执行发布前读取实际状态。当前项目不要求用户设置持久环境变量；本地 TLS 验证器只对自己的子进程设置 `SSL_CERT_FILE`，不修改系统信任。未单独登记预发布环境。

新模板目录为 `/srv/reading-notes`，构建工作目录为 `/opt/reading-notes-builder`；Node/pnpm 只存在于构建主机。Web 主机的 Python/rsync/flock 是一次性发布命令依赖，不是 HTTP 运行服务。现网目录保持原部署状态。
