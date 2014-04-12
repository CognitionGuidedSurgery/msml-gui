# -*- encoding: utf-8 -*-

__author__ = 'weigl'

import msml.model.alphabet
import msml.env
import msml.frontend
import msml.model
import msml.xml

from .widgets import *
from .dialogs import *
from msmlgui import shared
from msmlgui.helper import *


PKG_DIR = path(__file__).dirname()

from PyQt4 import QtCore, QtGui, QtWebKit

icon = lambda x: QIcon(r':/icons/tango/16x16/%s.png' % x)

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s


class MSMLMainFrame(QtGui.QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.msml_model = msml_file_factory()
        self.msml_pdata = UiPersistentData()
        self.msml_vdata = UiVolatileData()

        self.setupUi()

        opListModel = OperatorListModel()
        self.listOperators.setModel(opListModel)
        self.listOperators.setVerticalScrollMode(QtGui.QListView.ScrollPerPixel)

        self.listOperators.clicked.connect(
            lambda index: self.show_in_operator_help(index.data(Qt.UserRole).toPyObject()))
        self.listOperators.doubleClicked.connect(
            lambda index: self.drop_new_operator(index.data(Qt.UserRole).toPyObject()))
        #        self.graphicsView.dropEvent.connect(self.drop_new_operator)


        self.last_path = path("~").expanduser()  #TODO init by config
        self.env_dialog = EnvEditor(self)
        self.scene_dialog = SceneEditor(self)

        a = AnnotationShape(
            "<html><a href='https://github.com/CognitionGuidedSurgery/msml/' target='new'>Welcome to MSML</a>", self,
            self.graphicsScene)
        a.setPos(200, 200)

    def _setupMenu(self):
        self.actionShowEnvEditor = QAction("Edit Environment ...", self)
        self.actionShowSceneEditor = QAction("Edit Scene ...", self)

        self.actionShowEnvEditor.setShortcut(QKeySequence("Ctrl-e"))
        self.actionShowSceneEditor.setShortcut(QKeySequence("Ctrl-s"))

        self.actionShowEnvEditor.triggered.connect(self.show_env_dialog)
        self.actionShowSceneEditor.triggered.connect(self.show_scene_dialog)

        self.menubar = QtGui.QMenuBar(self)

        ## file
        self.menuFile = self.menubar.addMenu("File")

        self.actionNew = self.menuFile.addAction(icon("document-new"), "New")
        self.actionNew.setShortcut(QKeySequence.New)

        self.actionOpen = self.menuFile.addAction(icon("document-open"), "Open")
        self.actionOpen.setShortcut(QKeySequence.Open)

        self.actionOpen.triggered.connect(self.search_open_file)

        self.actionSave = self.menuFile.addAction(icon("document-save"), "Save")
        self.actionSave.setShortcut(QKeySequence.Save)

        self.actionSaveAs = self.menuFile.addAction(icon("document-save-as"), "Save as...")
        self.actionSaveAs.setShortcut(QKeySequence.SaveAs)

        self.menuFile.addSeparator()

        self.actionClose = self.menuFile.addAction(icon("document-close"), "Close")
        self.actionClose.setShortcut(QKeySequence("Ctrl-F4"))

        #Tools
        self.menuTools = self.menubar.addMenu("Tools")

        self.actionRun = self.menuTools.addAction(icon("format-text-bold"), "Execute...")
        self.actionRun = self.menuTools.addAction(icon("format-text-italic"), "Execute in Cloud...")

        self.menuTools.addAction(self.actionAddAnnotation)



        ##Views
        self.menuViews = self.menubar.addMenu("Views")
        self.menuViews.addAction(self.dockVariables.toggleViewAction())
        self.menuViews.addAction(self.dockOperator.toggleViewAction())
        self.menuViews.addAction(self.dockHelp.toggleViewAction())
        self.menuViews.addAction(self.dockParameters.toggleViewAction())
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

        self.toolBar.addAction(self.actionNew)
        self.toolBar.addAction(self.actionOpen)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionAddAnnotation)


    def _setupCentralWidget(self):
        self.centralwidget = QtGui.QWidget(self)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.centralWidgetLayout = QtGui.QGridLayout(self.centralwidget)
        self.graphicsView = MSMLGraphicsView(self, self.centralwidget)

        self.graphicsScene = self.graphicsView.renew()

        self.graphicsView.setRenderHints(
            QtGui.QPainter.Antialiasing | QtGui.QPainter.HighQualityAntialiasing | QtGui.QPainter.TextAntialiasing)
        self.graphicsView.setRubberBandSelectionMode(QtCore.Qt.ContainsItemBoundingRect)
        self.centralWidgetLayout.addWidget(self.graphicsView, 0, 0, 1, 1)
        self.setCentralWidget(self.centralwidget)

    def _setupDockOperators(self):
        self.dockOperator = QtGui.QDockWidget("Operators", self)
        self.listOperators = QtGui.QListView(self.dockOperator)
        self.listOperators.setDragEnabled(True)
        self.dockOperator.setWidget(self.listOperators)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.dockOperator)

    def _setupDockParameters(self):
        self.dockParameters = QDockWidget("Parameters", self)
        self.dockParameters.setFloating(False)
        self.tabProperties = QtGui.QTableView(self.dockParameters)
        self.dockParameters.setWidget(self.tabProperties)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.dockParameters)

    def _setupDockHelp(self):
        self.dockHelp = QtGui.QDockWidget("Help", self)
        self.webOperatorHelp = QtWebKit.QWebView(self.dockHelp)
        self.webOperatorHelp.setUrl(QtCore.QUrl(_fromUtf8("about:blank")))
        self.dockHelp.setWidget(self.webOperatorHelp)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.dockHelp)

    def _setupDockVariable(self):
        self.dockVariables = QDockWidget("Variables", self)
        widget = QWidget(self.dockVariables)
        self.tableVariables = QTableView()
        layout = QVBoxLayout(widget)
        widget.setLayout(layout)

        layout.addWidget(self.tableVariables)

        buttons = QWidget(widget)
        blayout = QBoxLayout(QBoxLayout.LeftToRight, buttons)

        self.actionAddVariable = QAction(icon('folder-new'), "add", self)
        self.actionDeleteVariable = QAction(icon('edit-cut'), "delete", self)

        blayout.addSpacing(10)

        btn1 = QToolButton(self)
        btn1.setDefaultAction(self.actionDeleteVariable)
        btn2 = QToolButton(self)
        btn2.setDefaultAction(self.actionAddVariable)

        blayout.addSpacing(20)
        blayout.addWidget(btn1)
        blayout.addWidget(btn2)

        layout.addWidget(buttons)

        self.dockVariables.setWidget(widget)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.dockVariables)


    def setupUi(self):
        self.setObjectName(_fromUtf8("MainWindow"))
        self.resize(1012, 771)
        self.setDockNestingEnabled(True)
        self.setDockOptions(
            QtGui.QMainWindow.AllowNestedDocks | QtGui.QMainWindow.AllowTabbedDocks | QtGui.QMainWindow.AnimatedDocks)

        self.actionAddAnnotation = QAction(icon("address-book-new"), "Add Annotation", self)


        ## centeral widget
        self._setupCentralWidget()
        self._setupDockOperators()
        self._setupDockParameters()
        self._setupDockHelp()
        self._setupDockVariable()

        self._setupMenu()
        self._setupStatusbar()
        self._setupToolBar()

        QtCore.QMetaObject.connectSlotsByName(self)

    def open_file(self, filename):
        try:
            self.msml_vdata = UiVolatileData()
            self.msml_pdata = UiPersistentData.load_from_msml(filename)
            self.msml_model = msml.xml.load_msml_file(filename)
            self.graphicsScene = self.graphicsView.renew()
        except IndexError as e:
            raise e


    def search_open_file(self):
        MSML_FILE_FILTER = "MSML (*.xml *.msml *.msml.xml);; All types (*.*)"
        filename, _ = QFileDialog.getOpenFileNameAndFilter(self, "Open MSML file", self.last_path, MSML_FILE_FILTER)

        if filename:
            filename = path(filename)
            self.last_path = filename.dirname()
            self.open_file(filename)

    def drop_new_operator(self, operator):
        name = generate_name()

        task = msml.model.Task(name, {'id': name})
        task.operator = operator
        self.msml_model.workflow.add_task(task)

        shape = TaskShape(task, self)
        self.graphicsScene.addItem(shape)

        self.msml_vdata.task_map[task] = shape
        self.msml_vdata.task_map[shape] = task

    def set_task_active_propertyeditor(self, task):
        model = PropertyOperatorModel(task, self.tabProperties)
        self.tabProperties.setModel(model)

    def show_in_operator_help(self, operator):
        html = tpl_operator_help(o=operator)
        self.webOperatorHelp.setHtml(html)

    def show_env_dialog(self, *args):
        self.env_dialog.open()

    def show_scene_dialog(self, *args):
        self.scene_dialog.model = self.msml_model
        self.scene_dialog.open()


class PropertyOperatorModel(QAbstractTableModel):
    def __init__(self, task, parent=None):
        QAbstractTableModel.__init__(self)
        assert isinstance(task.operator, msml.model.Operator)

        self.task = task
        self.keys = list(task.operator.parameters.keys())
        self.keys.sort()
        self.operator = task.operator

    def rowCount(self, parent=QModelIndex()):
        return len(self.operator.parameters)

    def columnCount(self, parent=QModelIndex()):
        return 2

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            a = ["parameter", "value"]
            return a[section]
        else:
            return QVariant()

    def data(self, index, role=Qt.DisplayRole):
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
        self.operators = shared.msml_app.alphabet.operators
        self._order = list(self.operators.keys())

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.operators)

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            key = self._order[index.row()]
            op = self.operators[key]
            assert isinstance(op, msml.model.alphabet.Operator)
            if role == Qt.DisplayRole:
                return QVariant(op.name)
            if role == Qt.UserRole:
                return op
        return QVariant()
