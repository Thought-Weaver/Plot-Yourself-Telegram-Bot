# -*- coding: utf-8 -*-
#!/usr/bin/env python3
from __future__ import unicode_literals

from matplotlib import pyplot as plt
from matplotlib import tri as tri
from colorhash import ColorHash
from io import BytesIO

import numpy as np
import pandas as pd
from sympy import S, symbols, printing

# I think it might be more elegant to return non-null and return strings with error text if need be. Sometimes,
# however, I'll be returning non-errors, so I might want to implement a tuple system: (err_code, data)
# Let 0 be success and 1 be some error.

# https://www.science-emergence.com/Articles/How-to-put-the-origin-in-the-center-of-the-figure-with-matplotlib-/
# https://pythonspot.com/matplotlib-scatterplot/
# https://stackoverflow.com/questions/51113062/how-to-receive-images-from-telegram-bot

class Plot:
    def __init__(self, name, xaxisleft, xaxisright, yaxisbottom, yaxistop, minx, maxx, miny, maxy, createdby, id, custompoints=False):
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
        self.__createdby = createdby
        self.__custompoints = custompoints
        self.__id = id
        self.__last_modified = None

    def __check_bounds(self, x, y):
        if (self.__minx is not None and x < self.__minx) or (self.__maxx is not None and x > self.__maxx) or \
                (self.__miny is not None and y < self.__miny) or (self.__maxy is not None and y > self.__maxy):
            return False
        return True

    def plot_point(self, label, x, y, err_x=0, err_y=0):
        if not self.__check_bounds(x + err_x, y + err_y) or not self.__check_bounds(x - err_x, y - err_y):
            return 1, "Error: Plot point and error cannot be out of bounds: " \
                      "x : [" + str(self.__minx if self.__minx is not None else "_") + ", " + \
                   str(self.__maxx if self.__maxx is not None else "_") + "] " + \
                   "y : [" + str(self.__miny if self.__miny is not None else "_") + ", " + \
                   str(self.__maxy if self.__maxy is not None else "_") + "]"

        for i in range(len(self.__points)):
            if self.__points[i][0] == label:
                self.__points[i] = (label, x, y, err_x, err_y)
                return 0, ""

        self.__points.append((label if label is not None else "", x, y, err_x, err_y))

        return 0, ""

    def remove_point(self, label):
        if label not in [t[0] for t in self.__points]:
            return 1, "Error: You haven't plotted yourself in this plot."
        self.__points.remove(next(p for p in self.__points if p[0] == label))

        return 0, ""

    def generate_plot(self, toggle_labels=True, zoom_x_min=None, zoom_y_min=None, zoom_x_max=None, zoom_y_max=None, contour=False):
        # Quick check that all the points have errors.
        for i in range(len(self.__points)):
            if len(self.__points[i]) != 5:
                self.__points[i] = (self.__points[i][0], self.__points[i][1], self.__points[i][2], 0, 0)

        X = [p[1] for p in self.__points]
        Y = [p[2] for p in self.__points]
        err_X = [p[3] for p in self.__points]
        err_Y = [p[4] for p in self.__points]
        labels = [p[0] for p in self.__points]
        colors = [(color_hash[0] / 255, color_hash[1] / 255, color_hash[2] / 255)
                  for color_hash in [ColorHash(label).rgb for label in labels]]

        fig = plt.figure()
        if self.__minx != self.__maxx and self.__miny != self.__maxy:
            plt.grid(True)
        if not contour:
            plt.errorbar(X, Y, xerr=err_X, yerr=err_Y, ecolor=colors, linestyle="None")
        else:
            center_x = sum(X) / len(X)
            center_y = sum(Y) / len(Y)
            colors.append((0, 0, 0))
            labels.append("")
            X.append(center_x)
            Y.append(center_y)
            xi = np.linspace(self.__minx, self.__maxx, 10 * (abs(self.__maxx) + abs(self.__minx)))
            yi = np.linspace(self.__miny, self.__maxy, 10 * (abs(self.__maxy) + abs(self.__miny)))
            z = np.sqrt((np.array(X) - center_x) ** 2 + (np.array(Y) - center_y) ** 2)
            triang = tri.Triangulation(np.array(X), np.array(Y))
            interpolator = tri.LinearTriInterpolator(triang, z)
            Xi, Yi = np.meshgrid(xi, yi)
            zi = interpolator(Xi, Yi)

            plt.contour(xi, yi, zi, levels=14, linewidths=0.5, colors='k')
            cntr = plt.contourf(xi, yi, zi, levels=14, cmap="RdBu_r")
            fig.colorbar(cntr)
        plt.scatter(X, Y, c=colors)

        if self.__minx != self.__maxx:
            plt.axhline(y=0, color='k')
        if self.__miny != self.__maxy:
            plt.axvline(x=0, color='k')

        if toggle_labels:
            for i in range(len(X)):
                plt.annotate(labels[i], (X[i], Y[i]))

        if self.__xaxisleft is not None and self.__xaxisright is not None:
            plt.xlabel("<-- " + str(self.__xaxisleft) + " || " + str(self.__xaxisright) + " -->", fontsize="medium")
        elif self.__xaxisright is None and self.__xaxisleft is not None:
            plt.xlabel(str(self.__xaxisleft), fontsize="medium")
        elif self.__xaxisleft is None and self.__xaxisright is not None:
            plt.xlabel(str(self.__xaxisright), fontsize="medium")

        if self.__yaxistop is not None and self.__yaxisbottom is not None:
            plt.ylabel("<-- " + str(self.__yaxisbottom) + " || " + str(self.__yaxistop) + " -->", fontsize="medium")
        elif self.__yaxisbottom is None and self.__yaxistop is not None:
            plt.ylabel(str(self.__yaxistop), fontsize="medium")
        elif self.__yaxistop is None and self.__yaxisbottom is not None:
            plt.ylabel(str(self.__yaxisbottom), fontsize="medium")

        if self.__name is not None:
            plt.title(str(self.__name), fontsize="large")
        plt.suptitle("ID: (" + str(self.__id) + ")", fontsize=8)

        plt.xlim(left=self.__minx, right=self.__maxx)
        plt.ylim(bottom=self.__miny, top=self.__maxy)
        if zoom_x_min is not None and zoom_y_min is not None and zoom_x_max is not None and zoom_y_max is not None:
            plt.axis([zoom_x_min, zoom_x_max, zoom_y_min, zoom_y_max])

        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        buffer.seek(0)

        # bot.send_photo(chat_id=chat_id, photo=buffer)
        # This returns the image itself that can then be sent.
        return 0, buffer

    def generate_stats(self):
        points_dict = { "Names" : pd.Series(np.asarray([p[0] for p in self.__points], dtype=str)),
                        "X" : pd.Series(np.asarray([p[1] for p in self.__points], dtype=float)),
                        "Y" : pd.Series(np.asarray([p[2] for p in self.__points], dtype=float)) }
        return 0, pd.DataFrame(points_dict).describe()

    def polyfit(self, deg, toggle_labels=True):
        X = [p[1] for p in self.__points]
        Y = [p[2] for p in self.__points]
        labels = [p[0] for p in self.__points]
        colors = [(color_hash[0] / 255, color_hash[1] / 255, color_hash[2] / 255)
                  for color_hash in [ColorHash(label).rgb for label in labels]]

        fig = plt.figure()

        if toggle_labels:
            for i in range(len(X)):
                plt.annotate(labels[i], (X[i], Y[i]))

        if self.__xaxisleft is not None and self.__xaxisright is not None:
            plt.xlabel("<-- " + str(self.__xaxisleft) + " || " + str(self.__xaxisright) + " -->", fontsize="medium")
        elif self.__xaxisright is None and self.__xaxisleft is not None:
            plt.xlabel(str(self.__xaxisleft), fontsize="medium")
        elif self.__xaxisleft is None and self.__xaxisright is not None:
            plt.xlabel(str(self.__xaxisright), fontsize="medium")

        if self.__yaxistop is not None and self.__yaxisbottom is not None:
            plt.ylabel("<-- " + str(self.__yaxisbottom) + " || " + str(self.__yaxistop) + " -->", fontsize="medium")
        elif self.__yaxisbottom is None and self.__yaxistop is not None:
            plt.ylabel(str(self.__yaxistop), fontsize="medium")
        elif self.__yaxistop is None and self.__yaxisbottom is not None:
            plt.ylabel(str(self.__yaxisbottom), fontsize="medium")

        if self.__name is not None:
            plt.title(str(self.__name), fontsize="large")
        plt.suptitle("ID: (" + str(self.__id) + ")", fontsize=8)

        p = np.polynomial.polynomial.polyfit(X, Y, deg)
        f = np.poly1d(p[::-1])

        x_new = np.linspace(min(X), max(X), 10 * len(X))
        y_new = f(x_new)

        x = symbols('x')
        poly = sum(S("{:6.3f}".format(v)) * x ** i for i, v in enumerate(p))
        eq_latex = printing.latex(poly)

        plt.grid(True)
        plt.scatter(X, Y, c=colors)
        plt.axhline(y=0, color='k')
        plt.axvline(x=0, color='k')
        plt.plot(x_new, y_new, label="${}$".format(eq_latex))
        plt.legend(fontsize="small")

        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        buffer.seek(0)

        yhat = f(X)
        ybar = np.sum(Y) / len(Y)
        ssres = np.sum((Y - yhat) ** 2)
        sstot = np.sum((Y - ybar) ** 2)

        return 0, (buffer, 1 - ssres / sstot)

    def full_equation(self, deg):
        X = [p[1] for p in self.__points]
        Y = [p[2] for p in self.__points]

        p = np.polynomial.polynomial.polyfit(X, Y, deg)

        x = symbols('x')
        poly = sum(S("{:f}".format(v)) * x ** i for i, v in enumerate(p))
        eq_latex = printing.latex(poly)

        #fig = plt.figure()
        #plt.grid(False)
        #plt.axis('off')
        #plt.tight_layout()
        #plt.text(0, 0.5, r"$%s$" % eq_latex, fontsize="medium", wrap=True)

        #buffer = BytesIO()
        #fig.savefig(buffer, format="png")
        #buffer.seek(0)

        return 0, eq_latex

    def lookup_label(self, label):
        for p in self.__points:
            if p[0] == label:
                return 0, (p[1], p[2])
        return 1, "Name not found on that plot."

    def edit_plot(self, plot_args):
        self.__name = " ".join(plot_args.get("title")) if plot_args.get("title") is not None else self.__name
        self.__xaxisright = " ".join(plot_args.get("xright")) if plot_args.get("xright") is not None else self.__xaxisright
        self.__xaxisleft = " ".join(plot_args.get("xleft")) if plot_args.get("xleft") is not None else self.__xaxisleft
        self.__yaxistop = " ".join(plot_args.get("ytop")) if plot_args.get("ytop") is not None else self.__yaxistop
        self.__yaxisbottom = " ".join(plot_args.get("ybottom")) if plot_args.get("ybottom") is not None else self.__yaxisbottom
        self.__minx = plot_args.get("minx") if plot_args.get("minx") is not None else self.__minx
        self.__maxx = plot_args.get("maxx") if plot_args.get("maxx") is not None else self.__maxx
        self.__miny = plot_args.get("miny") if plot_args.get("miny") is not None else self.__miny
        self.__maxy = plot_args.get("maxy") if plot_args.get("maxy") is not None else self.__maxy
        self.__custompoints = plot_args.get("custompoints") if plot_args.get("custompoints") is not None else self.__custompoints

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

    def get_creator(self):
        return self.__createdby

    def get_if_custom_points(self):
        return self.__custompoints

    def get_points(self):
        return self.__points

    def get_id(self):
        return self.__id

    def get_last_modified(self):
        try:
            timestamp = self.__last_modified
            return timestamp
        except AttributeError:
            return None

    def set_last_modified(self, timestamp):
        self.__last_modified = timestamp

    def set_creator(self, username, user_id):
        self.__createdby = (username, user_id)


