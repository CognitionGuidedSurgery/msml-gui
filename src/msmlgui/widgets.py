__author__ = 'weigl'

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from msml.titen import titen

TPL_BOX = titen('''<html><body>
        <center>
            <strong>{$i}</strong><br/>
            <hr/>
            {$op}
        </center></body></html>''')

def drange(start, stop, step):
    r = start
    while r < stop:
        yield r
        r += step

class MSMLGraphicsView(QGraphicsView):
    def __init__(self, parent = None):
        super(QGraphicsView, self).__init__(parent)
        self.setMouseTracking(True)

        self.zoom_widget = QSlider(Qt.Horizontal, parent)
        self.zoom_widget.setTickInterval(10)
        self.zoom_widget.setTickPosition(QSlider.TicksBelow)
        self.zoom_widget.setMaximum(400)
        self.zoom_widget.setValue(100)
        self.zoom_widget.setMinimum(50)
        self.zoom_widget.setPageStep(10)
        self.zoom_widget.setGeometry(300,0, 300, 30)

        self.zoom_widget.valueChanged.connect(self.set_zoom)
        #self.zoom_widget.valueChanged.connect(lambda v: self.update_overview_map())

        self.view = QGraphicsView()
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.overview_label = QLabel(self)
        self.overview_label.setGeometry(-10, -10, 250, 250)
        self.overview_label.setScaledContents(True)
        self.last_time = time.time()


    def set_zoom(self, value):
        value /=100.0
        transform = QTransform(value, 0, 0, 0, value, 0, 0, 0, 1)
        self.setTransform(transform)


    def drawForeground(self, painter, rect):
        run = time.time()
        if run - self.last_time  > 1:
            self.view.setGeometry(self.geometry())
            self.view.setScene(self.scene())
            pixMap = QPixmap.grabWidget(self.view)
            pixMap = pixMap.scaled(250, 250, Qt.KeepAspectRatio)#, Qt.SmoothTransformation)
            self.overview_label.setPixmap(pixMap)

            self.last_time = run

        QGraphicsView.drawForeground(self, painter, rect)

import time

class MSMLGraphicsScene(QGraphicsScene):
    def __init__(self, parent = None):
        super(QGraphicsScene, self).__init__(parent)
        self.selectionChanged.connect(self.onItemSelected)

        self.mainframe = None
        self.line_mode = False
        self.line_shape = None
        self.from_task = None
        self.view = parent

        self.mCellSize = QRectF(0,0,25,25)

        self._grid_pen = QPen()
        self._grid_pen.setStyle(Qt.DotLine)
        self._grid_pen.setBrush(Qt.lightGray)
        self._grid_pen.setWidth(0.5)


    def drawBackground(self, painter, rect):
        QGraphicsScene.drawBackground(self, painter, rect)

        left = int(rect.left()) - (int(rect.left()) % self.mCellSize.width())
        top = int(rect.top()) - (int(rect.top()) % self.mCellSize.height())

        lines = list()

        for x in drange(left, rect.right(), self.mCellSize.width()):
            lines.append(QLineF(x, rect.top(), x, rect.bottom()))

        for y in drange(top, rect.bottom(), self.mCellSize.height()):
            lines.append(QLineF(rect.left(), y, rect.right(), y))

        painter.save()
        painter.setPen(self._grid_pen)
        painter.drawLines(lines)
        painter.restore()


    def get_task_shape(self, point):
        item = self.itemAt(point)
        while item:
            if isinstance(item, TaskShape):
                return item
            else:
                item = item.parentItem()
        return None

    def mousePressEvent(self, event):
        assert isinstance(event, QGraphicsSceneMouseEvent)

        if event.modifiers() & Qt.CTRL:
            point = event.scenePos()
            item = self.get_task_shape(point)
            if item:
                self.line_mode = True
                self.line_shape = GraphicsArrowItem(point.x(), point.y(), point.x()+10, point.y()+10)
                self.addItem(self.line_shape)
                self.from_task = item
        else:
            QGraphicsScene.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        assert isinstance(event, QGraphicsSceneMouseEvent)

        if self.line_mode:
            line = self.line_shape.line()
            p = event.scenePos()
            line.setP2(p)
            self.line_shape.setLine(line)
        else:
            QGraphicsScene.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        assert isinstance(event, QGraphicsSceneMouseEvent)

        if self.line_mode:
            self.line_mode = False
            self.removeItem(self.line_shape)
            self.line_shape = None
            point = event.scenePos()
            end_task = self.get_task_shape(point)

            output_slots = self.from_task.task.operator.output_names()
            input_slots = end_task.task.operator.input_names()


            if len(output_slots) > 1:
                slotA, ok  = QInputDialog.getItem(self.mainframe, "Output", "Output Slot", output_slots, 0, False)
                if not ok: return
            elif len(output_slots) == 1:
                slotA = output_slots[0]
            else:
                print "ERROR!"


            if len(input_slots) > 1:
                slotB, ok = QInputDialog.getItem(self.mainframe, "Input", "Input Slot", input_slots, 0, False)
                if not ok: return
            if len(input_slots) == 1:
                slotB = input_slots[0]
            else:
                print "ERROR!"

            arrow = GraphicsTaskArrowItem(self.from_task, str(slotA), end_task, str(slotB))
            self.addItem(arrow)


        else:
            QGraphicsScene.mouseReleaseEvent(self, event)

    def keyPressEvent(self, event):
        assert  isinstance(event, QKeyEvent)
        print 'KeyEvent %s' % event.key()
        if event.key() == 16777223:
            items = self.selectedItems()
            for i in items: self.removeItem(i)

    def onItemSelected(self):
        items = self.selectedItems()
        if items:
            item = items[0]
            self.mainframe.show_in_operator_help(item.task.operator)
            self.mainframe.set_task_active_propertyeditor(item.task)


    def mouseDoubleClickEvent(self, event):
        QGraphicsScene.mouseDoubleClickEvent(self, event)



