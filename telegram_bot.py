# -*- coding: utf-8 -*-
#!/usr/bin/env python3
from __future__ import unicode_literals

import telegram
from telegram.ext import Updater, CommandHandler, PicklePersistence
from telegram.error import TelegramError
import logging

import os
import argparse
from collections import Counter, OrderedDict
import datetime

from plot import Plot, BoxedPlot, AlignmentChart, TrianglePlot

with open("api_key.txt", 'r') as f:
    TOKEN = f.read().rstrip()

PORT = int(os.environ.get('PORT', '8443'))

ARG_PARSER = argparse.ArgumentParser(description="The parser for creating plots.")
ARG_PARSER.add_argument("-t", "--title", type=str, nargs='*')
ARG_PARSER.add_argument("-xr", "--xright", type=str, nargs='*')
ARG_PARSER.add_argument("-xl", "--xleft", type=str, nargs='*')
ARG_PARSER.add_argument("-yt", "--ytop", type=str, nargs='*')
ARG_PARSER.add_argument("-yb", "--ybottom", type=str, nargs='*')
ARG_PARSER.add_argument("-h1", "--horiz1", type=str, nargs='*')
ARG_PARSER.add_argument("-h2", "--horiz2", type=str, nargs='*')
ARG_PARSER.add_argument("-h3", "--horiz3", type=str, nargs='*')
ARG_PARSER.add_argument("-v1", "--vert1", type=str, nargs='*')
ARG_PARSER.add_argument("-v2", "--vert2", type=str, nargs='*')
ARG_PARSER.add_argument("-v3", "--vert3", type=str, nargs='*')
ARG_PARSER.add_argument("-l1", "--label1", type=str, nargs='*')
ARG_PARSER.add_argument("-l2", "--label2", type=str, nargs='*')
ARG_PARSER.add_argument("-l3", "--label3", type=str, nargs='*')
ARG_PARSER.add_argument("-l4", "--label4", type=str, nargs='*')
ARG_PARSER.add_argument("-l5", "--label5", type=str, nargs='*')
ARG_PARSER.add_argument("-l6", "--label6", type=str, nargs='*')
ARG_PARSER.add_argument("-l7", "--label7", type=str, nargs='*')
ARG_PARSER.add_argument("-l8", "--label8", type=str, nargs='*')
ARG_PARSER.add_argument("-l9", "--label9", type=str, nargs='*')
ARG_PARSER.add_argument("-mx", "--minx", type=int)
ARG_PARSER.add_argument("-Mx", "--maxx", type=int)
ARG_PARSER.add_argument("-my", "--miny", type=int)
ARG_PARSER.add_argument("-My", "--maxy", type=int)
ARG_PARSER.add_argument("--custompoints", action="store_true")

def send_message(bot, chat_id, text):
    try:
        # print(text)
        bot.send_message(chat_id=chat_id, text=text)
    except TelegramError as e:
        raise e


def static_handler(command):
    text = open("static_responses/{}.txt".format(command), "r").read()
    if command == "help":
        return CommandHandler(command,
                              lambda bot, update: send_message(bot, update.message.from_user.id, text))

    return CommandHandler(command,
        lambda bot, update: send_message(bot, update.message.chat.id, text))


def create_plot_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = ""

    if user.username is not None:
        username = user.username
    else:
        if user.first_name is not None:
            username = user.first_name + " "
        if user.last_name is not None:
            username += user.last_name

    try:
        parsed = ARG_PARSER.parse_args(args)
        plot_args = vars(parsed)
    except SystemExit:
        send_message(bot, chat_id, "That is not a valid argument list. See /help.")
        return

    # I have two options as I see it:
    # (1) Use a counter as the key for the plots and iterate to find the name every time someone plots or removes.
    # (2) Use the name as the key and prevent duplicates. This means plots have to have a name.
    # Now that I've thought about it, selecting by name is a terrible idea; titles could be extremely long. I'm
    # going with option (1).

    # Args for plot definition (all are optional):
    # We'll have _ be a blank.
    # (1) name
    # (2) x-axis right title
    # (3) x-axis left title
    # (4) y-axis top title
    # (5) y-axis bottom title
    # (6) min x value
    # (7) max x value
    # (8) min y value
    # (9) max y value

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}

    max_key = max(chat_data["plots"].keys()) if len(chat_data["plots"].keys()) > 0 else 0
    plot = Plot(" ".join(plot_args.get("title")) if plot_args.get("title") is not None else None,
                " ".join(plot_args.get("xleft")) if plot_args.get("xleft") is not None else None,
                " ".join(plot_args.get("xright")) if plot_args.get("xright") is not None else None,
                " ".join(plot_args.get("ybottom")) if plot_args.get("ybottom") is not None else None,
                " ".join(plot_args.get("ytop")) if plot_args.get("ytop") is not None else None,
                plot_args.get("minx") if plot_args.get("minx") is not None else -10,
                plot_args.get("maxx") if plot_args.get("maxx") is not None else 10,
                plot_args.get("miny") if plot_args.get("miny") is not None else -10,
                plot_args.get("maxy") if plot_args.get("maxy") is not None else 10,
                username,
                max_key + 1,
                plot_args.get("custompoints") if plot_args.get("custompoints") is not None else False)
    chat_data["plots"][max_key + 1] = plot

    send_message(bot, chat_id, str(" ".join(plot_args.get("title", ""))) +
                                   " (" + str(max_key + 1) + ") was created successfully!")

    show_plot_handler(bot, update, chat_data, [max_key + 1])


