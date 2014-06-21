# -*- encoding: utf-8 -*-
__author__ = 'weigl'

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import ply.lex

from .xmllexer import tokenize
from .highlighter import XMLHighlighter, SOLARIZED_COLORS
from .flycheck import *
from .flowlayout import FlowLayout


DELAY_SEMANTIC_ANALYZE = 1000
ADDITIONAL_SPACE = 40
RIGHT_BORDER_MARGIN = 20

import collections

CompletionEntry = collections.namedtuple("CompletionEntry", "parent text insert")



class CompletionModel(QAbstractListModel):
    def __init__(self, parent = None):
        super(CompletionModel, self).__init__(parent)
        import msmlgui.shared

        self.entries = []

        self.active_entries = []

        for operator_name in msmlgui.shared.msml_app.alphabet.operators.keys():
            self.entries.append(CompletionEntry("workflow", operator_name, "<%s id=\"^$\" />"%operator_name))

        for operator in msmlgui.shared.msml_app.alphabet.operators.values():
            for name in operator.acceptable_names():
                self.entries.append(CompletionEntry(operator.name+"$", name,
                                                "%s=\"^%s$\" />"%(name, "type")))

        self.revalidate([])

    def revalidate(self, stack):
        self.beginResetModel()
        self.active_entries = []

        tagsInStack = {s.value for s in stack}

        try:
            topValue =stack[-1].value
        except:
            topValue = None


        for e in self.entries:
            if e.parent.endswith('$') and e.parent[:-1] == topValue:
                self.active_entries.append(e)
            elif e.parent in tagsInStack:
                self.active_entries.append(e)


        print "Revalidated: ", map(lambda x: x.text, self.active_entries)

        self.endResetModel()

    def data(self, index = QModelIndex(), role=Qt.DisplayRole):
        if not index.isValid():
            return

        row = index.row()
        entry = self.active_entries[row]
        if role == Qt.DisplayRole:
            return entry.text

        if role == Qt.UserRole:
            return entry.insert


    def rowCount(self, parent = QModelIndex()):
        return len(self.active_entries)

