# 风控管理员前端页面生成完成

## 已创建文件

### 布局组件
- `src/views/risk/RiskLayoutView.vue` - 风控角色侧边栏布局（6 个菜单项）

### 页面组件
1. `src/views/risk/RiskReviewWorkbenchView.vue` - 复核工作台（三栏布局）
   - 左栏：待复核任务列表（12 个任务）
   - 中栏：审查记录时间线（AI 初审意见 + 法务修订）
   - 右栏：风控最终裁断（AI 识别点处理、最终定级、复核意见）

2. `src/views/risk/RiskWarningView.vue` - 预警处置中心
   - Tab 切换：待处置预警 (3) / 整改复审 (2)
   - 卡片式预警列表（含风险等级、预警内容、风险点定位、时间线）
   - 操作按钮：书面豁免、转为正式预警

3. `src/views/risk/RiskAuditLedgerView.vue` - 审核台账
   - 筛选栏：搜索合同、风险等级、合同类型、审核阶段
   - 表格：合同编号、名称、上传人、AI 分数（进度条）、风险预警、法务状态、风控状态、最终结果、操作
   - 分页：共 428 条记录

4. `src/views/risk/RiskOverdueView.vue` - 逾期清单
   - 顶部统计卡片：逾期预警总数 (128)、超期 1-7 天 (84)、超期>7 天 (44)
   - 逾期明细表格：合同名称、预警类型、原截止日期、已逾期天数、当前负责人、状态
   - 分页：共 128 项

5. `src/views/risk/RiskReportView.vue` - 审核报告
   - 报告生成卡片：月度风控审核报告、风险统计分析、逾期预警汇总
   - 历史报告列表

6. `src/views/risk/RiskProfileView.vue` - 个人设置
   - 基础信息（用户信息、权限说明）
   - 通知设置（新任务、逾期预警、高风险预警、邮件通知）
   - 安全设置（修改密码、双因素认证、登录日志）

### 路由配置
已更新 `src/router/index.ts`，添加风控角色路由：
- `/risk/workbench` - 复核工作台
- `/risk/warning` - 预警处置
- `/risk/ledger` - 审核台账
- `/risk/overdue` - 逾期清单
- `/risk/report` - 审核报告
- `/risk/profile` - 个人设置

## 技术栈
- Vue 3 + TypeScript
- Element Plus UI 组件库
- Vue Router 路由管理
- Vite 构建工具

## 运行方式
```bash
cd D:\front
npm run dev
```
访问 http://localhost:3000

## 设计稿对应关系
- 截图 1（审核台账）→ RiskAuditLedgerView.vue
- 截图 2（逾期清单）→ RiskOverdueView.vue
- 截图 3（复核工作台）→ RiskReviewWorkbenchView.vue
- 截图 4（预警处置）→ RiskWarningView.vue

## 注意事项
1. 所有页面均为前端 Mock 数据，未连接后端 API
2. 侧边栏菜单项与截图完全一致
3. 样式风格与现有法务审核员页面保持一致
4. 颜色主题：主色 #1a6fc4（蓝色），风险色 #f56c6c（红）、#e6a23c（橙）、#67c23a（绿）
