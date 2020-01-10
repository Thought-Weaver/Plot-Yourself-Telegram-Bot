# -*- coding: utf-8 -*-
#!/usr/bin/env python3
from __future__ import unicode_literals

import telegram
from telegram.ext import Updater, CommandHandler, PicklePersistence
from telegram.error import TelegramError, Unauthorized
import logging

import os
import argparse
from collections import Counter, OrderedDict
import datetime
from operator import itemgetter

from plot import Plot, BoxedPlot, AlignmentChart, TrianglePlot, RadarPlot

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
ARG_PARSER.add_argument("-l", "--labels", type=str, action="append", nargs='*')

pp = PicklePersistence(filename="plotyourselfbot", on_flush=False)

def send_message(bot, chat_id, text):
    try:
        # print(text)
        bot.send_message(chat_id=chat_id, text=text)
    except TelegramError as e:
        raise e


def get_username(user):
    """
    Given a Telegram user object, return the username.
    :param user: A Telegram user object.
    :return: A string of the user's username, if it exists, else an empty string.
    """
    username = ""
    if user.username is not None:
        username = user.username
    else:
        if user.first_name is not None:
            username = user.first_name + " "
        if user.last_name is not None:
            username += user.last_name
    return username


def static_handler(command):
    """
    Sends the relevant text for a static command -- that is, a comamnd with a constant return value.
    :param command: A string for the command name.
    :return: A command handler for the Telegram bot.
    """
    text = open("static_responses/{}.txt".format(command), "r").read()
    if command == "help":
        text2 = open("static_responses/help2.txt", "r").read()
        return CommandHandler(command,
                              lambda bot, update: [send_message(bot, update.message.from_user.id, text),
                                                   send_message(bot, update.message.from_user.id, text2)])

    return CommandHandler(command,
        lambda bot, update: send_message(bot, update.message.chat.id, text))


def create_plot_handler(bot, update, chat_data, args):
    """
    Creates a standard xy-plot.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A possibly empty list of arguments for constructing the plot.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

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

    if len(args) == 0:
        send_message(bot, chat_id, "You have created an empty plot (" + str(max_key + 1) + ") successfully!")

    plot = Plot(" ".join(plot_args.get("title")) if plot_args.get("title") is not None else None,
                " ".join(plot_args.get("xleft")) if plot_args.get("xleft") is not None else None,
                " ".join(plot_args.get("xright")) if plot_args.get("xright") is not None else None,
                " ".join(plot_args.get("ybottom")) if plot_args.get("ybottom") is not None else None,
                " ".join(plot_args.get("ytop")) if plot_args.get("ytop") is not None else None,
                plot_args.get("minx") if plot_args.get("minx") is not None else -10,
                plot_args.get("maxx") if plot_args.get("maxx") is not None else 10,
                plot_args.get("miny") if plot_args.get("miny") is not None else -10,
                plot_args.get("maxy") if plot_args.get("maxy") is not None else 10,
                (username, user.id),
                max_key + 1,
                plot_args.get("custompoints") if plot_args.get("custompoints") is not None else False)
    chat_data["plots"][max_key + 1] = plot

    send_message(bot, chat_id, str(" ".join(plot_args.get("title", ""))) +
                                   " (" + str(max_key + 1) + ") was created successfully!")

    show_plot_handler(bot, update, chat_data, [max_key + 1])


def remove_plot_handler(bot, update, chat_data, args):
    """
    Removes a plot from the chat data.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing an integer ID for a plot.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

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

    if not isinstance(plot.get_creator(), tuple) and str(plot.get_creator()) == str(username):
        plot.set_creator(username, user.id)
    if not isinstance(plot.get_creator(), tuple) and str(plot.get_creator()) != str(username):
        send_message(bot, chat_id, "You didn't make that plot (" + str(plot_id) + ")!")
        return

    if str(plot.get_creator()[1]) != str(user.id):
        send_message(bot, chat_id, "You didn't make that plot (" + str(plot_id) + ")!")
        return

    del chat_data["plots"][plot_id]
    if chat_data.get("archived") is not None and chat_data["archived"].get(plot_id) is not None:
        del chat_data["archived"][plot_id]
    send_message(bot, chat_id, "Plot (" + str(plot_id) + ") has been removed!")
    telegram.ext.PicklePersistence.flush(pp)


def plot_me_handler(bot, update, chat_data, args):
    """
    Plots a user at a specified point.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing a plot ID, an x and y coordinate, and possibly error values for x and y.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

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

    if isinstance(plot, RadarPlot):
        send_message(bot, chat_id, "You can't do that on radar plots!")
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
    telegram.ext.PicklePersistence.flush(pp)


def remove_me_handler(bot, update, chat_data, args):
    """
    Removes the user from a plot.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing a plot ID.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

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
    telegram.ext.PicklePersistence.flush(pp)


def show_plot_handler(bot, update, chat_data, args):
    """
    Sends a message with the image of the plot with the input ID.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing a plot ID.
    """
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
        if not toggle_labels and isinstance(plot, RadarPlot):
            bot.send_animation(chat_id=chat_id, animation=result[1])
            return
        bot.send_photo(chat_id=chat_id, photo=result[1])
    telegram.ext.PicklePersistence.flush(pp)


