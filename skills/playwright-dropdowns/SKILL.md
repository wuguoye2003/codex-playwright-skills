---
name: playwright-transient-dropdowns
description: 诊断和修复由短暂下拉框与日期面板导致的 Playwright 不稳定交互。当上一个弹层尚未关闭、无法选择下一个选项或日期，或选择动作出现 strict mode violation、重复元素、不可见、视口外、元素不稳定、TargetClosed 等错误时使用。
---

# Playwright 短暂下拉框与日期面板

将下拉框和日期面板视为异步弹层。选择操作可能会关闭并重新渲染弹层，而 Playwright 已开始执行下一步。每次都要将操作范围限制在当前活跃弹层内，并在打开下一个字段前等待它完全关闭。

## 判断故障

| 现象 | 常见原因 | 处理方式 |
| --- | --- | --- |
| 选人名或日期时出现 `strict mode violation` | 旧弹层和当前弹层中都有相同文本 | 将定位限定到当前可见弹层。 |
| `element is not visible`、`outside of the viewport` 或 `element is not stable` | 定位到正在关闭、已隐藏或被裁剪的弹层项 | 不要点击全局定位器；重新打开字段并限定到活跃弹层。 |
| 下一个下拉框已打开，但无法选中选项 | 上一个下拉框的关闭动画与下一次点击发生竞态 | 等待上一个下拉弹层消失。 |
| 日期操作时出现 `TargetClosedError` | 之前的日历面板仍处于活跃状态，或测试在超时后触发了清理 | 每次选择日期后都要确认面板已关闭，再继续下一步。 |

除了排查组件自身问题时，不要用任意的 `wait_for_timeout()` 授码来排除竞态。优先使用状态断言。

## 下拉框

打开目标字段后，只能在当前活跃菜单中选择选项，并等待菜单关闭。

```python
ACTIVE_DROPDOWN = (
    ".hm-select-dropdown:visible"
    ":not(.hm-zoom-in-top-leave-active)"
    ":not(.hm-zoom-in-top-leave-to)"
)


def current_dropdown(page):
    # `:visible` alone can include the previous menu during its exit animation.
    dropdown = page.locator(ACTIVE_DROPDOWN)
    expect(dropdown).to_have_count(1, timeout=10_000)
    return dropdown


def select_dropdown_option(page, text: str):
    current_dropdown(page).get_by_text(text, exact=True).click()
    # The leaving element may remain visible briefly.
    expect(page.locator(ACTIVE_DROPDOWN)).to_have_count(0, timeout=10_000)
```

### Remote-search fallback

When an exact remote-search result does not appear, clear the query with keyboard input rather
than only `fill("")`. Confirm that the input is empty, then wait for the first enabled option in
the same active dropdown. This ensures that the empty-query event is delivered and that the
unfiltered remote response has rendered.

```python
def select_first_available_remote_option(page, control, keyword: str) -> None:
    control.fill(keyword)
    exact = current_dropdown(page).get_by_role("listitem").filter(
        has_text=re.compile(rf"^\s*{re.escape(keyword)}\s*$")
    )
    try:
        exact.wait_for(state="visible", timeout=2_000)
        option = exact
    except PlaywrightTimeoutError:
        control.click()
        control.press("ControlOrMeta+A")
        control.press("Backspace")
        expect(control).to_have_value("")
        option = current_dropdown(page).locator(
            ".hm-select-dropdown__item:not(.is-disabled)"
        ).first

    expect(option).to_be_visible(timeout=10_000)
    option.click()
```

当错误调用日志同时列出一个带 `*-leave-active` / `*-leave-to` 类的菜单和一个带
`*-enter-active` 类的菜单时，两个元素都可能匹配 `:visible`。从日志复制实际的退场类并
从活动菜单定位器中排除它们；不要用 `.first` 或任意 `wait_for_timeout()` 掩盖竞态。

```python
page.get_by_role("textbox", name="请选择").nth(2).click()
select_dropdown_option(page, "郭钊")

page.get_by_role("textbox", name="请选择").nth(3).click()
select_dropdown_option(page, "陈志")
```

对于字段顺序不会变化的旧表单，可以临时使用 `nth()`，但每次选择后必须重新查询它。存在稳定标签、`data-testid` 或正确关联的 `label` 时，优先使用它们。

## 日期面板

仅使用当前可见的日期面板进行导航，且只选择当月日期。日历网格通常会显示相邻月份的重复日期。

```python
def current_date_picker(page):
    picker = page.locator(".hm-picker-panel:visible")
    expect(picker).to_have_count(1)
    return picker


def select_date_day(page, day: str):
    date_cell = current_date_picker(page).locator(
        "td:not(.prev-month):not(.next-month)"
    ).filter(has_text=re.compile(rf"^\s*{re.escape(day)}\s*$"))
    expect(date_cell).to_have_count(1)
    date_cell.click()
    expect(page.locator(".hm-picker-panel:visible")).to_have_count(0)
```

```python
page.get_by_role("textbox", name="选择日期").nth(2).click()
current_date_picker(page).get_by_role("button", name="前一年").click()
current_date_picker(page).get_by_role("button", name="上个月").click()
select_date_day(page, "30")
```

年份、月份导航按钮和日期单元格也必须限定在 `current_date_picker(page)` 中。不要使用如 `page.get_by_text("30")` 这样的全局日期定位，也不要使用固定索引的日历容器。

## 修复检查清单

1. 通过弹层的 `:visible` 容器确认当前打开的弹层。
2. 将选项、导航按钮或日期单元格限定到该容器。
3. 执行选择。
4. 在操作下一个下拉框或日期输入框前，断言该容器计数为零。
5. 在增加重试前，先替换全局文本定位和已失效的弹层 CSS 路径。
