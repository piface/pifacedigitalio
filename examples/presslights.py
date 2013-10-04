import pifacedigitalio


def switch_pressed(event):
    event.chip.output_pins[event.pin_num].turn_on()


def switch_unpressed(event):
    event.chip.output_pins[event.pin_num].turn_off()


if __name__ == "__main__":
    pifacedigital = pifacedigitalio.PiFaceDigital()

    listener = pifacedigitalio.InputEventListener(chip=pifacedigital)
    for i in range(4):
        listener.register(i, pifacedigitalio.IODIR_ON, switch_pressed)
        listener.register(i, pifacedigitalio.IODIR_OFF, switch_unpressed)
    listener.activate()