def list_plots_handler(bot, update, chat_data):
    """
    Sends a message with a list of all unarchived plots in the chat.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    """
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id

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

    try:
        send_message(bot, user_id, text)
    except Unauthorized as u:
        send_message(bot, chat_id, "You haven't sent a DM to the bot and thus cannot receive DMs!")


def full_list_plots_handler(bot, update, chat_data):
    """
    Sends a message with a list of all plots in the chat.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    """
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}

    text = "All plots:\n\n"
    for (key, value) in OrderedDict(sorted(chat_data["plots"].items())).items():
        if isinstance(key, int):
            text += "(" + str(key) + "): " + str(value.get_name()) + "\n"

    try:
        send_message(bot, user_id, text)
    except Unauthorized as u:
        send_message(bot, chat_id, "You haven't sent a DM to the bot and thus cannot receive DMs!")


def get_plot_stats_handler(bot, update, chat_data, args):
    """
    Get descriptive statistics for the data on a plot with the input ID.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing a plot ID.
    """
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

    if isinstance(plot, RadarPlot):
        send_message(bot, chat_id, "You can't do that on radar plots!")
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
    """
    Fit a curve with the input degree to the plot with the input ID.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing a plot ID, an optional degree (default: 1), and a value for toggling labels.
    """
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

    if isinstance(plot, RadarPlot):
        send_message(bot, chat_id, "You can't do that on radar plots!")
        return

    if deg < 0:
        send_message(bot, chat_id, "Degree must be non-negative!")
        return

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
    """
    Send a message with who made the plot with the input ID.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing a plot ID.
    """
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

    if not isinstance(plot.get_creator(), tuple):
        send_message(bot, chat_id, "Plot (" + str(plot_id) + ") was made by: " + str(plot.get_creator()))
        return

    send_message(bot, chat_id, "Plot (" + str(plot_id) + ") was made by: " + str(plot.get_creator()[0]))


def custom_point_handler(bot, update, chat_data, args):
    """
    Plot a point with a custom label on the plot with the input ID.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing a plot ID, x and y coordinate, and a label.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

    # Args are: plot_id, x, y, label
    if len(args) < 4:
        send_message(bot, chat_id, "usage: /custompoint {plot_id} {x} {y} {label}")
        return

    try:
        plot_id = int(args[0])
        x = float(args[1])
        y = float(args[2])
        label = " ".join(args[3:])
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

    if not isinstance(plot.get_creator(), tuple) and str(plot.get_creator()) == str(username):
        plot.set_creator(username, user.id)

    if str(plot.get_creator()[1]) != str(user.id):
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

    telegram.ext.PicklePersistence.flush(pp)


def boxed_plot_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

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
        " ".join(plot_args.get("vert2")) if plot_args.get("vert2") is not None else "",
        " ".join(plot_args.get("vert1")) if plot_args.get("vert1") is not None else ""
    ]

    max_key = max(chat_data["plots"].keys()) if len(chat_data["plots"].keys()) > 0 else 0

    if len(args) == 0:
        send_message(bot, chat_id, "You have created an empty plot (" + str(max_key + 1) + ") successfully!")

    plot = BoxedPlot(" ".join(plot_args.get("title")) if plot_args.get("title") is not None else None,
                horiz,
                vert,
                (username, user.id),
                max_key + 1,
                plot_args.get("custompoints") if plot_args.get("custompoints") is not None else False)
    chat_data["plots"][max_key + 1] = plot

    send_message(bot, chat_id, str(" ".join(plot_args.get("title", ""))) +
                                   " (" + str(max_key + 1) + ") was created successfully!")

    show_plot_handler(bot, update, chat_data, [max_key + 1])


def lookup_handler(bot, update, chat_data, args):
    """
    Send a message with the location of the person with the input name on the plot with the input ID.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing a plot ID and a name.
    """
    chat_id = update.message.chat.id

    # Args are: plot_id, name (assume no spaces, will set lowercase)
    if len(args) < 2:
        send_message(bot, chat_id, "usage: /lookup {plot_id} {name}")
        return

    try:
        plot_id = int(args[0])
        name = " ".join(args[1:])
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
        vals_str = ", ".join([str(x) for x in result[1]])
        send_message(bot, chat_id, name + " exists at (" + vals_str + ").")
        return


def my_bet_handler(bot, update, chat_data, args):
    """
    Input the correlation bet of the user for the current bet.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing the R^2 value to bet.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

    if chat_data.get("current_bet") is None:
        send_message(bot, chat_id, "No bet currently exists!")
        return

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
    chat_data["current_bet"]["bets"][(username, user.id)] = R2
    send_message(bot, chat_id, "Your bet has been placed!")
    telegram.ext.PicklePersistence.flush(pp)


