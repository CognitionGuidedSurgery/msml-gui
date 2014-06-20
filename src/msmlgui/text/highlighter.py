__author__ = 'weigl'

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import xml.parsers.expat


SOLARIZED_COLORS = {
    "base03": 0x002b36,
    "base02": 0x073642,
    "base01": 0x586e75,
    "base00": 0x657b83,
    "base0": 0x839496,
    "base1": 0x93a1a1,
    "base2": 0xeee8d5,
    "base3": 0xfdf6e3,
    "yellow": 0xb58900,
    "orange": 0xcb4b16,
    "red": 0xdc322f,
    "magenta": 0xd33682,
    "violet": 0x6c71c4,
    "blue": 0x268bd2,
    "cyan": 0x2aa198,
    "green": 0x859900,
    # green = 0x719e07" "experimental
}


def defineFormat( fg = None, bg = None, italic = False, bold = False, underline = False):
    fmt = QTextCharFormat()
    if fg:
        fmt.setForeground(QBrush(QColor.fromRgb(fg)))

    if bg:
        fmt.setBackground(QBrush(QColor.fromRgb(bg)))


    fmt.setFontItalic(italic)
    if bold:
        fmt.setFontWeight(QFont.Bold)

    fmt.setFontUnderline(underline)

    return fmt



SOLARIZED_THEME = {
    "BACKGROUND" : QColor.fromRgb(SOLARIZED_COLORS['base03']),
    "FOREGROUND" : QColor.fromRgb(SOLARIZED_COLORS['base1']),
    "CURRENT_LINE" : QColor.fromRgb(SOLARIZED_COLORS['base02']),
    "COMMENTS"   : defineFormat(fg=SOLARIZED_COLORS['base1']),
    "KEYWORD"    : defineFormat(fg=SOLARIZED_COLORS['green']),
    "TAG_NAME"    : defineFormat(fg=SOLARIZED_COLORS['green']),
    "ATTRIBUTE_NAME" : defineFormat(fg=SOLARIZED_COLORS['green']),
    "ATTRIBUTE_VALUE": defineFormat(fg=SOLARIZED_COLORS['orange']),
    "ERROR"      : defineFormat(fg=SOLARIZED_COLORS['red'], underline=True),
}

SOLARIZED_THEME['ERROR'].setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)

class XMLHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super(XMLHighlighter, self).__init__(document)

        theme = SOLARIZED_THEME
        self.theme = theme

        keywordFormat = theme['KEYWORD']
        keywordPatterns = ["\\b?xml\\b", "/>", ">", "<"]

        self.highlightingRules = [(QRegExp(pattern), keywordFormat)
                                  for pattern in keywordPatterns]

        xmlElementFormat = theme['TAG_NAME']
        self.highlightingRules.append((QRegExp("\\b[A-Za-z0-9_]+(?=[\s/>])"), xmlElementFormat))

        xmlAttributeFormat = theme['ATTRIBUTE_NAME']
        self.highlightingRules.append((QRegExp("\\b[A-Za-z0-9_]+(?=\\=)"), xmlAttributeFormat))

        self.valueFormat = theme['ATTRIBUTE_NAME']
        self.valueFormat.setForeground(Qt.red)

        self.valueStartExpression = QRegExp("\"")
        self.valueEndExpression = QRegExp("\"(?=[\s></])")

        singleLineCommentFormat = theme['COMMENTS']
        self.highlightingRules.append((QRegExp("<!--[^\n]*-->"), singleLineCommentFormat))

    def getForeground(self):
        return self.theme['FOREGROUND']

    def getBackground(self):
        return self.theme['BACKGROUND']

    def getCurrentLineColor(self):
        return self.theme['CURRENT_LINE']



    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = QRegExp(pattern)

            #Check what index that expression occurs at with the ENTIRE text
            index = expression.indexIn(text)

            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        #HANDLE QUOTATION MARKS NOW.. WE WANT TO START WITH " AND END WITH ".. A THIRD " SHOULD NOT CAUSE THE WORDS INBETWEEN SECOND AND THIRD TO BE COLORED
        self.setCurrentBlockState(0)

        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = self.valueStartExpression.indexIn(text)

        while startIndex >= 0:
            endIndex = self.valueEndExpression.indexIn(text, startIndex)

            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + self.valueEndExpression.matchedLength()

            self.setFormat(startIndex, commentLength, self.valueFormat)

            startIndex = self.valueStartExpression.indexIn(text, startIndex + commentLength);


