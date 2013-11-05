import pifacecommon.mcp23s17
import pifacecommon.interrupts

# /dev/spidev<bus>.<chipselect>
DEFAULT_SPI_BUS = 0
DEFAULT_SPI_CHIP_SELECT = 0

MAX_BOARDS = 4
# list of PiFace Digitals for digital_read/digital_write
_pifacedigitals = [None] * MAX_BOARDS


class NoPiFaceDigitalDetectedError(Exception):
    pass


class NoPiFaceDigitalError(Exception):
    pass


class PiFaceDigital(pifacecommon.mcp23s17.MCP23S17,
                    pifacecommon.interrupts.GPIOInterruptDevice):
    """A PiFace Digital board.

    :attribute: input_pins -- list containing
        :class:`pifacecommon.mcp23s17.MCP23S17RegisterBitNeg`.
    :attribute: input_port -- See
        :class:`pifacecommon.mcp23s17.MCP23S17RegisterNeg`.
    :attribute: output_pins -- list containing
        :class:`pifacecommon.mcp23s17.MCP23S17RegisterBit`.
    :attribute: output_port -- See
        :class:`pifacecommon.mcp23s17.MCP23S17Register`.
    :attribute: leds --
        list containing :class:`pifacecommon.mcp23s17.MCP23S17RegisterBit`.
    :attribute: relays --
        list containing :class:`pifacecommon.mcp23s17.MCP23S17RegisterBit`.
    :attribute: switches --
        list containing :class:`pifacecommon.mcp23s17.MCP23S17RegisterBit`.

    Example:

    >>> pfd = pifacedigitalio.PiFaceDigital()
    >>> pfd.input_port.value
    0
    >>> pfd.output_port.value = 0xAA
    >>> pfd.leds[5].turn_on()
    """
    def __init__(self,
                 hardware_addr=0,
                 bus=DEFAULT_SPI_BUS,
                 chip_select=DEFAULT_SPI_CHIP_SELECT,
                 init_board=True):
        super(PiFaceDigital, self).__init__(hardware_addr, bus, chip_select)

        self.input_pins = [pifacecommon.mcp23s17.MCP23S17RegisterBitNeg(
            i, pifacecommon.mcp23s17.GPIOB, self)
            for i in range(8)]

        self.input_port = pifacecommon.mcp23s17.MCP23S17RegisterNeg(
            pifacecommon.mcp23s17.GPIOB, self)

        self.output_pins = [pifacecommon.mcp23s17.MCP23S17RegisterBit(
            i, pifacecommon.mcp23s17.GPIOA, self)
            for i in range(8)]

        self.output_port = pifacecommon.mcp23s17.MCP23S17Register(
            pifacecommon.mcp23s17.GPIOA, self)

        self.leds = [pifacecommon.mcp23s17.MCP23S17RegisterBit(
            i, pifacecommon.mcp23s17.GPIOA, self)
            for i in range(8)]

        self.relays = [pifacecommon.mcp23s17.MCP23S17RegisterBit(
            i, pifacecommon.mcp23s17.GPIOA, self)
            for i in range(2)]

        self.switches = [pifacecommon.mcp23s17.MCP23S17RegisterBitNeg(
            i, pifacecommon.mcp23s17.GPIOB, self)
            for i in range(4)]

        if init_board:
            self.init_board()

    def enable_interrupts(self):
        self.gpintenb.value = 0xFF  # enable interrupts
        self.gpio_interrupts_enable()

    def disable_interrupts(self):
        self.gpintenb.value = 0x00
        self.gpio_interrupts_disable()

    def init_board(self):
        ioconfig = (
            pifacecommon.mcp23s17.BANK_OFF |
            pifacecommon.mcp23s17.INT_MIRROR_OFF |
            pifacecommon.mcp23s17.SEQOP_OFF |
            pifacecommon.mcp23s17.DISSLW_OFF |
            pifacecommon.mcp23s17.HAEN_ON |
            pifacecommon.mcp23s17.ODR_OFF |
            pifacecommon.mcp23s17.INTPOL_LOW
        )
        self.iocon.value = ioconfig
        if self.iocon.value != ioconfig:
            raise NoPiFaceDigitalDetectedError(
                "No PiFace Digital board detected (hardware_addr={h}, "
                "bus={b}, chip_select={c}).".format(
                    h=self.hardware_addr, b=self.bus, c=self.chip_select))
        else:
            # finish configuring the board
            self.gpioa.value = 0
            self.iodira.value = 0  # GPIOA as outputs
            self.iodirb.value = 0xFF  # GPIOB as inputs
            self.gppub.value = 0xFF  # input pullups on
            self.enable_interrupts()

    def deinit_board(self):
        if self.gpintenb.value != 0x00:  # probably should be a function
            self.disable_interrupts()
        self.close_fd()


class InputEventListener(pifacecommon.interrupts.PortEventListener):
    """Listens for events on the input port and calls the mapped callback
    functions.

    >>> def print_flag(event):
    ...     print(event.interrupt_flag)
    ...
    >>> listener = pifacedigitalio.InputEventListener()
    >>> listener.register(0, pifacedigitalio.IODIR_ON, print_flag)
    >>> listener.activate()
    """
    def __init__(self, chip=None):
        if chip is None:
            chip = PiFaceDigital()
        super(InputEventListener, self).__init__(
            pifacecommon.mcp23s17.GPIOB, chip)