def setup_bet_handler(bot, update, chat_data, args):
    """
    Create a new correlation bet for the given plot and polynomial degree.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing the plot ID and the degree of the polynomial.
    """
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

    if isinstance(chat_data["plots"], RadarPlot):
        send_message(bot, chat_id, "You can't do that on radar plots!")
        return

    if degree < 0:
        send_message(bot, chat_id, "Degree must be non-negative!")
        return

    if len(chat_data["plots"][plot_id].get_points()) <= 1:
        send_message(bot, chat_id, "The plot must have at least two points.")
        return

    chat_data["current_bet"] = { "plot_id" : plot_id,
                                 "degree"  : degree,
                                 "bets"    : OrderedDict(),
                                 "created_at" : str(datetime.datetime.now()) }
    send_message(bot, chat_id, "The following bet was created:\n\nPlot ID: " +
                 str(chat_data["current_bet"]["plot_id"]) + "\nDegree: " +
                 str(chat_data["current_bet"]["degree"]))
    telegram.ext.PicklePersistence.flush(pp)


def cancel_bet_handler(bot, update, chat_data):
    """
    Cancels the current bet, if it exists.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    """
    chat_id = update.message.chat.id

    if chat_data.get("current_bet") is None:
        send_message(bot, chat_id, "No bet currently exists!")
        return

    chat_data["current_bet"] = None
    send_message(bot, chat_id, "The bet has been canceled.")
    telegram.ext.PicklePersistence.flush(pp)


def complete_bet_handler(bot, update, chat_data):
    """
    Determines the winner of the current bet.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    """
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

    if chat_data.get("all_user_bet_data") is None:
        chat_data["all_user_bet_data"] = {}

    if result[0] == 1:
        send_message(bot, chat_id, result[1])
        return
    elif result[0] == 0:
        best = ""
        best_id = 0
        bestr2 = 0
        best_diff = 2e30
        for (username, user_id), value in chat_data["current_bet"]["bets"].items():
            diff = abs(value - result[1][1])

            if chat_data["all_user_bet_data"].get(user_id) is None:
                chat_data["all_user_bet_data"][user_id] = {
                    "total_wins" : 0,
                    "win_keys" : [],
                    "total_bets" : 0,
                    "avg_diff" : 0,
                    "win_avg_diff" : 0,
                    "bets" : {}
                }

            # We update the user's running average of diffs, then store the bet info in the user data for easy reference.
            chat_data["all_user_bet_data"][user_id]["avg_diff"] *= chat_data["all_user_bet_data"][user_id]["total_bets"]
            chat_data["all_user_bet_data"][user_id]["total_bets"] += 1
            chat_data["all_user_bet_data"][user_id]["avg_diff"] += diff
            chat_data["all_user_bet_data"][user_id]["avg_diff"] /= chat_data["all_user_bet_data"][user_id]["total_bets"]
            chat_data["all_user_bet_data"][user_id]["bets"][chat_data["current_bet"]["created_at"]] = {
                "plot_id" : chat_data["current_bet"]["plot_id"],
                "degree"  : chat_data["current_bet"]["degree"],
                "bet"     : value
            }

            if diff < best_diff:
                best_diff = diff
                best = username
                best_id = user_id
                bestr2 = value

        bot.send_photo(chat_id=chat_id, photo=result[1][0])
        send_message(bot, chat_id, "Actual R^2: " + str(result[1][1]))
        send_message(bot, chat_id, "Winner: " + best + " with R^2 = " + str(bestr2) + "!")

        if chat_data.get("scoreboard") is None:
            chat_data["scoreboard"] = {}
        if chat_data.get("scoreboard_avg") is None:
            chat_data["scoreboard_avg"] = {}

        if chat_data["scoreboard"].get((best, best_id)) is None:
            chat_data["scoreboard"][(best, best_id)] = 1
        else:
            chat_data["scoreboard"][(best, best_id)] += 1

        if chat_data["scoreboard_avg"].get((best, best_id)) is None:
            chat_data["scoreboard_avg"][(best, best_id)] = best_diff
        else:
            # sum(x_i) / (n - 1) is currently stored.
            # (sum(x_i) + y) / n (n - 1) / (n - 1) clearly gives desired result.
            chat_data["scoreboard_avg"][(best, best_id)] *= chat_data["scoreboard"][(best, best_id)] - 1
            chat_data["scoreboard_avg"][(best, best_id)] += best_diff
            chat_data["scoreboard_avg"][(best, best_id)] /= chat_data["scoreboard"][(best, best_id)]

        # Update the best user's wins and win avg diff. Add the key of this win for easy lookup in the user's bets.
        chat_data["all_user_bet_data"][best_id]["win_avg_diff"] = chat_data["scoreboard_avg"][(best, best_id)]
        chat_data["all_user_bet_data"][best_id]["total_wins"] += 1
        chat_data["all_user_bet_data"][best_id]["win_keys"].append(chat_data["current_bet"]["created_at"])

        if chat_data.get("all_bets") is None:
            chat_data["all_bets"] = {}

        # Store the current bet into the history. Also add winner data and actual R^2 to the bet.
        chat_data["all_bets"][chat_data["current_bet"]["created_at"]] = chat_data["current_bet"]
        chat_data["all_bets"][chat_data["current_bet"]["created_at"]]["winner"] = best
        chat_data["all_bets"][chat_data["current_bet"]["created_at"]]["winner_id"] = best_id
        chat_data["all_bets"][chat_data["current_bet"]["created_at"]]["winner_value"] = bestr2
        chat_data["all_bets"][chat_data["current_bet"]["created_at"]]["actual_value"] = result[1][1]

    # Reset the current bet.
    chat_data["current_bet"] = None
    telegram.ext.PicklePersistence.flush(pp)


