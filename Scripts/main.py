from sense_service import SenseHatMQTT
from sense_service.sensors import SensorDataSmoother
from sense_service.arguments import PARSED


def main():

    smoother = SensorDataSmoother(PARSED.smoothing_algorithm, window_size=25)
    sense = SenseHatMQTT(
        PARSED.broker_address, PARSED.broker_port, PARSED.topic,
        data_smoother=smoother,
        high_res_interval=PARSED.high_res_interval,
        temp_source=PARSED.temp_source
    )
    sense.run()


if __name__ == '__main__':
    main()

