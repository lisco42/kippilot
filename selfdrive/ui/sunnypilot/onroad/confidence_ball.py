"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.

kp: left-side port of the mici confidence ball for the standard (3X) onroad UI.
The dot slides vertically with the driving model's steering/brake-override
confidence (1 - max disengage prob). Placed in a middle band on the far-left edge
so it clears the top-left MAX set-speed box and the bottom-left kitten.
"""
import math
import pyray as rl

from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.selfdrive.ui import UI_BORDER_SIZE
from openpilot.selfdrive.ui.ui_state import ui_state, UIStatus
from openpilot.selfdrive.ui.sunnypilot.mici.onroad.confidence_ball import ConfidenceBallSP
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.widgets import Widget

STATUS_DOT_RADIUS = 24
TOP_CLEARANCE = 270     # clear the top-left MAX set-speed box (≈ border + set_speed_height)
BOTTOM_CLEARANCE = 240  # clear the bottom-left kitten


def _draw_circle_gradient(center_x: float, center_y: float, radius: int,
                          top: rl.Color, bottom: rl.Color) -> None:
  # filled square gradient, then paint over the corners with a black ring to make a circle
  rl.draw_rectangle_gradient_v(int(center_x - radius), int(center_y - radius),
                               radius * 2, radius * 2, top, bottom)
  outer_radius = math.ceil(radius * math.sqrt(2)) + 1
  rl.draw_ring(rl.Vector2(int(center_x), int(center_y)), radius, outer_radius,
               0.0, 360.0, 20, rl.BLACK)


class ConfidenceBallRendererSP(Widget, ConfidenceBallSP):
  def __init__(self):
    Widget.__init__(self)
    ConfidenceBallSP.__init__(self)
    self._confidence_filter = FirstOrderFilter(-0.5, 0.5, 1 / gui_app.target_fps)

  def _update_state(self):
    if ui_state.status == UIStatus.DISENGAGED:
      self._confidence_filter.update(-0.5)
    elif ui_state.status in (UIStatus.LAT_ONLY, UIStatus.LONG_ONLY):
      self._confidence_filter.update(1 - max(self.get_animate_status_probs() or [1]))
    else:
      self._confidence_filter.update((1 - max(ui_state.sm['modelV2'].meta.disengagePredictions.brakeDisengageProbs or [1])) *
                                     (1 - max(ui_state.sm['modelV2'].meta.disengagePredictions.steerOverrideProbs or [1])))

  def _render(self, _):
    # only show the dot when openpilot is actually doing something
    if ui_state.status == UIStatus.DISENGAGED:
      return

    rect = self._rect
    radius = STATUS_DOT_RADIUS

    # far-left column; vertical travel confined to a middle band (clears MAX box + kitten)
    cx = rect.x + UI_BORDER_SIZE + radius
    top = rect.y + TOP_CLEARANCE
    bottom = rect.y + rect.height - BOTTOM_CLEARANCE
    travel = max(bottom - top, 0.0)
    # high confidence -> top, low confidence -> bottom; clamp so it never leaves the band
    cy = top + max(0.0, min(1.0, 1 - self._confidence_filter.x)) * travel

    # kp: color by confidence in ALL active modes (lat-only/long-only/engaged), not just
    # engaged — green > yellow > red as confidence drops. The screen border still carries
    # the MADS state color, so the ball is free to be a pure confidence meter here.
    if ui_state.status in (UIStatus.ENGAGED, UIStatus.LAT_ONLY, UIStatus.LONG_ONLY):
      if self._confidence_filter.x > 0.5:
        top_dot_color = rl.Color(0, 255, 204, 255)
        bottom_dot_color = rl.Color(0, 255, 38, 255)
      elif self._confidence_filter.x > 0.2:
        top_dot_color = rl.Color(255, 200, 0, 255)
        bottom_dot_color = rl.Color(255, 115, 0, 255)
      else:
        top_dot_color = rl.Color(255, 0, 21, 255)
        bottom_dot_color = rl.Color(255, 0, 89, 255)
    elif ui_state.status == UIStatus.OVERRIDE:
      top_dot_color = rl.Color(255, 255, 255, 255)
      bottom_dot_color = rl.Color(82, 82, 82, 255)
    else:
      top_dot_color = rl.Color(50, 50, 50, 255)
      bottom_dot_color = rl.Color(13, 13, 13, 255)

    _draw_circle_gradient(cx, cy, radius, top_dot_color, bottom_dot_color)
