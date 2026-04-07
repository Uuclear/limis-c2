# LIMIS 试验室信息管理系统 — 设计规格

**公司：** 上海建科检验有限公司  
**服务工程：** 浦东国际机场四期扩建工程  
**日期：** 2026-04-07  

---

## 1. 项目概述

为上海建科检验有限公司开发一套试验室信息管理系统（LIMIS），服务于浦东国际机场四期扩建工程。公司为全能力第三方工程检测单位，涵盖建筑材料、土工、桩基、结构、钢结构、市政道路/跑道、防水等全部检测类型。

系统需支持多项目管理，纸质与电子双轨并行，业务逻辑清晰，功能完善可直接运营，方便二次开发和拓展。

## 2. 系统架构

### 2.1 架构方案

单体应用 + 异步任务队列。

```
浏览器（Vue 3 + Element Plus）
        ↓ HTTP/WebSocket
Nginx（反向代理 + 静态资源）
        ↓
FastAPI 主服务（业务API · JWT认证 · RBAC）
Celery Worker（OCR · AI · 报告生成）   ← 可选增强
        ↓
PostgreSQL 16 + Redis 7 + 本地文件存储
```

### 2.2 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 前端 | Vue 3 + Element Plus + Pinia + Vue Router | 组合式API，状态管理，路由 |
| 构建工具 | Vite | 快速开发构建 |
| 后端 | FastAPI + SQLAlchemy + Alembic | API框架、ORM、数据库迁移 |
| 异步任务 | Celery + Redis (Broker) | OCR、AI、报告生成等耗时任务 |
| AI/OCR | PaddleOCR + PaddlePaddle | 文字识别、表格识别（可选） |
| 数据库 | PostgreSQL 16 + Redis 7 | 主存储 + 缓存/队列 |
| Web服务 | Nginx + Uvicorn | 反向代理 + ASGI服务器 |
| 报告生成 | python-docx + openpyxl + WeasyPrint | Word/Excel/PDF 生成 |

### 2.3 部署方式

- 本地私有化裸机部署，不使用Docker或虚拟化
- 性能最大化，方便调试
- 所有服务直接运行在本地服务器上

## 3. 用户角色与权限

系统支持8种角色，基于RBAC权限控制：

| 角色 | 职责 |
|------|------|
| 项目管理层 | 整体进度管理、报告审批 |
| 试验室主任 | 日常运作管理、任务分配、质量控制 |
| 检测人员/试验员 | 执行试验、录入原始数据 |
| 报告编制/审核人员 | 编写检测报告、技术审核、签发 |
| 样品管理员 | 样品接收、登记、流转、留样 |
| 委托方/甲方 | 提交委托、查看报告进度 |
| 设备管理员 | 仪器设备检定/校准、使用记录 |
| 质量管理员 | 内审、管理体系文件、不符合项管理 |

## 4. 数据模型

### 4.1 工程四级层级

```
工程（Project）
  └── 单位工程（UnitProject）
        └── 分部工程（Division）
              └── 分项工程（SubItem）
```

示例：浦东国际机场四期扩建工程 → T3航站楼 → 地基与基础 → 钢筋连接

### 4.2 核心数据模型（6大域）

**用户与权限：**
- User — 用户表
- Role — 角色表（8种角色）
- Permission — 权限表
- Department — 部门表

**工程层级：**
- Project — 工程
- UnitProject — 单位工程
- Division — 分部工程
- SubItem — 分项工程

**检测业务（核心）：**
- Commission — 委托单
- Sample — 样品
- TestTask — 检测任务
- TestRecord — 原始记录
- TestResult — 检测结果
- Report — 检测报告

**标准与判定：**
- Standard — 检测标准
- StandardClause — 标准条文
- JudgmentRule — 判定规则
- TestParameter — 检测参数

**设备管理：**
- Equipment — 设备台账
- Calibration — 检定/校准记录
- EquipmentUsage — 使用记录
- Maintenance — 维护保养

**质量管理：**
- AuditPlan — 内审计划
- NonConformity — 不符合项
- CorrectiveAction — 纠正措施
- QualityDocument — 体系文件

### 4.3 核心关联关系

```
委托单(Commission) → 关联分项工程(SubItem) → 生成样品(Sample) → 分配检测任务(TestTask)
检测任务(TestTask) → 关联检测标准(Standard) + 设备(Equipment) + 检测人员(User)
检测任务(TestTask) → 录入原始记录(TestRecord) → 产出检测结果(TestResult)
检测结果(TestResult) → 生成检测报告(Report) → 三级审签流程
```

## 5. 功能模块（9大模块）

### 5.1 工作台 Dashboard

- 待办事项（待检测/待审核/待签发）
- 项目检测进度统计
- 近期报告动态
- 设备到期提醒
- 数据看板（按角色展示不同内容）

### 5.2 项目管理

- 工程 → 单位工程 → 分部 → 分项（四级树形结构）
- 项目基本信息维护
- 项目成员配置
- 多项目切换

### 5.3 委托管理

