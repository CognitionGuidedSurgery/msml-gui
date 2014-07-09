# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'overviewdock.ui'
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

class Ui_OverviewDock(object):
    def setupUi(self, OverviewDock):
        OverviewDock.setObjectName(_fromUtf8("OverviewDock"))
        OverviewDock.resize(400, 300)
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))
        self.verticalLayout = QtGui.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.widget = QtGui.QWidget(self.dockWidgetContents)
        self.widget.setObjectName(_fromUtf8("widget"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout_2.setMargin(0)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        spacerItem = QtGui.QSpacerItem(694, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.pushButton = QtGui.QPushButton(self.widget)
        self.pushButton.setFlat(True)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.horizontalLayout_2.addWidget(self.pushButton)
        self.verticalLayout.addWidget(self.widget)
        self.treeOverview = QtGui.QTreeWidget(self.dockWidgetContents)
        self.treeOverview.setObjectName(_fromUtf8("treeOverview"))
        self.treeOverview.headerItem().setText(0, _fromUtf8("1"))
        self.treeOverview.header().setVisible(False)
        self.verticalLayout.addWidget(self.treeOverview)
        OverviewDock.setWidget(self.dockWidgetContents)

        self.retranslateUi(OverviewDock)
        QtCore.QMetaObject.connectSlotsByName(OverviewDock)

    def retranslateUi(self, OverviewDock):
        OverviewDock.setWindowTitle(QtGui.QApplication.translate("OverviewDock", "Overview", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.setText(QtGui.QApplication.translate("OverviewDock", "PushButton", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    OverviewDock = QtGui.QDockWidget()
    ui = Ui_OverviewDock()
    ui.setupUi(OverviewDock)
    OverviewDock.show()
    sys.exit(app.exec_())

