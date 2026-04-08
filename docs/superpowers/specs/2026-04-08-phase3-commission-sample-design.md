# Phase 3: 委托管理与样品管理 — 设计规格

**日期：** 2026-04-08  
**依赖：** Phase 1（认证/RBAC）、Phase 2（项目层级管理）

---

## 1. 概述

Phase 3 实现委托管理和样品管理两个核心业务模块，引入 Service 层架构和可配置编号规则引擎。委托单关联分项工程（SubItem），审核通过后样品管理员可登记样品。

**范围内：**
- 委托单 CRUD + 提交/审核流程
- 样品登记 + 6级状态流转
- 可配置编号规则引擎（委托单和样品共用）
- 前端列表页和详情页
- 编号规则管理 API

**范围外（后续实现）：**
- OCR 扫描识别委托单
- 样品标签打印
- 多级审核链配置
- 留样到期自动提醒

---

## 2. 数据模型

### 2.1 Commission（委托单）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| commission_no | String(50) UNIQUE | 委托编号（自动生成） |
| project_id | Integer FK → projects.id | 关联工程 |
| sub_item_id | Integer FK → sub_items.id | 关联分项工程 |
| client_name | String(100) | 委托方名称 |
| client_contact | String(50) | 委托方联系人 |
| client_phone | String(20) | 联系电话 |
| description | Text | 委托内容/检测要求 |
| sample_count | Integer | 预计样品数量 |
| status | String(20) | draft / submitted / approved / rejected |
| submitted_by | Integer FK → users.id | 提交人 |
| reviewed_by | Integer FK → users.id (nullable) | 审核人 |
| review_comment | Text (nullable) | 审核意见 |
| reviewed_at | DateTime (nullable) | 审核时间 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**状态流转：**
```
draft → submitted → approved
                  → rejected → draft（修改后可重新提交）
```

### 2.2 Sample（样品）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| sample_no | String(50) UNIQUE | 样品编号（自动生成） |
| commission_id | Integer FK → commissions.id | 关联委托单 |
| name | String(200) | 样品名称 |
| material_type | String(50) | 材料类型 |
| specification | String(100) | 规格型号 |
| quantity | Integer | 数量 |
| quantity_unit | String(20) | 单位（组、个、根等） |
| sampling_date | Date | 取样日期 |
| sampling_location | String(200) | 取样部位 |
| sampler | String(50) | 取样人 |
| status | String(20) | pending / received / testing / tested / retained / disposed |
| received_by | Integer FK → users.id (nullable) | 接收人 |
| received_at | DateTime (nullable) | 接收时间 |
| storage_location | String(100) (nullable) | 存放位置 |
| retention_deadline | Date (nullable) | 留样到期日 |
| disposed_at | DateTime (nullable) | 处置时间 |
| notes | Text (nullable) | 备注 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**状态流转（严格单向，仅允许相邻转换）：**
```
pending → received → testing → tested → retained → disposed
```

### 2.3 NumberingRule（编号规则）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| entity_type | String(30) UNIQUE | 适用实体：commission / sample |
| name | String(100) | 规则名称 |
| prefix | String(20) | 前缀（如 WT、YP） |
| date_format | String(20) | 日期格式：YYYY / YYYYMM / 空串 |
| separator | String(5) | 分隔符（如 -） |
| sequence_digits | Integer | 序号位数（如 4 → 0001） |
| sequence_reset | String(20) | 重置周期：yearly / monthly / never |
| current_sequence | Integer | 当前序号 |
| last_reset_date | Date | 上次重置日期 |
| is_active | Boolean | 是否启用 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**编号生成示例：** prefix + separator + date + separator + sequence → `WT-2026-0001`

---

## 3. Service 层架构

### 3.1 NumberingService（`services/numbering_service.py`）

```
generate_number(db, entity_type) -> str
```

- 查找 entity_type 对应的 active 规则
- 使用 `SELECT ... FOR UPDATE` 行级锁防止并发重复
- 检查序号重置周期，必要时重置 current_sequence
- current_sequence += 1，拼接编号
- 委托单和样品共用此引擎

### 3.2 CommissionService（`services/commission_service.py`）

```
create_commission(db, data, user_id) -> Commission    # 创建draft，自动编号
submit_commission(db, commission_id, user_id)          # draft → submitted
review_commission(db, id, reviewer_id, approved, comment)  # submitted → approved/rejected
reject_to_draft(db, commission_id)                     # rejected → draft
```

### 3.3 SampleService（`services/sample_service.py`）

```
create_sample(db, data, user_id) -> Sample   # 关联已approved委托单，自动编号
receive_sample(db, sample_id, user_id, storage_location)  # pending → received
update_status(db, sample_id, new_status)     # 校验合法相邻状态转换
list_samples(db, filters)                    # 台账查询，支持多维筛选
```

---

## 4. API 端点

