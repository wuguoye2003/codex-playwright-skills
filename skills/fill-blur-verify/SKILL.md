---
name: fill-blur-verify
description: 使用 Playwright 填写网页表单字段后触发失焦并断言输入值已保留。用于 Vue、React 等表单可能异步同步、校验或清空字段，或需要确认没有填错字段的自动化场景。
---

# 填写后失焦与值校验

对需要写入普通文本输入框的 Playwright 表单操作，按以下顺序执行：

1. 先用表单标签、字段容器或其他稳定语义定位输入框；避免全局 `nth()`。
2. 断言定位器唯一且可见。
3. 点击、填写、按 `Tab` 使字段失焦。
4. 断言输入框值仍与预期一致，再继续保存或提交。

```python
from playwright.sync_api import expect

input_box = field_container.locator("input:not([readonly]):not([disabled])")
expect(input_box).to_have_count(1)
expect(input_box).to_be_visible()
input_box.click()
input_box.fill(value)
input_box.press("Tab")
expect(input_box).to_have_value(value)
```

仅对普通可编辑输入框使用该流程。遇到 `readonly` 输入框、远程搜索下拉框或日期控件时，先检查实际 DOM 和控件交互方式；不要直接 `fill()`。

## 异步初始化与重渲染

弹窗或表单可能在显示后继续设置默认单选项、适用范围或其他初始状态；这类重渲染会清空已提前填写的字段。对这类表单，按以下顺序执行：

1. 先等待一个可验证的稳定业务状态，例如默认单选项已选中、依赖字段已可编辑；不要用固定等待代替。
2. 按字段标签定位并填写每个普通输入框，每项都失焦并校验当前值。
3. 所有字段填写完成后，重新获取每个关键字段的定位器并再次断言全部值仍保留，再执行保存。

若最终回读失败，停止提交并检查是否由初始化、字段联动或重渲染替换了控件；不要通过重复点击保存或缩短等待来掩盖问题。

## 先观测，不猜测

当定位器解析为 0 个元素、不唯一、只读、点击后失效，或控件属性会随状态改变时，**必须先读取实际页面 DOM，不得推测 CSS 类名、组件层级、占位文本、可访问名称或字段顺序。**不能从截图、其他页面、旧录制脚本或框架惯例推导当前页面的选择器。

使用已登录会话以只读模式完成下列观测：

1. 打开目标页面和相关弹窗，不点击保存、提交或删除。
2. 打印目标控件和它的字段容器的 `outerHTML`、`class`、`role`、`aria-*`、`placeholder`、`readonly`、`value` 与可见性。
3. 对下拉框或短暂弹层，点击打开后再采集当前可见弹层、选项和选中后的控件状态。
4. 只根据这些证据编写选择器；先运行不保存的最小交互来验证。
如果不能读取实际 DOM，不要修改为未验证的样式选择器；报告需要浏览器观测权限或用户提供的 DOM 快照。

## 按标签定位字段容器

对有重复占位文本、动态无障碍名称或多个相似输入框的表单，先用已验证的表单标签找到字段容器，再在容器内定位控件。不要依赖全局 `get_by_role(...).nth()`、绝对 CSS 路径或会随值变化的 `name`。

DOM 结构需先从当前页面检查确认。仅当目标页面已实测为 `.hm-form-item__group` 和 `.hm-form-item__label` 时，才可使用：

```python
import re
from playwright.sync_api import expect

label = page.locator(".hm-form-item__label").filter(
    has_text=re.compile(r"^\s*\*?\s*上级角色\s*$")
)
field = page.locator(".hm-form-item__group").filter(has=label)
expect(field).to_have_count(1)
control = field.locator(".hm-form-item__content input:not([disabled])")
expect(control).to_have_count(1)
```

标签选择器、容器选择器和控件选择器不能想当然复用；如果断言不成立，先重新检查 DOM，不要改用另一个 `nth()`。

## 动态下拉框与会变化的定位器

下拉框不是“填写后失焦”流程的对象。选中后，输入框的无障碍名称、占位文本、DOM 节点或可见性可能改变；不要在点击选项后仍复用如 `get_by_role("textbox", name="请选择")` 或 `input[placeholder="请选择"]` 的定位器做断言。打开和选中的两个阶段都要以实际 DOM 观测结果为准。

对会在失焦、聚焦或选中时重渲染的动态控件，不要使用 `expect(locator).to_have_count(1)` 或以计数为前置断言。这类断言会将短暂的重渲染当成测试失败。改用与当前交互阶段匹配的状态断言：

```python
control.wait_for(state="visible")
if not dropdown.is_visible():
    control.click()
dropdown.wait_for(state="visible")
option.wait_for(state="visible")
option.click()
expect(control).to_have_value(expected_value)
dropdown.wait_for(state="hidden")
```

仅对页面结构已实测且不会随交互改变的静态字段容器或普通输入框，才使用 `to_have_count(1)` 验证唯一性。

1. 打开已由标签容器定位的下拉控件。
2. 只在当前可见的下拉层中，以完整文本精确选择选项。
3. 确认下拉层关闭、选项激活态样式，或其他不依赖会变化名称的结果。
4. 无法从已确认的结构得到稳定结果时，先检查当前 DOM，不要通过 `element_handle()`、强制点击或任意等待来规避定位失效。

失焦后值校验失败时，停止后续提交操作并检查：定位器是否漂移、页面是否重渲染、字段是否受格式化/校验规则影响，或是否需要选择下拉候选项。
