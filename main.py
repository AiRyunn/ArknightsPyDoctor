#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
from functools import lru_cache
from tqdm import tqdm
import cv2
import numpy as np

play_times = 6


def get_screenshot():
    os.system("adb shell screencap -p > screenshot.png")
    return "screenshot.png"


def tap_screen(x, y):
    os.system(f"adb shell input tap {x} {y}")


@lru_cache(maxsize=32)
def imread_cached(img_addr, flags=None):
    if flags is not None:
        return cv2.imread(img_addr, flags=flags)
    return cv2.imread(img_addr)


def screen_match(img_addr, screenshot=None, threshold=0.8):
    if screenshot is None:
        screenshot = get_screenshot()
    img = cv2.imread(screenshot)
    img_temp = imread_cached(img_addr)
    res = cv2.matchTemplate(img, img_temp, cv2.TM_CCOEFF_NORMED)
    return cv2.minMaxLoc(res)[1] >= threshold


def get_digit(img):
    if img.shape[1] < 10:
        return "|"

    img = cv2.copyMakeBorder(img, 0, 0, 30, 30, cv2.BORDER_CONSTANT, value=0)
    sim = [None] * 11
    for i in range(10):
        img_digit = imread_cached(f"images/digit_{i}.png", flags=cv2.IMREAD_GRAYSCALE)
        res = cv2.matchTemplate(img, img_digit, cv2.TM_CCOEFF_NORMED)
        sim[i] = cv2.minMaxLoc(res)[1]

    img_sep = imread_cached(f"images/sep.png", flags=cv2.IMREAD_GRAYSCALE)
    res = cv2.matchTemplate(img, img_sep, cv2.TM_CCOEFF_NORMED)
    sim[10] = cv2.minMaxLoc(res)[1]

    result = np.argmax(sim)
    if result == 10:
        result = "/"
    else:
        result = str(result)

    return result


def get_progress():
    if not screen_match("images/fighting.png"):
        return None, None

    screenshot = cv2.imread("screenshot.png", cv2.IMREAD_GRAYSCALE)

    img_fighting_enemy = imread_cached(
        "images/fighting_enemy.png", flags=cv2.IMREAD_GRAYSCALE
    )
    img_fighting_hp = imread_cached(
        "images/fighting_hp.png", flags=cv2.IMREAD_GRAYSCALE
    )

    res_fighting_enemy = cv2.matchTemplate(
        screenshot, img_fighting_enemy, cv2.TM_CCOEFF_NORMED
    )
    res_fighting_hp = cv2.matchTemplate(
        screenshot, img_fighting_hp, cv2.TM_CCOEFF_NORMED
    )

    loc_fighting_enemy = cv2.minMaxLoc(res_fighting_enemy)[-1][::-1]
    loc_fighting_hp = cv2.minMaxLoc(res_fighting_hp)[-1][::-1]

    x0, y0, x1, y1 = (
        loc_fighting_enemy[0],
        loc_fighting_enemy[1] + img_fighting_enemy.shape[1],
        loc_fighting_enemy[0] + img_fighting_enemy.shape[1],
        loc_fighting_hp[1],
    )

    img = screenshot[x0:x1, y0:y1]  # img = screenshot[30:64, 1046:1211]
    img = cv2.resize(img, (img.shape[1] * 4, img.shape[0] * 4))
    _, img_bin = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)  # fade in

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
            if digit == "|":
                break
            elif digit == "/":
                sep = True
            elif not sep:
                a = a * 10 + int(digit)
            else:
                b = b * 10 + int(digit)
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
    time.sleep(3)

    if screen_match("images/sanity.png"):
        raise Exception("failed to start: lack of sanity")

    if screen_match("images/start.png", screenshot="screenshot.png"):
        raise Exception("failed to start")

    print("fighting!")
    tap_screen(1934, 768)
    time.sleep(12)

    a, b = None, None
    while b is None:
        a, b = get_progress()
        time.sleep(5)

    for i in tqdm(range(b)):
        while a is not None and i >= a:
            time.sleep(5)
            a, _ = get_progress()
        time.sleep(0.1)

    print("end")

    for _ in range(3):
        time.sleep(8)
        if screen_match("images/start.png"):
            return
        tap_screen(583, 303)

    raise Exception("unknown error")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        play_times = int(sys.argv[1])

    for _ in range(play_times):
        try:
            work()
        except Exception as e:
            print(str(e))
            break
