import logging
from typing import List
from gpiozero import OutputDevice, DigitalInputDevice
import time

from seedsigner.models.singleton import Singleton

logger = logging.getLogger(__name__)


# ============================================================
# NES controller wiring (BCM)
# ============================================================

DATA_PIN = 17
LATCH_PIN = 22
CLOCK_PIN = 27

latch = OutputDevice(LATCH_PIN)
clock = OutputDevice(CLOCK_PIN)
data = DigitalInputDevice(DATA_PIN, pull_up=True)


# ============================================================
# NES button reader
# ============================================================

def read_controller():
    states = []

    latch.on()
    time.sleep(0.00001)
    latch.off()

    for _ in range(8):
        states.append(data.value)

        clock.on()
        time.sleep(0.00001)

        clock.off()
        time.sleep(0.00001)

    return states


# Indexes returned by the NES controller
NES_A = 0
NES_B = 1
NES_SELECT = 2
NES_START = 3
NES_UP = 4
NES_DOWN = 5
NES_LEFT = 6
NES_RIGHT = 7


# ============================================================
# Button constants expected by SeedSigner
# ============================================================

class HardwareButtonsConstants:
    KEY_UP = 1
    KEY_DOWN = 2
    KEY_LEFT = 3
    KEY_RIGHT = 4

    KEY_PRESS = 5

    KEY1 = 6
    KEY2 = 7
    KEY3 = 8

    OVERRIDE = 1000

    ALL_KEYS = [
        KEY_UP,
        KEY_DOWN,
        KEY_LEFT,
        KEY_RIGHT,
        KEY_PRESS,
        KEY1,
        KEY2,
        KEY3,
    ]

    KEYS__LEFT_RIGHT_UP_DOWN = [
        KEY_LEFT,
        KEY_RIGHT,
        KEY_UP,
        KEY_DOWN,
    ]

    KEYS__ANYCLICK = [
        KEY_PRESS,
        KEY1,
        KEY2,
        KEY3,
    ]


class HardwareButtons(Singleton):

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)

            cls._instance.override_ind = False

            cls._instance.cur_input = None
            cls._instance.cur_input_started = None

            cls._instance.last_input_time = int(time.time() * 1000)

            cls._instance.first_repeat_threshold = 225
            cls._instance.next_repeat_threshold = 250

        return cls._instance

    def _get_pressed_keys(self):
        states = read_controller()

        pressed = []

        # NES -> SeedSigner mapping

        if states[NES_UP]:
            pressed.append(HardwareButtonsConstants.KEY_UP)

        if states[NES_DOWN]:
            pressed.append(HardwareButtonsConstants.KEY_DOWN)

        if states[NES_LEFT]:
            pressed.append(HardwareButtonsConstants.KEY_LEFT)

        if states[NES_RIGHT]:
            pressed.append(HardwareButtonsConstants.KEY_RIGHT)

        # Start = center/select
        if states[NES_START]:
            pressed.append(HardwareButtonsConstants.KEY_PRESS)

        # A, B, Select become KEY1, KEY2, KEY3
        if states[NES_A]:
            pressed.append(HardwareButtonsConstants.KEY1)

        if states[NES_B]:
            pressed.append(HardwareButtonsConstants.KEY2)

        if states[NES_SELECT]:
            pressed.append(HardwareButtonsConstants.KEY3)

        return pressed

    def wait_for(self, keys=[]) -> int:
        """
        Block execution until one of the target keys is pressed.

        Optionally override the wait by calling trigger_override().
        """

        from seedsigner.controller import Controller

        controller = Controller.get_instance()
        self.override_ind = False

        while True:

            if self.override_ind:
                self.override_ind = False
                return HardwareButtonsConstants.OVERRIDE

            cur_time = int(time.time() * 1000)

            if (
                cur_time - self.last_input_time >
                controller.screensaver_activation_ms
                and
                controller.is_screensaver_start_allowed
            ):

                controller.start_screensaver()

                self.update_last_input_time()

                time.sleep(
                    self.next_repeat_threshold / 1000.0
                )

                continue

            pressed = self._get_pressed_keys()

            for key in keys:

                if key in pressed:

                    if self.cur_input != key:

                        self.cur_input = key
                        self.cur_input_started = cur_time
                        self.last_input_time = cur_time

                        return key

                    else:

                        if (
                            cur_time - self.last_input_time >
                            self.next_repeat_threshold
                        ):

                            self.cur_input_started = cur_time
                            self.last_input_time = cur_time

                            return key

                        elif (
                            cur_time - self.cur_input_started >
                            self.first_repeat_threshold
                        ):

                            self.last_input_time = cur_time

                            return key

            time.sleep(0.01)

    def update_last_input_time(self):
        self.last_input_time = int(time.time() * 1000)

    def trigger_override(self) -> bool:
        self.override_ind = True

    def check_for_low(
        self,
        key: int = None,
        keys: List[int] = None
    ) -> bool:

        if key:
            keys = [key]

        if not keys:
            return False

        pressed = self._get_pressed_keys()

        for candidate in keys:
            if candidate in pressed:
                self.update_last_input_time()
                return True

        return False

    def has_any_input(self) -> bool:
        pressed = self._get_pressed_keys()
        return len(pressed) > 0