def remove_plot_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = ""

    if user.username is not None:
        username = user.username
    else:
        if user.first_name is not None:
            username = user.first_name + " "
        if user.last_name is not None:
            username += user.last_name

    if len(args) != 1:
        send_message(bot, chat_id, "usage: /removeplot {plot_id}")
        return

    try:
        plot_id = int(args[0])
    except ValueError:
        send_message(bot, chat_id, "The plot ID must be an integer!")
        return

    if chat_data.get("plots") is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    if str(plot.get_creator()) != str(username):
        send_message(bot, chat_id, "You didn't make that plot (" + str(plot_id) + ")!")
        return

    del chat_data["plots"][plot_id]
    if chat_data.get("archived") is not None and chat_data["archived"].get(plot_id) is not None:
        del chat_data["archived"][plot_id]
    send_message(bot, chat_id, "Plot (" + str(plot_id) + ") has been removed!")


def plot_me_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = ""

    if user.username is not None:
        username = user.username
    else:
        if user.first_name is not None:
            username = user.first_name + " "
        if user.last_name is not None:
            username += user.last_name

    # Args are: {plot_id, but defaults to max key in non-archived plots}, x, y, err_x, err_y
    if len(args) < 2 or len(args) > 5:
        send_message(bot, chat_id, "usage: /plotme {plot_id} {x} {y} {err_x} {err_y}")
        return

    if chat_data.get("archived") is None:
        chat_data["archived"] = {}

    try:
        # Select the most recent (max) key from plots that aren't archived by default.
        plot_id = int(args[0]) if len(args) >= 3 else int(max({k:v for k, v in chat_data["plots"].items()
                                                               if k not in chat_data["archived"]}.keys()))
        x = float(args[1] if len(args) >= 3 else args[0])
        y = float(args[2] if len(args) >= 3 else args[1])
        err_x = float(args[3] if len(args) >= 4 else 0)
        err_y = float(args[4] if len(args) == 5 else 0)
    except ValueError:
        send_message(bot, chat_id, "Plot ID must be an int and x, y, err_x, err_y must be floats!")
        return

    if chat_data.get("plots") is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    result = plot.plot_point(username, x, y, err_x=err_x, err_y=err_y)

    if result is None:
        return

    if result[0] == 1:
        send_message(bot, chat_id, result[1])
        return
    elif result[0] == 0:
        img = plot.generate_plot()

        if img is None:
            return

        if img[0] == 1:
            send_message(bot, chat_id, img[1])
            return
        elif img[0] == 0:
            bot.send_photo(chat_id=chat_id, photo=img[1])

        chat_data["plots"][plot_id].set_last_modified(datetime.datetime.now())


def remove_me_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = ""

    if user.username is not None:
        username = user.username
    else:
        if user.first_name is not None:
            username = user.first_name + " "
        if user.last_name is not None:
            username += user.last_name

    # Args are: plot_id
    if len(args) > 1:
        send_message(bot, chat_id, "usage: /removeme {plot_id}")
        return

    if chat_data.get("archived") is None:
        chat_data["archived"] = {}

    try:
        plot_id = int(args[0]) if len(args) == 1 else int(max({k:v for k, v in chat_data["plots"].items()
                                                               if k not in chat_data["archived"]}.keys()))
    except ValueError:
        send_message(bot, chat_id, "The plot ID must be an integer!")
        return

    if chat_data.get("plots") is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    result = plot.remove_point(username)

    if result is None:
        return

    if result[0] == 1:
        send_message(bot, chat_id, result[1])
        return
    elif result[0] == 0:
        img = plot.generate_plot()

        if img is None:
            return

        if img[0] == 1:
            send_message(bot, chat_id, img[1])
            return
        elif img[0] == 0:
            bot.send_photo(chat_id=chat_id, photo=img[1])

        chat_data["plots"][plot_id].set_last_modified(datetime.datetime.now())


def show_plot_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id

    # Args are: {optional plot_id} {optional toggle for labels}
    if len(args) > 2:
        send_message(bot, chat_id, "usage: /showplot {plot_id} {optional 0/1 toggle for labels}")
        return

    if chat_data.get("archived") is None:
        chat_data["archived"] = {}

    try:
        plot_id = int(args[0]) if len(args) >= 1 else int(max({k:v for k, v in chat_data["plots"].items()
                                                               if k not in chat_data["archived"]}.keys()))
        toggle = 1 if len(args) != 2 else int(args[1])
    except ValueError:
        send_message(bot, chat_id, "The plot ID and optional toggle must be an integer!")
        return

    if chat_data.get("plots") is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    toggle_labels = True if toggle > 0 else False
    result = plot.generate_plot(toggle_labels=toggle_labels)

    if result is None:
        return

    if result[0] == 1:
        send_message(bot, chat_id, result[1])
        return
    elif result[0] == 0:
        bot.send_photo(chat_id=chat_id, photo=result[1])


