# -*- encoding: utf-8 -*-
from PyQt4.QtGui import QFileDialog

__author__ = 'weigl'

from PyQt4 import QtGui, uic, QtCore
from path import path
import msml.model.alphabet
import msml.env
import msml.frontend
import msml.model

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from msml.titen import titen
from .widgets import *

OPERATOR_HELP  = titen("""
<html>
<body>
<style>
body {{font-size:9pt;}
h1   {{ font-size:11pt; font-weight:bold;}
h2   {{ font-size: 10pt; font-weight:bold;}
table {{ width: 100%;}
td {{ border: 1;}

</style>

<h1>{$name}</h1>
<br />

<table>
<tr>
    <td>Name</td>
    <td>Sort</td>
    <td>Format</td>
    <td>Type</td>
</tr>

<tr>
  <td colspan="4">
    <h2>Inputs</h2>
  </td>
</tr>

{for i in inputs}
<tr>
    <td>{$i.name}</td>
    <td>{$i.sort}</td>
    <td>{$i.format}</td>
    <td>{$i.type}</td>
</tr>
{end}

<tr>
  <td colspan="4">
    <h2>Outputs</h2>
  </td>
</tr>

{for i in outputs}
<tr>
    <td>{$i.name} </td>
    <td>{$i.sort} </td>
    <td>{$i.format}</td>
    <td>{$i.type}</td>
</tr>
{end}

<tr>
  <td colspan="4">
    <h2>Parameters</h2>
  </td>
</tr>

{for i in parameters}
<tr>
    <td>{$i.name} </td>
    <td>{$i.sort} </td>
    <td>{$i.format}</td>
    <td>{$i.type}</td>
</tr>
{end}
</table>

</body>
</html>
""")

PKG_DIR = path(__file__).dirname()


from PyQt4 import QtCore, QtGui, QtWebKit

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

from msmlgui.widgets import MSMLGraphicsView
import msmlgui.rcc

from .dialogs import *

