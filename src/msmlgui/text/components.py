#-*- encoding: utf-8 -*-
__author__ = 'weigl'

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from .xmllexer import tokenize
from .highlighter import XMLHighlighter, SOLARIZED_COLORS
from .flycheck import *

DELAY_SEMANTIC_ANALYZE = 1000
ADDITIONAL_SPACE = 40
RIGHT_BORDER_MARGIN = 20


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
        self.textChanged.connect(self.triggerSemanticAnalyze)

        self.updateLineNumberAreaWidth(0)

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

    def triggerSemanticAnalyze(self):
        print "Trigger Semantic Analyze"
        if self.document().isModified():
            self.timer.stop()
            self.timer.start(DELAY_SEMANTIC_ANALYZE)
            self.document().setModified(False)

    def runSemanticAnalyze(self):
        print "ANALyze"

        text = str(self.toPlainText())
        char2line = self.charLine(text)
        self.findSections(text, char2line)
        tokens = tokenize(text)
        self.whereIam(tokens)
        self.findErrorsAndWarnings(tokens)

    def findErrorsAndWarnings(self,toks):
        errors = find_errors(toks)

        cursor = self.textCursor();
        errorFormat = self.highlighter.theme['ERROR']

        for er in errors:
            s,e = er.position
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

    firePositionStackUpdate = pyqtSignal([list])


import ply.lex



from .flowlayout import FlowLayout

class BreadCrump(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        layout = FlowLayout()
        self.setLayout(layout)
        self.clear()

    def clear(self):
        self.layout().itemList =[]

    def setBreads(self, lis):
        self.clear()
        for item in lis:

            lbl = QLabel(item[0], self)
            sep = QLabel(u"▸", self)

            print item
            self.layout().addWidget(lbl)
            self.layout().addWidget(sep)

        try:
            self.layout().itemList.pop()
        except IndexError: pass

        #self.layout().addStretch()
        self.repaint()


    def positionStackUpdate(self, tokens):
        values = map(operator.attrgetter("value", "lexpos"), tokens)
        self.setBreads(values)

import operator