# -*- coding: utf-8 -*-
#!/usr/bin/env python3
from __future__ import unicode_literals

import telegram
from telegram.ext import Updater, CommandHandler, PicklePersistence
from telegram.error import TelegramError
import logging

import os
import argparse
from collections import Counter

from plot import Plot, BoxedPlot

with open("api_key.txt", 'r') as f:
    TOKEN = f.read().rstrip()

PORT = int(os.environ.get('PORT', '8443'))

ARG_PARSER = argparse.ArgumentParser(description="The parser for creating plots.")
ARG_PARSER.add_argument("-t", "--title", type=str, nargs='*')
ARG_PARSER.add_argument("-xr", "--xright", type=str, nargs='*')
ARG_PARSER.add_argument("-xl", "--xleft", type=str, nargs='*')
ARG_PARSER.add_argument("-yt", "--ytop", type=str, nargs='*')
ARG_PARSER.add_argument("-yb", "--ybottom", type=str, nargs='*')
ARG_PARSER.add_argument("-mx", "--minx", type=int)
ARG_PARSER.add_argument("-Mx", "--maxx", type=int)
ARG_PARSER.add_argument("-my", "--miny", type=int)
ARG_PARSER.add_argument("-My", "--maxy", type=int)
ARG_PARSER.add_argument("--custompoints", action="store_true")

BOX_ARG_PARSER = argparse.ArgumentParser(description="The parser for creating plots.")
BOX_ARG_PARSER.add_argument("-t", "--title", type=str, nargs='*')
BOX_ARG_PARSER.add_argument("-h1", "--horiz1", type=str, nargs='*')
BOX_ARG_PARSER.add_argument("-h2", "--horiz2", type=str, nargs='*')
BOX_ARG_PARSER.add_argument("-h3", "--horiz3", type=str, nargs='*')
BOX_ARG_PARSER.add_argument("-v1", "--vert1", type=str, nargs='*')
BOX_ARG_PARSER.add_argument("-v2", "--vert2", type=str, nargs='*')
BOX_ARG_PARSER.add_argument("-v3", "--vert3", type=str, nargs='*')
BOX_ARG_PARSER.add_argument("-mx", "--minx", type=int)
BOX_ARG_PARSER.add_argument("-Mx", "--maxx", type=int)
BOX_ARG_PARSER.add_argument("-my", "--miny", type=int)
BOX_ARG_PARSER.add_argument("-My", "--maxy", type=int)
BOX_ARG_PARSER.add_argument("--custompoints", action="store_true")

def send_message(bot, chat_id, text):
    try:
        # print(text)
        bot.send_message(chat_id=chat_id, text=text)
    except TelegramError as e:
        raise e


def static_handler(command):
    text = open("static_responses/{}.txt".format(command), "r").read()

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

    if len(plot_args.keys()) > 10:
        send_message(bot, chat_id, "usage (all args optional): /createplot {title} {x_axis_right_label} "
                                   "{x_axis_left_label} {y_axis_top_label} {y_axis_bottom_label}"
                                   "{min_x_value} {max_x_value} {min_y_value} {max_y_value} {--custompoints}")
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

    plot = Plot(" ".join(plot_args.get("title")) if plot_args.get("title") is not None else None,
                " ".join(plot_args.get("xright")) if plot_args.get("xright") is not None else None,
                " ".join(plot_args.get("xleft")) if plot_args.get("xleft") is not None else None,
                " ".join(plot_args.get("ytop")) if plot_args.get("ytop") is not None else None,
                " ".join(plot_args.get("ybottom")) if plot_args.get("ybottom") is not None else None,
                plot_args.get("minx") if plot_args.get("minx") is not None else -10,
                plot_args.get("maxx") if plot_args.get("maxx") is not None else 10,
                plot_args.get("miny") if plot_args.get("miny") is not None else -10,
                plot_args.get("maxy") if plot_args.get("maxy") is not None else 10,
                username,
                plot_args.get("custompoints") if plot_args.get("custompoints") is not None else False)
    chat_data[len(chat_data.keys()) + 1] = plot

    send_message(bot, chat_id, str(" ".join(plot_args.get("title", ""))) + " (" + str(len(chat_data.keys())) + ") was created successfully!")


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

    plot = chat_data.get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    if str(plot.get_creator()) != str(username):
        send_message(bot, chat_id, "You didn't make that plot (" + str(plot_id) + ")!")
        return

    del chat_data[plot_id]
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

    # Args are: plot_id, x, y
    if len(args) != 3:
        send_message(bot, chat_id, "usage: /plotme {plot_id} {x} {y}")
        return

    try:
        plot_id = int(args[0])
        x = float(args[1])
        y = float(args[2])
    except ValueError:
        send_message(bot, chat_id, "Plot ID must be an int and x, y must be floats!")
        return

    plot = chat_data.get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot (" + str(plot_id) + ") doesn't exist!")
        return

    result = plot.plot_point(username, x, y)

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
    if len(args) != 1:
        send_message(bot, chat_id, "usage: /removeme {plot_id}")
        return

    try:
        plot_id = int(args[0])
    except ValueError:
        send_message(bot, chat_id, "The plot ID must be an integer!")
        return

    plot = chat_data.get(plot_id)

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