def list_plots_handler(bot, update, chat_data):
    chat_id = update.message.chat.id

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}

    if chat_data.get("archived") is None:
        chat_data["archived"] = {}

    # Plots that aren't archived.
    cur_plots = OrderedDict(sorted({k:v for k, v in chat_data["plots"].items() if k not in chat_data["archived"]}.items()))

    text = "Current plots:\n\n"
    for (key, value) in cur_plots.items():
        if isinstance(key, int):
            text += "(" + str(key) + "): " + str(value.get_name()) + "\n"
    send_message(bot, chat_id, text)


def full_list_plots_handler(bot, update, chat_data):
    chat_id = update.message.chat.id

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}

    text = "All plots:\n\n"
    for (key, value) in OrderedDict(sorted(chat_data["plots"].items())).items():
        if isinstance(key, int):
            text += "(" + str(key) + "): " + str(value.get_name()) + "\n"
    send_message(bot, chat_id, text)


def get_plot_stats_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id

    # Args are: plot_id
    if len(args) != 1:
        send_message(bot, chat_id, "usage: /plotstats {plot_id}")
        return

    try:
        plot_id = int(args[0])
    except ValueError:
        send_message(bot, chat_id, "The plot ID must be an integer!")
        return

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    result = plot.generate_stats()

    if result is None:
        return

    if result[0] == 1:
        send_message(bot, chat_id, result[1])
        return
    elif result[0] == 0:
        send_message(bot, chat_id, "Plot (" + str(plot_id) + ") Stats:\n\n" + str(result[1]))


def polyfit_plot_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id

    # Args are: plot_id {optional degree} {optional toggle_labels}
    if len(args) == 0 or len(args) > 3:
        send_message(bot, chat_id, "usage: /polyfitplot {plot_id} {optional degree} {optional label toggle}")
        return

    try:
        plot_id = int(args[0])
        deg = 1 if len(args) < 2 else int(args[1])
        toggle = 1 if len(args) < 3 else int(args[2])
    except ValueError:
        send_message(bot, chat_id, "All input arguments must be integers!")
        return

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    if deg < 0:
        send_message(bot, chat_id, "Degree must be non-negative!")
        return

    """
    if type(plot) != Plot:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") is not the right type!")
        return
    """

    toggle_labels = True if toggle > 0 else False
    result = plot.polyfit(deg, toggle_labels=toggle_labels)

    if result is None:
        return

    if result[0] == 1:
        send_message(bot, chat_id, result[1])
        return
    elif result[0] == 0:
        bot.send_photo(chat_id=chat_id, photo=result[1][0])
        send_message(bot, chat_id, "Plot (" + str(plot_id) + ") R^2: " + str(result[1][1]))


def whomademe_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id

    # Args are: plot_id
    if len(args) < 1:
        send_message(bot, chat_id, "usage: /whomademe {plot_id}")
        return

    try:
        plot_id = int(args[0])
    except ValueError:
        send_message(bot, chat_id, "The plot ID must be an integer!")
        return

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    send_message(bot, chat_id, "Plot (" + str(plot_id) + ") was made by: " + str(plot.get_creator()))


def custom_point_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = ""

    if user.username is not None:
        username = user.username
    else:
        if user.first_name is not None:
            username = user.first_name + " "
        if user.last_name is not None:
            username += user.last_name

    # Args are: plot_id, x, y, label
    if len(args) != 4:
        send_message(bot, chat_id, "usage: /custompoint {plot_id} {x} {y} {label}")
        return

    try:
        plot_id = int(args[0])
        x = float(args[1])
        y = float(args[2])
        label = str(args[3])
    except ValueError:
        send_message(bot, chat_id, "Plot ID must be an int and x, y must be floats.")
        return

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    if str(plot.get_creator()) != str(username):
        send_message(bot, chat_id, "You didn't make that plot (" + str(plot_id) + ")!")
        return

    if not plot.get_if_custom_points():
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't support custom points!")
        return

    result = plot.plot_point(label, x, y)

    if result is None:
        return

    if result[0] == 1:
        send_message(bot, chat_id, result[1])
        return
    elif result[0] == 0:
        img = plot.generate_plot()

        if img is None:
            return

        if img[0] == 1:
            send_message(bot, chat_id, img[1])
            return
        elif img[0] == 0:
            bot.send_photo(chat_id=chat_id, photo=img[1])

        chat_data["plots"][plot_id].set_last_modified(datetime.datetime.now())


