import pifacecommon
import pifacedigitalio


def switch_pressed(event):
    global pifacedigital
    pifacedigital.output_pins[event.pin_num].turn_on()


def switch_unpressed(event):
    global pifacedigital
    pifacedigital.output_pins[event.pin_num].turn_off()


if __name__ == "__main__":
    pifacedigitalio.init()

    global pifacedigital
    pifacedigital = pifacedigitalio.PiFaceDigital()

    listener = pifacedigitalio.InputEventListener()
    for i in range(4):
        listener.register(i, pifacedigitalio.IODIR_ON, switch_pressed)
        listener.register(i, pifacedigitalio.IODIR_OFF, switch_unpressed)
    listener.activate()