class BoxedPlot:
    # We'll define horiz = [h1, h2, h3], vertical = [v1, v2, v3]
    def __init__(self, name, horiz, vert, createdby, id, custompoints=False):
        self.__name = name
        self.__horiz = horiz
        self.__vert = vert
        self.__minx = -10
        self.__maxx = 10
        self.__miny = -10
        self.__maxy = 10
        self.__points = []
        self.__createdby = createdby
        self.__custompoints = custompoints
        self.__id = id
        self.__last_modified = None

    def __check_bounds(self, x, y):
        if (self.__minx is not None and x < self.__minx) or (self.__maxx is not None and x > self.__maxx) or \
                (self.__miny is not None and y < self.__miny) or (self.__maxy is not None and y > self.__maxy):
            return False
        return True

    def plot_point(self, label, x, y, err_x=0, err_y=0):
        if not self.__check_bounds(x + err_x, y + err_y) or not self.__check_bounds(x - err_x, y - err_y):
            return 1, "Error: Plot point and error cannot be out of bounds: " \
                      "x : [" + str(self.__minx if self.__minx is not None else "_") + ", " + \
                   str(self.__maxx if self.__maxx is not None else "_") + "] " + \
                   "y : [" + str(self.__miny if self.__miny is not None else "_") + ", " + \
                   str(self.__maxy if self.__maxy is not None else "_") + "]"

        for i in range(len(self.__points)):
            if self.__points[i][0] == label:
                self.__points[i] = (label, x, y, err_x, err_y)
                return 0, ""

        self.__points.append((label if label is not None else "", x, y, err_x, err_y))

        return 0, ""

    def remove_point(self, label):
        if label not in [t[0] for t in self.__points]:
            return 1, "Error: You haven't plotted yourself in this plot."
        self.__points.remove(next(p for p in self.__points if p[0] == label))

        return 0, ""

    def generate_plot(self, toggle_labels=True, zoom_x_min=None, zoom_y_min=None, zoom_x_max=None, zoom_y_max=None, contour=False):
        # Quick check that all the points have errors.
        for i in range(len(self.__points)):
            if len(self.__points[i]) != 5:
                self.__points[i] = (self.__points[i][0], self.__points[i][1], self.__points[i][2], 0, 0)

        X = [p[1] for p in self.__points]
        Y = [p[2] for p in self.__points]
        err_X = [p[3] for p in self.__points]
        err_Y = [p[4] for p in self.__points]
        labels = [p[0] for p in self.__points]
        colors = [(color_hash[0] / 255, color_hash[1] / 255, color_hash[2] / 255)
                  for color_hash in [ColorHash(label).rgb for label in labels]]

        fig = plt.figure()
        plt.grid(False)
        if not contour:
            plt.errorbar(X, Y, xerr=err_X, yerr=err_Y, ecolor=colors, linestyle="None")
        else:
            center_x = sum(X) / len(X)
            center_y = sum(Y) / len(Y)
            colors.append((0, 0, 0))
            labels.append("")
            X.append(center_x)
            Y.append(center_y)
            xi = np.linspace(self.__minx, self.__maxx, 10 * (abs(self.__maxx) + abs(self.__minx)))
            yi = np.linspace(self.__miny, self.__maxy, 10 * (abs(self.__maxy) + abs(self.__miny)))
            z = np.sqrt((np.array(X) - center_x) ** 2 + (np.array(Y) - center_y) ** 2)
            triang = tri.Triangulation(np.array(X), np.array(Y))
            interpolator = tri.LinearTriInterpolator(triang, z)
            Xi, Yi = np.meshgrid(xi, yi)
            zi = interpolator(Xi, Yi)

            plt.contour(xi, yi, zi, levels=14, linewidths=0.5, colors='k')
            cntr = plt.contourf(xi, yi, zi, levels=14, cmap="RdBu_r")
            fig.colorbar(cntr)

        plt.scatter(X, Y, c=colors)
        plt.axhline(y=self.__minx, color='k')
        plt.axvline(x=self.__miny, color='k')
        plt.axhline(y=self.__maxx, color='k')
        plt.axvline(x=self.__maxy, color='k')
        plt.axhline(y=self.__minx + (self.__maxx - self.__minx) / 3, color='k')
        plt.axvline(x=self.__miny + (self.__maxy - self.__miny) / 3, color='k')
        plt.axhline(y=self.__minx + 2 * (self.__maxx - self.__minx) / 3, color='k')
        plt.axvline(x=self.__miny + 2 * (self.__maxy - self.__miny) / 3, color='k')

        if toggle_labels:
            for i in range(len(X)):
                plt.annotate(labels[i], (X[i], Y[i]))

        x_axis_title = ""
        if self.__horiz is not None:
            for h in self.__horiz:
                x_axis_title += h + " || "
        x_axis_title = x_axis_title[:-4]

        y_axis_title = ""
        if self.__vert is not None:
            for v in self.__vert:
                y_axis_title += v + " || "
        y_axis_title = y_axis_title[:-4]

        plt.xlabel(x_axis_title, fontsize="medium")
        plt.ylabel(y_axis_title, fontsize="medium")

        plt.xlim(left=self.__minx, right=self.__maxx)
        plt.ylim(bottom=self.__miny, top=self.__maxy)
        if zoom_x_min is not None and zoom_y_min is not None and zoom_x_max is not None and zoom_y_max is not None:
            plt.axis([zoom_x_min, zoom_x_max, zoom_y_min, zoom_y_max])

        if self.__name is not None:
            plt.title(str(self.__name), fontsize="large")
        plt.suptitle("ID: (" + str(self.__id) + ")", fontsize=8)

        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        buffer.seek(0)

        # bot.send_photo(chat_id=chat_id, photo=buffer)
        # This returns the image itself that can then be sent.
        return 0, buffer

    def generate_stats(self):
        points_dict = { "Names" : pd.Series(np.asarray([p[0] for p in self.__points], dtype=str)),
                        "X" : pd.Series(np.asarray([p[1] for p in self.__points], dtype=float)),
                        "Y" : pd.Series(np.asarray([p[2] for p in self.__points], dtype=float)) }
        return 0, pd.DataFrame(points_dict).describe()

    def polyfit(self, deg, toggle_labels=True):
        X = [p[1] for p in self.__points]
        Y = [p[2] for p in self.__points]
        labels = [p[0] for p in self.__points]
        colors = [(color_hash[0] / 255, color_hash[1] / 255, color_hash[2] / 255)
                  for color_hash in [ColorHash(label).rgb for label in labels]]

        fig = plt.figure()
        plt.grid(False)
        plt.scatter(X, Y, c=colors)
        plt.axhline(y=self.__minx, color='k')
        plt.axvline(x=self.__miny, color='k')
        plt.axhline(y=self.__maxx, color='k')
        plt.axvline(x=self.__maxy, color='k')
        plt.axhline(y=self.__minx + (self.__maxx - self.__minx) / 3, color='k')
        plt.axvline(x=self.__miny + (self.__maxy - self.__miny) / 3, color='k')
        plt.axhline(y=self.__minx + 2 * (self.__maxx - self.__minx) / 3, color='k')
        plt.axvline(x=self.__miny + 2 * (self.__maxy - self.__miny) / 3, color='k')

        if toggle_labels:
            for i in range(len(X)):
                plt.annotate(labels[i], (X[i], Y[i]))

        x_axis_title = ""
        if self.__horiz is not None:
            for h in self.__horiz:
                x_axis_title += h + " || "
        x_axis_title = x_axis_title[:-4]

        y_axis_title = ""
        if self.__vert is not None:
            for v in self.__vert:
                y_axis_title += v + " || "
        y_axis_title = y_axis_title[:-4]

        plt.xlabel(x_axis_title, fontsize="medium")
        plt.ylabel(y_axis_title, fontsize="medium")

        plt.xlim(left=self.__minx, right=self.__maxx)
        plt.ylim(bottom=self.__miny, top=self.__maxy)

        if self.__name is not None:
            plt.title(str(self.__name), fontsize="large")
        plt.suptitle("ID: (" + str(self.__id) + ")", fontsize=8)

        p = np.polynomial.polynomial.polyfit(X, Y, deg)
        f = np.poly1d(p[::-1])

        x_new = np.linspace(min(X), max(X), 10 * len(X))
        y_new = f(x_new)

        x = symbols("x")
        poly = sum(S("{:6.3f}".format(v)) * x ** i for i, v in enumerate(p))
        eq_latex = printing.latex(poly)

        plt.plot(x_new, y_new, label="${}$".format(eq_latex))
        plt.legend(fontsize="small")

        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        buffer.seek(0)

        yhat = f(X)
        ybar = np.sum(Y) / len(Y)
        ssres = np.sum((Y - yhat) ** 2)
        sstot = np.sum((Y - ybar) ** 2)

        return 0, (buffer, 1 - ssres / sstot)

    def full_equation(self, deg):
        X = [p[1] for p in self.__points]
        Y = [p[2] for p in self.__points]

        p = np.polynomial.polynomial.polyfit(X, Y, deg)

        x = symbols('x')
        poly = sum(S("{:f}".format(v)) * x ** i for i, v in enumerate(p))
        eq_latex = printing.latex(poly)

        #fig = plt.figure()
        #plt.grid(False)
        #plt.axis('off')
        #plt.tight_layout()
        #plt.text(0, 0.5, r"$%s$" % eq_latex, fontsize="medium", wrap=True)

        #buffer = BytesIO()
        #fig.savefig(buffer, format="png")
        #buffer.seek(0)

        return 0, eq_latex

    def lookup_label(self, label):
        for p in self.__points:
            if p[0] == label:
                return 0, (p[1], p[2])
        return 1, "Name not found on that plot."

    def edit_plot(self, plot_args):
        self.__name = " ".join(plot_args.get("title")) if plot_args.get("title") is not None else self.__name
        self.__horiz = [
            " ".join(plot_args.get("horiz1")) if plot_args.get("horiz1") is not None else self.__horiz[0],
            " ".join(plot_args.get("horiz2")) if plot_args.get("horiz2") is not None else self.__horiz[1],
            " ".join(plot_args.get("horiz3")) if plot_args.get("horiz3") is not None else self.__horiz[2]
        ]
        self.__vert = [
            " ".join(plot_args.get("vert1")) if plot_args.get("vert1") is not None else self.__vert[0],
            " ".join(plot_args.get("vert2")) if plot_args.get("vert2") is not None else self.__vert[1],
            " ".join(plot_args.get("vert3")) if plot_args.get("vert3") is not None else self.__vert[2]
        ]
        self.__custompoints = plot_args.get("custompoints") if plot_args.get("custompoints") is not None else self.__custompoints

    def get_name(self):
        return self.__name

    def get_horiz(self):
        return self.__horiz

    def get_vert(self):
        return self.__vert

    def get_minx(self):
        return self.__minx

    def get_maxx(self):
        return self.__maxx

    def get_miny(self):
        return self.__miny

    def get_maxy(self):
        return self.__maxy

    def get_creator(self):
        return self.__createdby

    def get_if_custom_points(self):
        return self.__custompoints

    def get_points(self):
        return self.__points

    def get_id(self):
        return self.__id

    def get_last_modified(self):
        try:
            timestamp = self.__last_modified
            return timestamp
        except AttributeError:
            return None

    def set_last_modified(self, timestamp):
        self.__last_modified = timestamp

    def set_creator(self, username, user_id):
        self.__createdby = (username, user_id)


