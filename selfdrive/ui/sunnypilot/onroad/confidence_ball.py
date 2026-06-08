"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.

kp: confidence indicator for the standard (3X) onroad UI. Instead of a dot that
slides up/down the left edge (distracting), the driving model's steering/brake
override confidence (1 - max disengage prob) is shown as the COLOR of the
steering-arc center dot: green = high, yellow = medium, red = low. The dot is
anchored on the arc vertex published by TorqueBar each frame and stays put while
lateral control is active. Gated by the "Steering Arc Confidence" visuals toggle
(SteeringArcConfidence param).
"""
import math
import pyray as rl

from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.selfdrive.ui.ui_state import ui_state, UIStatus
from openpilot.selfdrive.ui.sunnypilot.mici.onroad.confidence_ball import ConfidenceBallSP
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.widgets import Widget

FALLBACK_DOT_RADIUS = 15.0  # used until TorqueBar has published its center-dot geometry


def _draw_circle_gradient(center_x: float, center_y: float, radius: float,
                          top: rl.Color, bottom: rl.Color, alpha: float = 1.0) -> None:
  # filled square gradient, then paint over the corners with a black ring to make a circle
  a = max(0.0, min(1.0, alpha))
  top = rl.Color(top.r, top.g, top.b, int(top.a * a))
  bottom = rl.Color(bottom.r, bottom.g, bottom.b, int(bottom.a * a))
  radius = int(radius)
  rl.draw_rectangle_gradient_v(int(center_x - radius), int(center_y - radius),
                               radius * 2, radius * 2, top, bottom)
  outer_radius = math.ceil(radius * math.sqrt(2)) + 1
  rl.draw_ring(rl.Vector2(int(center_x), int(center_y)), radius, outer_radius,
               0.0, 360.0, 20, rl.Color(0, 0, 0, int(255 * a)))


class ConfidenceBallRendererSP(Widget, ConfidenceBallSP):
  def __init__(self):
    Widget.__init__(self)
    ConfidenceBallSP.__init__(self)
    self._confidence_filter = FirstOrderFilter(-0.5, 0.5, 1 / gui_app.target_fps)
    # published by AugmentedRoadViewSP.render_confidence_ball from the TorqueBar each frame
    self.center_pos: tuple[float, float] | None = None
    self.center_radius: float = FALLBACK_DOT_RADIUS
    self.center_alpha: float = 0.0

  def _update_state(self):
    sm = ui_state.sm
    # Don't read model state until we're onroad with a freshly-received, valid modelV2.
    # Matches the guard ModelRenderer uses (recv_frame >= started_frame) so we never touch
    # stale/empty model data on the offroad->onroad transition.
    model_ready = (ui_state.started and sm.valid['modelV2'] and
                   sm.recv_frame['modelV2'] >= ui_state.started_frame)
    if not model_ready or ui_state.status == UIStatus.DISENGAGED:
      self._confidence_filter.update(-0.5)
    elif ui_state.status in (UIStatus.LAT_ONLY, UIStatus.LONG_ONLY):
      self._confidence_filter.update(1 - max(self.get_animate_status_probs() or [1]))
    else:
      meta = sm['modelV2'].meta
      self._confidence_filter.update((1 - max(meta.disengagePredictions.brakeDisengageProbs or [1])) *
                                     (1 - max(meta.disengagePredictions.steerOverrideProbs or [1])))

  def _render(self, _):
    # toggle off, or openpilot isn't doing anything -> nothing to show
    if not ui_state.steering_arc_confidence or ui_state.status == UIStatus.DISENGAGED:
      return

    # anchor on the steering-arc center dot; skip if the arc hasn't rendered / has faded out
    if self.center_pos is None or self.center_alpha < 5e-2:
      return

    cx, cy = self.center_pos
    radius = self.center_radius or FALLBACK_DOT_RADIUS

    # kp: color by confidence in ALL active modes (lat-only/long-only/engaged) -- green >
    # yellow > red as confidence drops. The screen border still carries the MADS state
    # color, so the dot is free to be a pure confidence meter here.
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

    _draw_circle_gradient(cx, cy, radius, top_dot_color, bottom_dot_color, alpha=self.center_alpha)
