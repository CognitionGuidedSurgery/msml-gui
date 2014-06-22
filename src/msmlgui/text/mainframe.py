__author__ = 'weigl'


from path import path
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import msmlgui.rcc

from .flycheck import build_overview

from .editor_ui import Ui_MainWindow
from ..help import *

icon = lambda x: QIcon(r':/icons/tango/16x16/%s.png' % x)


class MainFrame(Ui_MainWindow, QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)

        self._setupActions()
        self.setupToolBar()

        self.readSettings()

        self.textEditor.firePositionStackUpdate.connect(self.breadcrump.positionStackUpdate)
        self.textEditor.firePositionStackUpdate.connect(self.openHelp)
        self.textEditor.problemsChanged.connect(self.updateProblems)

        self.textEditor.contentChanged.connect(self.updateOverview)

        self.open("/org/share/home/weigl/workspace/msml/examples/BunnyExample/bunnyCGAL.msml.xml")

        self.oldHelp = None

    def _setupActions(self):
        self.actionNew = QAction(icon("document-new"), "New", self)
        self.actionNew.setShortcut(QKeySequence.New)

        self.actionOpen = QAction(icon("document-open"), "Open", self)
        self.actionOpen.setShortcut(QKeySequence.Open)

        self.actionOpen.triggered.connect(self.search_open_file)

        self.actionSave = QAction(icon("document-save"), "Save", self)
        self.actionSave.setShortcut(QKeySequence.Save)
        self.actionSave.triggered.connect(self.save_file)

        self.actionSaveAs = QAction(icon("document-save-as"), "Save as...", self)
        self.actionSaveAs.setShortcut(QKeySequence.SaveAs)
        self.actionSaveAs.triggered.connect(self.save_file_as)

        self.actionClose = QAction(icon("document-close"), "Close", self)
        self.actionClose.setShortcut(QKeySequence("Alt-F4"))


    def setupToolBar(self):
        file = [self.actionNew, self.actionOpen, self.actionSave, self.actionSaveAs, self.actionClose]
        self.toolBar.addActions(file)
        self.menuFile.clear()
        self.menuFile.addActions(file)

        self.menuWindow.addAction(self.dockHelp.toggleViewAction())


    def open_file(self, filename):
        pass

    def closeEvent(self, event=QCloseEvent()):
        settings = QSettings("CoginitionGuidedSurgery", "msml-gui-editor")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        QMainWindow.closeEvent(self, event)

    def readSettings(self):
        settings = QSettings("CoginitionGuidedSurgery", "msml-gui-editor")
        self.restoreGeometry(settings.value("geometry").toByteArray())
        self.restoreState(settings.value("windowState").toByteArray())

    def search_open_file(self):
        MSML_FILE_FILTER = "MSML (*.xml *.msml *.msml.xml);; All types (*.*)"
        filename, _ = QFileDialog.getOpenFileNameAndFilter(self, "Open MSML file", self.last_path, MSML_FILE_FILTER)

        if filename:
            filename = path(filename)
            self.last_path = filename.dirname()
            self.open_file(filename)

    def save_file(self):
        if self.last_save_path is None:
            self.save_file_as()

        from msmlgui.helper.writer import to_xml, save_xml

        xml = to_xml(self.msml_model)
        save_xml(self.last_save_path, xml)


    def save_file_as(self):
        MSML_FILE_FILTER = "MSML (*.xml *.msml *.msml.xml);; All types (*.*)"

        last_dir = ""
        if self.last_save_path:
            last_dir = self.last_save_path.dirname()

        filename = QFileDialog.getSaveFileName(self, "Open MSML file", last_dir, MSML_FILE_FILTER)

        if filename:
            self.last_save_path = path(filename)
            self.save_file()

    def openHelp(self, toks):
        try:
            tok = toks[-1]
            c = get_help(tok.value)

            if c == self.oldHelp: return

            self.oldHelp = c


            if c.startswith("http://"):
                print "Open Help: %s" % c
                self.webView.setUrl(QUrl(c))
            else:
                self.webView.setHtml(c)
        except IndexError: pass

    def updateOverview(self, tokens, char2line):
        overview = build_overview(tokens)

        self.treeOverview.clear()

        def appendUnder(name, seq):
            item = QTreeWidgetItem(self.treeOverview)
            item.setText(0, name)
            item.addChildren(seq)


        appendUnder("Variables", overview.variables)
        appendUnder("Objects", overview.objects)
        appendUnder("Tasks", overview.tasks)
        appendUnder("Environment", overview.environment)

    def updateProblems(self, problems):
        print "updateProblems", problems
        self.tableProblems.clear()

        self.tableProblems.setColumnCount(3)
        self.tableProblems.setRowCount(len(problems))

        for i, p in enumerate(problems):
            c2 = QTableWidgetItem(p.message)
            c3 = QTableWidgetItem(str(p.position))

            if p.level == 1:
                c2.setForeground(QBrush(Qt.darkRed))
                c3.setForeground(QBrush(Qt.darkRed))
            else:
                c2.setForeground(QBrush(Qt.darkBlue))
                c3.setForeground(QBrush(Qt.darkBlue))


            self.tableProblems.setItem(i, 0, c2)
            self.tableProblems.setItem(i, 1, c3)




    def open(self, filename):
        with open(filename) as fp:
            content = fp.read()
            self.textEditor.insertPlainText(content)