class AlignmentChart:
    # We'll define labels = [row1col1, row1col2, row1col3, row2col1, ..., row3col3]
    def __init__(self, name, labels, createdby, id, custompoints=False):
        self.__name = name
        self.__labels = labels
        self.__label_spacing = 1
        self.__minx = -10
        self.__maxx = 10
        self.__miny = -10
        self.__maxy = 10
        self.__points = []
        self.__createdby = createdby
        self.__custompoints = custompoints
        self.__id = id
        self.__last_modified = None

    def __check_bounds(self, x, y):
        if (self.__minx is not None and x < self.__minx) or (self.__maxx is not None and x > self.__maxx) or \
                (self.__miny is not None and y < self.__miny) or (self.__maxy is not None and y > self.__maxy):
            return False
        return True

    def plot_point(self, label, x, y, err_x=0, err_y=0):
        if not self.__check_bounds(x + err_x, y + err_y) or not self.__check_bounds(x - err_x, y - err_y):
            return 1, "Error: Plot point and error cannot be out of bounds: " \
                      "x : [" + str(self.__minx if self.__minx is not None else "_") + ", " + \
                   str(self.__maxx if self.__maxx is not None else "_") + "] " + \
                   "y : [" + str(self.__miny if self.__miny is not None else "_") + ", " + \
                   str(self.__maxy if self.__maxy is not None else "_") + "]"

        for i in range(len(self.__points)):
            if self.__points[i][0] == label:
                self.__points[i] = (label, x, y, err_x, err_y)
                return 0, ""

        self.__points.append((label if label is not None else "", x, y, err_x, err_y))

        return 0, ""

    def remove_point(self, label):
        if label not in [t[0] for t in self.__points]:
            return 1, "Error: You haven't plotted yourself in this plot."
        self.__points.remove(next(p for p in self.__points if p[0] == label))

        return 0, ""

    def generate_plot(self, toggle_labels=True, zoom_x_min=None, zoom_y_min=None, zoom_x_max=None, zoom_y_max=None, contour=False):
        # Quick check that all the points have errors.
        for i in range(len(self.__points)):
            if len(self.__points[i]) != 5:
                self.__points[i] = (self.__points[i][0], self.__points[i][1], self.__points[i][2], 0, 0)

        X = [p[1] for p in self.__points]
        Y = [p[2] for p in self.__points]
        err_X = [p[3] for p in self.__points]
        err_Y = [p[4] for p in self.__points]
        labels = [p[0] for p in self.__points]
        colors = [(color_hash[0] / 255, color_hash[1] / 255, color_hash[2] / 255)
                  for color_hash in [ColorHash(label).rgb for label in labels]]

        fig = plt.figure()
        plt.grid(False)

        if not contour:
            plt.errorbar(X, Y, xerr=err_X, yerr=err_Y, ecolor=colors, linestyle="None")
        else:
            center_x = sum(X) / len(X)
            center_y = sum(Y) / len(Y)
            colors.append((0, 0, 0))
            labels.append("")
            X.append(center_x)
            Y.append(center_y)
            xi = np.linspace(self.__minx, self.__maxx, 10 * (abs(self.__maxx) + abs(self.__minx)))
            yi = np.linspace(self.__miny, self.__maxy, 10 * (abs(self.__maxy) + abs(self.__miny)))
            z = np.sqrt((np.array(X) - center_x) ** 2 + (np.array(Y) - center_y) ** 2)
            triang = tri.Triangulation(np.array(X), np.array(Y))
            interpolator = tri.LinearTriInterpolator(triang, z)
            Xi, Yi = np.meshgrid(xi, yi)
            zi = interpolator(Xi, Yi)

            plt.contour(xi, yi, zi, levels=14, linewidths=0.5, colors='k')
            cntr = plt.contourf(xi, yi, zi, levels=14, cmap="RdBu_r")
            fig.colorbar(cntr)

        plt.scatter(X, Y, c=colors)
        plt.axhline(y=self.__minx, color='k')
        plt.axvline(x=self.__miny, color='k')
        plt.axhline(y=self.__maxx, color='k')
        plt.axhline(y=self.__maxx - self.__label_spacing, color='k')
        plt.axvline(x=self.__maxy, color='k')
        plt.axhline(y=self.__minx + (self.__maxx - self.__minx) / 3, color='k')
        plt.axhline(y=self.__minx + (self.__maxx - self.__minx) / 3 - self.__label_spacing, color='k')
        plt.axvline(x=self.__miny + (self.__maxy - self.__miny) / 3, color='k')
        plt.axhline(y=self.__minx + 2 * (self.__maxx - self.__minx) / 3, color='k')
        plt.axhline(y=self.__minx + 2 * (self.__maxx - self.__minx) / 3 - self.__label_spacing, color='k')
        plt.axvline(x=self.__miny + 2 * (self.__maxy - self.__miny) / 3, color='k')

        if toggle_labels:
            for i in range(len(X)):
                plt.annotate(labels[i], (X[i], Y[i]))

        plt.xlabel("Lawful || Neutral || Chaotic", fontsize="medium")
        plt.ylabel("Evil || Neutral || Good", fontsize="medium")

        plt.text(-9.8, 9.2, self.__labels[0], fontsize=10)
        plt.text(-3.2, 9.2, self.__labels[1], fontsize=10)
        plt.text(3.5, 9.2, self.__labels[2], fontsize=10)
        plt.text(-9.8, 2.6, self.__labels[3], fontsize=10)
        plt.text(-3.2, 2.6, self.__labels[4], fontsize=10)
        plt.text(3.5, 2.6, self.__labels[5], fontsize=10)
        plt.text(-9.8, -4.0, self.__labels[6], fontsize=10)
        plt.text(-3.2, -4.0, self.__labels[7], fontsize=10)
        plt.text(3.5, -4.0, self.__labels[8], fontsize=10)

        plt.xlim(left=self.__minx, right=self.__maxx)
        plt.ylim(bottom=self.__miny, top=self.__maxy)
        if zoom_x_min is not None and zoom_y_min is not None and zoom_x_max is not None and zoom_y_max is not None:
            plt.axis([zoom_x_min, zoom_x_max, zoom_y_min, zoom_y_max])

        if self.__name is not None:
            plt.title(str(self.__name), fontsize="large")
        plt.suptitle("ID: (" + str(self.__id) + ")", fontsize=8)

        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        buffer.seek(0)

        # bot.send_photo(chat_id=chat_id, photo=buffer)
        # This returns the image itself that can then be sent.
        return 0, buffer

    def generate_stats(self):
        points_dict = { "Names" : pd.Series(np.asarray([p[0] for p in self.__points], dtype=str)),
                        "X" : pd.Series(np.asarray([p[1] for p in self.__points], dtype=float)),
                        "Y" : pd.Series(np.asarray([p[2] for p in self.__points], dtype=float)) }
        return 0, pd.DataFrame(points_dict).describe()

    def polyfit(self, deg, toggle_labels=True):
        X = [p[1] for p in self.__points]
        Y = [p[2] for p in self.__points]
        labels = [p[0] for p in self.__points]
        colors = [(color_hash[0] / 255, color_hash[1] / 255, color_hash[2] / 255)
                  for color_hash in [ColorHash(label).rgb for label in labels]]

        fig = plt.figure()
        plt.grid(False)
        plt.scatter(X, Y, c=colors)
        plt.axhline(y=self.__minx, color='k')
        plt.axvline(x=self.__miny, color='k')
        plt.axhline(y=self.__maxx, color='k')
        plt.axhline(y=self.__maxx - self.__label_spacing, color='k')
        plt.axvline(x=self.__maxy, color='k')
        plt.axhline(y=self.__minx + (self.__maxx - self.__minx) / 3, color='k')
        plt.axhline(y=self.__minx + (self.__maxx - self.__minx) / 3 - self.__label_spacing, color='k')
        plt.axvline(x=self.__miny + (self.__maxy - self.__miny) / 3, color='k')
        plt.axhline(y=self.__minx + 2 * (self.__maxx - self.__minx) / 3, color='k')
        plt.axhline(y=self.__minx + 2 * (self.__maxx - self.__minx) / 3 - self.__label_spacing, color='k')
        plt.axvline(x=self.__miny + 2 * (self.__maxy - self.__miny) / 3, color='k')

        if toggle_labels:
            for i in range(len(X)):
                plt.annotate(labels[i], (X[i], Y[i]))

        plt.xlabel("Lawful || Neutral || Chaotic", fontsize="medium")
        plt.ylabel("Evil || Neutral || Good", fontsize="medium")

        plt.text(-9.8, 9.2, self.__labels[0], fontsize=10)
        plt.text(-3.2, 9.2, self.__labels[1], fontsize=10)
        plt.text(3.5, 9.2, self.__labels[2], fontsize=10)
        plt.text(-9.8, 2.6, self.__labels[3], fontsize=10)
        plt.text(-3.2, 2.6, self.__labels[4], fontsize=10)
        plt.text(3.5, 2.6, self.__labels[5], fontsize=10)
        plt.text(-9.8, -4.0, self.__labels[6], fontsize=10)
        plt.text(-3.2, -4.0, self.__labels[7], fontsize=10)
        plt.text(3.5, -4.0, self.__labels[8], fontsize=10)

        plt.xlim(left=self.__minx, right=self.__maxx)
        plt.ylim(bottom=self.__miny, top=self.__maxy)

        if self.__name is not None:
            plt.title(str(self.__name), fontsize="large")
        plt.suptitle("ID: (" + str(self.__id) + ")", fontsize=8)

        p = np.polynomial.polynomial.polyfit(X, Y, deg)
        f = np.poly1d(p[::-1])

        x_new = np.linspace(min(X), max(X), 10 * len(X))
        y_new = f(x_new)

        x = symbols("x")
        poly = sum(S("{:6.3f}".format(v)) * x ** i for i, v in enumerate(p))
        eq_latex = printing.latex(poly)

        plt.plot(x_new, y_new, label="${}$".format(eq_latex))
        plt.legend(fontsize="small")

        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        buffer.seek(0)

        yhat = f(X)
        ybar = np.sum(Y) / len(Y)
        ssres = np.sum((Y - yhat) ** 2)
        sstot = np.sum((Y - ybar) ** 2)

        return 0, (buffer, 1 - ssres / sstot)

    def full_equation(self, deg):
        X = [p[1] for p in self.__points]
        Y = [p[2] for p in self.__points]

        p = np.polynomial.polynomial.polyfit(X, Y, deg)

        x = symbols('x')
        poly = sum(S("{:f}".format(v)) * x ** i for i, v in enumerate(p))
        eq_latex = printing.latex(poly)

        #fig = plt.figure()
        #plt.grid(False)
        #plt.axis('off')
        #plt.tight_layout()
        #plt.text(0, 0.5, r"$%s$" % eq_latex, fontsize="medium", wrap=True)

        #buffer = BytesIO()
        #fig.savefig(buffer, format="png")
        #buffer.seek(0)

        return 0, eq_latex

    def lookup_label(self, label):
        for p in self.__points:
            if p[0] == label:
                return 0, (p[1], p[2])
        return 1, "Name not found on that plot."

    def edit_plot(self, plot_args):
        self.__name = " ".join(plot_args.get("title")) if plot_args.get("title") is not None else self.__name
        self.__labels = [
        " ".join(plot_args.get("label1")) if plot_args.get("label1") is not None else self.__labels[0],
        " ".join(plot_args.get("label2")) if plot_args.get("label2") is not None else self.__labels[1],
        " ".join(plot_args.get("label3")) if plot_args.get("label3") is not None else self.__labels[2],
        " ".join(plot_args.get("label4")) if plot_args.get("label4") is not None else self.__labels[3],
        " ".join(plot_args.get("label5")) if plot_args.get("label5") is not None else self.__labels[4],
        " ".join(plot_args.get("label6")) if plot_args.get("label6") is not None else self.__labels[5],
        " ".join(plot_args.get("label7")) if plot_args.get("label7") is not None else self.__labels[6],
        " ".join(plot_args.get("label8")) if plot_args.get("label8") is not None else self.__labels[7],
        " ".join(plot_args.get("label9")) if plot_args.get("label9") is not None else self.__labels[8]
    ]
        self.__custompoints = plot_args.get("custompoints") if plot_args.get("custompoints") is not None else self.__custompoints

    def get_name(self):
        return self.__name

    def get_labels(self):
        return self.__labels

    def get_minx(self):
        return self.__minx

    def get_maxx(self):
        return self.__maxx

    def get_miny(self):
        return self.__miny

    def get_maxy(self):
        return self.__maxy

    def get_creator(self):
        return self.__createdby

    def get_if_custom_points(self):
        return self.__custompoints

    def get_points(self):
        return self.__points

    def get_id(self):
        return self.__id

    def get_last_modified(self):
        try:
            timestamp = self.__last_modified
            return timestamp
        except AttributeError:
            return None

    def set_last_modified(self, timestamp):
        self.__last_modified = timestamp

    def set_creator(self, username, user_id):
        self.__createdby = (username, user_id)


