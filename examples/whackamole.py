import threading
from time import sleep
from random import randint, random
import pifacecommon
import pifacedigitalio


NUM_MOLES = 4  # max 4


class Mole(object):
    def __init__(self, number, pifacedigital):
        led_start_index = number * 2
        self.leds = (
            pifacedigital.leds[::-1][led_start_index],
            pifacedigital.leds[::-1][led_start_index+1]
        )
        self.hiding = True

    @property
    def hiding(self):
        return self._is_hiding

    @hiding.setter
    def hiding(self, should_hide):
        if should_hide:
            self.hide()
        else:
            self.show()

    def hide(self):
        for led in self.leds:
            led.turn_off()
        self._is_hiding = True

    def show(self):
        for led in self.leds:
            led.turn_on()
        self._is_hiding = False

    def hit(self):
        """Attempt to hit a mole, return success."""
        if self.hiding:
            return False
        else:
            self.hide()
            return True


class WhackAMoleGame(threading.Thread):
    def __init__(self):
        self.should_stop = False
        self.moles = [Mole(i, pfd) for i in range(NUM_MOLES)]
        self._current_points = 0
        self.max_points = 0
        super().__init__()

    def run(self):
        while not self.should_stop:
            # randomly moves moles up and down
            for mole in self.moles:
                should_hide = (randint(0, 1) == 1)
                mole.hiding = should_hide

            #sleep(random() * 3)
            sleep(1)

    @property
    def points(self):
        return self._current_points

    @points.setter
    def points(self, new_value):
        if self.max_points > 1 and new_value <= 1:
            self.should_stop = True  # end the game
            return

        self.max_points = max(self.max_points, new_value)
        self._current_points = new_value


class InputWatcher(threading.Thread):
    def __init__(self, game):
        self.should_stop = False

        def hit_mole(flag, byte):
            if self.should_stop:
                return False

            bit_num = pifacecommon.get_bit_num(flag)
            print("You pressed", bit_num)

            if game.moles[bit_num].hit():
                game.points += 1
                print("You hit a mole!")
            else:
                game.points -= 1
                print("You missed!")

            return True

        self.ifm = pifacecommon.InputFunctionMap()
        for i in range(4):
            self.ifm.register(i, pifacecommon.IN_EVENT_DIR_ON, hit_mole)

        super().__init__()

    def run(self):
        pifacedigitalio.wait_for_input(self.ifm)


if __name__ == "__main__":
    pifacedigitalio.init()
    pfd = pifacedigitalio.PiFaceDigital()
    game = WhackAMoleGame()
    game.start()
    input_watcher = InputWatcher(game)
    input_watcher.start()
    game.join()
    pfd.output_port.all_on()
    for i in range(10):
        pfd.output_port.toggle()
        sleep(0.1)
    print("You scored {}!".format(game.max_points))
    print("press any button to finnish")
    input_watcher.should_stop = True
    input_watcher.join()
    pfd.output_port.all_off()
    pifacedigitalio.deinit()
