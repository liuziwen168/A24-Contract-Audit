# A24 Contract Audit Backend

Python 3.11+、FastAPI、SQLAlchemy 2、Alembic 和 MySQL 8 业务后端。当前数据库 head 为 `20260713_0004`。

## 本地启动

```powershell
cd backend
Copy-Item .env.example .env
python -m pip install -e ".[dev]"
```

在当前进程安全加载 `.env` 后执行：

```powershell
alembic upgrade head
python -m app.init_demo
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

项目不自动读取 `.env`。不得提交 `.env`，也不得在日志或命令输出中打印完整数据库 URL、JWT、AI 内部 Token 或演示密码。

演示账号固定为 `demo_user`、`demo_legal`、`demo_risk`、`demo_admin`；密码分别由四个 `DEMO_*_PASSWORD` 环境变量提供。四个角色不能混用。

## 配置

必需生产配置：`DATABASE_URL`、`JWT_SECRET`、`AI_SERVICE_BASE_URL`、`AI_INTERNAL_TOKEN`、`UPLOAD_ROOT`、`REPORT_ROOT`、`CORS_ORIGINS`、`TRUSTED_HOSTS`。生产环境设置 `APP_ENV=production`；默认关闭 OpenAPI，可用 `OPENAPI_ENABLED=true` 显式开启。

AI 与报告执行器分别由 `TASK_EXECUTOR_ENABLED` 和 `REPORT_EXECUTOR_ENABLED` 控制。AI 测试必须使用受控 Mock，不调用真实模型额度。

`UPLOAD_ROOT` 和 `REPORT_ROOT` 必须位于源码目录之外并挂载为持久目录。多实例部署必须共享同一 `REPORT_ROOT`；数据库条件更新负责防止重复领取，但不替代共享文件存储。当前建议保持一个 Uvicorn worker。

## 测试

```powershell
ruff check app tests alembic
pytest -q -p no:cacheprovider
alembic heads
```

真实 MySQL 测试使用独立白名单数据库 URL。最终验收变量为 `BACKEND_FINAL_MYSQL_DATABASE_URL`，数据库名必须是 `a24_backend_final_audit_20260713`。Windows 出现 pytest 临时目录 ACL 错误时，应使用可访问的独立 `--basetemp`，不能把 ACL 错误视为业务失败。

## Docker

```powershell
docker build -t a24-contract-audit-backend:test backend
docker run --rm --env-file backend/.env -e APP_ENV=production -e TRUSTED_HOSTS=localhost,127.0.0.1 a24-contract-audit-backend:test alembic upgrade head
docker run --rm -p 8000:8000 --env-file backend/.env -e APP_ENV=production -e TRUSTED_HOSTS=localhost,127.0.0.1 -v a24-uploads:/data/uploads -v a24-reports:/data/reports a24-contract-audit-backend:test
```

镜像固定 Python 3.11，以非 root 用户运行，包含 Alembic、HTML 模板、Noto 中文字体和 OFL 许可证。`GET /health` 只检查 API 进程存活，不依赖 AI 服务。生产域名必须加入 `TRUSTED_HOSTS`。