class LineNumberArea(QWidget):
    def __init__(self, codeeditor):
        super(LineNumberArea, self).__init__(codeeditor)
        self.codeeditor = codeeditor

    def sizeHint(self):
        return QSize(self.codeeditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        assert isinstance(event, QPaintEvent)
        QWidget.paintEvent(self, event)
        self.codeeditor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        QTextEdit.__init__(self, parent)
        self.lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.cursorPositionChanged.connect(self.onCursorPositionChanged)
        self.textChanged.connect(self.triggerSemanticAnalyze)

        self.updateLineNumberAreaWidth(0)

        self.semantic_enabled = True

        self.highlighter = XMLHighlighter(self.document())

        p = self.palette()
        p.setColor(QPalette.Base, self.highlighter.getBackground())
        p.setColor(QPalette.Text, self.highlighter.getForeground())
        self.setPalette(p)

        self.highlightCurrentLine()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.runSemanticAnalyze)
        self.timer.setSingleShot(True)

        self.triggerSemanticAnalyze()

        self.sections = {}

        ## completer

        self._completer = None

        completer = QCompleter(self)
        self.completion_model = CompletionModel()

        self.firePositionStackUpdate.connect(self.completion_model.revalidate)

        completer.setModel(self.completion_model)
        completer.setModelSorting(QCompleter.CaseSensitivelySortedModel)
        completer.setCaseSensitivity(Qt.CaseSensitive)
        completer.setWrapAround(False)
        self.setCompleter(completer)


    def lineNumberAreaPaintEvent(self, event):
        assert isinstance(event, QPaintEvent)

        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()

        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        font_height = self.fontMetrics().height()
        rightpos = self.lineNumberArea.width() - RIGHT_BORDER_MARGIN

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = "%d" % (blockNumber + 1)
                painter.setPen(Qt.black)

                painter.drawText(0, top, rightpos,
                                 font_height,
                                 Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height());
            blockNumber += 1

        painter.save()
        offset = self.firstVisibleBlock().blockNumber()
        x = self.lineNumberArea.width() - 5
        for (a, b), clr in self.sections.items():
            a -= offset + 1
            b -= offset

            if a < 0:
                pxA = 0
            else:
                pxA = int(font_height * a)

            pxB = int(font_height * b)

            painter.setPen(QPen(QBrush(QColor(clr)), 3))
            painter.drawLine(x, pxA, x, pxB)
        painter.restore()

    def lineNumberAreaWidth(self):

        mx = max(1, self.blockCount())
        digits = 1
        while mx >= 10:
            mx /= 10
            digits += 1

        space = ADDITIONAL_SPACE + self.fontMetrics().width('9') * digits
        return space

    def resizeEvent(self, event):
        assert isinstance(event, QResizeEvent)

        QPlainTextEdit.resizeEvent(self, event)

        cr = self.contentsRect()
        width = self.lineNumberAreaWidth()
        rect = QRect(cr.left(), cr.top(), width, cr.height())
        self.lineNumberArea.setGeometry(rect)

    def updateLineNumberAreaWidth(self, newBlockCount):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def highlightCurrentLine(self):

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            lineColor = self.highlighter.getCurrentLineColor()

            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()

            self.setExtraSelections([selection])
        else:
            self.setExtraSelections([])

    def updateLineNumberArea(self, rect, dy):
        if dy > 0:
            self.lineNumberArea.scroll(0, dy)
        else:
            area_width = self.lineNumberArea.width()
            self.lineNumberArea.update(0, rect.y(), area_width, rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def onCursorPositionChanged(self):
        text = str(self.toPlainText())
        tokens = tokenize(text)
        self.whereIam(tokens)

    def triggerSemanticAnalyze(self):
        print "Trigger Semantic Analyze"
        if self.semantic_enabled:
            self.timer.stop()
            self.timer.start(DELAY_SEMANTIC_ANALYZE)
            self.document().setModified(False)

    def runSemanticAnalyze(self):
        print "ANALyze"

        self.semantic_enabled = False
        text = str(self.toPlainText())
        char2line = self.charLine(text)

        self.findSections(text, char2line)
        tokens = tokenize(text)
        self.findErrorsAndWarnings(tokens)
        self.contentChanged.emit(tokens, char2line)
        self.semantic_enabled = True

    def findErrorsAndWarnings(self, toks):
        errors = find_errors(toks)

        cursor = self.textCursor();
        errorFormat = self.highlighter.theme['ERROR']

        for er in errors:
            s, e = er.position
            cursor.setPosition(s)
            cursor.setPosition(e, QTextCursor.KeepAnchor)
            cursor.mergeCharFormat(errorFormat)

        self.document().setModified(False)

    def charLine(self, text):
        d = list()
        line = 1

        for c in text:
            d.append(line)
            if c == "\n": line += 1

        return d

    def findSections(self, text, c2l):
        self.sections = {}

        def fS(start, end, color):
            a = text.find(start)
            b = text.find(end) + len(end)
            try:
                self.sections[c2l[a], c2l[b]] = color
            except:
                pass

        fS("<variables>", "</variables>", SOLARIZED_COLORS['orange'])
        fS("<workflow>", "</workflow>", SOLARIZED_COLORS['blue'])
        fS("<scene>", "</scene>", SOLARIZED_COLORS['magenta'])
        fS("<environment>", "</environment>", SOLARIZED_COLORS['violet'])

        print self.sections

    def whereIam(self, tokens):
        cursor = self.textCursor().position()
        stack = []

        it = iter(tokens)
        for tok in it:
            assert isinstance(tok, ply.lex.LexToken)

            if tok.lexpos > cursor: break

            if tok.type == "OPENTAGOPEN":
                stack.append(next(it))
            if tok.type in ("LONETAGCLOSE", "CLOSETAGOPEN") and len(stack) > 0:
                stack.pop()

        self.positionStack = stack
        self.firePositionStackUpdate.emit(self.positionStack)


    def setCompleter(self, completer):
        assert isinstance(completer, QCompleter)

        if self._completer:
            self._completer.disconnect(self, 0)

        self._completer = completer

        if self._completer:
            self._completer.setWidget(self)
            self._completer.activated.connect(self.insertCompletion)

    def completer(self):
        return self._completer

    def insertCompletion(self, text):
        if self._completer.widget() == self:
            text = str(text)
            tc = self.textCursor()
            extra = len(text) - len(self._completer.completionPrefix())

            tc.movePosition(QTextCursor.Left)
            tc.movePosition(QTextCursor.EndOfWord)
            tc.insertText(text[-extra:])
            self.setTextCursor(tc)

    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def focusInEvent(self, event):
        assert isinstance(event, QFocusEvent)

        if self._completer:
            self._completer.setWidget(self)

        QPlainTextEdit.focusInEvent(self, event)

    def keyPressEvent(self, event):
        assert isinstance(event, QKeyEvent)

        if self._completer and self._completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                event.ignore()
                return

        isShortcut = ((event.modifiers() & Qt.ControlModifier) and event.key() == Qt.Key_E)

        if not self._completer or not isShortcut:  # do not process the shortcut when we have a completer
            QPlainTextEdit.keyPressEvent(self, event)
            return

        ctrlOrShift = event.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)
        if not self._completer or (ctrlOrShift and event.text().isEmpty()):
            return

        eow = "~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="
        hasModifier = (event.modifiers() != Qt.NoModifier) and not ctrlOrShift
        completionPrefix = self.textUnderCursor()

        if not isShortcut \
                and (hasModifier \
                             or event.text().isEmpty() \
                             or completionPrefix.length() < 3 \
                             or eow.contains(event.text().right(1))):
            self._completer.popup().hide()
            return

        if completionPrefix != self._completer.completionPrefix():
            self._completer.setCompletionPrefix(completionPrefix)
            self._completer.popup().setCurrentIndex(self._completer.completionModel().index(0, 0))

        cr = self.cursorRect()
        cr.setWidth(self._completer.popup().sizeHintForColumn(0)
                    + self._completer.popup().verticalScrollBar().sizeHint().width())
        self._completer.complete(cr);


    firePositionStackUpdate = pyqtSignal([list])
    contentChanged = pyqtSignal([list, list])


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