def boxed_plot_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = ""

    if user.username is not None:
        username = user.username
    else:
        if user.first_name is not None:
            username = user.first_name + " "
        if user.last_name is not None:
            username += user.last_name

    try:
        parsed = ARG_PARSER.parse_args(args)
        plot_args = vars(parsed)
    except SystemExit:
        send_message(bot, chat_id, "That is not a valid argument list. See /help.")
        return

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}

    horiz = [
        " ".join(plot_args.get("horiz1")) if plot_args.get("horiz1") is not None else "",
        " ".join(plot_args.get("horiz2")) if plot_args.get("horiz2") is not None else "",
        " ".join(plot_args.get("horiz3")) if plot_args.get("horiz3") is not None else ""
    ]
    vert = [
        " ".join(plot_args.get("vert3")) if plot_args.get("vert3") is not None else "",
        " ".join(plot_args.get("vert1")) if plot_args.get("vert1") is not None else "",
        " ".join(plot_args.get("vert2")) if plot_args.get("vert2") is not None else ""
    ]

    max_key = max(chat_data["plots"].keys()) if len(chat_data["plots"].keys()) > 0 else 0
    plot = BoxedPlot(" ".join(plot_args.get("title")) if plot_args.get("title") is not None else None,
                horiz,
                vert,
                username,
                max_key + 1,
                plot_args.get("custompoints") if plot_args.get("custompoints") is not None else False)
    chat_data[max_key + 1] = plot

    send_message(bot, chat_id, str(" ".join(plot_args.get("title", ""))) +
                                   " (" + str(max_key + 1) + ") was created successfully!")

    show_plot_handler(bot, update, chat_data, [max_key + 1])


def lookup_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id

    # Args are: plot_id, name (assume no spaces, will set lowercase)
    if len(args) != 2:
        send_message(bot, chat_id, "usage: /custompoint {plot_id} {name (remove spaces)}")
        return

    try:
        plot_id = int(args[0])
        name = str(args[1])
    except ValueError:
        send_message(bot, chat_id, "Plot ID must be an int and name must be a string.")
        return

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    result = plot.lookup_label(name)

    if result is None:
        return

    if result[0] == 1:
        send_message(bot, chat_id, result[1])
        return
    elif result[0] == 0:
        (x, y) = result[1]
        send_message(bot, chat_id, name + " exists at (" + str(x) + ", " + str(y) + ").")
        return


def my_bet_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = ""

    if chat_data.get("current_bet") is None:
        send_message(bot, chat_id, "No bet currently exists!")
        return

    if user.username is not None:
        username = user.username
    else:
        if user.first_name is not None:
            username = user.first_name + " "
        if user.last_name is not None:
            username += user.last_name

    # Args are: R^2
    if len(args) != 1:
        send_message(bot, chat_id, "usage: /bet {R^2}")
        return

    try:
        R2 = float(args[0])
    except ValueError:
        send_message(bot, chat_id, "R^2 must be a float!")
        return

    # We assume there can only be one bet at a time. This has an associated degree and plot ID.
    chat_data["current_bet"]["bets"][username] = R2
    send_message(bot, chat_id, "Your bet has been placed!")


def setup_bet_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id

    # Args are: plot_id degree
    if len(args) != 2:
        send_message(bot, chat_id, "usage: /setupbet {plot_id} {degree}")
        return

    if chat_data.get("current_bet") is not None:
        send_message(bot, chat_id, "The following bet is already in progress:\n\nPlot ID: " +
                         str(chat_data["current_bet"]["plot_id"]) + "\nDegree: " +
                         str(chat_data["current_bet"]["degree"]))
        return

    try:
        plot_id = int(args[0])
        degree = int(args[1])
    except ValueError:
        send_message(bot, chat_id, "Plot ID and degree must both be integers!")
        return

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "That plot does not exist!")
        return

    if chat_data["plots"].get(plot_id) is None:
        send_message(bot, chat_id, "That plot does not exist!")
        return

    if degree < 0:
        send_message(bot, chat_id, "Degree must be non-negative!")
        return

    if len(chat_data["plots"][plot_id].get_points()) <= 1:
        send_message(bot, chat_id, "The plot must have at least two points.")
        return

    chat_data["current_bet"] = { "plot_id" : plot_id,
                                 "degree"  : degree,
                                 "bets"    : OrderedDict() }
    send_message(bot, chat_id, "The following bet was created:\n\nPlot ID: " +
                 str(chat_data["current_bet"]["plot_id"]) + "\nDegree: " +
                 str(chat_data["current_bet"]["degree"]))


def cancel_bet_handler(bot, update, chat_data):
    chat_id = update.message.chat.id

    if chat_data.get("current_bet") is None:
        send_message(bot, chat_id, "No bet currently exists!")
        return

    chat_data["current_bet"] = None
    send_message(bot, chat_id, "The bet has been canceled.")


