# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import telegram
from telegram.ext import Updater, CommandHandler, PicklePersistence
from telegram.error import TelegramError
import logging

import os

from plot import Plot

with open("api_key.txt", 'r') as f:
    TOKEN = f.read().rstrip()

PORT = int(os.environ.get('PORT', '8443'))


def createplot_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id

    if len(args) <= 0:
        # Need a name
        pass

    if len(args) > 9:
        # Can't do this!
        pass

    # I have two options as I see it:
    # (1) Use a counter as the key for the plots and iterate to find the name every time someone plots or removes.
    # (2) Use the name as the key and prevent duplicates. This means plots have to have a name.

    if args[0] in chat_data.keys():
        # Can't have a duplicate name!
        pass

    # Args for plot definition (all are optional, except name in the current version):
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

    plot_args = [None for i in range(9)]
    for i in range(len(args)):
        plot_args[i] = None if args[i] == '_' else args[i]

    plot = Plot(plot_args[0],
                plot_args[1],
                plot_args[2],
                plot_args[3],
                plot_args[4],
                plot_args[5],
                plot_args[6],
                plot_args[7],
                plot_args[8])
    chat_data[args[0]] = plot

    # Ideally, we'll be able to save the entire
    # dictionary into a text file and load it
    # from there.


def removeplot_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id


def plotme_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id


def removeme_handler(bot, update, chat_data, args):
    chat_id = update.message.chat.id


def handle_error(bot, update, error):
    try:
        raise error
    except TelegramError:
        logging.getLogger(__name__).warning('Telegram Error! %s caused by this update: %s', error, update)


if __name__ == "__main__":
    pp = PicklePersistence(filename="plotyourselfbot")
    bot = telegram.Bot(token=TOKEN)
    updater = Updater(token=TOKEN, persistence=pp, use_context=True)
    dispatcher = updater.dispatcher

    create_plot_aliases = ["createplot", "cp"]
    load_plots_aliases = ["loadplots", "lp"]
    commands = [("createplot", 1, create_plot_aliases)]
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