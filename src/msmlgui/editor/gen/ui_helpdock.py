# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'helpdock.ui'
#
# Created: Wed Jul  9 08:29:50 2014
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_HelpDock(object):
    def setupUi(self, HelpDock):
        HelpDock.setObjectName(_fromUtf8("HelpDock"))
        HelpDock.resize(400, 357)
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))
        self.verticalLayout = QtGui.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.checkFixHelp_2 = QtGui.QCheckBox(self.dockWidgetContents)
        self.checkFixHelp_2.setObjectName(_fromUtf8("checkFixHelp_2"))
        self.horizontalLayout.addWidget(self.checkFixHelp_2)
        spacerItem = QtGui.QSpacerItem(691, 17, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.webView_2 = QtWebKit.QWebView(self.dockWidgetContents)
        self.webView_2.setUrl(QtCore.QUrl(_fromUtf8("about:blank")))
        self.webView_2.setObjectName(_fromUtf8("webView_2"))
        self.verticalLayout.addWidget(self.webView_2)
        HelpDock.setWidget(self.dockWidgetContents)

        self.retranslateUi(HelpDock)
        QtCore.QMetaObject.connectSlotsByName(HelpDock)

    def retranslateUi(self, HelpDock):
        HelpDock.setWindowTitle(QtGui.QApplication.translate("HelpDock", "Help", None, QtGui.QApplication.UnicodeUTF8))
        self.checkFixHelp_2.setText(QtGui.QApplication.translate("HelpDock", "fix content", None, QtGui.QApplication.UnicodeUTF8))

from PyQt4 import QtWebKit

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    HelpDock = QtGui.QDockWidget()
    ui = Ui_HelpDock()
    ui.setupUi(HelpDock)
    HelpDock.show()
    sys.exit(app.exec_())