def complete_bet_handler(bot, update, chat_data):
    chat_id = update.message.chat.id

    if chat_data.get("current_bet") is None:
        send_message(bot, chat_id, "No bet currently exists!")
        return

    if chat_data["current_bet"].get("bets") is None or len(chat_data["current_bet"]["bets"].keys()) == 0:
        send_message(bot, chat_id, "No one has yet bet!")
        return

    plot = chat_data["plots"][chat_data["current_bet"]["plot_id"]]
    result = plot.polyfit(chat_data["current_bet"]["degree"])

    if result is None:
        return

    if result[0] == 1:
        send_message(bot, chat_id, result[1])
        return
    elif result[0] == 0:
        best = ""
        bestr2 = 0
        best_diff = 2e30
        for username, value in chat_data["current_bet"]["bets"].items():
            diff = abs(value - result[1][1])
            if diff < best_diff:
                best_diff = diff
                best = username
                bestr2 = value

        bot.send_photo(chat_id=chat_id, photo=result[1][0])
        send_message(bot, chat_id, "Actual R^2: " + str(result[1][1]))
        send_message(bot, chat_id, "Winner: " + best + " with R^2 = " + str(bestr2) + "!")

        if chat_data.get("scoreboard") is None:
            chat_data["scoreboard"] = {}
        if chat_data.get("scoreboard_avg") is None:
            chat_data["scoreboard_avg"] = {}

        if chat_data["scoreboard"].get(best) is None:
            chat_data["scoreboard"][best] = 1
        else:
            chat_data["scoreboard"][best] += 1

        if chat_data["scoreboard_avg"].get(best) is None:
            chat_data["scoreboard_avg"][best] = best_diff
        else:
            # sum(x_i) / (n - 1) is currently stored.
            # (sum(x_i) + y) / n (n - 1) / (n - 1) clearly gives desired result.
            chat_data["scoreboard_avg"][best] *= chat_data["scoreboard"][best] - 1
            chat_data["scoreboard_avg"][best] += best_diff
            chat_data["scoreboard_avg"][best] /= chat_data["scoreboard"][best]

    chat_data["current_bet"] = None


def scoreboard_handler(bot, update, chat_data):
    chat_id = update.message.chat.id

    if chat_data.get("scoreboard") is None:
        send_message(bot, chat_id, "No scoreboard exists!")
        return

    scoreboard = chat_data["scoreboard"]
    highest = Counter(scoreboard).most_common(3)

    text = "Top 3 Scoreboard:\n\n"
    for i in range(len(highest)):
        # Just in case, somehow, someone exists in scoreboard but not avg.
        if chat_data["scoreboard_avg"].get(str(highest[i][0])) is None:
            chat_data["scoreboard_avg"][str(highest[i][0])] = 0
        highest[i] = (highest[i][0],
                      highest[i][1],
                      chat_data["scoreboard_avg"][str(highest[i][0])])
    highest.sort(key=lambda x: (-x[1], x[2]))

    for x in highest:
        text += str(x[0]) + ": " + str(x[1]) + " with Avg Diff: " + \
                str(chat_data["scoreboard_avg"][str(x[0])]) + "\n"

    send_message(bot, chat_id, text)


def equation_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id

    # Args are: plot_id {optional degree}
    if len(args) == 0 or len(args) > 2:
        send_message(bot, chat_id, "usage: /equation {plot_id} {optional degree}")
        return

    try:
        plot_id = int(args[0])
        deg = 1 if len(args) < 2 else int(args[1])
    except ValueError:
        send_message(bot, chat_id, "All input arguments must be integers!")
        return

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    if deg < 0:
        send_message(bot, chat_id, "Degree must be non-negative!")
        return

    result = plot.full_equation(deg)

    if result is None:
        return

    if result[0] == 1:
        send_message(bot, chat_id, result[1])
        return
    elif result[0] == 0:
        send_message(bot, chat_id, result[1])
        #bot.send_photo(chat_id=chat_id, photo=result[1])


def edit_plot_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = ""

    if user.username is not None:
        username = user.username
    else:
        if user.first_name is not None:
            username = user.first_name + " "
        if user.last_name is not None:
            username += user.last_name

    if len(args) <= 1:
        send_message(bot, chat_id, "usage: /editplot {plot_id} --title {t} --xright {xr} "
                                   "--xleft {xl} --ytop {yt} --ybottom {yb}"
                                   "--horiz2 {h1} --horiz2 {h2} --horiz3 {h3} "
                                   "--vert1 {v1} --vert2 {v2} --vert3 {v3} "
                                   "--minx {mx} --maxx {Mx} --miny {my} --maxy {My} {--custompoints}")
        return

    try:
        plot_id = int(args[0])
    except ValueError:
        send_message(bot, chat_id, "Plot ID must be an integer!")
        return

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    if str(plot.get_creator()) != str(username):
        send_message(bot, chat_id, "You didn't make that plot (" + str(plot_id) + ")!")
        return

    try:
        parsed = ARG_PARSER.parse_args(args[1:])
        plot_args = vars(parsed)
    except SystemExit:
        send_message(bot, chat_id, "That is not a valid argument list. See /help.")
        return

    plot.edit_plot(plot_args)
    send_message(bot, chat_id, "Plot (" + str(plot_id) + ") has been updated!")


