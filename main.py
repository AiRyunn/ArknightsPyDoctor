#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
from functools import lru_cache
from tqdm import tqdm
import cv2
import numpy as np

play_times = 6


def get_screenshot():
    os.system("adb shell screencap -p /sdcard/screenshot.png")
    os.system("adb pull /sdcard/screenshot.png screenshot.png>/dev/null")
    return "screenshot.png"


def tap_screen(x, y):
    os.system(f"adb shell input tap {x} {y}")


@lru_cache(maxsize=32)
def imread_cached(img_addr, flags=None):
    if flags is not None:
        return cv2.imread(img_addr, flags=flags)
    return cv2.imread(img_addr)


def screen_match(img_addr, threshhold=0.9):
    screenshot = get_screenshot()
    img = cv2.imread(screenshot)
    img_temp = imread_cached(img_addr)
    res = cv2.matchTemplate(img, img_temp, cv2.TM_CCOEFF_NORMED)
    return cv2.minMaxLoc(res)[1] > threshhold


def get_digit(img):
    img = cv2.copyMakeBorder(img, 0, 0, 30, 30, cv2.BORDER_CONSTANT, value=0)
    sim = [None] * 11
    for i in range(10):
        img_digit = imread_cached(f"images/digit_{i}.png", flags=cv2.IMREAD_GRAYSCALE)
        # print(img.shape, img_digit.shape)
        res = cv2.matchTemplate(img, img_digit, cv2.TM_CCOEFF_NORMED)
        sim[i] = cv2.minMaxLoc(res)[1]

    img_sep = imread_cached(f"images/sep.png", flags=cv2.IMREAD_GRAYSCALE)
    # print(img.shape, img_sep.shape)
    res = cv2.matchTemplate(img, img_sep, cv2.TM_CCOEFF_NORMED)
    sim[10] = cv2.minMaxLoc(res)[1]

    result = np.argmax(sim)
    if result == 10:
        result = -1

    return result


def get_progress():
    if not screen_match("images/fighting.png"):
        return 99999, -1

    screenshot = cv2.imread("screenshot.png", cv2.IMREAD_GRAYSCALE)
    img = screenshot[30:64, 1046:1211]
    img = cv2.resize(img, (img.shape[1] * 4, img.shape[0] * 4))
    _, img_bin = cv2.threshold(img, 192, 255, cv2.THRESH_BINARY)

    width = img_bin.shape[1]
    col = 0

    a, b, sep = 0, 0, False
    while col < width:
        l = col
        while col < width and np.sum(img_bin[:, col]) > 0:
            col += 1
        r = col
        if l != r:
            digit = get_digit(img_bin[:, l:r])
            if digit < 0:
                sep = True
            elif not sep:
                a = a * 10 + digit
            else:
                b = b * 10 + digit
        col += 1

    # Fix digital occlusion in special cases
    if b == 0:
        return 0, 0

    return a, b


def work():
    if not screen_match("images/start.png"):
        raise Exception("failed to start: please select mission")

    print("start!")
    tap_screen(2091, 1008)
    time.sleep(1)

    if screen_match("images/sanity.png"):
        raise Exception("failed to start: lack of sanity")

    print("fighting!")
    tap_screen(1934, 768)
    time.sleep(10)

    a, b = -1, -1
    while b < 0:
        a, b = get_progress()
        time.sleep(1)

    for i in tqdm(range(b)):
        while i >= a:
            time.sleep(1)
            a, _ = get_progress()
        time.sleep(0.1)

    print("end")
    time.sleep(10)
    for _ in range(3):
        tap_screen(583, 303)
        time.sleep(10)
        if screen_match("images/start.png"):
            return

    raise Exception("unknown error")


for _ in range(play_times):
    try:
        work()
    except Exception as e:
        print(str(e))
        break