class TrianglePlot:
    def __init__(self, name, xaxisleft, xaxisright, yaxistop, createdby, id, custompoints=False):
        self.__name = name
        self.__xaxisleft = xaxisleft
        self.__xaxisright = xaxisright
        self.__yaxistop = yaxistop
        self.__minx = 0
        self.__maxx = 10
        self.__miny = 0
        self.__maxy = 10
        self.__points = []
        self.__createdby = createdby
        self.__custompoints = custompoints
        self.__id = id
        self.__last_modified = None

    def __check_sign(self, x1, y1, x2, y2, x3, y3):
        return (x1 - x3) * (y2 - y3) - (x2 - x3) * (y1 - y3)

    def __check_bounds(self, x, y):
        d1 = self.__check_sign(x, y, self.__minx, self.__miny, self.__maxx / 2, self.__maxy)
        d2 = self.__check_sign(x, y, self.__maxx / 2, self.__maxy, self.__maxx, self.__miny)
        d3 = self.__check_sign(x, y, self.__maxx, self.__miny, self.__minx, self.__miny)

        negative = (d1 < 0) or (d2 < 0) or (d3 < 0)
        positive = (d1 > 0) or (d2 > 0) or (d3 > 0)

        return not (negative and positive)

    def plot_point(self, label, x, y, err_x=0, err_y=0):
        if not self.__check_bounds(x + err_x, y + err_y) or not self.__check_bounds(x - err_x, y - err_y)\
                or not self.__check_bounds(x + err_x, y) or not self.__check_bounds(x, y + err_y) or\
                not self.__check_bounds(x, y - err_y) or not self.__check_bounds(x - err_x, y):
            return 1, "Error: Plot point and error cannot be out of triangle bounds!"

        for i in range(len(self.__points)):
            if self.__points[i][0] == label:
                self.__points[i] = (label, x, y, err_x, err_y)
                return 0, ""

        self.__points.append((label if label is not None else "", x, y, err_x, err_y))

        return 0, ""

    def remove_point(self, label):
        if label not in [t[0] for t in self.__points]:
            return 1, "Error: You haven't plotted yourself in this plot."
        self.__points.remove(next(p for p in self.__points if p[0] == label))

        return 0, ""

    def generate_plot(self, toggle_labels=True, zoom_x_min=None, zoom_y_min=None, zoom_x_max=None, zoom_y_max=None, contour=False):
        # Quick check that all the points have errors.
        for i in range(len(self.__points)):
            if len(self.__points[i]) != 5:
                self.__points[i] = (self.__points[i][0], self.__points[i][1], self.__points[i][2], 0, 0)

        X = [p[1] for p in self.__points]
        Y = [p[2] for p in self.__points]
        err_X = [p[3] for p in self.__points]
        err_Y = [p[4] for p in self.__points]
        labels = [p[0] for p in self.__points]
        colors = [(color_hash[0] / 255, color_hash[1] / 255, color_hash[2] / 255)
                  for color_hash in [ColorHash(label).rgb for label in labels]]

        fig = plt.figure()
        plt.grid(False)

        if not contour:
            plt.errorbar(X, Y, xerr=err_X, yerr=err_Y, ecolor=colors, linestyle="None")
        else:
            center_x = sum(X) / len(X)
            center_y = sum(Y) / len(Y)
            colors.append((0, 0, 0))
            labels.append("")
            X.append(center_x)
            Y.append(center_y)
            xi = np.linspace(self.__minx, self.__maxx, 10 * (abs(self.__maxx) + abs(self.__minx)))
            yi = np.linspace(self.__miny, self.__maxy, 10 * (abs(self.__maxy) + abs(self.__miny)))
            z = np.sqrt((np.array(X) - center_x) ** 2 + (np.array(Y) - center_y) ** 2)
            triang = tri.Triangulation(np.array(X), np.array(Y))
            interpolator = tri.LinearTriInterpolator(triang, z)
            Xi, Yi = np.meshgrid(xi, yi)
            zi = interpolator(Xi, Yi)

            plt.contour(xi, yi, zi, levels=14, linewidths=0.5, colors='k')
            cntr = plt.contourf(xi, yi, zi, levels=14, cmap="RdBu_r")
            fig.colorbar(cntr)

        plt.scatter(X, Y, c=colors)

        triangle = plt.Polygon([[self.__minx, self.__miny], [self.__maxx / 2, self.__maxy], [self.__maxx, self.__miny]], fill=False, color='k')
        plt.gca().add_patch(triangle)

        if toggle_labels:
            for i in range(len(X)):
                plt.annotate(labels[i], (X[i], Y[i]))

        if self.__xaxisleft is not None and self.__xaxisright is not None:
            plt.xlabel("<-- " + str(self.__xaxisleft) + " || " + str(self.__xaxisright) + " -->", fontsize="medium")
        elif self.__xaxisright is None and self.__xaxisleft is not None:
            plt.xlabel(str(self.__xaxisleft), fontsize="medium")
        elif self.__xaxisleft is None and self.__xaxisright is not None:
            plt.xlabel(str(self.__xaxisright), fontsize="medium")

        if self.__yaxistop is not None:
            plt.title(str(self.__yaxistop), fontsize="medium")

        if self.__name is not None:
            plt.ylabel(str("ID: (" + str(self.__id) + ")\n" + self.__name), fontsize="large")
        else:
            plt.ylabel("ID: (" + str(self.__id) + ")", fontsize="large")

        plt.xlim(left=self.__minx, right=self.__maxx)
        plt.ylim(bottom=self.__miny, top=self.__maxy)
        if zoom_x_min is not None and zoom_y_min is not None and zoom_x_max is not None and zoom_y_max is not None:
            plt.axis([zoom_x_min, zoom_x_max, zoom_y_min, zoom_y_max])

        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        buffer.seek(0)

        # bot.send_photo(chat_id=chat_id, photo=buffer)
        # This returns the image itself that can then be sent.
        return 0, buffer

    def generate_stats(self):
        points_dict = { "Names" : pd.Series(np.asarray([p[0] for p in self.__points], dtype=str)),
                        "X" : pd.Series(np.asarray([p[1] for p in self.__points], dtype=float)),
                        "Y" : pd.Series(np.asarray([p[2] for p in self.__points], dtype=float)) }
        return 0, pd.DataFrame(points_dict).describe()

    def polyfit(self, deg, toggle_labels=True):
        X = [p[1] for p in self.__points]
        Y = [p[2] for p in self.__points]
        labels = [p[0] for p in self.__points]
        colors = [(color_hash[0] / 255, color_hash[1] / 255, color_hash[2] / 255)
                  for color_hash in [ColorHash(label).rgb for label in labels]]

        fig = plt.figure()

        if toggle_labels:
            for i in range(len(X)):
                plt.annotate(labels[i], (X[i], Y[i]))

        if self.__xaxisleft is not None and self.__xaxisright is not None:
            plt.xlabel("<-- " + str(self.__xaxisleft) + " || " + str(self.__xaxisright) + " -->", fontsize="medium")
        elif self.__xaxisright is None and self.__xaxisleft is not None:
            plt.xlabel(str(self.__xaxisleft), fontsize="medium")
        elif self.__xaxisleft is None and self.__xaxisright is not None:
            plt.xlabel(str(self.__xaxisright), fontsize="medium")

        if self.__yaxistop is not None:
            plt.title(str(self.__yaxistop), fontsize="medium")

        if self.__name is not None:
            plt.ylabel("ID: (" + str(self.__id) + ")\n" + str(self.__name), fontsize="large")
        else:
            plt.ylabel("ID: (" + str(self.__id) + ")", fontsize="large")

        p = np.polynomial.polynomial.polyfit(X, Y, deg)
        f = np.poly1d(p[::-1])

        x_new = np.linspace(min(X), max(X), 10 * len(X))
        y_new = f(x_new)

        x = symbols('x')
        poly = sum(S("{:6.3f}".format(v)) * x ** i for i, v in enumerate(p))
        eq_latex = printing.latex(poly)

        plt.grid(False)
        plt.scatter(X, Y, c=colors)
        triangle = plt.Polygon([[self.__minx, self.__miny], [self.__maxx / 2, self.__maxy], [self.__maxx, self.__miny]], fill=False, color='k')
        plt.gca().add_patch(triangle)

        plt.plot(x_new, y_new, label="${}$".format(eq_latex))
        plt.legend(fontsize="small")

        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        buffer.seek(0)

        yhat = f(X)
        ybar = np.sum(Y) / len(Y)
        ssres = np.sum((Y - yhat) ** 2)
        sstot = np.sum((Y - ybar) ** 2)

        return 0, (buffer, 1 - ssres / sstot)

    def full_equation(self, deg):
        X = [p[1] for p in self.__points]
        Y = [p[2] for p in self.__points]

        p = np.polynomial.polynomial.polyfit(X, Y, deg)

        x = symbols('x')
        poly = sum(S("{:f}".format(v)) * x ** i for i, v in enumerate(p))
        eq_latex = printing.latex(poly)

        #fig = plt.figure()
        #plt.grid(False)
        #plt.axis('off')
        #plt.tight_layout()
        #plt.text(0, 0.5, r"$%s$" % eq_latex, fontsize="medium", wrap=True)

        #buffer = BytesIO()
        #fig.savefig(buffer, format="png")
        #buffer.seek(0)

        return 0, eq_latex

    def lookup_label(self, label):
        for p in self.__points:
            if p[0] == label:
                return 0, (p[1], p[2])
        return 1, "Name not found on that plot."

    def edit_plot(self, plot_args):
        self.__name = " ".join(plot_args.get("title")) if plot_args.get("title") is not None else self.__name
        self.__xaxisright = " ".join(plot_args.get("xright")) if plot_args.get("xright") is not None else self.__xaxisright
        self.__xaxisleft = " ".join(plot_args.get("xleft")) if plot_args.get("xleft") is not None else self.__xaxisleft
        self.__yaxistop = " ".join(plot_args.get("ytop")) if plot_args.get("ytop") is not None else self.__yaxistop
        self.__custompoints = plot_args.get("custompoints") if plot_args.get("custompoints") is not None else self.__custompoints

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

    def get_creator(self):
        return self.__createdby

    def get_if_custom_points(self):
        return self.__custompoints

    def get_points(self):
        return self.__points

    def get_id(self):
        return self.__id

    def get_last_modified(self):
        try:
            timestamp = self.__last_modified
            return timestamp
        except AttributeError:
            return None

    def set_last_modified(self, timestamp):
        self.__last_modified = timestamp

    def set_creator(self, username, user_id):
        self.__createdby = (username, user_id)


