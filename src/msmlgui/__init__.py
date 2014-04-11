__author__ = "Alexander Weigl <uiduw@student.kit.edu>"
__date__ = "2014-04-09"

import sys

from .base import *

import msmlgui.rcc
import msmlgui.shared

from msml.frontend import App as MsmlApp
from PyQt4.QtGui import QIcon


class App(object):
    def __init__(self):
        pass

    def run(self):

        #TODO parse command line for addition arguments
        msmlgui.shared.msml_app = MsmlApp(add_search_path=["/home/weigl/workspace/msml/share/"])

        app = QtGui.QApplication(sys.argv)
        app.setAttribute(Qt.AA_DontShowIconsInMenus, False)

        QIcon.setThemeName("tango")

        for path in QtGui.QIcon.themeSearchPaths():
            print "%s/%s" % (path, QtGui.QIcon.themeName())

            print QIcon.hasThemeIcon("document-open")


        #TODO parse command line for open files
        frame = MSMLMainFrame()

        from path import path
        f = path("/home/weigl/workspace/msml/examples/PythonExamples/color-example.xml")
        frame.open_file(f)

        frame.show()
        sys.exit(app.exec_())

