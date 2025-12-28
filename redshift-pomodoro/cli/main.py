#!/usr/bin/env python3
import subprocess
import time
from enum import StrEnum

import pygame as pg
from viztools.utils import Align
from viztools.viewer import UIViewer
from viztools.ui.elements import Button, Label, CheckBox, Slider

REDSHIFTS = [
    (0, 6500),
    (20, 6500),
    (25, 5000),
    (35, 4000),
    (50, 3000),
    (70, 2000),
]
DEFAULT_REDSHIFT = 6500
RECOVERY_SPEED = 4.0


def get_redshift_value(t: float) -> int:
    index = -1
    for i, (d, _) in enumerate(REDSHIFTS):
        if d > t:
            index = i
            break
    if index == -1:
        return REDSHIFTS[-1][1]
    left, right = REDSHIFTS[index - 1], REDSHIFTS[index]
    return int(left[1] + (right[1] - left[1]) * (t - left[0]) / (right[0] - left[0]))


class Mode(StrEnum):
    WORK = "Work"
    BREAK = "Break"

    def toggle(self) -> 'Mode':
        return Mode.WORK if self == Mode.BREAK else Mode.BREAK


def set_redshift(redshift: int):
    res = subprocess.run(["redshift", "-P", "-O", str(redshift)], capture_output=True)
    try:
        res.check_returncode()
    except subprocess.CalledProcessError:
        raise ValueError(f"Failed to execute redshift:\n{res.stderr.decode('utf-8')}\n{res.stdout.decode('utf-8')}")


class PomodoroViewer(UIViewer):
    def __init__(self):
        super().__init__((600, 370), title="Redshift Pomodoro", framerate=60)

        self.mode = Mode.BREAK

        width = 100
        self.title = Label(
            pg.Rect((600 - width) // 2, 50, width, 50), "Redshift Pomodoro", align=Align.CENTER, font_size=32
        )
        self.label = Label(
            pg.Rect((600 - width) // 2, 90, width, 50), f"Current mode: {self.mode.value}", align=Align.CENTER,
            font_size=22
        )
        self.enabled_checkbox = CheckBox(pg.Rect(220, 150, 30, 30), checked=True)
        self.enabled_label = Label(pg.Rect(255, 151, 100, 30), "Enable Redshift", align=Align.LEFT)
        self.start_stop_button = Button(pg.Rect((600 - width) // 2, 200, width, 50), self.mode.toggle().value)
        self.exhaustion_level = 0  # in minutes
        self.last_update_time = time.perf_counter()
        self.exhaustion_slider = Slider(pg.Rect(20, 280, 600 - 2 * 20, 30), self.exhaustion_level, 0, 100)
        self.exhaustion_label = Label(pg.Rect(250, 310, 100, 30), "Work Duration: 0.0", align=Align.CENTER)

        self.current_redshift = DEFAULT_REDSHIFT
        set_redshift(self.current_redshift)

    def set_redshift(self, redshift: int):
        if redshift != self.current_redshift:
            self.current_redshift = redshift
            set_redshift(redshift)

    def handle_event(self, event: pg.event.Event):
        super().handle_event(event)
        if event.type == pg.KEYDOWN and event.key in (pg.K_RETURN, pg.K_SPACE):
            self.toggle_mode()

    def update(self):
        if self.start_stop_button.is_clicked:
            self.toggle_mode()
        self.update_work_duration()
        self.apply_redshift()

    def apply_redshift(self):
        if self.enabled_checkbox.checked:
            red_shift_value = get_redshift_value(self.exhaustion_level)
            self.set_redshift(red_shift_value)
        else:
            self.set_redshift(DEFAULT_REDSHIFT)

    def toggle_mode(self):
        self.mode = self.mode.toggle()
        self.start_stop_button.set_text(self.mode.toggle().value)
        self.label.set_text(f"Current mode: {self.mode.value}")

    def update_work_duration(self):
        now = time.perf_counter()
        duration = (now - self.last_update_time) / 60
        self.last_update_time = now

        if self.exhaustion_slider.has_changed:
            self.exhaustion_level = self.exhaustion_slider.value
        else:
            if self.mode == Mode.WORK:
                self.exhaustion_level += duration
            elif self.mode == Mode.BREAK:
                self.exhaustion_level = max(self.exhaustion_level - duration * RECOVERY_SPEED, 0)
            self.exhaustion_slider.value = self.exhaustion_level
        text = f"Work Duration: {int(self.exhaustion_level)} min"
        if self.exhaustion_label._text != text:
            self.exhaustion_label.set_text(text)

def main():
    viewer = PomodoroViewer()
    viewer.run()
    set_redshift(DEFAULT_REDSHIFT)


if __name__ == '__main__':
    main()