def scoreboard_handler(bot, update, chat_data):
    """
    Sends a message with the betting scoreboard.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    """
    chat_id = update.message.chat.id

    if chat_data.get("scoreboard") is None:
        send_message(bot, chat_id, "No scoreboard exists!")
        return

    scoreboard = chat_data["scoreboard"]
    highest = Counter(scoreboard).most_common(3)

    text = "Top 3 Scoreboard:\n\n"
    for i in range(len(highest)):
        # Just in case, somehow, someone exists in scoreboard but not avg.
        if chat_data["scoreboard_avg"].get(highest[i][0]) is None:
            chat_data["scoreboard_avg"][highest[i][0]] = 0
        highest[i] = (highest[i][0],
                      highest[i][1],
                      chat_data["scoreboard_avg"][highest[i][0]])
    highest.sort(key=lambda x: (-x[1], x[2]))

    for x in highest:
        text += str(x[0][0]) + ": " + str(x[1]) + " with Avg Diff: " + \
                str(chat_data["scoreboard_avg"][x[0]]) + "\n"

    send_message(bot, chat_id, text)


def equation_handler(bot, update, chat_data, args):
    """
    Get the equation of a polynomial for the plot matching the input ID.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing the plot ID and the degree of the polynomial.
    """
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

    if isinstance(plot, RadarPlot):
        send_message(bot, chat_id, "You can't do that on radar plots!")
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
    """
    Edits the parameters for the plot matching the input ID, if the creator used the handler.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list of unix-esque plot arguments to be parsed.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

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

    if not isinstance(plot.get_creator(), tuple) and str(plot.get_creator()) == str(username):
        plot.set_creator(username, user.id)

    if str(plot.get_creator()[1]) != str(user.id):
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
    telegram.ext.PicklePersistence.flush(pp)


def current_bet_handler(bot, update, chat_data, args):
    """
    Sends a message with the current bet status, listing participants and their bets.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A possibly empty list containing an integer specifying a sort method.
    """
    chat_id = update.message.chat.id

    if chat_data.get("current_bet") is None:
        send_message(bot, chat_id, "No bet currently exists!")
        return

    # Args are: {optional sort method}
    if len(args) > 1:
        send_message(bot, chat_id, "usage: /currentbet {optional sort method}")
        return

    try:
        sortby = int(args[0]) if len(args) == 1 else 0
    except ValueError:
        send_message(bot, chat_id, "Sorting method must be an int!")
        return

    send_message(bot, chat_id, "The following bet is in progress:\n\nPlot ID: " +
                 str(chat_data["current_bet"]["plot_id"]) + "\nDegree: " +
                 str(chat_data["current_bet"]["degree"]))

    if chat_data["current_bet"].get("bets") is None or len(chat_data["current_bet"]["bets"].keys()) == 0:
        send_message(bot, chat_id, "No one has yet placed a bet!")
        return

    sorted_dict = chat_data["current_bet"]["bets"]

    # If sortby <= 0, leave it as is.
    if sortby == 1:
        sorted_dict = OrderedDict(sorted(chat_data["current_bet"]["bets"].items(), key=itemgetter(0)))
    elif sortby >= 2:
        sorted_dict = OrderedDict(sorted(chat_data["current_bet"]["bets"].items(),
                                         key=itemgetter(1), reverse=True))

    text = "Current Bets:\n\n"
    for ((username, id), value) in sorted_dict.items():
        text += str(username) + ": " + str(value) + "\n"
    send_message(bot, chat_id, text)


def alignment_chart_handler(bot, update, chat_data, args):
    """
    Creates an alignment chart.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: The unix-esque arg list for making an alignment chart.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

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

    if len(args) == 0:
        send_message(bot, chat_id, "You have created an empty plot (" + str(max_key + 1) + ") successfully!")

    plot = AlignmentChart(" ".join(plot_args.get("title")) if plot_args.get("title") is not None else None,
                labels,
                (username, user.id),
                max_key + 1,
                plot_args.get("custompoints") if plot_args.get("custompoints") is not None else False)
    chat_data["plots"][max_key + 1] = plot

    send_message(bot, chat_id, str(" ".join(plot_args.get("title", ""))) +
                                   " (" + str(max_key + 1) + ") was created successfully!")

    show_plot_handler(bot, update, chat_data, [max_key + 1])


