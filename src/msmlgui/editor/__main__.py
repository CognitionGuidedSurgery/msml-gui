__author__ = 'weigl'

import sys
from PyQt4.QtGui import QApplication
from msmlgui.editor import *

print("Application start...")
app = QApplication(sys.argv)
ed = MainFrame()
ed.show()
app.exec_()