class TaskShape(QGraphicsItemGroup):
    def __init__(self, task, mainframe,  parent = None):
        QGraphicsItemGroup.__init__(self, parent)
        self.mainframe = mainframe
        self.task = task

        self.setAcceptDrops(True)
        self.setCursor(Qt.OpenHandCursor)

        self.outer_rect = QGraphicsRectItem(-100, -50, 200, 100, self)
        self.addToGroup(self.outer_rect)

        self.text  = QGraphicsTextItem(self.task.id, self)
        self.addToGroup(self.text)
        self.text.setPos(-80,-40)

        self.text.setTextWidth(160)
        self.text.setHtml(TPL_BOX(i=self.task.id, op=self.task.operator.name))

        self.inputs = {}

        y = -40
        x = -100
        delta = 15
        sz = 10

        for idx, slot in enumerate(self.task.operator.input_names()):
            rect = QGraphicsRectItem(x - sz/2,  y + idx * delta, sz, sz, self)
            rect.setBrush(QBrush(Qt.darkRed))
            self.addToGroup(rect)
            self.inputs[slot] = rect

        y = 30
        x = 100
        delta = 15
        sz = 10

        self.outputs =  {}

        for idx, slot in enumerate(self.task.operator.output_names()):
            rect = QGraphicsRectItem(x-sz/2,  y - idx * delta, sz, sz, self)
            rect.setBrush(QBrush(Qt.blue))
            self.addToGroup(rect)
            self.outputs[slot] = rect



        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsFocusable)

    def dragEnterEvent(self, event):
        assert isinstance(event, QGraphicsSceneDragDropEvent)

    def dragLeaveEvent(self, event):
        assert isinstance(event, QGraphicsSceneDragDropEvent)

    def dropEvent(self, event):
            assert isinstance(event, QGraphicsSceneDragDropEvent)



    # def paint(self, painter, option, widget = None):
    #
    #     if self.isSelected():
    #         self.mainframe.show_in_operator_help(self.task.operator)
    #
    #         painter.save()
    #         painter.setBrush(QBrush(Qt.lightGray))
    #         painter.drawRoundedRect(self.rect, 20, 20)
    #         painter.restore()
    #     else:
    #         painter.drawRoundedRect(self.rect, 20, 20)
    #
    #     painter.drawText(self.rect, Qt.AlignHCenter | Qt.AlignTop, self.task.id)
    #
    #     r = QRectF(self.rect)
    #     r.setY(r.y() + 15)
    #     painter.drawText(r,  Qt.AlignHCenter | Qt.AlignTop, self.task.operator.name)

