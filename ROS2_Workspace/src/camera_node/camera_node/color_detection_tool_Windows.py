"""
Standalone HSV color-tuning tool — not a ROS2 node, run directly with
`python3 color_detection_tool_Windows.py`. Laptop/Windows only — opens
the laptop's own webcam via OpenCV's DirectShow backend, not the RPi's
Logitech C310. Lets students practice the tuning workflow on their own
machine without needing the robot connected.

Purpose: find the HSV threshold range that isolates a target color (e.g. a
rescue target) in a camera feed, independent of lighting. Saved ranges go to
color_ranges_windows.json (written next to this file) — a separate file
from color_ranges.json (used by color_detection_tool_RPi.py and read by
camera_feed_publisher on the robot), so tuning on a laptop webcam never
overwrites the real calibration the robot uses. A range tuned here is a
practice run only — the robot's actual color ranges must still be tuned on
the RPi with its own camera via color_detection_tool_RPi.py.

How to start:
  On a Windows laptop, cd into this file's directory
  (ROS2_Workspace/src/camera_node/camera_node/) and run:
    python3 color_detection_tool_Windows.py

Known fix — ModuleNotFoundError: No module named 'cv2' (2026-07-22):
  Root cause either way: whichever Python actually runs this script has no
  opencv-python/numpy installed. Which fix applies depends on the machine:

  Windows 11 dev laptop, no pixi env installed (confirmed working 2026-07-22):
    Plain system Python (e.g. VSCode's default interpreter) is what's
    running the script, and pixi was never set up on this machine. Fix:
      python3 -m pip install opencv-python numpy
    This installs straight into the system Python — fine here since there's
    no pixi env to keep separate from.

  Windows 10 student laptop, pixi ROS2 env (per ros2_windows_pixi_install.md
  — not yet confirmed on real hardware, update this note once it is):
    Must run inside the pixi env, not system Python, or camera_feed_publisher
    /color_detection_tool_RPi.py's environment won't match what gets tested
    here. From C:\pixi_ws:
      pixi shell
      call ros2-windows\local_setup.bat
      python3 -m pip install opencv-python numpy
    (see ros2_windows_pixi_usage_reference.md for the pixi pip-install quirks
    — retries/timeout flags — students have hit before).

How to use:
  1. Run the script as above. Three windows open: Camera (live feed), Mask
     (black/white threshold preview), and HSV Tuning (six sliders).
  2. Press 1 / 2 / 3 to load a starting point for YELLOW / GREEN / BLUE onto
     the sliders (the last saved range for that color if there is one,
     otherwise a rough default).
  3. Adjust the sliders while watching the Mask window — the goal is white
     only where the target object is, black everywhere else. Narrow H Min/
     H Max first, then raise S Min/V Min to kill background noise.
  4. Press S to save the current sliders under the active color's name to
     color_ranges_windows.json.
  5. Press Q to quit.
"""

import json
import os

import cv2
import numpy as np

CAMERA_INDEX = 0
TRACKBAR_WINDOW = 'HSV Tuning'

# A blob has to be at least this many pixels to count as the target — filters
# out small flecks of background that happen to fall inside the HSV range.
MIN_TARGET_AREA = 500

# Kept separate from color_ranges.json (the RPi tool's file) so practicing on
# a laptop webcam can never overwrite the robot's real calibration.
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'color_ranges_windows.json')

# Rough starting points, used only the first time a color is picked (before
# it's been tuned and saved). Yellow sits at OpenCV H~20-35 (pure yellow is
# ~30) — unlike red, it doesn't wrap around the hue wheel, but it does sit
# close to skin/wood tones indoors, so keep S Min/V Min raised while tuning
# rather than widening H too far to compensate.
DEFAULT_PRESETS = {
    'YELLOW': ((20, 100, 100), (35, 255, 255)),
    'GREEN': ((35, 80, 50), (85, 255, 255)),
    'BLUE': ((90, 80, 50), (130, 255, 255)),
}
KEY_TO_COLOR = {ord('1'): 'YELLOW', ord('2'): 'GREEN', ord('3'): 'BLUE'}


def _on_trackbar_change(_value):
    pass  # cv2.createTrackbar requires a callback — values are read fresh each frame instead.


