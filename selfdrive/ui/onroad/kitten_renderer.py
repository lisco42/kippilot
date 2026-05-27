import pyray as rl
from openpilot.selfdrive.ui import UI_BORDER_SIZE
from openpilot.system.ui.lib.application import FontWeight, gui_app
from openpilot.system.ui.widgets import Widget

KITTEN_LINES = (
  "  /\\_/\\",
  "=( o.o )=",
  " )'   '( //",
  " (__ __)//",
)

FONT_SIZE = 32
LINE_SPACING = 4
SHADOW_OFFSET = 2


class KittenRenderer(Widget):
  def __init__(self, visible_when=None):
    super().__init__()
    self._font = gui_app.font(FontWeight.MONO)
    self._fg = rl.Color(255, 255, 255, 230)
    self._shadow = rl.Color(0, 0, 0, 200)
    if visible_when is not None:
      self.set_visible(visible_when)

  def _render(self, rect):
    line_h = FONT_SIZE + LINE_SPACING
    x = rect.x + UI_BORDER_SIZE + 16
    y = rect.y + rect.height - line_h * len(KITTEN_LINES) - UI_BORDER_SIZE - 16
    for i, line in enumerate(KITTEN_LINES):
      pos = rl.Vector2(x, y + i * line_h)
      rl.draw_text_ex(self._font, line, rl.Vector2(pos.x + SHADOW_OFFSET, pos.y + SHADOW_OFFSET), FONT_SIZE, 0, self._shadow)
      rl.draw_text_ex(self._font, line, pos, FONT_SIZE, 0, self._fg)
