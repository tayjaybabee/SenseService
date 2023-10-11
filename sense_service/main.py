from __future__ import annotations

from atexit import register

from sense_service import SenseHatMQTT
from sense_service.sensors import SensorDataSmoother

if __name__ == "__main__":
    smoother = SensorDataSmoother('moving_average', window_size=25)
    sense_mqtt = SenseHatMQTT("ds9.local", data_smoother=smoother, high_res_interval=.5, temp_source='pressure')
    register(sense_mqtt.stop)
    sense_mqtt.run(display=True)
