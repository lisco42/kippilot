import pyray as rl
from openpilot.selfdrive.ui import UI_BORDER_SIZE
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.widgets import Widget

KITTEN_LINES = (
  " /\\_/\\",
  "=( o.o )=",
  " )   (   //",
  "(__ __)//",
)

FONT_SIZE = 32
LINE_SPACING = 4


class KittenRenderer(Widget):
  def __init__(self):
    super().__init__()
    self._color = rl.Color(0, 0, 0, 180)
    self.set_visible(lambda: ui_state.started)

  def _render(self, rect):
    line_h = FONT_SIZE + LINE_SPACING
    x = int(rect.x + UI_BORDER_SIZE + 16)
    y = int(rect.y + rect.height - line_h * len(KITTEN_LINES) - UI_BORDER_SIZE - 16)
    for i, line in enumerate(KITTEN_LINES):
      rl.draw_text(line, x, y + i * line_h, FONT_SIZE, self._color)
