#! /usr/bin/python3

# TODO: how to get/set CTM with Xlib only

import os
import subprocess
import argparse
from Xlib import display
from Xlib.ext import xinput

class Stylus:
    def __init__(self) -> None:
        self.name       :str    = ""
        self.id         :int
        self.x          :int
        self.y          :int

    def __str__(self) -> str:
        return ", ".join(f"{key}: {value}" for key, value in vars(self).items())

class Monitor:
    def __init__(self) -> None:
        self.width      :int
        self.height     :int
        self.max_width  :int = 0
        self.max_height :int = 0
        self.offset_x   :int
        self.offset_y   :int

    def __str__(self) -> str:
        return ", ".join(f"{key}: {value}" for key, value in vars(self).items())

stylus = Stylus()
monitor = Monitor()
d = display.Display()
CTM_FILE = "/tmp/.wacom-precision-mode-ctm"

def error(msg) -> None:
    print("ERROR:", msg)
    exit(1)

def get_stylus_info() -> None:
    for dev in xinput.query_device(d, xinput.AllDevices).devices:
        if all(x in dev.name.lower() for x in ("wacom", "stylus")):
            stylus.name = dev.name
            stylus.id = dev.deviceid
    if not stylus.name:
        error("Stylus not found.")

    stylus_pos = d.screen().root.query_pointer()._data
    stylus.x = stylus_pos["root_x"]
    stylus.y = stylus_pos["root_y"]

def get_monitor_info() -> None:
    monitors = d.screen().root.xrandr_get_monitors().monitors
    for mon in monitors:
        monitor.max_width = max(monitor.max_width, mon["x"] + mon["width_in_pixels"])
        monitor.max_height = max(monitor.max_height, mon["y"] + mon["height_in_pixels"])

        if stylus.x >= mon["x"] and stylus.x <= mon["x"] + mon["width_in_pixels"]:
            monitor.width = mon["width_in_pixels"]
            monitor.height = mon["height_in_pixels"]
            monitor.offset_x = mon["x"]
            monitor.offset_y = mon["y"]


def set_ctm(scale, scale_x=None, scale_y=None, offset_x=None, offset_y=None) -> None:
    # don't use `... = ... or ...` because given values may be zero
    scale_x = scale_x if scale_x is not None else (scale * (monitor.width / monitor.max_width))
    scale_y = scale_y if scale_y is not None else (scale * (monitor.height / monitor.max_height))
    offset_x = offset_x if offset_x is not None else (stylus.x / monitor.max_width)
    offset_y = offset_y if offset_y is not None else (stylus.y / monitor.max_height)

    subprocess.run(["xinput", "set-prop", str(stylus.id),
                    "Coordinate Transformation Matrix",
                    str(scale_x), "0", str(offset_x),
                    "0", str(scale_y), str(offset_y),
                    "0", "0", "1"], check=True)

def get_ctm() -> list[str]:
    res = subprocess.run(["xinput", "list-props", str(stylus.id)], capture_output=True, text=True)
    for line in res.stdout.splitlines():
        if "Coordinate Transformation Matrix" in line:
            return line.split(":")[1].strip().split(", ")
    return []

def is_precision_mode_enabled() -> bool:
    return os.path.exists(CTM_FILE)

def enable_precision_mode(scale) -> None:
    backup_ctm()
    set_ctm(scale)
    print("Enabled precision mode.")

def backup_ctm() -> None:
    if not is_precision_mode_enabled():
        with open(CTM_FILE, "w") as f:
            f.write(" ".join(get_ctm()))

def restore_ctm() -> list[float]:
    with open(CTM_FILE, "r") as f:
        ctm = f.readline().split(" ")
    ctm = [float(el) for el in ctm]
    if len(ctm) != 9 or not all([0 <= el <= 1 for el in ctm]):
        error("CTM backup corrupted.")
    os.remove(CTM_FILE)
    return ctm

def disable_precision_mode() -> None:
    if not is_precision_mode_enabled():
        return
    ctm = restore_ctm()
    set_ctm(1.0, ctm[0], ctm[4], ctm[2], ctm[5])
    print("Disabled precision mode.")

def toggle_precision_mode(scale) -> None:
    if is_precision_mode_enabled():
        disable_precision_mode()
    else:
        enable_precision_mode(scale)

def parse_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, help="Set precision scale (float between 0 and 1).")
    parser.add_argument("--action", type=str, required=True, help="toggle|enable|disable precision mode.")
    parser.add_argument("--gui", action="store_true", help="Enable GUI mode.")
    args = parser.parse_args()

    if args.scale is not None and not (0 < args.scale < 1):
        error("--scale must be between 0 and 1 (both exclusive).")

    if args.action and not args.action in ("toggle", "enable", "disable"):
        error("--action must be one of toggle|enable|disable.")

    if args.action in ("toggle", "enable") and args.scale is None:
        error("--scale must be set if --action toggle|enable.")

    return args


if __name__ == "__main__":
    args = parse_cli_args()

    get_stylus_info()
    get_monitor_info()

    print("STYLUS -", stylus)
    print("MONITOR -", monitor)

    if args.action == "toggle":
        toggle_precision_mode(args.scale)
    elif args.action == "enable":
        enable_precision_mode(args.scale)
    else:
        disable_precision_mode()

    if args.gui and is_precision_mode_enabled():
        from gui import gui_init
        gui_init(stylus.x - monitor.offset_x,
                 stylus.y - monitor.offset_y,
                 int(args.scale * monitor.width),
                 int(args.scale * monitor.height))
        exit(0)