def current_bet_handler(bot, update, chat_data):
    chat_id = update.message.chat.id

    if chat_data.get("current_bet") is None:
        send_message(bot, chat_id, "No bet currently exists!")
        return

    send_message(bot, chat_id, "The following bet is in progress:\n\nPlot ID: " +
                 str(chat_data["current_bet"]["plot_id"]) + "\nDegree: " +
                 str(chat_data["current_bet"]["degree"]))

    if chat_data["current_bet"].get("bets") is None or len(chat_data["current_bet"]["bets"].keys()) == 0:
        send_message(bot, chat_id, "No one has yet placed a bet!")
        return

    text = "Current Bets:\n\n"
    for (username, value) in chat_data["current_bet"]["bets"].items():
        text += str(username) + ": " + str(value) + "\n"
    send_message(bot, chat_id, text)


def alignment_chart_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = ""

    if user.username is not None:
        username = user.username
    else:
        if user.first_name is not None:
            username = user.first_name + " "
        if user.last_name is not None:
            username += user.last_name

    try:
        parsed = ARG_PARSER.parse_args(args)
        plot_args = vars(parsed)
    except SystemExit:
        send_message(bot, chat_id, "That is not a valid argument list. See /help.")
        return

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}

    labels = [
        " ".join(plot_args.get("label1")) if plot_args.get("label1") is not None else "",
        " ".join(plot_args.get("label2")) if plot_args.get("label2") is not None else "",
        " ".join(plot_args.get("label3")) if plot_args.get("label3") is not None else "",
        " ".join(plot_args.get("label4")) if plot_args.get("label4") is not None else "",
        " ".join(plot_args.get("label5")) if plot_args.get("label5") is not None else "",
        " ".join(plot_args.get("label6")) if plot_args.get("label6") is not None else "",
        " ".join(plot_args.get("label7")) if plot_args.get("label7") is not None else "",
        " ".join(plot_args.get("label8")) if plot_args.get("label8") is not None else "",
        " ".join(plot_args.get("label9")) if plot_args.get("label9") is not None else ""
    ]

    max_key = max(chat_data["plots"].keys()) if len(chat_data["plots"].keys()) > 0 else 0
    plot = AlignmentChart(" ".join(plot_args.get("title")) if plot_args.get("title") is not None else None,
                labels,
                username,
                max_key + 1,
                plot_args.get("custompoints") if plot_args.get("custompoints") is not None else False)
    chat_data[max_key + 1] = plot

    send_message(bot, chat_id, str(" ".join(plot_args.get("title", ""))) +
                                   " (" + str(max_key + 1) + ") was created successfully!")

    show_plot_handler(bot, update, chat_data, [max_key + 1])


def archive_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = ""

    if user.username is not None:
        username = user.username
    else:
        if user.first_name is not None:
            username = user.first_name + " "
        if user.last_name is not None:
            username += user.last_name

    if len(args) != 1:
        send_message(bot, chat_id, "usage: /archive {plot_id}")
        return

    try:
        plot_id = int(args[0])
    except ValueError:
        send_message(bot, chat_id, "Plot ID must be an integer!")
        return

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    if str(plot.get_creator()) != str(username):
        send_message(bot, chat_id, "You didn't make that plot (" + str(plot_id) + ")!")
        return

    if chat_data.get("archived") is None:
        chat_data["archived"] = {}

    if plot_id in chat_data["archived"].keys():
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") has already been archived!")
        return

    chat_data["archived"][plot_id] = chat_data["plots"][plot_id]
    send_message(bot, chat_id, "Plot (" + str(plot_id) + ") has been archived!")


def unarchive_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = ""

    if user.username is not None:
        username = user.username
    else:
        if user.first_name is not None:
            username = user.first_name + " "
        if user.last_name is not None:
            username += user.last_name

    if len(args) != 1:
        send_message(bot, chat_id, "usage: /unarchive {plot_id}")
        return

    try:
        plot_id = int(args[0])
    except ValueError:
        send_message(bot, chat_id, "Plot ID must be an integer!")
        return

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    if str(plot.get_creator()) != str(username):
        send_message(bot, chat_id, "You didn't make that plot (" + str(plot_id) + ")!")
        return

    if chat_data.get("archived") is None:
        chat_data["archived"] = {}
        send_message(bot, chat_id, "There aren't any archived plots!")
        return

    if plot_id not in chat_data["archived"].keys():
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") has not been archived!")
        return

    del chat_data["plots"][plot_id]
    send_message(bot, chat_id, "Plot (" + str(plot_id) + ") has been unarchived!")


def my_plots_handler(bot, update, chat_data):
    chat_id = update.message.chat.id
    user = update.message.from_user
    user_id = user.id
    username = ""

    if user.username is not None:
        username = user.username
    else:
        if user.first_name is not None:
            username = user.first_name + " "
        if user.last_name is not None:
            username += user.last_name

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "No plots currently exist!")
        return

    text = "Your plots:\n\n"
    for (key, value) in chat_data["plots"].items():
        if isinstance(key, int) and value.get_creator() == username:
            text += "(" + str(key) + "): " + str(value.get_name()) + "\n"
    send_message(bot, user_id, text)


