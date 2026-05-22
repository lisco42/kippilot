#!/usr/bin/env python3
import cereal.messaging as messaging
from cereal import log
from openpilot.common.params import Params
from openpilot.common.realtime import Ratekeeper, config_realtime_process

AlertLevel = log.DriverMonitoringState.AlertLevel
MonitoringPolicy = log.DriverMonitoringState.MonitoringPolicy


def dmonitoringd_thread():
  # kippilot: driver monitoring is intentionally disabled (comma-3X-only fork).
  # Publish a constant "attentive / never-alert / never-lockout" driverMonitoringState
  # so DM can never block engagement (controlsd forceDecel gates on alertLevel==three)
  # or raise an alert/lockout (selfdrived gates on lockout/alwaysOnLockout/alertLevel).
  config_realtime_process([0, 1, 2, 3], 5)

  params = Params()
  pm = messaging.PubMaster(['driverMonitoringState'])
  rk = Ratekeeper(20, print_delay_threshold=None)

  is_rhd = params.get_bool("IsRhdDetected")

  while True:
    dat = messaging.new_message('driverMonitoringState', valid=True)
    dm = dat.driverMonitoringState
    dm.lockout = False
    dm.alwaysOn = False
    dm.alwaysOnLockout = False
    dm.alertLevel = AlertLevel.none
    dm.activePolicy = MonitoringPolicy.vision
    dm.isRHD = is_rhd
    dm.rhdCalibration.calibratedPercent = 100
    dm.visionPolicyState.awarenessPercent = 100
    dm.visionPolicyState.isDistracted = False
    dm.visionPolicyState.faceDetected = True
    dm.visionPolicyState.pose.calibrated = True
    dm.visionPolicyState.uncertainOffroadAlertPercent = 0
    dm.wheeltouchPolicyState.awarenessPercent = 100
    pm.send('driverMonitoringState', dat)

    if rk.frame % 100 == 0:
      is_rhd = params.get_bool("IsRhdDetected")

    rk.keep_time()


def main():
  dmonitoringd_thread()


if __name__ == '__main__':
  main()
