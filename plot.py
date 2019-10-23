# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from PIL import Image, ImageDraw
from colorhash import ColorHash

import telegram
from telegram.error import TelegramError

import random

with open("api_key.txt", 'r') as f:
    TOKEN = f.read().rstrip()

bot = telegram.Bot(token=TOKEN)

# I think it might be more elegant to return non-null and return strings with error text if need be.

# https://www.science-emergence.com/Articles/How-to-put-the-origin-in-the-center-of-the-figure-with-matplotlib-/
# https://pythonspot.com/matplotlib-scatterplot/
# https://stackoverflow.com/questions/51113062/how-to-receive-images-from-telegram-bot

class Plot:
    def __init__(self, name, xaxisleft, xaxisright, yaxisbottom, yaxistop, minx, maxx, miny, maxy):
        self.__name = name
        self.__xaxisleft = xaxisleft
        self.__xaxisright = xaxisright
        self.__yaxisbottom = yaxisbottom
        self.__yaxistop = yaxistop
        self.__minx = minx
        self.__maxx = maxx
        self.__miny = miny
        self.__maxy = maxy
        self.__points = []

    def plot_point(self, label, x, y):
        if not (self.__minx < x < self.__maxx and self.__miny < y < self.__maxy):
            # Send error with bounds for plot name.
            pass
        self.__points.append((label, x, y))

    def get_name(self):
        return self.__name

    def get_xaxisleft(self):
        return self.__xaxisleft

    def get_xaxisright(self):
        return self.__xaxisright

    def get_yaxisbottom(self):
        return self.__yaxisbottom

    def get_yaxistop(self):
        return self.__yaxistop

    def get_minx(self):
        return self.__minx

    def get_maxx(self):
        return self.__maxx

    def get_miny(self):
        return self.__miny

    def get_maxy(self):
        return self.__maxy