# -*- encoding: utf-8 -*-
__author__ = 'weigl'

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import ply.lex

from .xmllexer import tokenize
from .highlighter import SOLARIZED_COLORS
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

    # writer = QImageWriter(char + "_test.bmp", "bmp")
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


from PyQt4.Qsci import *


class CodeEditor(QsciScintilla):
    def __init__(self, parent=None):
        super(CodeEditor, self).__init__(parent)

        self.textChanged.connect(self.triggerSemanticAnalyze)
        self.semantic_enabled = True

        # Set the default font
        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(10)
        self.setFont(font)
        self.setMarginsFont(font)

        # Margin 0 is used for line numbers
        fontmetrics = QFontMetrics(font)
        self.setMarginsFont(font)
        self.setMarginWidth(0, fontmetrics.width("000") + 6)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QColor("#cccccc"))


        # Clickable margin 1 for showing markers
        self.setMarginSensitivity(1, True)
        self.connect(self,
                     SIGNAL('marginClicked(int, int, Qt::KeyboardModifiers)'),
                     self.on_margin_clicked)
        self.markerDefine(QsciScintilla.RightArrow,
                          self.Circle)
        self.setMarkerBackgroundColor(QColor("#ee1111"),
                                      QsciScintilla.Circle)
        # Brace matching: enable for a brace immediately before or after
        # the current position
        #
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        # Current line visible with special background color
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#ffe4e4"))

        #lexer = QsciLexerXML()
        #lexer.setDefaultFont(font)
        #self.setLexer(lexer)


        lexer = QsciLexerXML(self)
        compl = MSMLScintillaCompleter(lexer)
        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionSource(QsciScintilla.AcsAPIs)
        self.setLexer(lexer)



        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionSource(QsciScintilla.AcsAPIs)

        self.SendScintilla(QsciScintilla.SCI_STYLESETFONT, 1, 'Courier')

        # Don't want to see the horizontal scrollbar at all
        # Use raw message to Scintilla here (all messages are documented
        # here: http://www.scintilla.org/ScintillaDoc.html)
        self.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, 0)

        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionSource(QsciScintilla.AcsAPIs)

        # not too small
        self.setMinimumSize(600, 450)

    def on_margin_clicked(self, nmargin, nline, modifiers):
        # Toggle marker for the line the margin was clicked on
        if self.markersAtLine(nline) != 0:
            self.markerDelete(nline, self.Circle)
        else:
            self.markerAdd(nline, self.Circle)

    def onCursorPositionChanged(self):
        text = str(self.toPlainText())
        tokens = tokenize(text)
        self.whereIam(tokens)

    def triggerSemanticAnalyze(self):
        print "Trigger Semantic Analyze"
        if self.semantic_enabled:
            #self.timer.stop()
            #self.timer.start(DELAY_SEMANTIC_ANALYZE)
            #self.document().setModified(False)
            pass

    def runSemanticAnalyze(self):
        print "ANALyze"

        self.semantic_enabled = False
        text = str(self.toPlainText())
        char2line = self.charLine(text)

        self.findSections(text, char2line)
        tokens = tokenize(text)
        self.findErrorsAndWarnings(text, tokens)
        self.contentChanged.emit(tokens, char2line)
        self.semantic_enabled = True

    def findErrorsAndWarnings(self, text, toks):
        errors = find_errors(toks)

        cursor = self.textCursor();
        errorFormat = self.highlighter.theme['ERROR']

        # clear errors
        cursor.movePosition(0)
        cursor.movePosition(len(text) + 1, QTextCursor.KeepAnchor)
        format = cursor.charFormat()
        format.setUnderlineStyle(QTextCharFormat.NoUnderline)
        cursor.setCharFormat(format)
        cursor.clearSelection()

        for er in errors:
            s, e = er.position
            cursor.setPosition(s)
            cursor.setPosition(e, QTextCursor.KeepAnchor)
            cursor.mergeCharFormat(errorFormat)

        self.problemsChanged.emit(errors)
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

    @pyqtSlot("QModelIndex")
    def insertCompletion(self, index):
        if self._completer.widget() == self:
            row = index.row()
            insert_text = self.completion_model.active_entries[row].insert

            tc = self.textCursor()
            # extra = len(text) - len(self._completer.completionPrefix())

            tc.movePosition(QTextCursor.Left)
            tc.movePosition(QTextCursor.EndOfWord, QTextCursor.KeepAnchor)
            tc.insertText(insert_text)

            tc.clearSelection()
            self.setTextCursor(tc)

            self.find("$", QTextDocument.FindBackward)

    def findInsert(self):
        self.find("$")

    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        return tc.selectedText()

    problemsChanged = pyqtSignal([list])
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