def archive_handler(bot, update, chat_data, args):
    """
    Archives a plot from the full list of plots.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing the plot ID to be archived.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

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

    if not isinstance(plot.get_creator(), tuple) and str(plot.get_creator()) == str(username):
        plot.set_creator(username, user.id)
    if not isinstance(plot.get_creator(), tuple) and str(plot.get_creator()) != str(username):
        send_message(bot, chat_id, "You didn't make that plot (" + str(plot_id) + ")!")
        return

    if str(plot.get_creator()[1]) != str(user.id):
        send_message(bot, chat_id, "You didn't make that plot (" + str(plot_id) + ")!")
        return

    if chat_data.get("archived") is None:
        chat_data["archived"] = {}

    if plot_id in chat_data["archived"].keys():
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") has already been archived!")
        return

    chat_data["archived"][plot_id] = chat_data["plots"][plot_id]
    send_message(bot, chat_id, "Plot (" + str(plot_id) + ") has been archived!")
    telegram.ext.PicklePersistence.flush(pp)


def unarchive_handler(bot, update, chat_data, args):
    """
    Unarchives a plot from the archived list of plots.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing the plot ID to be unarchived.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

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

    if not isinstance(plot.get_creator(), tuple) and str(plot.get_creator()) == str(username):
        plot.set_creator(username, user.id)
    if not isinstance(plot.get_creator(), tuple) and str(plot.get_creator()) != str(username):
        send_message(bot, chat_id, "You didn't make that plot (" + str(plot_id) + ")!")
        return

    if str(plot.get_creator()[1]) != str(user.id):
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
    telegram.ext.PicklePersistence.flush(pp)


def my_plots_handler(bot, update, chat_data):
    """
    Sends a message to the caller with their created plots.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    user_id = user.id
    username = get_username(user)

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "No plots currently exist!")
        return

    text = "Your plots:\n\n"
    for (key, value) in chat_data["plots"].items():
        if isinstance(key, int):
            creator = value.get_creator()
            if isinstance(creator, tuple) and str(creator[1]) == str(user_id):
                text += "(" + str(key) + "): " + str(value.get_name()) + "\n"
            elif not isinstance(creator, tuple) and str(creator) == str(username):
                text += "(" + str(key) + "): " + str(value.get_name()) + "\n"
                value.set_creator(username, user_id)

    try:
        send_message(bot, user_id, text)
    except Unauthorized as u:
        send_message(bot, chat_id, "You haven't sent a DM to the bot and thus cannot receive DMs!")


def archive_all_handler(bot, update, chat_data):
    """
    Archives all the caller's plots.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "No plots currently exist!")
        return

    if chat_data.get("archived") is None:
        chat_data["archived"] = {}

    for (key, value) in chat_data["plots"].items():
        if isinstance(key, int) and key not in chat_data["archived"].keys():
            creator = value.get_creator()
            if isinstance(creator, tuple) and str(creator[1]) == str(user.id):
                chat_data["archived"][key] = value
            elif not isinstance(creator, tuple) and str(creator) == str(username):
                chat_data["archived"][key] = value
                value.set_creator(username, user.id)

    send_message(bot, chat_id, "Your plots have been archived.")
    telegram.ext.PicklePersistence.flush(pp)


def unarchive_all_handler(bot, update, chat_data):
    """
    Unarchives all the caller's plots.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "No plots currently exist!")
        return

    if chat_data.get("archived") is None:
        chat_data["archived"] = {}

    for (key, value) in chat_data["plots"].items():
        if isinstance(key, int) and key in chat_data["archived"].keys():
            creator = value.get_creator()
            if isinstance(creator, tuple) and str(creator[1]) == str(user.id):
                del chat_data["archived"][key]
            elif not isinstance(creator, tuple) and str(creator) == str(username):
                del chat_data["archived"][key]
                value.set_creator(username, user.id)

    send_message(bot, chat_id, "Your plots have been unarchived.")
    telegram.ext.PicklePersistence.flush(pp)


def last_updated_handler(bot, update, chat_data, args):
    """
    Get the time when the plot with the matching ID was last changed.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing the plot ID.
    """
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
    """
    Sends a message with the list of people plotted on the plot with the matching input ID.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing the plot ID.
    """
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
        if isinstance(plot, RadarPlot):
            if len(p[1]) >= 2:
                vals_str = ", ".join([str(x) for x in p[1][::-1][-1:] + p[1][::-1][:-1]])
            else:
                vals_str = ", ".join([str(x) for x in p[1]])
            text += str(p[0]) + ": (" + vals_str + ")\n"
        else:
            text += str(p[0]) + ": (" + str(p[1]) + ", " + str(p[2]) + ")\n"
    send_message(bot, chat_id, text)


def triangle_plot_handler(bot, update, chat_data, args):
    """
    Creates a triangle plot.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A unix-esque arg list for creating a triangle plot.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

    try:
        parsed = ARG_PARSER.parse_args(args)
        plot_args = vars(parsed)
    except SystemExit:
        send_message(bot, chat_id, "That is not a valid argument list. See /help.")
        return

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}

    max_key = max(chat_data["plots"].keys()) if len(chat_data["plots"].keys()) > 0 else 0

    if len(args) == 0:
        send_message(bot, chat_id, "You have created an empty plot (" + str(max_key + 1) + ") successfully!")

    plot = TrianglePlot(" ".join(plot_args.get("title")) if plot_args.get("title") is not None else None,
                " ".join(plot_args.get("xleft")) if plot_args.get("xleft") is not None else None,
                " ".join(plot_args.get("xright")) if plot_args.get("xright") is not None else None,
                " ".join(plot_args.get("ytop")) if plot_args.get("ytop") is not None else None,
                (username, user.id),
                max_key + 1,
                plot_args.get("custompoints") if plot_args.get("custompoints") is not None else False)
    chat_data["plots"][max_key + 1] = plot

    send_message(bot, chat_id, str(" ".join(plot_args.get("title", ""))) +
                                   " (" + str(max_key + 1) + ") was created successfully!")

    show_plot_handler(bot, update, chat_data, [max_key + 1])


