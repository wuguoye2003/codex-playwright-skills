---
name: playwright-test-report-upgrade
description: "为同步 Python Playwright 脚本接入统一截图与自包含 HTML 测试报告；用于新增、查询、保存、删除等业务自动化脚本的报告升级与复核。"
---

# Playwright 测试报告升级

适用于当前项目的同步 Playwright 脚本。保持原业务顺序和既有断言，不引入 pytest、Allure 或第三方报告依赖。

## 统一入口

使用项目根目录的 `playwright_test_report.py`：

```python
from playwright_test_report import PlaywrightTestReport, run_test_with_report


def run(playwright: Playwright, report: PlaywrightTestReport) -> None:
    browser = playwright.chromium.launch(channel="chrome", headless=False)
    context = browser.new_context(storage_state=AUTH_STATE)
    page = context.new_page()
    page.set_default_timeout(30_000)
    try:
        with report.page_scope(page):
            # 保留原有业务流程，并在保存、查询、删除处接入报告。
            ...
    finally:
        context.close()
        browser.close()


if __name__ == "__main__":
    run_test_with_report(__file__, run)
```

`report.page_scope(page)` 必须在页面、Context 和浏览器关闭前包裹业务流程。它负责在普通异常、超时和中断时立即截取失败现场；不要只调用 `report.bind_page(page)` 后马上在 `finally` 关闭页面。

## 截图和关键操作

只在已确认语义与作用域的控件上调用包装器，不用全局同名按钮猜测保存或查询。

```python
# 保存：前截图 -> 点击记录 -> 成功业务断言 -> 后截图
report.click_save(page, save_button, action_name="保存设备配置")
expect(save_popup).to_be_hidden(timeout=30_000)
report.verify(
    "保存后目标记录可见",
    lambda: expect(target_row).to_be_visible(),
    expected="目标记录可见",
    actual="结果表",
)
report.capture_after_save(page, action_name="保存设备配置")

# 查询：前截图 -> 点击记录 -> 结果断言 -> 后截图
report.click_query(page, query_button, action_name="查询设备")
expect(target_row).to_be_visible(timeout=30_000)
report.capture_after_query(page, action_name="查询设备")

# 删除：前截图和 DELETE 关键操作 -> 确认删除 -> 结果断言 -> 后截图
report.click_delete(page, delete_button, action_name="删除设备")
confirm_button.click()
expect(target_row).to_have_count(0, timeout=30_000)
report.capture(page, "删除设备后", category="after_delete")
```

公共包装器已处理截图画面稳定缓冲，不能以固定等待替代保存、查询或删除后的业务状态断言。对于其他不可逆动作，在动作前调用 `report.checkpoint(page, "动作名称前")`。

## 定位与等待

- 使用当前页面真实 DOM 验证过的弹窗、字段标签、表格行和可见下拉层；限制在表单、筛选面板或目标行范围内。
- 不使用图标字符、动态 ID、全局同名按钮或 `nth()` 作为常规定位方案。重复 placeholder 或远程下拉应按字段标签和活动下拉层定位。
- 单页应用导航采用 `wait_until="domcontentloaded"` 和明确超时；不要默认等待 `networkidle`。
- 保存后等待弹窗关闭、成功提示、响应或目标行状态；查询后等待目标行、分页总数或筛选结果；删除后等待目标记录消失。固定短等待只可用于截图视觉稳定，不能代表业务成功。

## 业务断言与测试数据

- 使用 `report.verify()` 记录业务断言名称、预期、实际描述和结果；不删除或放宽已有 `expect()`。
- 新增类脚本使用单次运行唯一的测试值，避免历史数据重名，例如 `uuid4().hex[:8]` 后缀。
- 删除动作必须先限制到本次查询得到的目标行；不得通过全选误删无关数据。
- 不要声称已实际运行写入流程，除非用户明确授权并确实完成实际运行。

## 报告目录与中文名称

- 报告是自包含 HTML，PNG 原图保留在同次运行的 `screenshots/` 目录。
- 目录规则为 `test_artifacts/YYYY-MM-DD/中文脚本名/运行编号/report.html`。
- `playwright_test_report.py` 优先读取项目根目录 `hmtest-script-name-mapping.xlsx`；存在脚本名映射时使用中文名，未映射时使用英文脚本名。不要手写中文目录名。
- 历史目录迁移仅在用户明确授权时进行。迁移前盘点映射、目标冲突、目录内报告数量；只重命名存在映射且无冲突的目录，未映射目录保持不动。

## 交付前复核

1. 运行 `python -m py_compile` 检查公共模块和被改脚本。
2. 复读所有修改后的调用点，确认保存、查询、删除动作都使用了正确包装器，并且每次操作后有业务状态断言及后截图。
3. 用户已授权真实运行时，顺序运行全部脚本；某一脚本失败时仍继续其余脚本，最终报告每支的 PASS、FAIL 或 TIMEOUT、截图数、关键操作数、断言数和报告路径。
4. 从 HTML 内嵌 JSON 元数据核对实际状态，不只依据控制台输出。失败报告必须检查是否包含失败现场截图；若失败截图缺失，先修复页面作用域再交付。
5. 未经用户授权时，只做语法检查和无写入 DOM 核验，并明确说明没有实际执行写入流程。