def init(init_board=True,
         bus=DEFAULT_SPI_BUS,
         chip_select=DEFAULT_SPI_CHIP_SELECT):
    """Initialises all PiFace Digital boards. Only required when using
    :func:`digital_read` and :func:`digital_write`.

    :param init_board: Initialise each board (default: True)
    :type init_board: boolean
    :param bus: SPI bus /dev/spidev<bus>.<chipselect> (default: {bus})
    :type bus: int
    :param chip_select: SPI chip select /dev/spidev<bus>.<chipselect>
        (default: {chip})
    :type chip_select: int
    :raises: :class:`NoPiFaceDigitalDetectedError`
    """.format(bus=DEFAULT_SPI_BUS, chip=DEFAULT_SPI_CHIP_SELECT)
    failed_boards = list()
    for hardware_addr in range(MAX_BOARDS):
        try:
            global _pifacedigitals
            _pifacedigitals[hardware_addr] = PiFaceDigital(hardware_addr,
                                                           bus,
                                                           chip_select,
                                                           init_board)
        except NoPiFaceDigitalDetectedError as e:
            failed_boards.append(e)
    if len(failed_boards) >= MAX_BOARDS:
        raise failed_boards[0]


def deinit(bus=DEFAULT_SPI_BUS,
           chip_select=DEFAULT_SPI_CHIP_SELECT):
    """Stops interrupts on all boards. Only required when using
    :func:`digital_read` and :func:`digital_write`.

    :param bus: SPI bus /dev/spidev<bus>.<chipselect> (default: {bus})
    :type bus: int
    :param chip_select: SPI chip select /dev/spidev<bus>.<chipselect>
        (default: {chip})
    :type chip_select: int
    """
    global _pifacedigitals
    for pfd in _pifacedigitals:
        try:
            pfd.deinit_board()
        except AttributeError:
            pass


# wrapper functions for backwards compatibility
def digital_read(pin_num, hardware_addr=0):
    """Returns the value of the input pin specified.

    .. note:: This function is for familiarality with users of other types of
       IO board. Consider accessing the ``input_pins`` attribute of a
       PiFaceDigital object:

       >>> pfd = PiFaceDigital(hardware_addr)
       >>> pfd.input_pins[pin_num].value
       0

    :param pin_num: The pin number to read.
    :type pin_num: int
    :param hardware_addr: The board to read from (default: 0)
    :type hardware_addr: int
    :returns: int -- value of the pin
    """
    return _get_pifacedigital(hardware_addr).input_pins[pin_num].value


def digital_write(pin_num, value, hardware_addr=0):
    """Writes the value to the input pin specified.

    .. note:: This function is for familiarality with users of other types of
       IO board. Consider accessing the ``output_pins`` attribute of a
       PiFaceDigital object:

       >>> pfd = PiFaceDigital(hardware_addr)
       >>> pfd.output_pins[pin_num].value = 1

    :param pin_num: The pin number to write to.
    :type pin_num: int
    :param value: The value to write.
    :type value: int
    :param hardware_addr: The board to read from (default: 0)
    :type hardware_addr: int
    """
    _get_pifacedigital(hardware_addr).output_pins[pin_num].value = value


def digital_read_pullup(pin_num, hardware_addr=0):
    """Returns the value of the input pullup specified.

    .. note:: This function is for familiarality with users of other types of
       IO board. Consider accessing the ``gppub`` attribute of a
       PiFaceDigital object:

       >>> pfd = PiFaceDigital(hardware_addr)
       >>> hex(pfd.gppub.value)
       0xff
       >>> pfd.gppub.bits[pin_num].value
       1

    :param pin_num: The pin number to read.
    :type pin_num: int
    :param hardware_addr: The board to read from (default: 0)
    :type hardware_addr: int
    :returns: int -- value of the pin
    """
    return _get_pifacedigital(hardware_addr).gppub.bits[pin_num].value


def digital_write_pullup(pin_num, value, hardware_addr=0):
    """Writes the value to the input pullup specified.

    .. note:: This function is for familiarality with users of other types of
       IO board. Consider accessing the ``gppub`` attribute of a
       PiFaceDigital object:

       >>> pfd = PiFaceDigital(hardware_addr)
       >>> hex(pfd.gppub.value)
       0xff
       >>> pfd.gppub.bits[pin_num].value = 1

    :param pin_num: The pin number to write to.
    :type pin_num: int
    :param value: The value to write.
    :type value: int
    :param hardware_addr: The board to read from (default: 0)
    :type hardware_addr: int
    """
    _get_pifacedigital(hardware_addr).gppub.bits[pin_num].value = value


def _get_pifacedigital(hardware_addr):
    global _pifacedigitals
    if _pifacedigitals[hardware_addr] is None:
        raise NoPiFaceDigitalError("There is no PiFace Digital with "
                                   "hardware_addr {}".format(hardware_addr))
    else:
        return _pifacedigitals[hardware_addr]
