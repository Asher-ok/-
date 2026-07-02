# 澳州项目后端

FastAPI + SQLAlchemy + SQLite 后端服务

## 项目结构

后端采用模块化设计，统一运行一个服务，通过路由前缀区分三个模块：

```
aozhou-houduan/
├── core/                          # 共享核心（最小化）
│   ├── database.py               # 数据库连接和会话管理
│   ├── config.py                 # 配置管理
│   ├── auth/                     # 认证核心（JWT、密码加密）
│   │   ├── jwt.py
│   │   └── password.py
│   └── utils/                    # 基础工具函数
│       └── file_utils.py
│
├── modules/                       # 业务模块（完全独立）
│   ├── guanwang/                 # 官网模块
│   │   ├── api/                 # API 路由层
│   │   ├── services/            # 业务逻辑层
│   │   └── schemas/             # Pydantic 模型
│   │
│   ├── app/                      # 应用模块（移动应用后端）
│   │   ├── api/                 # API 路由层
│   │   ├── services/            # 业务逻辑层
│   │   ├── repositories/        # 数据访问层
│   │   ├── schemas/             # Pydantic 模型
│   │   └── dependencies.py      # 模块特定的依赖注入
│   │
│   └── houtai/                   # 后台模块（管理后台）
│       ├── api/                 # API 路由层
│       ├── services/            # 业务逻辑层
│       ├── repositories/        # 数据访问层
│       ├── schemas/             # Pydantic 模型
│       └── dependencies.py     # 模块特定的依赖注入
│
├── shared/                        # 共享数据模型
│   └── models/                   # SQLAlchemy 模型
│
├── middleware/                    # 全局中间件
│   ├── cors.py                  # CORS 配置
│   ├── error_handler.py        # 错误处理
│   └── logging.py              # 日志中间件
│
├── main.py                        # 应用入口
├── init_db.py                     # 数据库初始化
└── README.md
```

## 架构设计

### 分层架构
- **API 层**：只负责路由和请求验证
- **Service 层**：业务逻辑处理
- **Repository 层**：数据访问抽象（可选，根据模块需要）

### 模块独立性
- 每个模块完全独立，可以单独开发和测试
- 模块间通过共享的数据库和认证系统通信
- 避免循环依赖

### 共享资源
- ✅ 数据库连接（SQLite）
- ✅ 认证系统（JWT，token 可跨模块使用）
- ✅ 数据模型（shared/models）
- ✅ 基础工具函数（core/utils）

## 安装和运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量（复制 `.env.example` 为 `.env` 并修改）：
```bash
cp .env.example .env
```

3. 初始化数据库：
```bash
python init_db.py
```

4. 运行服务：
```bash
python main.py
# 或
uvicorn main:app --reload
```

5. （可选）插入请假/修改审批测试数据：若需验证 houtai 请假管理和修改审批页面的操作功能，可运行：
```bash
python scripts/seed_leave_correction_test_data.py
```
脚本会创建待审批的请假请求和修改请求，刷新 houtai 对应页面即可进行批准/拒绝操作。

6. 访问API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 默认管理员账户

- 用户名: `admin`
- 密码: `admin123`

## API 端点

### 官网模块（/api/guanwang）
- `/api/guanwang` - 官网API（待开发）

### 应用模块（/api/app）- 移动应用后端
- `/api/app/auth/employee/login` - 员工登录
- `/api/app/employees/me` - 获取当前员工信息
- `/api/app/tasks` - 任务列表
- `/api/app/customers` - 客户列表
- `/api/app/questionnaires` - 问卷列表

### 后台模块（/api/houtai）- 管理后台后端
- `/api/app/auth/admin/login` - 管理员登录（注意：登录端点仍在 /api/app/auth 下）
- `/api/houtai/employees` - 员工管理
- `/api/houtai/customers` - 客户管理
- `/api/houtai/tasks` - 任务管理
- `/api/houtai/questionnaires` - 问卷管理
- `/api/houtai/qualifications/expiring` - 资质到期提醒
- `/api/houtai/export/task/{task_id}/materials` - 审核资料导出
- `/api/houtai/invoices` - 发票管理

## 数据库

使用 SQLite，数据库文件：`aozhou.db`

## 发票生成

发票生成功能支持：
- 从已完成的任务自动生成发票
- PDF格式发票（基于模板）
- 邮件发送发票到客户邮箱

## 文件上传

上传的文件存储在 `uploads/` 目录下。
