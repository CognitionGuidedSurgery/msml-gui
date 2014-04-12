__author__ = 'Alexander Weigl'
__date__ = ''

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from ..helper import *


class HelpItem(object):
    def get_help(self):
        return "No help information"


class Config(object):
    OUTER_RECT = QRectF(0, 0, 200, 100)
    TEXT_RECT = QRectF(10, 10, 180, 80)


class SimpleTextRectShape(QGraphicsItemGroup):
    def __init__(self, text=None, parent=None, scene=None,
                 outer_rect=Config.OUTER_RECT,
                 text_rect=Config.TEXT_RECT):


        QGraphicsItemGroup.__init__(self, parent, scene)

        self.setCursor(Qt.OpenHandCursor)

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsFocusable)

        self.shape_outer = outer_rect
        self.text_rect = text_rect

        self._text = text

        self._docking_ports = dict()

        self.build()

    def dock_point(self, name, category=None):
        try:
            return self._docking_ports[name, category]
        except KeyError as e:
            return self

    def add_dock_point(self, name, shape, category=None):
        assert isinstance(shape, QGraphicsItem)
        self._docking_ports[name, category] = shape


    @property
    def text(self):
        return self._text or ""

    def build(self):
        self.shape_outer = QGraphicsRectItem(self.shape_outer, self)
        self.addToGroup(self.shape_outer)
        self.shape_text = QGraphicsTextItem(self.text, self.shape_outer)

        self.shape_text.setPos(self.text_rect.x(), self.text_rect.y())

        self.shape_text.setHtml(self.text)
        #self.shape_text.document().setPageSize(QSizeF(self.text_rect.width(), self.text_rect.height()))
        self.shape_text.setTextWidth(self.text_rect.width())


class VariableShape(SimpleTextRectShape, HelpItem):
    def __init__(self, variable, mainframe, scene):
        self.variable = variable
        self.mainframe = mainframe
        SimpleTextRectShape.__init__(self, scene=scene,
                                     outer_rect=QRectF(0, 0, 250, 75),
                                     text_rect=QRectF(5, 5, 240, 70))

        self.shape_outer.setBrush(QBrush(Qt.yellow))

    def get_help(self):
        return tpl_variable_help(v=self.variable)

    @property
    def text(self):
        return tpl_variable_shape(v=self.variable)


class TaskShape(SimpleTextRectShape, HelpItem):
    def __init__(self, task, mainframe, parent=None):
        self.mainframe = mainframe
        self.task = task
        SimpleTextRectShape.__init__(self, None, scene=parent)

    def build(self):
        SimpleTextRectShape.build(self)
        box_size = 10
        box_margin = 15

        def position(count, start_x, start_y, direction=1):
            for i in range(count):
                x = start_x + direction * i * box_margin
                y = start_y
                yield x, y

        def add_boxes(names, category, start_x, start_y):
            if category == "input":
                direction = 1
                color = QBrush(Qt.blue)
            else:
                direction = -1
                color = QBrush(Qt.darkRed)

            p = position(len(names), start_x, start_y, direction)

            for (x, y), n in zip(p, names):
                rect = QGraphicsRectItem(x, y, box_size, box_size, self)
                rect.setBrush(color)
                self.add_dock_point(n, rect, category)

        a = lambda top, i: (top.x() + i * box_margin, top.y() + i * box_margin)

        x_top, y_top = a(self.shape_outer.rect().topLeft(), 1)
        x_bottom, y_bottom = a(self.shape_outer.rect().bottomRight(), -1)

        add_boxes(self.task.operator.input_names(),
                  "input", x_top, y_top)

        add_boxes(self.task.operator.output_names(),
                  "output", x_bottom, y_bottom)


    def get_help(self):
        return tpl_operator_help(o=self.task.operator)

    @property
    def text(self):
        return tpl_task_shape(i=self.task.id, op=self.task.name)

    def dragEnterEvent(self, event):
        assert isinstance(event, QGraphicsSceneDragDropEvent)

    def dragLeaveEvent(self, event):
        assert isinstance(event, QGraphicsSceneDragDropEvent)

    def dropEvent(self, event):
        assert isinstance(event, QGraphicsSceneDragDropEvent)


