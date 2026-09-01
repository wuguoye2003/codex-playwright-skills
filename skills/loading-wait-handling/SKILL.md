---
name: loading-wait-handling
description: 为 Playwright 浏览器自动化建立可靠的等待加载处理方式。创建、审查或修复网页脚本时使用，尤其适用于导航、筛选、分页或保存后使用 networkidle、固定等待或不稳定就绪条件的场景。
---

# 等待加载处理方式

以页面业务状态而非全局网络静默作为就绪条件。

## 页面导航

对单页应用优先使用 `wait_until="domcontentloaded"` 并设置显式超时（通常为 60 秒）。不要默认使用 `networkidle`：应用可能持续轮询、保持 Socket 连接或存在长请求。

导航后立刻断言首个页面特有元素，例如必需页签、表单标签或已加载的表格行。

```python
page.set_default_timeout(30_000)
page.goto(route, wait_until="domcontentloaded", timeout=60_000)
expect(page.get_by_role("tab", name="目标页签", exact=True)).to_be_visible()
```

## 异步操作

筛选、分页或保存后，等待业务结果；不要调用 `wait_for_load_state("networkidle")` 或使用无意义的固定等待。

- 筛选：填值后按 `Tab`，再点击已检查的查询按钮。已知请求路径时等待对应响应，再断言目标行或筛选总数。
- 分页：断言请求页码处于激活状态，且目标行状态已变化。
- 保存：滚动已确认的保存按钮到可见区，断言其可用后点击；存在成功提示或其他可验证的保存状态时，再等待该状态。

```python
input_box.fill(value)
input_box.press("Tab")
expect(input_box).to_have_value(value)

with page.expect_response(
    lambda response: "/known-query-route" in response.url and response.ok,
    timeout=30_000,
):
    query_button.click()
expect(table.get_by_text(expected_value, exact=True)).to_be_visible(timeout=30_000)
```

## 检查与兜底

定义目标控件前先检查真实 DOM。将定位器限制在字段或表格容器内；不要使用全局空按钮定位器、易变的生成 ID 或强制点击。

未知请求路径时，使用一个带合理超时的业务状态断言。断言失败时停止并报告缺失结果，不要重试无关点击。