- 新建委托单（手动录入）
- 委托单列表/查询/筛选
- 委托单审核
- 自动编号（可配置规则）
- 关联工程层级
- *可选：OCR扫描识别委托单*

### 5.4 样品管理

- 样品接收登记
- 样品编号（自动生成）
- 样品状态流转（待接收 → 已接收 → 检测中 → 已检测 → 留样中 → 已处置）
- 样品台账查询
- 留样管理与到期提醒
- 样品标签打印

### 5.5 检测管理（核心）

- 任务分配（试验室主任 → 检测员）
- 原始记录录入（按检测类型动态表单）
- 检测数据自动计算
- 结果判定（依据标准自动/手动判定）
- 数据修约（按标准规则修约）
- *可选：AI异常数据检测*
- *可选：OCR手写记录识别*

### 5.6 报告管理

- 报告模板管理（Word模板配置）
- 报告自动生成（填充数据到模板）
- 三级审签流程（编制 → 审核 → 批准）
- 报告编号管理
- 报告导出（Word/PDF/打印）
- 报告台账与查询
- *可选：AI报告初稿生成*

### 5.7 设备管理

- 设备台账（型号/编号/状态）
- 检定/校准记录与证书管理
- 到期自动提醒
- 使用记录（关联检测任务）
- 维护保养计划与记录
- *可选：OCR检定证书识别*

### 5.8 质量管理

- 内审计划与执行记录
- 不符合项登记与跟踪
- 纠正/预防措施
- 体系文件管理
- 人员资质管理（持证上岗）

### 5.9 系统管理

- 用户管理（CRUD/密码重置）
- 角色权限配置
- 检测标准库管理（预置 + 手动新增，预留爬取csres.com接口）
- 编号规则配置
- 数据字典维护
- 操作日志/审计日志
- 系统参数设置

## 6. 核心业务流程

### 6.1 主业务链（8步）

1. **委托受理** — 委托方提交委托单 → 样品管理员审核委托信息 → 系统自动编号
2. **样品接收** — 样品登记编号 → 样品标签打印 → 样品入库
3. **任务分配** — 试验室主任根据样品类型 → 分配检测人员 → 关联标准和设备
4. **试验执行** — 检测员执行试验 → 录入原始记录（动态表单）→ 自动计算 → 数据修约
5. **结果判定** — 根据检测标准条文自动判定合格/不合格 → 检测人员确认 → 支持手动修正
6. **报告生成** — 选择报告模板 → 系统自动填充数据 → 报告编号
7. **三级审签** — 编制人提交 → 审核人审核(通过/退回) → 批准人签发(通过/退回)
8. **签发归档** — PDF归档防篡改 → 可打印盖章 → 委托方可查看/下载

### 6.2 样品状态流转

待接收 → 已接收 → 检测中 → 已检测 → 留样中 → 已处置

### 6.3 报告审签状态流转

草稿 → 待审核 → 待批准 → 已签发

任意环节可退回至上一环节，需填写退回原因。

## 7. 检测标准库

### 7.1 预置标准

系统预置常用建筑材料和市政道路检测标准：

**建筑材料类：**
- GB/T 50081-2019 混凝土物理力学性能试验方法标准
- GB/T 1499.2-2018 钢筋混凝土用钢 第2部分：热轧带肋钢筋
- GB/T 17671-2021 水泥胶砂强度检验方法
- GB/T 14684-2022 建设用砂
- GB/T 14685-2022 建设用卵石、碎石
- JGJ 52-2006 普通混凝土用砂、石质量及检验方法标准
- GB/T 228.1-2021 金属材料 拉伸试验 第1部分：室温试验方法

**市政道路/跑道类：**
- JTG E20-2011 公路工程沥青及沥青混合料试验规程
- JTG E42-2005 公路工程集料试验规程
- JTG E51-2009 公路工程无机结合料稳定材料试验规程
- JTG 3450-2019 公路路基路面现场测试规程
- MH/T 5004-2010 民用机场水泥混凝土道面设计规范（机场专用）

### 7.2 标准维护

- 质量管理员可手动新增/编辑/停用标准
- 标准包含：编号、名称、版本、发布日期、实施日期、条文内容、判定规则
- 预留工标网（csres.com）标准自动爬取接口，后续可按需启用

## 8. 报告输出

- **Word（.docx）** — 套用固定模板生成检测报告，支持模板管理
- **PDF** — 直接生成或Word转PDF，防篡改归档
- **Excel（.xlsx）** — 数据统计报表、台账导出

## 9. AI/OCR 功能（可选增强）

以下功能为可选模块，核心业务不依赖：

- **委托单OCR识别** — PaddleOCR识别扫描/拍照的纸质委托单
- **原始记录OCR** — 识别手写试验原始记录数据
- **检测报告AI生成** — AI根据原始数据生成报告初稿
- **数据异常检测** — AI识别试验数据中的异常值
- **智能判定** — 根据标准自动判定检测结果
- **证书/资质OCR** — 识别设备检定证书、人员资质证书

所有AI/OCR任务通过Celery异步执行，不影响主业务性能。

