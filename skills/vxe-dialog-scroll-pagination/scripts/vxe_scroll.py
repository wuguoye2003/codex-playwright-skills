from __future__ import annotations

from playwright.sync_api import Locator, Page, expect


def scroll_vxe_scrollbar(
    page: Page,
    handle: Locator,
    *,
    horizontal: bool,
    to_end: bool,
    steps: int = 4,
    duration_seconds: float = 3,
) -> None:
    """Scroll one VXE handle to an exact end point in timed steps."""
    if steps < 1:
        raise ValueError("steps must be at least 1")

    expect(handle).to_have_count(1)
    axis = "scrollLeft" if horizontal else "scrollTop"
    dimension = "scrollWidth" if horizontal else "scrollHeight"
    viewport = "clientWidth" if horizontal else "clientHeight"
    maximum = handle.evaluate(
        f"element => element.{dimension} - element.{viewport}"
    )
    if maximum <= 0:
        return

    start = handle.evaluate(f"element => element.{axis}")
    target = maximum if to_end else 0
    for step in range(1, steps + 1):
        position = start + (target - start) * step / steps
        handle.evaluate(
            f"""(element, value) => {{
                element.{axis} = value;
                element.dispatchEvent(new Event('scroll', {{bubbles: true}}));
            }}""",
            position,
        )
        page.wait_for_timeout(duration_seconds * 1_000 / steps)

    actual = handle.evaluate(f"element => element.{axis}")
    if abs(actual - target) > 1:
        raise RuntimeError("VXE scrollbar did not reach the requested edge")


def scroll_table_once_in_each_direction(
    page: Page,
    table: Locator,
    *,
    steps: int = 4,
    duration_seconds: float = 3,
) -> None:
    """Scroll a VXE table down, right, up, and left once."""
    expect(table).to_have_count(1)
    vertical = table.locator(".vxe-table--scroll-y-handle")
    horizontal = table.locator(".vxe-table--scroll-x-handle")

    scroll_vxe_scrollbar(page, vertical, horizontal=False, to_end=True, steps=steps, duration_seconds=duration_seconds)
    scroll_vxe_scrollbar(page, horizontal, horizontal=True, to_end=True, steps=steps, duration_seconds=duration_seconds)
    scroll_vxe_scrollbar(page, vertical, horizontal=False, to_end=False, steps=steps, duration_seconds=duration_seconds)
    scroll_vxe_scrollbar(page, horizontal, horizontal=True, to_end=False, steps=steps, duration_seconds=duration_seconds)