class MSMLMainFrame(QtGui.QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi()

        opListModel = OperatorListModel()

        self.listOperators.setModel(opListModel)
        view = ViewDelegate()
        self.listOperators.setItemDelegate(view)
        self.listOperators.setVerticalScrollMode(QtGui.QListView.ScrollPerPixel)

        self.listOperators.clicked.connect(lambda index: self.show_in_operator_help(index.data().toPyObject()))
        self.listOperators.doubleClicked.connect(
            lambda index: self.drop_new_operator(index.data().toPyObject()))
#        self.graphicsView.dropEvent.connect(self.drop_new_operator)

        self.msmlobj = msml.model.MSMLFile()
        self.graphicsScene = MSMLGraphicsScene(self.graphicsView)
        self.graphicsScene.mainframe = self
        self.graphicsView.setScene(self.graphicsScene)

        self.mappingTask = {}

        self.actionOpen.setIcon(QIcon.fromTheme("document-open"))

        self.env_dialog = EnvEditor(self)
        self.scene_dialog = SceneEditor(self)

    def _setupMenu(self):
        self.actionOpen = QtGui.QAction("Open", self)
        self.actionClose = QtGui.QAction("Close", self)

        self.actionShowDockParameters = QAction("Paramters", self)
        self.actionShowDockHelp = QAction("Help", self)
        self.actionShowDockVariables = QAction("Variables", self)
        self.actionShowDockOperators = QAction("Operators", self)

        self.actionShowDockParameters.setCheckable(True)
        self.actionShowDockOperators.setCheckable(True)
        self.actionShowDockHelp.setCheckable(True)
        self.actionShowDockVariables.setCheckable(True)

        self.actionShowEnvEditor = QAction("Edit Environment ...", self)
        self.actionShowSceneEditor = QAction("Edit Scene ...", self)

        self.actionShowEnvEditor.setShortcut(QKeySequence("Alt-e"))
        self.actionShowSceneEditor.setShortcut(QKeySequence("Alt-s"))


        self.actionShowEnvEditor.triggered.connect(self.show_env_dialog)
        self.actionShowSceneEditor.triggered.connect(self.show_scene_dialog)


        self.menubar = QtGui.QMenuBar(self)

        ## file
        self.menuFile = self.menubar.addMenu("File")
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionClose)

        ##Views
        self.menuViews = self.menubar.addMenu("Views")
        self.menuViews.addAction(self.actionShowDockVariables)
        self.menuViews.addAction(self.actionShowDockOperators)
        self.menuViews.addAction(self.actionShowDockHelp)
        self.menuViews.addAction(self.actionShowDockParameters)
        self.menuViews.addSeparator()

        self.menuViews.addAction(self.actionShowEnvEditor)
        self.menuViews.addAction(self.actionShowSceneEditor)

        ## help
        self.menuHelp = self.menubar.addMenu("Help")

        self.setMenuBar(self.menubar)

    def _setupStatusbar(self):
        self.statusbar = QtGui.QStatusBar(self)
        self.setStatusBar(self.statusbar)

    def _setupToolBar(self):
        self.toolBar = QtGui.QToolBar(self)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)

    def _setupCentralWidget(self):
        self.centralwidget = QtGui.QWidget(self)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.centralWidgetLayout = QtGui.QGridLayout(self.centralwidget)
        self.graphicsView = MSMLGraphicsView(self.centralwidget)
        self.graphicsView.setRenderHints(
            QtGui.QPainter.Antialiasing | QtGui.QPainter.HighQualityAntialiasing | QtGui.QPainter.TextAntialiasing)
        self.graphicsView.setRubberBandSelectionMode(QtCore.Qt.ContainsItemBoundingRect)
        self.centralWidgetLayout.addWidget(self.graphicsView, 0, 0, 1, 1)
        self.setCentralWidget(self.centralwidget)

    def _setupDockOperators(self):
        self.dockWidget = QtGui.QDockWidget("Operators", self)
        self.dockWidget.setFeatures(QtGui.QDockWidget.DockWidgetFloatable | QtGui.QDockWidget.DockWidgetMovable)
        self.dockWidget.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        self.dockWidgetContents = QtGui.QWidget()
        self.gridLayout_2 = QtGui.QGridLayout(self.dockWidgetContents)
        self.scrollArea = QtGui.QScrollArea(self.dockWidgetContents)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.gridLayout_5 = QtGui.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_5.setMargin(0)
        self.listOperators = QtGui.QListView(self.scrollAreaWidgetContents)
        self.listOperators.setDragEnabled(True)
        self.listOperators.setDragDropMode(QtGui.QAbstractItemView.DragOnly)
        self.listOperators.setObjectName(_fromUtf8("listOperators"))
        self.gridLayout_5.addWidget(self.listOperators, 0, 1, 1, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.gridLayout_2.addWidget(self.scrollArea, 0, 1, 1, 1)
        self.dockWidget.setWidget(self.dockWidgetContents)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.dockWidget)

    def _setupDockParameters(self):
        self.dockWidget_3 = QtGui.QDockWidget("Parameters", self)
        self.dockWidget_3.setFloating(False)
        self.dockWidgetContents_3 = QtGui.QWidget()
        self.gridLayout = QtGui.QGridLayout(self.dockWidgetContents_3)
        self.scrollArea_2 = QtGui.QScrollArea(self.dockWidgetContents_3)
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollAreaWidgetContents_2 = QtGui.QWidget()
        self.gridLayout_6 = QtGui.QGridLayout(self.scrollAreaWidgetContents_2)
        self.gridLayout_6.setMargin(0)
        self.tabProperties = QtGui.QTableView(self.scrollAreaWidgetContents_2)
        self.gridLayout_6.addWidget(self.tabProperties, 0, 0, 1, 1)
        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_2)
        self.gridLayout.addWidget(self.scrollArea_2, 0, 0, 1, 1)
        self.dockWidget_3.setWidget(self.dockWidgetContents_3)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.dockWidget_3)

    def _setupDockHelp(self):
        self.dockWidget_6 = QtGui.QDockWidget("Help", self)
        self.dockWidget_6.setFeatures(QtGui.QDockWidget.DockWidgetFloatable | QtGui.QDockWidget.DockWidgetMovable)
        self.dockWidgetContents_6 = QtGui.QWidget()
        self.gridLayout_7 = QtGui.QGridLayout(self.dockWidgetContents_6)
        self.webOperatorHelp = QtWebKit.QWebView(self.dockWidgetContents_6)
        self.webOperatorHelp.setUrl(QtCore.QUrl(_fromUtf8("about:blank")))
        self.gridLayout_7.addWidget(self.webOperatorHelp, 0, 0, 1, 1)
        self.dockWidget_6.setWidget(self.dockWidgetContents_6)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.dockWidget_6)

    def setupUi(self):
        self.setObjectName(_fromUtf8("MainWindow"))
        self.resize(1012, 771)
        self.setDockNestingEnabled(True)
        self.setDockOptions(QtGui.QMainWindow.AllowNestedDocks|QtGui.QMainWindow.AllowTabbedDocks|QtGui.QMainWindow.AnimatedDocks)

        self._setupMenu()
        self._setupStatusbar()
        self._setupToolBar()

        ## centeral widget
        self._setupCentralWidget()
        self._setupDockOperators()
        self._setupDockParameters()
        self._setupDockHelp()

        QtCore.QMetaObject.connectSlotsByName(self)

    def open_file(self, filename):
        pass #TODO

    def search_open_file(self):
        pass #TODO

    def drop_new_operator(self, operator):
        name = generate_name()

        task = msml.model.Task(name, {'id': name})
        task.operator = operator
        self.msmlobj.workflow.add_task(task)

        shape = TaskShape(task,self)

        self.graphicsScene.addItem(shape)

        self.mappingTask[task] = shape
        self.mappingTask[shape] = task

    def set_task_active_propertyeditor(self, task):
        model = PropertyOperatorModel(task, self.tabProperties)
        self.tabProperties.setModel(model)

    def show_in_operator_help(self, operator):

        html = OPERATOR_HELP(name = operator.name,
                      inputs = operator.input.values(),
                      outputs = operator.output.values(),
                      parameters = operator.parameters.values())

        self.webOperatorHelp.setHtml(html)
        pass

    def show_env_dialog(self, *args):
        self.env_dialog.open()

    def show_scene_dialog(self, *args):
        self.scene_dialog.model = self.msmlobj
        self.scene_dialog.open()