def create_trackbars():
    cv2.namedWindow(TRACKBAR_WINDOW)
    # OpenCV's Hue range is 0-179, not the usual 0-359 — half of everywhere else.
    cv2.createTrackbar('H Min', TRACKBAR_WINDOW, 0, 179, _on_trackbar_change)
    cv2.createTrackbar('H Max', TRACKBAR_WINDOW, 179, 179, _on_trackbar_change)
    cv2.createTrackbar('S Min', TRACKBAR_WINDOW, 0, 255, _on_trackbar_change)
    cv2.createTrackbar('S Max', TRACKBAR_WINDOW, 255, 255, _on_trackbar_change)
    cv2.createTrackbar('V Min', TRACKBAR_WINDOW, 0, 255, _on_trackbar_change)
    cv2.createTrackbar('V Max', TRACKBAR_WINDOW, 255, 255, _on_trackbar_change)


def get_hsv_range():
    h_min = cv2.getTrackbarPos('H Min', TRACKBAR_WINDOW)
    h_max = cv2.getTrackbarPos('H Max', TRACKBAR_WINDOW)
    s_min = cv2.getTrackbarPos('S Min', TRACKBAR_WINDOW)
    s_max = cv2.getTrackbarPos('S Max', TRACKBAR_WINDOW)
    v_min = cv2.getTrackbarPos('V Min', TRACKBAR_WINDOW)
    v_max = cv2.getTrackbarPos('V Max', TRACKBAR_WINDOW)
    return np.array([h_min, s_min, v_min]), np.array([h_max, s_max, v_max])


def set_hsv_range(lower, upper):
    cv2.setTrackbarPos('H Min', TRACKBAR_WINDOW, int(lower[0]))
    cv2.setTrackbarPos('S Min', TRACKBAR_WINDOW, int(lower[1]))
    cv2.setTrackbarPos('V Min', TRACKBAR_WINDOW, int(lower[2]))
    cv2.setTrackbarPos('H Max', TRACKBAR_WINDOW, int(upper[0]))
    cv2.setTrackbarPos('S Max', TRACKBAR_WINDOW, int(upper[1]))
    cv2.setTrackbarPos('V Max', TRACKBAR_WINDOW, int(upper[2]))


def load_saved_ranges():
    """Read color_ranges_windows.json — {} if nothing's been saved yet."""
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_range(color_name, lower, upper):
    saved = load_saved_ranges()
    saved[color_name] = {'lower': lower.tolist(), 'upper': upper.tolist()}
    with open(CONFIG_PATH, 'w') as f:
        json.dump(saved, f, indent=2)


def range_for_color(color_name):
    """The last-saved range for a color, falling back to its rough default preset."""
    saved = load_saved_ranges()
    if color_name in saved:
        return np.array(saved[color_name]['lower']), np.array(saved[color_name]['upper'])
    lower, upper = DEFAULT_PRESETS[color_name]
    return np.array(lower), np.array(upper)


def find_target(mask):
    """Return the (x, y, w, h) bounding box of the largest blob in the mask, or None."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < MIN_TARGET_AREA:
        return None

    return cv2.boundingRect(largest)


def main():
    # CAP_DSHOW instead of the RPi tool's CAP_V4L2 — DirectShow is the
    # Windows-native backend and avoids the multi-second startup delay
    # OpenCV's default (MSMF) backend has on some laptops. No forced
    # MJPG/resolution here: that was a fix for the RPi's specific USB
    # bandwidth bottleneck with the C310, which doesn't apply to a laptop's
    # built-in webcam.
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print(f'Could not open camera index {CAMERA_INDEX}')
        return

    create_trackbars()
    current_color = 'YELLOW'
    set_hsv_range(*range_for_color(current_color))

    print('Press 1/2/3 to load YELLOW/GREEN/BLUE, tune the sliders, then S to save. Q to quit.')

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower, upper = get_hsv_range()
        mask = cv2.inRange(hsv, lower, upper)
        # Erode then dilate to knock out small speckles of noise in the mask
        # without shrinking the real target back down.
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        bbox = find_target(mask)
        frame_width = frame.shape[1]
        if bbox is None:
            position = 'NONE'
        else:
            x, y, w, h = bbox
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cx = x + w // 2
            if cx < frame_width / 3:
                position = 'LEFT'
            elif cx > frame_width * 2 / 3:
                position = 'RIGHT'
            else:
                position = 'CENTER'

        cv2.putText(frame, f'{current_color} {position}', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow('Camera', frame)
        cv2.imshow('Mask', mask)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key in KEY_TO_COLOR:
            current_color = KEY_TO_COLOR[key]
            set_hsv_range(*range_for_color(current_color))
        elif key == ord('s'):
            save_range(current_color, lower, upper)
            print(f'Saved {current_color}: H {lower[0]}-{upper[0]}  S {lower[1]}-{upper[1]}  V {lower[2]}-{upper[2]}')

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
