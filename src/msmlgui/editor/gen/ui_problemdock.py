# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'problemdock.ui'
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

class Ui_ProblemDock(object):
    def setupUi(self, ProblemDock):
        ProblemDock.setObjectName(_fromUtf8("ProblemDock"))
        ProblemDock.resize(400, 300)
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))
        self.verticalLayout = QtGui.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.widget_3 = QtGui.QWidget(self.dockWidgetContents)
        self.widget_3.setObjectName(_fromUtf8("widget_3"))
        self.horizontalLayout_4 = QtGui.QHBoxLayout(self.widget_3)
        self.horizontalLayout_4.setMargin(0)
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        spacerItem = QtGui.QSpacerItem(694, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem)
        self.pushButton_2 = QtGui.QPushButton(self.widget_3)
        self.pushButton_2.setFlat(True)
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.horizontalLayout_4.addWidget(self.pushButton_2)
        self.verticalLayout.addWidget(self.widget_3)
        self.tableProblems = QtGui.QTableWidget(self.dockWidgetContents)
        self.tableProblems.setGridStyle(QtCore.Qt.DashLine)
        self.tableProblems.setColumnCount(3)
        self.tableProblems.setObjectName(_fromUtf8("tableProblems"))
        self.tableProblems.setRowCount(0)
        self.tableProblems.verticalHeader().setVisible(True)
        self.verticalLayout.addWidget(self.tableProblems)
        ProblemDock.setWidget(self.dockWidgetContents)

        self.retranslateUi(ProblemDock)
        QtCore.QMetaObject.connectSlotsByName(ProblemDock)

    def retranslateUi(self, ProblemDock):
        ProblemDock.setWindowTitle(QtGui.QApplication.translate("ProblemDock", "Problems", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_2.setText(QtGui.QApplication.translate("ProblemDock", "PushButton", None, QtGui.QApplication.UnicodeUTF8))
        self.tableProblems.setSortingEnabled(True)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ProblemDock = QtGui.QDockWidget()
    ui = Ui_ProblemDock()
    ui.setupUi(ProblemDock)
    ProblemDock.show()
    sys.exit(app.exec_())

