"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import pyray as rl
from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.common.swaglog import cloudlog
from openpilot.selfdrive.ui.ui_state import UIStatus, ui_state
from openpilot.system.ui.lib.application import gui_app

BORDER_COLORS_SP = {
  UIStatus.LAT_ONLY: rl.Color(0x00, 0xC8, 0xC8, 0xFF),  # Cyan for lateral-only state
  UIStatus.LONG_ONLY: rl.Color(0x96, 0x1C, 0xA8, 0xFF),  # Purple for longitudinal-only state
}


class AugmentedRoadViewSP:
  def __init__(self):
    self._fade_texture = gui_app.texture("icons_mici/onroad/onroad_fade.png")
    self._fade_alpha_filter = FirstOrderFilter(0, 0.1, 1 / gui_app.target_fps)
    # kp: confidence ball on the left edge of the standard (3X) onroad UI.
    # Lazy import to avoid a circular import (confidence_ball -> mici ConfidenceBallSP
    # -> onroad.augmented_road_view.BORDER_COLORS, which is still importing this module).
    from openpilot.selfdrive.ui.sunnypilot.onroad.confidence_ball import ConfidenceBallRendererSP
    self._confidence_ball = ConfidenceBallRendererSP()
    self._confidence_ball_failed = False

  def render_confidence_ball(self, _content_rect):
    # kp: ported from the mici UI; shows the model's lat/long override confidence.
    # Defensive: this is a cosmetic widget and must never crash-loop the onroad UI on the
    # car. On the first failure, log to swaglog (so the cause is still captured) and disable
    # it for the rest of the session rather than taking the whole UI process down.
    if self._confidence_ball_failed:
      return
    try:
      self._confidence_ball.render(_content_rect)
    except Exception:
      cloudlog.exception("confidence ball render failed; disabling for this session")
      self._confidence_ball_failed = True

  def update_fade_out_bottom_overlay(self, _content_rect):
    # Fade out bottom of overlays for looks (only when engaged)
    fade_alpha = self._fade_alpha_filter.update(ui_state.status != UIStatus.DISENGAGED)
    if ui_state.torque_bar and fade_alpha > 1e-2:
      # Scale the fade texture to the content rect
      rl.draw_texture_pro(self._fade_texture,
                          rl.Rectangle(0, 0, self._fade_texture.width, self._fade_texture.height),
                          _content_rect, rl.Vector2(0, 0), 0.0,
                          rl.Color(255, 255, 255, int(255 * fade_alpha)))
