import pifacecommon
import pifacedigitalio


pifacedigital = None


def switch_pressed(flag, input_byte):
    # led_number = pifacecommon.get_bit_num(flag)
    # global pifacedigital
    # pifacedigital.leds[led_number].turn_on()
    pifacedigital.output_port.value = input_byte ^ 0xFF
    return True


def switch_unpressed(flag, input_byte):
    # led_number = pifacecommon.get_bit_num(flag)
    # global pifacedigital
    # pifacedigital.leds[led_number].turn_off()
    pifacedigital.output_port.value = input_byte ^ 0xFF
    return True


if __name__ == "__main__":
    pifacedigitalio.init()
    pifacedigital = pifacedigitalio.PiFaceDigital()

    ifm = pifacecommon.InputFunctionMap()
    for i in range(4):
        ifm.register(i, pifacecommon.IN_EVENT_DIR_ON, switch_pressed)
        ifm.register(i, pifacecommon.IN_EVENT_DIR_OFF, switch_unpressed)

    pifacedigitalio.wait_for_input(ifm)