def show_plot_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id

    # Args are: plot_id {optional toggle for labels}
    if len(args) == 0 or len(args) > 2:
        send_message(bot, chat_id, "usage: /showplot {plot_id} {optional 0/1 toggle for labels}")
        return

    try:
        plot_id = int(args[0])
        toggle = 1 if len(args) != 2 else int(args[1])
    except ValueError:
        send_message(bot, chat_id, "The plot ID and optional toggle must be an integer!")
        return

    plot = chat_data.get(plot_id)

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

    text = "Current plots:\n\n"
    for key in chat_data.keys():
        if isinstance(key, int):
            text += "(" + str(key) + "): " + str(chat_data[key].get_name()) + "\n"
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

    plot = chat_data.get(plot_id)

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

    plot = chat_data.get(plot_id)

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

    plot = chat_data.get(plot_id)

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

    plot = chat_data.get(plot_id)

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
        parsed = BOX_ARG_PARSER.parse_args(args)
        plot_args = vars(parsed)
    except SystemExit:
        send_message(bot, chat_id, "That is not a valid argument list. See /help.")
        return

    if len(plot_args.keys()) > 12:
        send_message(bot, chat_id, "usage (all args optional): /boxedplot --title {title} "
                                   "--horiz2 {h1} --horiz2 {h2} --horiz3 {h3} "
                                   "--vert1 {v1} --vert2 {v2} --vert3 {v3} "
                                   "--xmin {xmin} --xmax {xmax} --ymin {ymin} --ymax {ymax} "
                                   "--custompoints")
        return

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

    plot = BoxedPlot(" ".join(plot_args.get("title")) if plot_args.get("title") is not None else None,
                horiz,
                vert,
                plot_args.get("minx") if plot_args.get("minx") is not None else -10,
                plot_args.get("maxx") if plot_args.get("maxx") is not None else 10,
                plot_args.get("miny") if plot_args.get("miny") is not None else -10,
                plot_args.get("maxy") if plot_args.get("maxy") is not None else 10,
                username,
                plot_args.get("custompoints") if plot_args.get("custompoints") is not None else False)
    chat_data[len(chat_data.keys()) + 1] = plot

    send_message(bot, chat_id, str(" ".join(plot_args.get("title", ""))) + " (" + str(len(chat_data.keys())) + ") was created successfully!")


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

    plot = chat_data.get(plot_id)

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

    if chat_data.get(plot_id) is None:
        send_message(bot, chat_id, "That plot does not exist!")
        return

    if degree < 0:
        send_message(bot, chat_id, "Degree must be non-negative!")
        return

    chat_data["current_bet"] = { "plot_id" : plot_id,
                                 "degree"  : degree,
                                 "bets"    : {} }
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

    plot = chat_data.get(chat_data["current_bet"]["plot_id"])
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
        for key in chat_data["current_bet"]["bets"].keys():
            diff = abs(chat_data["current_bet"]["bets"][key] - result[1][1])
            if diff < best_diff:
                best_diff = diff
                best = key
                bestr2 = chat_data["current_bet"]["bets"][key]

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
    for i in highest:
        if chat_data["scoreboard_avg"].get(str(i[0])) is None:
            chat_data["scoreboard_avg"][str(i[0])] = 0
        text += str(i[0]) + ": " + str(i[1]) + " with Avg Diff: " + str(chat_data["scoreboard_avg"][str(i[0])]) + "\n"

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

    plot = chat_data.get(plot_id)

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

    static_commands = ["help", "patchnotes"]
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
                ("equation", 2, equation_aliases)]
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