def zoom_handler(bot, update, chat_data, args):
    """
    Sends a message with a specific rectangular area of a plot.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing a plot ID and the corner coordinates for a rectangle.
    """
    chat_id = update.message.chat.id

    if len(args) != 5:
        send_message(bot, chat_id, "usage: /zoom {plot_id} {min_x} {min_y} {max_x} {max_y}")
        return

    try:
        plot_id = int(args[0])
        min_x = float(args[1])
        min_y = float(args[2])
        max_x = float(args[3])
        max_y = float(args[4])
    except ValueError:
        send_message(bot, chat_id, "Plot ID must be an integer and rectangle bounds must be floats!")
        return

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    if isinstance(plot, RadarPlot):
        send_message(bot, chat_id, "You can't do that on radar plots!")
        return

    result = plot.generate_plot(zoom_x_min=min_x, zoom_y_min=min_y, zoom_x_max=max_x, zoom_y_max=max_y)

    if result is None:
        return

    if result[0] == 1:
        send_message(bot, chat_id, result[1])
        return
    elif result[0] == 0:
        bot.send_photo(chat_id=chat_id, photo=result[1])


def contour_handler(bot, update, chat_data, args):
    """
    Sends a message with a contour of the points as distances from the center of the data.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A possibly empty list containing a plot ID and a label toggle value.
    """
    chat_id = update.message.chat.id

    # Args are: {optional plot_id} {optional toggle for labels}
    if len(args) > 2:
        send_message(bot, chat_id, "usage: /contour {plot_id} {optional 0/1 toggle for labels}")
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

    if isinstance(plot, RadarPlot):
        send_message(bot, chat_id, "You can't do that on radar plots!")
        return

    if len(plot.get_points()) < 2:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") must have at least 2 points!")

    toggle_labels = True if toggle > 0 else False
    result = plot.generate_plot(toggle_labels=toggle_labels, contour=True)

    if result is None:
        return

    if result[0] == 1:
        send_message(bot, chat_id, result[1])
        return
    elif result[0] == 0:
        bot.send_photo(chat_id=chat_id, photo=result[1])


def my_bet_data_handler(bot, update, chat_data):
    """
    Sends the caller a message with the bets they've placed and their win data.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    user_id = user.id

    if chat_data.get("all_user_bet_data") is None:
        chat_data["all_user_bet_data"] = {}

    if chat_data["all_user_bet_data"].get(user_id) is None:
        send_message(bot, chat_id, "You don't have any bet data!")
        return

    text = "Your bet data:\n\n" + \
           "Total wins: " + str(chat_data["all_user_bet_data"][user_id].get("total_wins")) + "\n" + \
           "Total bets: " + str(chat_data["all_user_bet_data"][user_id].get("total_bets")) + "\n" +  \
           "Average Difference: " + str(chat_data["all_user_bet_data"][user_id].get("avg_diff")) + "\n" +  \
           "Winning Average Difference: " + str(chat_data["all_user_bet_data"][user_id].get("win_avg_diff"))

    try:
        send_message(bot, user_id, text)
    except Unauthorized as u:
        send_message(bot, chat_id, "You haven't sent a DM to the bot and thus cannot receive DMs!")


def bet_history_handler(bot, update, chat_data):
    """
    Sends the caller a message with the history of all bets made in that chat.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    user_id = user.id

    if chat_data.get("all_bets") is None:
        send_message(bot, chat_id, "There haven't been any bets yet!")
        return

    text = "All bets:\n\n"
    for key in chat_data["all_bets"].keys():
        text += "Created At: " + key + \
                "\nPlot ID: " + str(chat_data["all_bets"][key].get("plot_id")) + \
                "\nDegree: " + str(chat_data["all_bets"][key].get("degree")) + \
                "\nWinner: " + str(chat_data["all_bets"][key].get("winner")) + \
                "\nWinner R^2: " + str(chat_data["all_bets"][key].get("winner_value")) + \
                "\nActual R^2: " + str(chat_data["all_bets"][key].get("actual_value"))
        text += "\n\nBets:\n\n"
        for ((username, id), value) in chat_data["all_bets"][key]["bets"].items():
            text += str(username) + ": " + str(value) + "\n"
        text += "\n---\n\n"

        # Send and reset.
        try:
            send_message(bot, user_id, text)
        except Unauthorized as u:
            send_message(bot, chat_id, "You haven't sent a DM to the bot and thus cannot receive DMs!")
            break
        text = ""


