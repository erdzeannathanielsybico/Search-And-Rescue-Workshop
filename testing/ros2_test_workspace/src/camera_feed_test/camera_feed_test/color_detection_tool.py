"""
Standalone HSV color-tuning tool — not a ROS2 node, run directly with
`python3 color_detection_tool.py`.

Purpose: find and save the HSV threshold range that isolates a target color
(e.g. a rescue target) in the camera feed, independent of lighting. This
script's only lasting output is color_ranges.json (written next to this
file) — it doesn't publish anything itself. Other code (camera_feed_publisher
for HUD overlays, and a future color-tracking node for autonomous driving)
reads that file via range_for_color() instead of re-tuning from scratch.

How to use:
  1. Run the script. Three windows open: Camera (live feed), Mask (black/
     white threshold preview), and HSV Tuning (six sliders).
  2. Press 1 / 2 / 3 to load a starting point for RED / GREEN / BLUE onto
     the sliders (the last saved range for that color if there is one,
     otherwise a rough default).
  3. Adjust the sliders while watching the Mask window — the goal is white
     only where the target object is, black everywhere else. Narrow H Min/
     H Max first, then raise S Min/V Min to kill background noise.
  4. Press S to save the current sliders under the active color's name to
     color_ranges.json.
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

# Saved tunings live next to this script so any other node (e.g. a future
# tracking node) can load the same calibrated ranges without re-tuning.
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'color_ranges.json')

# Rough starting points, used only the first time a color is picked (before
# it's been tuned and saved). Red is deliberately narrow (0-10) rather than
# the full 0-179 wheel — red also wraps around to 170-179, which a single
# range like this can't cover; nudge H Min/Max toward that side instead if
# your red object needs it.
DEFAULT_PRESETS = {
    'RED': ((0, 120, 70), (10, 255, 255)),
    'GREEN': ((35, 80, 50), (85, 255, 255)),
    'BLUE': ((90, 80, 50), (130, 255, 255)),
}
KEY_TO_COLOR = {ord('1'): 'RED', ord('2'): 'GREEN', ord('3'): 'BLUE'}


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
    """Read color_ranges.json — {} if nothing's been saved yet."""
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
    # Same V4L2/MJPG setup as camera_feed_publisher.py — forcing raw YUYV
    # capture at 720p makes frames arrive at an irregular rate on this bus.
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    create_trackbars()
    current_color = 'RED'
    set_hsv_range(*range_for_color(current_color))

    print('Press 1/2/3 to load RED/GREEN/BLUE, tune the sliders, then S to save. Q to quit.')

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
