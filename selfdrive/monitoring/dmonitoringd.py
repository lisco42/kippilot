#!/usr/bin/env python3
import cereal.messaging as messaging
from openpilot.common.params import Params
from openpilot.common.realtime import Ratekeeper, config_realtime_process


def dmonitoringd_thread():
  config_realtime_process([0, 1, 2, 3], 5)

  params = Params()
  pm = messaging.PubMaster(['driverMonitoringState'])
  rk = Ratekeeper(20, print_delay_threshold=None)

  is_rhd = params.get_bool("IsRhdDetected")

  while True:
    dat = messaging.new_message('driverMonitoringState', valid=True)
    dat.driverMonitoringState = {
      "events": [],
      "faceDetected": True,
      "isDistracted": False,
      "distractedType": 0,
      "awarenessStatus": 1.0,
      "posePitchOffset": 0.0,
      "posePitchValidCount": 0,
      "poseYawOffset": 0.0,
      "poseYawValidCount": 0,
      "stepChange": 0.0,
      "awarenessActive": 1.0,
      "awarenessPassive": 1.0,
      "isLowStd": True,
      "hiStdCount": 0,
      "isActiveMode": True,
      "isRHD": is_rhd,
      "uncertainCount": 0,
    }
    pm.send('driverMonitoringState', dat)

    if rk.frame % 100 == 0:
      is_rhd = params.get_bool("IsRhdDetected")

    rk.keep_time()


def main():
  dmonitoringd_thread()


if __name__ == '__main__':
  main()
