---
name: playwright-form-field-labels
description: 修复 Playwright 表单自动化中由重复 placeholder、get_by_role(...).nth(...)、字段索引漂移或远程下拉导致的错误填充。用于需要根据真实 DOM 识别弹窗、字段标签、字段容器及可见下拉层的场景。
---

# Playwright 表单字段标签定位

录制脚本中的 `nth()` 只能作为最后手段。表单增加字段、多个控件共用 placeholder，或“请输入”同时匹配“请输入关键字”时，索引都会漂移。

## 定位前先检查

- 点击“新增”后，先检查**本次会话、当前页签中实际可见的 DOM**，再编写任何表单定位器。不要根据截图、其他页面或历史录制结果假设框架、弹窗 class、字段容器或标签 class。
- 不得把“新增”写死为 `.hm-popup`，也不得先调用“等待 `.hm-popup`”的通用函数再寻找字段。`.hm-popup` 仅能在本次 DOM 已验证其可见、唯一且确实承载目标表单后使用。
- 新增界面可能是 `.hm-popup`、`role=dialog`、`role=tooltip` 的 popover、抽屉，或挂在新增按钮下的页面内联表单。点击新增后先列出可见候选容器，并以“包含目标字段标签、目标输入框及保存按钮”的同一容器作为表单根节点。
- 确认实际表单根节点、字段项和标签的选择器。例如一个页面可能使用 `.hm-popup > .hm-form-item > .hm-form-item__label`，另一个可能使用 `.hm-popover-select form.el-form > .el-form-item > .el-form-item__label`；两者不能共用容器假设。
- 断言弹窗、匹配标签、字段祖先和控件都恰好匹配一个元素。断言失败时重新检查 DOM，不得猜测新选择器或改用 `nth()`。
- 向普通字段填值却遇到 readonly，通常说明定位已经漂移，或该字段本质是远程下拉。

## 新增表单容器识别

将以下步骤作为新增、修改和保存前的强制检查：

1. 点击当前页签内唯一的新增入口。
2. 检查点击后新出现或变为可见的容器；不要用固定 class 预判结果。
3. 在同一个候选容器内同时断言目标字段标签、可编辑控件和保存按钮各唯一。
4. 将该候选容器传给字段填写和保存函数；保存按钮不得全局定位。
5. 保存后断言该**实际容器**已关闭、隐藏或卸载。

如果页面的新增 UI 是内联 popover，以下模式是正确的；动态 `id` 不可作为定位依据：

```python
# 该选择器必须来自本次 DOM 检查，不是所有页面通用模板。
popover = page.locator(".hm-popover-select:visible")
expect(popover).to_have_count(1)
form = popover.locator("form.el-form.hm-title__underline__body")
expect(form).to_have_count(1)

label = form.locator(".el-form-item__label").filter(has_text=label_pattern)
field = label.locator("xpath=ancestor::div[contains(@class, 'el-form-item')][1]")
control = field.locator("input.el-input__inner:not([readonly]):not([disabled])")
expect(control).to_have_count(1)

save = popover.get_by_role("button", name="保存", exact=True)
expect(save).to_have_count(1)
```

## 使用字段标签

`form_field` 是模式而非可直接复制的选择器。必须先根据真实页面检查结果替换 `LABEL_SELECTOR` 和 `FIELD_ANCESTOR_SELECTOR`。

```python
import re
from playwright.sync_api import expect


def form_field(dialog, label: str):
    label_node = dialog.locator(LABEL_SELECTOR).filter(
        has_text=re.compile(rf"^\s*\*?\s*{re.escape(label)}\s*$")
    )
    expect(label_node).to_have_count(1)
    field = label_node.locator(FIELD_ANCESTOR_SELECTOR)
    expect(field).to_have_count(1)
    return field


def fill_form_field(dialog, label: str, value: str):
    control = form_field(dialog, label).locator(
        "input:not([readonly]):not([disabled])"
    )
    expect(control).to_have_count(1)
    control.fill(value)
    expect(control).to_have_value(value)
```

## 远程下拉控件

本项目的表单 select 控件均按远程搜索处理。

初始 input 可能 readonly。先点击标签范围内的控件，等待其变为可编辑，填入有意义的搜索词，再只在当前可见下拉层中选择返回项。控件未变为可编辑前，不得调用 `fill()`。

控件没有变为可编辑，或可见远程弹层没有出现时，应视为 UI 契约或定位问题并调查；不得绕过该过程。

### 动态远程候选项

字段有可选关键字时，优先选精确匹配项。关键字不存在或已不在返回结果中时，仅当测试允许任意当前有效关联记录时，才选择活跃下拉层中的第一个可用项。

