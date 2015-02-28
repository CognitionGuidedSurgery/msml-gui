# -*- encoding: utf-8 -*-
__author__ = 'weigl'

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import ply.lex

from .xmllexer import tokenize
from msmlgui.editor.codeeditor.highlighter import XMLHighlighter, SOLARIZED_COLORS
from .flycheck import *
from .flowlayout import FlowLayout


DELAY_SEMANTIC_ANALYZE = 1000
ADDITIONAL_SPACE = 40
RIGHT_BORDER_MARGIN = 20


class Memoize(object):
    def __init__(self, f):
        self.f = f
        self.memo = {}

    def __call__(self, *args):
        if not args in self.memo:
            self.memo[args] = self.f(*args)
        return self.memo[args]


@Memoize
def create_round_icon(char, color=Qt.white):
    SIZE = 16
    pixmap = QPixmap(SIZE, SIZE)

    whole_rect = QRectF(0, 0, SIZE, SIZE)
    rect = QRectF(1, 1, SIZE - 2, SIZE - 2)

    painter = QPainter(pixmap)
    painter.begin(pixmap)

    painter.fillRect(whole_rect, Qt.white)

    painter.setBrush(QColor(color))
    flags = Qt.TextSingleLine | Qt.AlignCenter | Qt.AlignHCenter
    painter.drawEllipse(rect)

    painter.setPen(QPen(Qt.white))
    painter.drawText(rect, flags, char)

    painter.end()

    #writer = QImageWriter(char + "_test.bmp", "bmp")
    #writer.write(pixmap.toImage())
    return pixmap


class CompletionEntry(object):
    def __init__(self, text="n/a", insert=None, anchestor=True, parent=True, foreground=None, background=None,
                 icon=None, order=-1):
        self.anchestor = anchestor
        self.parent = parent
        self.text = text
        self.insert = insert if insert else text
        self.foreground = foreground
        self.background = background
        self.icon = icon
        self.order = order

    def __cmp__(self, other):
        return self.order - other.order


class CompletionModel(QAbstractListModel):
    def __init__(self, parent=None):
        super(CompletionModel, self).__init__(parent)
        import msmlgui.shared

        self.entries = []
        self.active_entries = []

        operator_icon = create_round_icon("o", Qt.darkBlue)
        attribute_icon = create_round_icon("a", Qt.darkGreen)

        for operator_name in msmlgui.shared.msml_app.alphabet.operators.keys():
            self.append(operator_name,
                        insert="<%s id=\"$\" />" % operator_name,
                        anchestor="workflow",
                        icon=operator_icon)

        for operator in msmlgui.shared.msml_app.alphabet.operators.values():
            for name in operator.acceptable_names():
                self.append(parent=operator.name,
                            text=name, icon=attribute_icon,
                            insert="%s=\"%s$\" />" % (name, ""))

        self.revalidate([])


    def append(self, *args, **kwargs):
        self.entries.append(CompletionEntry(*args, **kwargs))

    def revalidate(self, stack):
        self.beginResetModel()
        self.active_entries = []

        tagsInStack = {s.value for s in stack}

        try:
            topValue = stack[-1].value
        except:
            topValue = None

        for e in self.entries:
            select = True
            if e.parent is not True and e.parent != topValue:
                select = select and False

            if e.anchestor is not True and e.anchestor not in tagsInStack:
                select = select and False

            if select:
                self.active_entries.append(e)

        print "Revalidated: ", map(lambda x: x.text, self.active_entries)

        self.endResetModel()

    def data(self, index=QModelIndex(), role=Qt.DisplayRole):
        if not index.isValid():
            return

        row = index.row()
        entry = self.active_entries[row]

        if role == Qt.DisplayRole:
            return entry.text

        elif role == Qt.DecorationRole:
            return entry.icon

        elif role == Qt.BackgroundRole:
            return entry.background

        elif role == Qt.ForegroundRole:
            return entry.background

        elif role == Qt.UserRole:
            return entry.insert


    def rowCount(self, parent=QModelIndex()):
        return len(self.active_entries)


class BreadCrump(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        layout = FlowLayout()
        self.setLayout(layout)

        self.label = QLabel("", self)
        self.layout().addWidget(self.label)

    def clear(self):
        self.label.setText("")

    def setBreads(self, lis):
        self.clear()
        s = u" ▸ ".join(map(operator.itemgetter(0), lis))
        self.label.setText(s)


    def positionStackUpdate(self, tokens):
        values = map(operator.attrgetter("value", "lexpos"), tokens)
        self.setBreads(values)


import operator

