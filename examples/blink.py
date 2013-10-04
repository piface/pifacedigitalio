from time import sleep
import pifacedigitalio


DELAY = 1.0  # seconds


if __name__ == "__main__":
    pifacedigital = pifacedigitalio.PiFaceDigital()
    while True:
        pifacedigital.leds[7].toggle()
        sleep(DELAY)
