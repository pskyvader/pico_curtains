import machine


class LEDControl:
    default_state = True

    def __init__(self, pin_number):
        self.pin = machine.Pin(pin_number, machine.Pin.OUT)
        self.is_blinking = False

    def set_led_state(self, state):
        self.default_state = state
        self.pin.value(self.default_state)

    def toggle_led(self):
        current_state = self.pin.value()
        self.pin.value(not current_state)

    def start_blinking(self):
        self.is_blinking = True
        self._blink()

    def stop_blinking(self):
        self.is_blinking = False
        self.pin.value(self.default_state)

    def _blink(self):
        if self.is_blinking:
            self.toggle_led()
            timer = machine.Timer()
            timer.init(
                period=500,
                mode=machine.Timer.ONE_SHOT,
                callback=lambda t: self._blink(),
            )
