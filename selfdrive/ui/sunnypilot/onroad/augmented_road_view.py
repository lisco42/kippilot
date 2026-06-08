"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import pyray as rl
from openpilot.common.swaglog import cloudlog
from openpilot.selfdrive.ui.ui_state import UIStatus, ui_state

BORDER_COLORS_SP = {
  UIStatus.LAT_ONLY: rl.Color(0x00, 0xC8, 0xC8, 0xFF),  # Cyan for lateral-only state
  UIStatus.LONG_ONLY: rl.Color(0x96, 0x1C, 0xA8, 0xFF),  # Purple for longitudinal-only state
}


class AugmentedRoadViewSP:
  def __init__(self):
    # kp: confidence indicator on the standard (3X) onroad UI. Rather than a moving left-edge
    # dot, it colors the steering-arc center dot by the model's confidence (see confidence_ball).
    # Lazy import to avoid a circular import (confidence_ball -> mici ConfidenceBallSP
    # -> onroad.augmented_road_view.BORDER_COLORS, which is still importing this module).
    from openpilot.selfdrive.ui.sunnypilot.onroad.confidence_ball import ConfidenceBallRendererSP
    self._confidence_ball = ConfidenceBallRendererSP()
    self._confidence_ball_failed = False

  def render_confidence_ball(self, _content_rect):
    # kp: shows the model's lat/long override confidence as the COLOR of the steering-arc
    # center dot. Defensive: this is a cosmetic widget and must never crash-loop the onroad
    # UI on the car. On the first failure, log to swaglog (so the cause is still captured)
    # and disable it for the rest of the session rather than taking the whole UI down.
    if self._confidence_ball_failed:
      return
    try:
      # anchor on the steering-arc vertex the TorqueBar published this frame; only feed a
      # position when the arc is actually being drawn (Steering Arc toggle on)
      torque_bar = self._hud_renderer._torque_bar
      self._confidence_ball.center_pos = torque_bar.center_dot_pos if ui_state.torque_bar else None
      self._confidence_ball.center_radius = torque_bar.center_dot_radius
      self._confidence_ball.center_alpha = torque_bar.center_dot_alpha
      self._confidence_ball.render(_content_rect)
    except Exception:
      cloudlog.exception("confidence ball render failed; disabling for this session")
      self._confidence_ball_failed = True