class SceneShape(SimpleTextRectShape, HelpItem):
    def __init__(self, mainframe, parent=None):
        self.mainframe = mainframe
        SimpleTextRectShape.__init__(self, scene=parent)

    def get_help(self):
        return tpl_scene_help(scene=self.mainframe.msml_model.scene)

    @property
    def text(self):
        return tpl_scene_shape(scene=self.mainframe.msml_model.scene)


class AnnotationShape(SimpleTextRectShape, HelpItem):
    def __init__(self, text, mainframe, scene=None):
        SimpleTextRectShape.__init__(self, text, scene=scene)
        self.shape_outer.setBrush(QBrush(Qt.green))
        self.mainframe = mainframe
        self._in_edit_mode = False
        self.shape_text.setTextInteractionFlags(Qt.TextEditorInteraction)


    def edit_mode(self):
        def handle_cancel():
            self.scene().removeItem(self.input_proxy)
            del self.input_proxy
            del self.input_widget

        def handle_ok():
            self.text = self.input_widget.toHtml()
            handle_cancel()

    def get_help(self):
        return self.text


class GraphicsArrowItem(QGraphicsLineItem):
    def __init__(self, *args):
        QGraphicsLineItem.__init__(self, *args)
        self.arrow = QPolygonF()
        self.arrow_size = 20

    def paint(self, painter, option, widget=None):
        QGraphicsLineItem.paint(self, painter, option, widget)
        import math

        phi = 45 / 360.0 * 2 * math.pi

        angle = math.acos(self.line().dx() / self.line().length())

        if self.line().dy() >= 0:
            angle = 2 * math.pi - angle

        end_point = self.line().p2()
        pi = math.pi

        arrowP1 = end_point + QPointF(math.sin(angle + phi + pi) * self.arrow_size,
                                      math.cos(angle + phi + pi) * self.arrow_size)
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

    def boundingRect(self):
        extra = (self.pen().width() + 20) / 2.0

        return QRectF(self.line().p1(), QSizeF(self.line().p2().x() - self.line().p1().x(),
                                               self.line().p2().y() - self.line().p1().y())).normalized().adjusted(
            -extra, -extra, extra, extra)

    def shape(self):
        path = QGraphicsLineItem.shape()
        path.addPolygon(self.arrowHead)
        return path


class GraphicsTaskArrowItem(QGraphicsPolygonItem, HelpItem):
    def __init__(self, taskA, slotA, taskB, slotB):
        QGraphicsPolygonItem.__init__(self)

        self.taskA = taskA
        self.taskB = taskB

        self.slotA = slotA
        self.slotB = slotB

        self._calc_polygon()

        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)


    def get_help(self):
        return "todo"

    def _calc_polygon(self):
        rectA = self.taskA.dock_point(self.slotA, 'output')
        rectB = self.taskB.dock_point(self.slotB, 'input')

        centerA = self.taskA.mapRectToScene(rectA.boundingRect()).center()
        centerB = self.taskB.mapRectToScene(rectB.boundingRect()).center()

        half_y = 0.5 * abs(centerB.y() - centerA.y())

        #print(half_y, centerB.y() , centerA.y())
        mid_one = QPointF(centerA.x(), centerA.y() + half_y)
        mid_two = QPointF(centerB.x(), centerA.y() + half_y)

        polygon = QPolygonF()
        polygon << centerA << mid_one << mid_two << centerB
        self.setPolygon(polygon)

    def paint(self, painter, option, widget=None):
        self._calc_polygon()
        #QGraphicsPolygonItem.paint(self, painter, option, widget)
        painter.drawPolyline(self.polygon())






