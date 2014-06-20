__author__ = 'weigl'

import sys
from PyQt4.QtGui import QApplication
from msmlgui.text import *

print("Application start...")
app = QApplication(sys.argv)
ed = MainFrame()
ed.show()
app.exec_()