def archive_all_handler(bot, update, chat_data):
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = ""

    if user.username is not None:
        username = user.username
    else:
        if user.first_name is not None:
            username = user.first_name + " "
        if user.last_name is not None:
            username += user.last_name

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "No plots currently exist!")
        return

    if chat_data.get("archived") is None:
        chat_data["archived"] = {}

    for (key, value) in chat_data["plots"].items():
        if isinstance(key, int) and value.get_creator() == username and key not in chat_data["archived"].keys():
            chat_data["archived"][key] = value

    send_message(bot, chat_id, "Your plots have been archived.")


def unarchive_all_handler(bot, update, chat_data):
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = ""

    if user.username is not None:
        username = user.username
    else:
        if user.first_name is not None:
            username = user.first_name + " "
        if user.last_name is not None:
            username += user.last_name

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "No plots currently exist!")
        return

    if chat_data.get("archived") is None:
        chat_data["archived"] = {}

    for (key, value) in chat_data["plots"].items():
        if isinstance(key, int) and value.get_creator() == username and key in chat_data["archived"].keys():
            del chat_data["archived"][key]

    send_message(bot, chat_id, "Your plots have been unarchived.")


def last_updated_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id

    # Args are: plot_id
    if len(args) != 1:
        send_message(bot, chat_id, "usage: /lastupdated {plot_id}")
        return

    try:
        plot_id = int(args[0])
    except ValueError:
        send_message(bot, chat_id, "The plot ID must be an integer!")
        return

    if chat_data.get("plots") is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    update_time = plot.get_last_modified()
    if update_time is None:
        update_time = "This plot hasn't been updated!"
    send_message(bot, chat_id, "Last Updated: " + str(update_time))


def whos_plotted_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id

    # Args are: plot_id
    if len(args) != 1:
        send_message(bot, chat_id, "usage: /whosplotted {plot_id}")
        return

    try:
        plot_id = int(args[0])
    except ValueError:
        send_message(bot, chat_id, "The plot ID must be an integer!")
        return

    if chat_data.get("plots") is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    points = plot.get_points()
    text = "Currently plotted on (" + str(plot_id) +  "):\n\n"
    for p in points:
        text += str(p[0]) + ": (" + str(p[1]) + ", " + str(p[2]) + ")\n"
    send_message(bot, chat_id, text)


def triangle_plot_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = ""

    if user.username is not None:
        username = user.username
    else:
        if user.first_name is not None:
            username = user.first_name + " "
        if user.last_name is not None:
            username += user.last_name

    try:
        parsed = ARG_PARSER.parse_args(args)
        plot_args = vars(parsed)
    except SystemExit:
        send_message(bot, chat_id, "That is not a valid argument list. See /help.")
        return

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}

    max_key = max(chat_data["plots"].keys()) if len(chat_data["plots"].keys()) > 0 else 0
    plot = TrianglePlot(" ".join(plot_args.get("title")) if plot_args.get("title") is not None else None,
                " ".join(plot_args.get("xleft")) if plot_args.get("xleft") is not None else None,
                " ".join(plot_args.get("xright")) if plot_args.get("xright") is not None else None,
                " ".join(plot_args.get("ytop")) if plot_args.get("ytop") is not None else None,
                username,
                max_key + 1,
                plot_args.get("custompoints") if plot_args.get("custompoints") is not None else False)
    chat_data["plots"][max_key + 1] = plot

    send_message(bot, chat_id, str(" ".join(plot_args.get("title", ""))) +
                                   " (" + str(max_key + 1) + ") was created successfully!")

    show_plot_handler(bot, update, chat_data, [max_key + 1])


def zoom_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id

    if len(args) != 5:
        send_message(bot, chat_id, "usage: /zoom {plot_id} {min_x} {min_y} {max_x} {max_y}")
        return

    try:
        plot_id = int(args[0])
        min_x = int(args[1])
        min_y = int(args[2])
        max_x = int(args[3])
        max_y = int(args[4])
    except ValueError:
        send_message(bot, chat_id, "Plot ID and rectangle bounds must be integers!")
        return

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    result = plot.generate_plot(zoom_x_min=min_x, zoom_y_min=min_y, zoom_x_max=max_x, zoom_y_max=max_y)

    if result is None:
        return

    if result[0] == 1:
        send_message(bot, chat_id, result[1])
        return
    elif result[0] == 0:
        bot.send_photo(chat_id=chat_id, photo=result[1])


def handle_error(bot, update, error):
    try:
        raise error
    except TelegramError:
        logging.getLogger(__name__).warning('Telegram Error! %s caused by this update: %s', error, update)