def generate_name(prefix = "task", suffix = ""):
    import random
    chars = [chr(i) for i in range(65, 110)]
    rand =''.join(random.sample(chars, 5))
    return prefix + rand + suffix



class ViewDelegate(QtGui.QItemDelegate):
    def __init__(self):
        QtGui.QItemDelegate.__init__(self)

    def sizeHint(self, QStyleOptionViewItem, QModelIndex):
        return QtCore.QSize(15,20)

    def paint(self, painter, option, index):
        variant = index.data()
        assert(painter, QtGui.QPainter)
        assert(variant,QtCore.QVariant)
        op = variant.toPyObject()
        assert(op, msml.model.alphabet.Operator)

#        print option

        painter.save()
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        if option.state & QtGui.QStyle.State_Selected:
            painter.setBrush(option.palette.highlightedText())
            painter.setBrush(QtGui.QBrush(QtCore.Qt.green))
        else:
            painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
        painter.drawRect(option.rect)

        painter.setPen(QtGui.QPen(QtCore.Qt.black))
        painter.drawText(option.rect, QtCore.Qt.AlignLeft,  op.name)
        painter.restore()


        # rahmen = option.rect.adjusted(self.abstand, self.abstand,
        #                             -self.abstand, -self.abstand)
        # rahmenTitel = rahmen.adjusted(self.abstandInnen,
        #               self.abstandInnen, -self.abstandInnen+1, 0)
        # rahmenTitel.setHeight(self.titelHoehe)
        # rahmenTitelText = rahmenTitel.adjusted(self.abstandText,
        #                                 0, self.abstandText, 0)
        # datensatz = index.data().toList()
        # painter.save()
        # painter.setPen(self.rahmenStift)
        # painter.drawRect(rahmen)
        # painter.fillRect(rahmenTitel, self.titelFarbe)
        #
        # # Titel schreiben
        # painter.setPen(self.titelTextStift)
        # painter.setFont(self.titelSchriftart)
        # painter.drawText(rahmenTitelText,
        #             QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
        #             datensatz[0].toString())
        #
        # # Adresse schreiben
        # painter.setPen(self.textStift)
        # painter.setFont(self.textSchriftart)
        # for i, eintrag in enumerate(datensatz[1:]):
        #     painter.drawText(rahmenTitel.x() + self.abstandText,
        #            rahmenTitel.bottom() + (i+1)*self.zeilenHoehe,
        #            "%s" % eintrag.toString())
        # painter.restore()


class PropertyOperatorModel(QAbstractTableModel):
    def __init__(self, task, parent = None):
        QAbstractTableModel.__init__(self)
        assert isinstance(task.operator, msml.model.Operator)

        self.task = task
        self.keys = list(task.operator.parameters.keys())
        self.keys.sort()
        self.operator = task.operator

    def rowCount(self, parent = QModelIndex()):
        return len(self.operator.parameters)

    def columnCount(self, parent = QModelIndex()):
        return 2

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            a = ["parameter", "value"]
            return a[section]
        else:
            return QVariant()

    def data(self, index, role = Qt.DisplayRole):
        #ToolTipRole, DecorationRole
        if role == Qt.DisplayRole:
            i = index.row()
            j = index.column()

            k = self.keys[i]

            if j == 0:
                return self.operator.parameters[k].name
            else:
                try:
                    return self.task.attributes[k]
                except:
                    pass
#        print role
        return QVariant()

    def flags(self, index):
        f = QAbstractTableModel.flags(self, index)
        if index.column == 1:
            return f | Qt.ItemIsEditable | Qt.ItemIsEnabled
        else:
            return f


class OperatorListModel(QtCore.QAbstractListModel):
    def __init__(self):
        QtCore.QAbstractListModel.__init__(self)
        self.operators = msml.env.current_alphabet.operators
        self._order = list(self.operators.keys())

    def rowCount(self, parent = QtCore.QModelIndex()):
        return len(self.operators)

    def data(self, index, role = QtCore.Qt.DisplayRole):
        key = self._order[index.row()]
        op = self.operators[key]
        assert isinstance(op, msml.model.alphabet.Operator)
        return op

def run():
    import sys
    import msmlgui.rcc

    QIcon.setThemeName("tango")


    msml.env.load_user_file()
    msml.env.current_alphabet = msml.frontend.alphabet({'<paths>':[], 'alphabet': 'a', '--xsd-file':False, '-S': True})

    app = QtGui.QApplication(sys.argv)
    frame = MSMLMainFrame()
    frame.show()
    sys.exit(app.exec_())