class RadarPlot:
    def __init__(self, name, labels, createdby, id):
        self.__name = name
        self.__labels = labels
        self.__points = []
        self.__createdby = createdby
        self.__id = id
        self.__last_modified = None

    def plot_point(self, label, vals):
        if len(vals) != len(self.__labels):
            return 1, "That list doesn't match the number of labels."

        for i in range(len(self.__points)):
            if self.__points[i][0] == label:
                self.__points[i] = (label, vals)
                return 0, ""

        self.__points.append((label if label is not None else "", vals))

        return 0, ""

    def remove_point(self, label):
        if label not in [t[0] for t in self.__points]:
            return 1, "Error: You haven't plotted yourself in this plot."
        self.__points.remove(next(p for p in self.__points if p[0] == label))

        return 0, ""

    def generate_plot(self, toggle_labels=True):
        point_labels = [p[0] for p in self.__points]
        vals = [np.concatenate((p[1], [p[1][0]])) for p in self.__points]
        colors = [(color_hash[0] / 255, color_hash[1] / 255, color_hash[2] / 255)
                  for color_hash in [ColorHash(label).rgb for label in point_labels]]

        angles = np.linspace(0, 2 * np.pi, len(self.__labels), endpoint=False)
        angles = np.concatenate((angles, [angles[0]]))

        fig = plt.figure()
        ax = fig.add_subplot(111, polar=True)
        for i in range(len(vals)):
            ax.plot(angles, vals[i], "o-", linewidth=2, color=colors[i])
            ax.fill(angles, vals[i], alpha=0.25, color=colors[i])
        ax.set_thetagrids(angles * 180 / np.pi, self.__labels)
        ax.set_title(self.__name)
        ax.grid(True)

        if toggle_labels:
            ax.legend(point_labels, loc=(0.9, .95), labelspacing=0.1, fontsize="small")

        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        buffer.seek(0)

        # bot.send_photo(chat_id=chat_id, photo=buffer)
        # This returns the image itself that can then be sent.
        return 0, buffer

    def lookup_label(self, label):
        for p in self.__points:
            if p[0] == label:
                return 0, (p[1], p[2])
        return 1, "Name not found on that plot."

    def edit_plot(self, plot_args):
        self.__name = " ".join(plot_args.get("title")) if plot_args.get("title") is not None else self.__name
        self.__labels = " ".join(plot_args.get("labels")) if plot_args.get("labels") is not None else self.__labels
        self.__custompoints = plot_args.get("custompoints") if plot_args.get("custompoints") is not None else self.__custompoints

    def get_name(self):
        return self.__name

    def get_labels(self):
        return self.__labels

    def get_creator(self):
        return self.__createdby

    def get_points(self):
        return self.__points

    def get_id(self):
        return self.__id

    def get_last_modified(self):
        try:
            timestamp = self.__last_modified
            return timestamp
        except AttributeError:
            return None

    def set_last_modified(self, timestamp):
        self.__last_modified = timestamp

    def set_creator(self, username, user_id):
        self.__createdby = (username, user_id)