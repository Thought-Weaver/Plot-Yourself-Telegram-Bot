# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import telegram
from telegram.ext import Updater, CommandHandler, PicklePersistence
from telegram.error import TelegramError
import logging

import os
import argparse

from plot import Plot

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
    username = update.message.from_user.username

    plot_args = vars(ARG_PARSER.parse_args(args))

    if len(plot_args.keys()) > 9:
        send_message(bot, chat_id, "usage (all args optional): /createplot {title} {x_axis_right_label} "
                                   "{x_axis_left_label} {y_axis_top_label} {y_axis_bottom_label}"
                                   "{min_x_value} {max_x_value} {min_y_value} {max_y_value}")
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

    plot = Plot(" ".join(plot_args.get("title", "")),
                " ".join(plot_args.get("xright", "")),
                " ".join(plot_args.get("xleft", "")),
                " ".join(plot_args.get("ytop", "")),
                " ".join(plot_args.get("ybottom", "")),
                plot_args.get("minx"),
                plot_args.get("maxx"),
                plot_args.get("miny"),
                plot_args.get("maxy"),
                username)
    chat_data[len(chat_data.keys()) + 1] = plot

    send_message(bot, chat_id, str(" ".join(plot_args.get("title", ""))) + " (" + str(len(chat_data.keys())) + ") was created successfully!")


def remove_plot_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id

    if len(args) != 1:
        send_message(bot, chat_id, "usage: /removeplot {plot_id}")
        return

    try:
        plot_id = int(args[0])
    except TypeError:
        send_message(bot, chat_id, "The plot ID must be a number!")
        return

    plot = chat_data.get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot doesn't exist!")
        return

    del chat_data[plot_id]


def plot_me_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    username = update.message.from_user.username

    # Args are: plot_id, x, y
    if len(args) != 3:
        send_message(bot, chat_id, "usage: /plotme {plot_id} {x} {y}")
        return

    try:
        plot_id = int(args[0])
        x = int(args[1])
        y = int(args[2])
    except TypeError:
        send_message(bot, chat_id, "All input arguments must be integers!")
        return

    plot = chat_data.get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot doesn't exist!")
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
    username = update.message.from_user.username

    # Args are: plot_id
    if len(args) != 1:
        send_message(bot, chat_id, "usage: /removeme {plot_id}")
        return

    try:
        plot_id = int(args[0])
    except TypeError:
        send_message(bot, chat_id, "The plot ID must be a number!")
        return

    plot = chat_data.get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot doesn't exist!")
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
            send_message(bot, chat_id, result[1])
            return
        elif img[0] == 0:
            bot.send_photo(chat_id=chat_id, photo=result[1])


def show_plot_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id

    # Args are: plot_id
    if len(args) != 1:
        send_message(bot, chat_id, "usage: /showplot {plot_id}")
        return

    try:
        plot_id = int(args[0])
    except TypeError:
        send_message(bot, chat_id, "The plot ID must be a number!")
        return

    plot = chat_data.get(plot_id)

    if plot is None:
        send_message(bot, chat_id, "That plot doesn't exist!")
        return

    result = plot.generate_plot()

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
        text += "(" + str(key) + "): " + str(chat_data[key].get_name())
    send_message(bot, chat_id, text)


def edit_plot_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    username = update.message.from_user.username


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

    static_commands = ["help"]
    for c in static_commands:
        dispatcher.add_handler(static_handler(c))

    create_plot_aliases = ["createplot", "cp"]
    plot_me_aliases = ["plotme", "pm", "plot"]
    remove_me_aliases = ["removeme", "rm", "begone"]
    remove_plot_aliases = ["removeplot", "rp"]
    show_plot_aliases = ["showplot", "sp"]
    list_plots_aliases = ["listplots", "lp"]
    commands = [("create_plot", 2, create_plot_aliases),
                ("plot_me", 2, plot_me_aliases),
                ("remove_me", 2, remove_me_aliases),
                ("remove_plot", 2, remove_plot_aliases),
                ("show_plot", 2, show_plot_aliases),
                ("list_plots", 1, list_plots_aliases)]
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