def percent_plot_me_handler(bot, update, chat_data, args):
    """
    Plots the caller at that percent value of the limits of the plot.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing a plot ID and the percent values.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

    # Assume that percent_x and percent_y are entered out of 100.
    if len(args) < 2 or len(args) > 5:
        send_message(bot, chat_id, "usage: /percentplotme {plot_id} {percent x} {percent y} {err_x} {err_y}")
        return

    if chat_data.get("archived") is None:
        chat_data["archived"] = {}

    try:
        # Select the most recent (max) key from plots that aren't archived by default.
        plot_id = int(args[0]) if len(args) >= 3 else int(max({k: v for k, v in chat_data["plots"].items()
                                                               if k not in chat_data["archived"]}.keys()))
        percent_x = float(args[1] if len(args) >= 3 else args[0])
        percent_y = float(args[2] if len(args) >= 3 else args[1])
        err_x = float(args[3] if len(args) >= 4 else 0)
        err_y = float(args[4] if len(args) == 5 else 0)
    except ValueError:
        send_message(bot, chat_id, "Plot ID must be an int and percent x, percent y, err_x, err_y must be floats!")
        return

    if chat_data.get("plots") is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    if isinstance(plot, RadarPlot):
        send_message(bot, chat_id, "You can't do that on radar plots!")
        return

    # This check is technically unnecessary since the plot will catch out of bounds points,
    # but it gives the user a slightly more informative error message.
    if percent_x > 100 or percent_x < -100 or percent_y > 100 or percent_y < -100:
        send_message(bot, chat_id, "The percents entered must be within [-100, 100]!")
        return

    min_x = plot.get_minx()
    max_x = plot.get_maxx()
    min_y = plot.get_miny()
    max_y = plot.get_maxy()
    x = 0
    y = 0

    if percent_x >= 0:
        x = percent_x / 100 * max_x
    else:
        x = abs(percent_x) / 100 * min_x

    if not isinstance(plot, TrianglePlot):
        if percent_y >= 0:
            y = percent_y / 100 * max_y
        else:
            y = abs(percent_y) / 100 * min_y
    else:
        height = max_y - min_y
        dist_abs_diff = 1 - (abs(max_x / 2 - x) / (max_x / 2))
        y = dist_abs_diff * height * percent_y / 100

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
    telegram.ext.PicklePersistence.flush(pp)


def radar_plot_handler(bot, update, chat_data, args):
    """
    Creates a radar plot.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A unix-esque arg list for creating a radar plot.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

    try:
        parsed = ARG_PARSER.parse_args(args)
        plot_args = vars(parsed)
    except SystemExit:
        send_message(bot, chat_id, "That is not a valid argument list. See /help.")
        return

    if chat_data.get("plots") is None:
        chat_data["plots"] = {}

    max_key = max(chat_data["plots"].keys()) if len(chat_data["plots"].keys()) > 0 else 0

    if len(args) == 0:
        send_message(bot, chat_id, "You have created an empty plot (" + str(max_key + 1) + ") successfully!")

    plot = RadarPlot(" ".join(plot_args.get("title")) if plot_args.get("title") is not None else None,
                plot_args.get("labels") if plot_args.get("labels") is not None else [""],
                (username, user.id),
                max_key + 1)
    chat_data["plots"][max_key + 1] = plot

    send_message(bot, chat_id, str(" ".join(plot_args.get("title", ""))) +
                                   " (" + str(max_key + 1) + ") was created successfully!")

    show_plot_handler(bot, update, chat_data, [max_key + 1])


def radar_plot_me_handler(bot, update, chat_data, args):
    """
    Plots the caller on a radar plot with the matching ID.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing a plot ID and the values for plotting.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

    # Args are: plot_id, values
    if len(args) < 2:
        send_message(bot, chat_id, "usage: /plotmeradar {plot_id} {value1} ...")
        return

    if chat_data.get("archived") is None:
        chat_data["archived"] = {}

    try:
        # Select the most recent (max) key from plots that aren't archived by default.
        plot_id = int(args[0])
        values = [float(f) for f in args[1:]]
    except ValueError:
        send_message(bot, chat_id, "Plot ID must be an int and the value list must be floats!")
        return

    if chat_data.get("plots") is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    result = plot.plot_point(username, values)

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
    telegram.ext.PicklePersistence.flush(pp)


def plot_crowdsource_handler(bot, update, chat_data, args):
    """
    Add a plot contribution for the specified label on the specified plot.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing a plot ID, a label, and the plotting values.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

    # Must have x, y values at least.
    if len(args) < 4:
        send_message(bot, chat_id, "usage: /plotcrowdsource {plot_id} {label} {vals}")
        return

    if chat_data.get("archived") is None:
        chat_data["archived"] = {}

    try:
        # Select the most recent (max) key from plots that aren't archived by default.
        plot_id = int(args[0])
        label = str(args[1])
        vals = [float(f) for f in args[2:]]
    except ValueError:
        send_message(bot, chat_id, "Plot ID must be an int, label must be a string, and vals must be floats!")
        return

    if label == username.replace(" ", ""):
        send_message(bot, chat_id, "You cannot crowdsource yourself!")
        return

    if chat_data.get("plots") is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    if isinstance(plot, RadarPlot):
        result = plot.add_crowdsource_point(user.id, label, vals)
    else:
        if len(vals) == 2:
            result = plot.add_crowdsource_point(user.id, label, vals[0], vals[1])
        else:
            send_message(bot, chat_id, "You need to specify both an x and y coordinate.")
            return

    if result is None:
        return

    send_message(bot, chat_id, result[1])
    telegram.ext.PicklePersistence.flush(pp)
    show_plot_handler(bot, update, chat_data, [plot_id])


