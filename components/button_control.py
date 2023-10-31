import machine
import time


class Button:
    def __init__(
        self,
        pin,
        name,
        debounce_time=300,
        holding_time=700,
        on_pressed=None,
        on_released=None,
        on_held=None,
    ):
        self.pin = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.name = name
        self.debounce_time = debounce_time
        self.holding_time = holding_time
        self.last_state = 1
        self.pressed = False
        self.press_time = 0
        self.holding = False

        # Event handlers for button presses, releases, and holds
        self.on_pressed = on_pressed
        self.on_released = on_released
        self.on_held = on_held

    def _handle_pressed(self, current_time):
        if current_time - self.press_time >= self.debounce_time:
            self.press_time = current_time
            self.pressed = True
            if self.on_pressed:
                self.on_pressed()

    def _handle_released(self):
        self.pressed = False
        if self.holding:
            self.holding = False
            if self.on_released:
                self.on_released()

    def _handle_held(self, current_time):
        if self.pressed and current_time - self.press_time >= self.holding_time:
            self.holding = True
            if self.on_held:
                self.on_held()

    def check(self):
        current_state = self.pin.value()
        current_time = time.ticks_ms()

        if current_state == 0 and self.last_state == 1:
            self._handle_pressed(current_time)
        elif current_state == 1 and self.last_state == 0:
            self._handle_released()

        self._handle_held(current_time)

        self.last_state = current_state


class ButtonController:
    def __init__(self):
        self.buttons = []

    def add_button(self, pin, name, debounce_time=300, holding_time=700):
        button = Button(pin, name, debounce_time, holding_time)
        self.buttons.append(button)
        return button

    def check_buttons(self):
        for button in self.buttons:
            button.check()