class GraphicsArrowItem(QGraphicsLineItem):
    def __init__(self, *args):
        QGraphicsLineItem.__init__(self, *args)
        self.arrow = QPolygonF()
        self.arrow_size = 20

    def paint(self, painter, option, widget=None):
        QGraphicsLineItem.paint(self, painter, option, widget)
        import math

        phi = 45/360.0*2*math.pi



        angle = math.acos(self.line().dx() / self.line().length())

        if self.line().dy() >= 0:
            angle = 2*math.pi - angle

        end_point = self.line().p2()
        pi = math.pi

        arrowP1 = end_point + QPointF(math.sin(angle + phi + pi) * self.arrow_size, math.cos(angle + phi + pi) * self.arrow_size)
        arrowP2 = end_point + QPointF(math.sin(angle - phi) * self.arrow_size, math.cos(angle - phi) * self.arrow_size)


        #print math.degrees(angle), math.degrees(angle - phi), math.degrees(angle + phi + pi)
        #print math.degrees(angle), math.degrees(angle - phi), math.degrees(angle + phi + pi)

        self.arrow.clear()
        self.arrow << end_point << arrowP1 << arrowP2
        painter.drawLine(self.line())
        painter.drawPolygon(self.arrow)


        if self.isSelected():
            #painter.setPen(QPen(self, 1, Qt::DashLine))
            pass

    '''
        if self.start.collidesWithItem(self.end):
            return

        myPen = self.pen()
        painter.setPen(myPen)
        #painter.setBrush(myColor)

        centerLine = QLineF(self.start.pos(), self.end.pos())
        endPolygon = QPolygonF(self.end.polygon())
        p1 = endPolygon.first() + self.end.pos()

        for i in range(endPolygon.count()):
            p2 = endPolygon.at(i) + self.end.pos()
            polyLine = QLineF(p1, p2)
            intersectType, intersectPoint = polyLine.intersect(centerLine)
            if intersectType == QLineF.BoundedIntersection: break
            p1 = p2

        self.setLine(QLineF(intersectPoint, myStartItem.pos()))

        import math
        angle = math.acos(line().dx() / line().length())
        if line().dy() >= 0:
            angle = (Pi * 2) - angle

            arrowP1 = self.line().p1() + QPointF(sin(angle + math.pi / 3) * arrowSize, math.cos(angle + math.pi / 3) * arrowSize)
            arrowP2 = self.line().p1() + QPointF(sin(angle + math.pi - math.pi / 3) * arrowSize, math.cos(angle + math.pi - math.pi / 3) * arrowSize)

            self.arrow.clear()
            self.arrow << line().p1() << arrowP1 << arrowP2
            painter.drawLine(self.line())
            painter.drawPolygon(self.arrow)
            if self.isSelected():
                #painter.setPen(QPen(self, 1, Qt::DashLine))
                pass

            myLine = self.line()
            myLine.translate(0, 4.0)
            painter.drawLine(myLine)
            myLine.translate(0,-8.0)
            painter.drawLine(myLine)'''

    def boundingRect(self):
        extra = (self.pen().width() + 20) / 2.0

        return QRectF(self.line().p1(), QSizeF(self.line().p2().x() - self.line().p1().x(),
                      self.line().p2().y() - self.line().p1().y())) .normalized().adjusted(-extra, -extra, extra, extra)

    def shape(self):
        path = QGraphicsLineItem.shape()
        path.addPolygon(self.arrowHead)
        return path


class GraphicsTaskArrowItem(QGraphicsPolygonItem):
    def __init__(self, taskA, slotA, taskB, slotB):
        QGraphicsPolygonItem.__init__(self)

        self.taskA = taskA
        self.taskB = taskB

        self.slotA = slotA
        self.slotB = slotB

        self._calc_polygon()


        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)


    def _calc_polygon(self):
        rectA = self.taskA.outputs[self.slotA]
        rectB = self.taskB.inputs[self.slotB]

        assert isinstance(rectA, QGraphicsRectItem)
        assert isinstance(rectB, QGraphicsRectItem)

        centerA = self.taskA.mapRectToScene(rectA.rect()).center()
        centerB = self.taskB.mapRectToScene(rectB.rect()).center()


        polygon = QPolygonF()
        polygon << centerA << centerB
        self.setPolygon(polygon)



    def paint(self, painter, option, widget=None):
        self._calc_polygon()
        QGraphicsPolygonItem.paint(self, painter, option, widget)