### 4.1 委托管理（`api/commissions.py`）

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/commissions` | 创建委托单 | commission:create |
| GET | `/commissions` | 列表查询（分页/筛选） | commission:read |
| GET | `/commissions/{id}` | 委托单详情（含关联样品） | commission:read |
| PUT | `/commissions/{id}` | 编辑（仅 draft 状态） | commission:update |
| POST | `/commissions/{id}/submit` | 提交审核 | commission:create |
| POST | `/commissions/{id}/review` | 审核通过/退回 | commission:approve |
| DELETE | `/commissions/{id}` | 删除（仅 draft 状态） | commission:update |

### 4.2 样品管理（`api/samples.py`）

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/samples` | 登记样品 | sample:create |
| GET | `/samples` | 样品台账（分页/筛选） | sample:read |
| GET | `/samples/{id}` | 样品详情 | sample:read |
| PUT | `/samples/{id}` | 编辑样品信息 | sample:update |
| POST | `/samples/{id}/receive` | 接收样品 | sample:update |
| POST | `/samples/{id}/status` | 状态流转 | sample:update |

### 4.3 编号规则（`api/commissions.py` 附加）

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/numbering-rules` | 查询编号规则 | system:manage |
| PUT | `/numbering-rules/{id}` | 修改编号规则 | system:manage |

### 4.4 筛选参数

**委托单列表：** keyword（名称/编号模糊搜索）、status、project_id、page、page_size  
**样品台账：** keyword（名称/编号）、status、commission_id、material_type、page、page_size

---

## 5. 前端页面

### 5.1 委托管理

**`views/commission/index.vue` — 委托单列表页：**
- 筛选栏：关键词、状态下拉、项目下拉、搜索按钮
- 数据表格：委托编号、委托内容、关联分项、委托方、状态标签、创建时间、操作
- 操作列：查看详情、编辑（draft）、提交（draft）、删除（draft）
- 新建委托单按钮 → 弹窗表单
- 分页

**`views/commission/detail.vue` — 委托单详情页：**
- 委托信息卡片（Descriptions 组件展示全部字段）
- 审核操作区（仅 submitted 状态、有审核权限时显示通过/退回按钮 + 意见输入）
- 关联样品列表（表格展示该委托单下的样品）
- 编辑按钮（仅 draft 状态）

### 5.2 样品管理

**`views/sample/index.vue` — 样品台账页：**
- 筛选栏：关键词、状态下拉、材料类型下拉、搜索按钮
- 数据表格：样品编号、名称、材料类型、规格、委托编号（链接）、状态标签、取样日期、操作
- 操作列：查看详情、接收（pending）、状态流转
- 登记样品按钮 → 弹窗表单（含委托单选择器）
- 分页

**`views/sample/detail.vue` — 样品详情页：**
- 样品信息卡片
- 状态流转时间线（展示各状态变更记录）
- 状态操作按钮（根据当前状态显示下一步操作）
- 关联委托单信息

### 5.3 前端 API 模块

- `api/commission.js` — 委托单相关接口封装
- `api/sample.js` — 样品相关接口封装

### 5.4 路由

```
/commissions          → CommissionList
/commissions/:id      → CommissionDetail
/samples              → SampleList
/samples/:id          → SampleDetail
```

### 5.5 侧边栏菜单

在 Sidebar 组件中新增"委托管理"和"样品管理"两个菜单项。

---

## 6. 测试

- `tests/test_numbering.py` — 编号生成、周期重置、规则不存在时报错
- `tests/test_commissions.py` — CRUD、状态流转完整链路、权限校验、重复提交拒绝
- `tests/test_samples.py` — CRUD、状态流转校验、关联未审核委托单拒绝、非法状态跳转拒绝

---

## 7. 种子数据

扩展 `seed.py`：
- 预置编号规则：委托单（WT-YYYY-0001）、样品（YP-YYYY-0001）
- 基于浦东机场项目创建 2-3 条委托单（draft、submitted、approved 各一条）
- approved 委托单下创建 2-3 个样品（pending、received、testing 状态）

---

## 8. 数据库迁移

新增 Alembic migration 创建三张表：`commissions`、`samples`、`numbering_rules`。

---

## 9. 文件清单

**后端新增：**
- `backend/app/models/commission.py` — Commission 模型
- `backend/app/models/sample.py` — Sample 模型
- `backend/app/models/numbering.py` — NumberingRule 模型
- `backend/app/schemas/commission.py` — 委托单 Pydantic schemas
- `backend/app/schemas/sample.py` — 样品 Pydantic schemas
- `backend/app/services/numbering_service.py` — 编号规则引擎
- `backend/app/services/commission_service.py` — 委托单业务逻辑
- `backend/app/services/sample_service.py` — 样品业务逻辑
- `backend/app/api/commissions.py` — 委托单 API 路由
- `backend/app/api/samples.py` — 样品 API 路由
- `backend/tests/test_numbering.py`
- `backend/tests/test_commissions.py`
- `backend/tests/test_samples.py`

**后端修改：**
- `backend/app/models/__init__.py` — 导出新模型
- `backend/app/main.py` — 注册新路由
- `backend/app/seed.py` — 新增编号规则和示例数据

**前端新增：**
- `frontend/src/api/commission.js`
- `frontend/src/api/sample.js`
- `frontend/src/views/commission/index.vue`
- `frontend/src/views/commission/detail.vue`
- `frontend/src/views/sample/index.vue`
- `frontend/src/views/sample/detail.vue`

**前端修改：**
- `frontend/src/router/index.js` — 添加路由
- `frontend/src/components/layout/Sidebar.vue` — 添加菜单项
