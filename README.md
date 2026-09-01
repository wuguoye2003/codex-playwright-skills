这 7 个 skill 都围绕 Playwright 的“真实 DOM、稳定定位、状态断言和可追溯报告”展开：

| Skill | 作用总结 |
| --- | --- |
| `device-discovery-management` | 用于设备发现、添加监控、补充信息和纳管流程。重点处理 IP 批量输入、VXE 结果表、真实复选框勾选、设备状态变化和纳管确认；要求把“已监控/已纳管”视为幂等结果。 |
| `fill-blur-verify` | 用于普通表单输入。标准动作是：按标签定位 → 确认唯一可见 → 填写 → `Tab` 失焦 → 断言值仍保留。适合 Vue/React 表单异步校验、重渲染或字段被清空的问题。 |
| `loading-wait-handling` | 用于改善等待策略。要求以业务状态作为就绪条件：导航用 `domcontentloaded` 加页面特征断言；查询、保存、分页后等待目标行、总数、弹窗关闭或响应，而不是 `networkidle` 或固定等待。 |
| `playwright-dropdowns` | 用于短暂下拉框和日期面板的竞态问题。所有选项、日期和按钮都限定在当前可见弹层中；每次选择后确认旧弹层已关闭，再操作下一个字段，避免 strict mode、不可见和不稳定元素错误。 |
| `playwright-form-field-labels` | 用于修复重复 placeholder、`nth()` 索引漂移和远程下拉误填。核心是先检查真实 DOM，识别实际弹窗和字段容器，再按字段标签定位控件；远程下拉只能在当前可见菜单中选择。 |
| `playwright-test-report-upgrade` | 为同步 Python Playwright 脚本接入统一报告。保存、查询、删除前后自动截图；记录关键操作、业务断言、异常、超时和失败现场，并输出自包含 HTML 报告及结构化 JSON。 |
| `vxe-dialog-scroll-pagination` | 专门处理 VXE 表格和设备选择弹窗的滚动、分页、筛选、全选和确认。要求使用真实滚动句柄，按“滚动 → 分页 → 筛选 → 全选 → 确认”执行，并以分页总数或业务结果验证筛选完成。 |