if __name__ == "__main__":
    pp = PicklePersistence(filename="plotyourselfbot")
    bot = telegram.Bot(token=TOKEN)
    updater = Updater(token=TOKEN, persistence=pp)
    dispatcher = updater.dispatcher

    static_commands = ["start", "help", "patchnotes"]
    for c in static_commands:
        dispatcher.add_handler(static_handler(c))

    create_plot_aliases = ["createplot", "crp"]
    plot_me_aliases = ["plotme", "pm", "plot"]
    remove_me_aliases = ["removeme", "rm", "begone"]
    remove_plot_aliases = ["removeplot", "rp", "begoneplot"]
    show_plot_aliases = ["showplot", "sp", "lookatthisgraph"]
    list_plots_aliases = ["listplots", "lp"]
    get_plot_stats_aliases = ["getplotstats", "plotstats", "ps"]
    polyfit_plot_aliases = ["polyfitplot", "pp"]
    whomademe_aliases = ["whomademe", "who", "w"]
    custom_point_aliases = ["custompoint", "cp", "dk"]
    boxed_plot_aliases = ["boxedplot", "bp"]
    lookup_aliases = ["lookup", "l", "wheremst"]
    setup_bet_aliases = ["setupbet", "sb"]
    my_bet_aliases = ["bet", "mybet", "mb", "putitallonblack", "putitallonred"]
    cancel_bet_aliases = ["cancelbet"]
    complete_bet_aliases = ["completebet", "cb", "rollthedice"]
    scoreboard_aliases = ["scoreboard", "tellmeimwinning", "scores", "tops"]
    equation_aliases = ["equation", "eq", "fuckrounding"]
    edit_plot_aliases = ["editplot", "ep"]
    current_bet_aliases = ["currentbet", "curbet", "curbit", "curb", "youmangycur"]
    alignment_chart_aliases = ["alignmentchart", "ac"]
    archive_aliases = ["archive", "ap"]
    unarchive_aliases = ["unarchive", "uap"]
    full_list_plots_aliases = ["fulllistplots", "flp"]
    my_plots_aliases = ["myplots", "mp"]
    archive_all_aliases = ["archiveall", "aap"]
    unarchive_all_aliases = ["unarchiveall", "uapp"]
    last_updated_aliases = ["lastupdated", "lup"]
    whosplotted_aliases = ["whosplotted", "whoops", "wps"]
    triangle_plot_aliases = ["triangleplot", "tp"]
    zoom_aliases = ["zoom", "z", "sonic", "sanic"]
    commands = [("create_plot", 2, create_plot_aliases),
                ("plot_me", 2, plot_me_aliases),
                ("remove_me", 2, remove_me_aliases),
                ("remove_plot", 2, remove_plot_aliases),
                ("show_plot", 2, show_plot_aliases),
                ("list_plots", 1, list_plots_aliases),
                ("get_plot_stats", 2, get_plot_stats_aliases),
                ("polyfit_plot", 2, polyfit_plot_aliases),
                ("whomademe", 2, whomademe_aliases),
                ("custom_point", 2, custom_point_aliases),
                ("boxed_plot", 2, boxed_plot_aliases),
                ("lookup", 2, lookup_aliases),
                ("setup_bet", 2, setup_bet_aliases),
                ("my_bet", 2, my_bet_aliases),
                ("cancel_bet", 1, cancel_bet_aliases),
                ("complete_bet", 1, complete_bet_aliases),
                ("scoreboard", 1, scoreboard_aliases),
                ("equation", 2, equation_aliases),
                ("edit_plot", 2, edit_plot_aliases),
                ("current_bet", 1, current_bet_aliases),
                ("alignment_chart", 2, alignment_chart_aliases),
                ("archive", 2, archive_aliases),
                ("unarchive", 2, unarchive_aliases),
                ("full_list_plots", 1, full_list_plots_aliases),
                ("my_plots", 1, my_plots_aliases),
                ("archive_all", 1, archive_all_aliases),
                ("unarchive_all", 1, unarchive_all_aliases),
                ("last_updated", 2, last_updated_aliases),
                ("whos_plotted", 2, whosplotted_aliases),
                ("triangle_plot", 2, triangle_plot_aliases),
                ("zoom", 2, zoom_aliases)]
    for c in commands:
        func = locals()[c[0] + "_handler"]
        if c[1] == 0:
            dispatcher.add_handler(CommandHandler(c[2], func, pass_args=True))
        elif c[1] == 1:
            dispatcher.add_handler(CommandHandler(c[2], func, pass_chat_data=True))
        elif c[1] == 2:
            dispatcher.add_handler(CommandHandler(c[2], func, pass_chat_data=True, pass_args=True))
        elif c[1] == 3:
            dispatcher.add_handler(CommandHandler(c[2], func, pass_chat_data=True, pass_user_data=True))

    dispatcher.add_error_handler(handle_error)

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO, filename='logging.txt', filemode='a+')

    #updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
    #updater.bot.set_webhook("https://plot-yourself-bot.herokuapp.com/" + TOKEN)

    updater.start_polling()
    updater.idle()
