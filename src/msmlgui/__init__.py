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

class MSMLMainFrame(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        uic.loadUi(PKG_DIR / "mainframe.ui", self)

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

    def drop_new_operator(self, operator):
        task = msml.model.Task(operator.name, {'id': "<i>not set</i>"})
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
        print role
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

    msml.env.load_user_file()
    msml.env.current_alphabet = msml.frontend.alphabet({'<paths>':[], 'alphabet': 'a', '--xsd-file':False, '-S': True})

    app = QtGui.QApplication(sys.argv)
    frame = MSMLMainFrame()
    frame.show()
    sys.exit(app.exec_())

