---
name: vxe-dialog-scroll-pagination
description: 使用 Playwright 在 VXE 表格及设备选择弹窗中验证滚动、分页、筛选和全选流程。适用于需要模拟纵向或横向滚动，或在弹窗内按滚动、分页、筛选、勾选、确认顺序操作 VXE 列表的场景。
---

# VXE 弹窗滚动与分页

使用真实滚动句柄，不使用 `*-appearance` 装饰层、鼠标坐标或拖拽。

- 纵向：`.vxe-table--scroll-y-handle`，操作 `scrollTop`
- 横向：`.vxe-table--scroll-x-handle`，操作 `scrollLeft`

## 通用表格流程

1. 检查目标 VXE 表格与所需滚动句柄均唯一。
2. 复用 `scripts/vxe_scroll.py` 的 `scroll_vxe_scrollbar`。
3. 每次滚动后只验证最终位置达到 `0` 或最大可滚动距离。
4. 仅当横纵方向都存在可滚动范围时，执行下、右、上、左四个方向；否则只执行用户要求的方向。

## 设备选择弹窗流程

按以下顺序执行：**滚动 → 分页 → 筛选 → 全选 → 确认**。

1. 定位唯一可见弹窗、左侧 VXE 表格和可见分页器；先检查真实 DOM，不要假定组件层级。
2. 仅当下一页按钮可用时，执行分页。每次点击后断言目标页码带有激活状态，再读取新的表格状态；不要使用 `networkidle`。
3. 从筛选按钮的实际关联属性或可见弹层定位筛选面板。按标签填写筛选项、触发失焦并确认值保留。
4. 点击查询后等待筛选总数或目标结果行变为预期状态，再点击全选。不要用固定等待替代该断言。
5. 检查真实表头全选控件，确认右侧已选列表数量与筛选结果一致，再点击当前可见弹窗内的确认按钮并等待弹窗关闭。

```python
query.click()
expect(page.locator(".hm-pagination:visible .hm-pagination__total")).to_have_text(
    re.compile(r"^\s*共\s*1\s*条\s*$"), timeout=15_000
)

select_all.click()
expect(page.locator("#plRightParent .vxe-body--row")).to_have_count(1)
confirm.click()
```

## 筛选后的重渲染与全选

点击筛选面板的“查询”后，VXE 可能短暂保留筛选前的 `.vxe-body--row` 节点；不得仅因目标 IP 行已经存在，就立即点击表头全选。必须先断言与左侧表格对应的分页总数已变为预期结果，再定位唯一目标行并全选。

```python
query_button.click()

left_panel = dialog.locator("#plLeftParent")
left_pagination = left_panel.locator("xpath=..").locator(
    ".hm-pagination:visible"
)
result_total = left_pagination.locator(".hm-pagination__total")
expect(result_total).to_have_text(
    re.compile(r"^\s*共\s*1\s*条\s*$"), timeout=30_000
)

result_row = left_panel.locator(".vxe-body--row").filter(has_text=target_ip)
expect(result_row).to_have_count(1, timeout=30_000)
header_select_all.click()
```

不要用“当前渲染的 `.vxe-body--row` 数量”作为筛选完成标志：虚拟表格可能同时保留旧行。对于预期不止一条的筛选结果，以对应分页总数或业务唯一结果集合的明确状态作为断言。

## 失败处理

- 滚动范围为零或句柄未渲染时，等待表格初始化；不要改用装饰层。
- 分页器或筛选面板不在弹窗子树时，根据真实 DOM 重新定位，禁止使用不稳定的 `.nth()`。
- 筛选后总数仍为旧值时，不要全选或确认；先等待可验证的筛选结果。