def crowdsource_consent_handler(bot, update, chat_data, args):
    """
    Toggles the caller's consent to be crowdsourced on a plot with the matching input ID.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A possibly empty list containing a plot ID.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

    if len(args) > 1:
        send_message(bot, chat_id, "usage: /crowdsourceconsent {optional plot_id}")
        return

    if chat_data.get("archived") is None:
        chat_data["archived"] = {}

    try:
        # Select the most recent (max) key from plots that aren't archived by default.
        plot_id = int(args[0]) if len(args) == 1 else int(max({k:v for k, v in chat_data["plots"].items()
                                                               if k not in chat_data["archived"]}.keys()))
    except ValueError:
        send_message(bot, chat_id, "Plot ID must be an int!")
        return

    if chat_data.get("plots") is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    plot = chat_data["plots"].get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    result = plot.add_crowdsource_consent(user.id, username)

    if result is None:
        return

    send_message(bot, chat_id, result[1])
    telegram.ext.PicklePersistence.flush(pp)


def my_crowdsourced_points_handler(bot, update, chat_data, args):
    """
    Sends a message with the points making up the caller's crowdsource on a specified plot.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing a plot ID.
    """
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = get_username(user)

    if len(args) != 1:
        send_message(bot, chat_id, "usage: /mycrowdsourcedpoints {plot_id}")
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

    result = plot.get_crowdsourced_points(username)
    if result[0] == 1:
        send_message(bot, chat_id, result[1])
    else:
        items = result[1]
        text = ""
        for (id, value) in items:
            member = bot.get_chat_member(chat_id, id)
            member_username = member.user.username
            if member_username is None:
                if member.user.first_name is not None:
                    member_username = member.user.first_name + " "
                if user.last_name is not None:
                    member_username += member.user.last_name
            text += str(member_username) + ": " + str(value) + "\n"
        send_message(bot, chat_id, text)


def whos_crowdsourceable_handler(bot, update, chat_data, args):
    """
    Sends a message with the users who have consented to being crowdsourced on a plot.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param chat_data: The dictionary of data for the chat.
    :param args: A list containing a plot ID.
    """
    chat_id = update.message.chat.id

    if len(args) != 1:
        send_message(bot, chat_id, "usage: /whoscrowdsourceable {plot_id}")
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

    result = plot.whos_crowdsourceable()
    send_message(bot, chat_id, result[1])


def handle_error(bot, update, error):
    """
    Handle a Telegram or Python error. If a Telegram error, log it specically.
    :param bot: The Telegram bot for handling messages.
    :param update: The update data from the message, including the chat and user that sent it.
    :param error: The error to be raised.
    """
    try:
        raise error
    except TelegramError:
        logging.getLogger(__name__).warning('Telegram Error! %s caused by this update: %s', error, update)


if __name__ == "__main__":
    bot = telegram.Bot(token=TOKEN)
    updater = Updater(token=TOKEN, persistence=pp)
    dispatcher = updater.dispatcher

    static_commands = ["start", "help", "patchnotes", "kevinmemorial"]
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
    contour_aliases = ["contour", "cont", "ilikerings"]
    my_bet_data_aliases = ["mybetdata", "mbd"]
    bet_history_aliases = ["bethistory", "bh"]
    percent_plot_me_aliases = ["percentplotme", "ppm"]
    radar_plot_aliases = ["radarplot", "radp", "ilikecircles"]
    radar_plot_me_aliases = ["plotmeradar", "pmr", "helicoptersir"]
    plot_crowdsource_aliases = ["plotcrowdsource", "pc"]
    crowdsource_consent_aliases = ["crowdsourceconsent", "cc"]
    my_crowdsourced_points_aliases = ["mycrowdsourcedpoints", "mcp"]
    whos_crowdsourceable_aliases = ["whoscrowdsourceable", "wcs"]
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
                ("current_bet", 2, current_bet_aliases),
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
                ("zoom", 2, zoom_aliases),
                ("contour", 2, contour_aliases),
                ("my_bet_data", 1, my_bet_data_aliases),
                ("bet_history", 1, bet_history_aliases),
                ("percent_plot_me", 2, percent_plot_me_aliases),
                ("radar_plot", 2, radar_plot_aliases),
                ("radar_plot_me", 2, radar_plot_me_aliases),
                ("plot_crowdsource", 2, plot_crowdsource_aliases),
                ("crowdsource_consent", 2, crowdsource_consent_aliases),
                ("my_crowdsourced_points", 2, my_crowdsourced_points_aliases),
                ("whos_crowdsourceable", 2, whos_crowdsourceable_aliases)]
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