```python
def select_first_available_remote_field_option(
    dialog, page, label: str, keyword: str | None = None
):
    control = form_field(dialog, label).locator("input:not([disabled])")
    expect(control).to_have_count(1)
    control.click()
    expect(control).to_be_editable()

    option = None
    if keyword is not None:
        control.fill(keyword)
        preferred = current_dropdown(page).get_by_role("listitem").filter(
            has_text=re.compile(rf"^\s*{re.escape(keyword)}\s*$")
        ).first
        try:
            preferred.wait_for(state="visible", timeout=2_000)
            option = preferred
        except PlaywrightTimeoutError:
            control.fill("")  # 恢复未筛选的候选列表

    if option is None:
        option = current_dropdown(page).locator(
            ".hm-select-dropdown__item:not(.is-disabled)"
        ).first

    expect(option).to_be_visible()
    option.click()
    expect(page.locator(".hm-select-dropdown:visible")).to_have_count(0)
    expect(control).not_to_have_value("")
```

精确关键字匹配失败后，选择兜底项前先清空远程输入框；否则菜单可能仍被筛选为空。不得因为早期录制曾可用，就保留过期的序列号、资产标识或人员名称。对于必需业务记录，传入关键字并走精确匹配；不可用时，除非用户明确允许任意有效关联，否则报告缺少所需记录。

## 代码注释

对不直观的定位器、弹层和兜底逻辑写简洁中文注释或 docstring。不要注释显而易见的赋值，也不要翻译 Python 或 Playwright 标识符。

### Unicode 转义注释

为兼容 Windows 源码环境，表单标签、远程下拉关键字和测试值中的中文可使用 `\uXXXX` 形式。这是 Python Unicode 转义，不是 UTF-8 字节编码。

任何含 `\uXXXX` 的代码行，包括模块常量、可执行语句、按钮名称、文本过滤条件和菜单项 locator，都必须在行尾添加简短中文注释，完整还原该行的中文含义。一行有多个转义值时，可用一条行尾注释说明所有值；不得以变量名、相邻说明或模块常量为由省略注释。

```python
FIELD_LABEL = "\u7ef4\u4fdd\u91d1\u989d"  # 维保金额
fill_form_field(page, "\u7ef4\u4fdd\u91d1\u989d", "1000")  # 维保金额
select_first_available_remote_field_option(
    page, "\u7ba1\u7406\u5458A", "\u90ed\u948a"
)  # 管理员A；关键字：郭钊
page.get_by_role("button").filter(has_text="\u5355\u53f0\u6dfb\u52a0").click()  # 单台添加
```

## 修复清单

1. 检查已打开页面的真实 DOM，并根据证据定义弹窗、标签和字段祖先选择器。
2. 用标签范围内的帮助函数替换“重复 placeholder + nth”定位。
3. 用经过验证的字段容器和可见弹层替换动态 ID 与全局文本定位。
4. 仅在没有稳定语义时保留 `nth()`；每次使用前立即重新查询。
5. 继续下一步前确认字段值已选中，或确认弹层已关闭。
6. 可选远程字段没有已知有效业务值时，保持为空并向用户询问，不得杜撰值。
7. 动态远程候选项优先精确匹配；缺失或不可用时，仅当允许任意有效关联时，才使用第一个可用候选项。

## 注释交付检查

交付前复读本次修改的函数与调用点：

1. 所有新增或修改的非直观定位器、弹窗层级、DOM 状态断言与兜底分支，都使用简洁中文注释或 docstring 说明“为何这样定位/断言”。
2. 不要为明显的赋值、点击或 Playwright 语法逐行翻译；保留英文标识符、CSS 类名和 API 名称。
3. 若代码因 Windows 兼容性使用 `\uXXXX`，该行末尾必须有能还原含义的中文注释；直接写中文字符串时，无需重复翻译字符串本身。
4. 修改后用 `rg -n '(^\s*#|"""|\x27\x27\x27)' <脚本>` 复核新增说明是否覆盖关键逻辑，并确认没有以注释掩盖未验证的 DOM 假设。

## 状态触发重渲染

勾选复选框、切换开关或选择选项后，若其所属分区会整体重渲染：

1. 不要从交互前的控件 locator 继续用 `xpath=ancestor::...` 查找后续控件。
2. 从当前可见弹窗或表单根节点重新按已验证的分区文本、标签或状态类查询目标分区。
3. 对新控件使用 `wait_for(state="visible")` 等待可交互状态，再执行点击或填写；不要以动态 locator 的计数作为重渲染完成标志。
