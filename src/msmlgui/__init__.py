__author__ = "Alexander Weigl <uiduw@student.kit.edu>"
__date__ = "2014-04-09"

import sys
import msmlgui.rcc

from .base import *

import msmlgui.shared

from msml.frontend import App as MsmlApp
from PyQt4.QtGui import QIcon


class App(object):
    def __init__(self):
        pass

    def run(self):

        #TODO parse command line for addition arguments
        msmlgui.shared.msml_app = MsmlApp(add_search_path=["/home/weigl/workspace/msml/share/"])
        QIcon.setThemeName("tango")


        app = QtGui.QApplication(sys.argv)

        #TODO parse command line for open files
        frame = MSMLMainFrame()
        frame.show()
        sys.exit(app.exec_())

