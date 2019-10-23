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

class Plot:
    def __init__(self, name, xaxis, yaxis, minx, maxx, miny, maxy):
        self.__name = name
        self.__xaxis = xaxis
        self.__yaxis = yaxis
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

    def get_xaxis(self):
        return self.__xaxis

    def get_yaxis(self):
        return self.__xaxis

    def get_minx(self):
        return self.__minx

    def get_maxx(self):
        return self.__maxx

    def get_miny(self):
        return self.__miny

    def get_maxy(self):
        return self.__maxy