## 10. 界面设计

### 10.1 整体布局

顶栏 + 左侧菜单 + 主内容区：

- **顶栏（56px）：** 深色背景，Logo + 系统名称、当前项目切换、消息通知、用户信息
- **左侧菜单（200px）：** 深色主题（#263238），9大模块导航，支持子菜单展开/折叠
- **主内容区：** 浅灰背景（#f0f2f5），面包屑导航 + 白色内容卡片

### 10.2 关键页面

- **登录页：** 蓝色渐变背景，居中登录卡片，公司和项目名称
- **工作台：** 统计卡片（待检测/待审核/已签发/设备到期）+ 待办列表
- **检测数据录入：** 基本信息 + 动态数据表格 + 自动计算结果 + 判定显示
- **报告审签：** 审签流程可视化 + 退回原因 + 操作按钮
- **列表页通用：** 顶部筛选条件 + 数据表格 + 分页

### 10.3 设计风格

- Element Plus 默认主题色 #409EFF
- 白色卡片 + 浅灰背景，清晰分层
- 状态标签用不同颜色区分（蓝/橙/绿/红）

## 11. 项目目录结构

```
limis-c2/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI 入口
│   │   ├── config.py              # 配置管理
│   │   ├── database.py            # 数据库连接
│   │   ├── models/                # SQLAlchemy 数据模型
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── commission.py
│   │   │   ├── sample.py
│   │   │   ├── test_task.py
│   │   │   ├── report.py
│   │   │   ├── standard.py
│   │   │   ├── equipment.py
│   │   │   └── quality.py
│   │   ├── schemas/               # Pydantic 请求/响应模型
│   │   ├── api/                   # API 路由
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── projects.py
│   │   │   ├── commissions.py
│   │   │   ├── samples.py
│   │   │   ├── test_tasks.py
│   │   │   ├── reports.py
│   │   │   ├── standards.py
│   │   │   ├── equipment.py
│   │   │   ├── quality.py
│   │   │   ├── dashboard.py
│   │   │   └── system.py
│   │   ├── services/              # 业务逻辑层
│   │   │   ├── auth_service.py
│   │   │   ├── commission_service.py
│   │   │   ├── sample_service.py
│   │   │   ├── test_service.py
│   │   │   ├── report_service.py
│   │   │   ├── judgment_service.py
│   │   │   └── numbering_service.py
│   │   ├── tasks/                 # Celery 异步任务
│   │   │   ├── celery_app.py
│   │   │   ├── ocr_tasks.py
│   │   │   ├── ai_tasks.py
│   │   │   └── report_tasks.py
│   │   ├── core/                  # 核心工具
│   │   │   ├── security.py
│   │   │   ├── permissions.py
│   │   │   ├── dependencies.py
│   │   │   └── exceptions.py
│   │   └── utils/                 # 工具函数
│   │       ├── report_generator.py
│   │       ├── data_rounding.py
│   │       └── file_storage.py
│   ├── alembic/                   # 数据库迁移
│   ├── templates/                 # 报告模板(Word)
│   ├── tests/
│   ├── requirements.txt
│   └── alembic.ini
│
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/index.js
│   │   ├── stores/
│   │   │   ├── user.js
│   │   │   ├── project.js
│   │   │   └── app.js
│   │   ├── api/
│   │   │   ├── request.js
│   │   │   ├── auth.js
│   │   │   ├── project.js
│   │   │   ├── commission.js
│   │   │   ├── sample.js
│   │   │   ├── testTask.js
│   │   │   ├── report.js
│   │   │   ├── equipment.js
│   │   │   └── system.js
│   │   ├── views/
│   │   │   ├── login/
│   │   │   ├── dashboard/
│   │   │   ├── project/
│   │   │   ├── commission/
│   │   │   ├── sample/
│   │   │   ├── test/
│   │   │   ├── report/
│   │   │   ├── equipment/
│   │   │   ├── quality/
│   │   │   └── system/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── AppLayout.vue
│   │   │   │   ├── Sidebar.vue
│   │   │   │   └── Header.vue
│   │   │   ├── ProjectTree.vue
│   │   │   ├── ApprovalFlow.vue
│   │   │   ├── DynamicForm.vue
│   │   │   └── FileUpload.vue
│   │   ├── hooks/
│   │   │   ├── usePermission.js
│   │   │   ├── usePagination.js
│   │   │   └── useProject.js
│   │   └── utils/
│   │       ├── auth.js
│   │       ├── format.js
│   │       └── validate.js
│   ├── public/
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
└── docs/                          # 文档
```

## 12. 非功能需求

- **安全性：** JWT认证 + RBAC权限控制 + 操作审计日志 + 密码加密存储
- **数据安全：** 签发后的报告不可修改，数据库定期备份
- **性能：** 裸机部署，FastAPI + Uvicorn 多worker，Redis缓存热点数据
- **可扩展：** 模块化设计，新增检测类型通过配置驱动无需改代码，预留外部系统接口
- **标准爬取：** 预留工标网（csres.com）标准自动爬取接口
