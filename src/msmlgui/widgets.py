__author__ = 'weigl'

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from msmlgui.helper.template import *
import msml.model

def drange(start, stop, step):
    r = start
    while r < stop:
        yield r
        r += step

class MSMLGraphicsView(QGraphicsView):
    def __init__(self, mainframe, parent = None):
        super(QGraphicsView, self).__init__(parent)
        self.setMouseTracking(True)
        self.mainframe = mainframe

        # self.zoom_widget = QSlider(Qt.Horizontal, parent)
        # self.zoom_widget.setTickInterval(10)
        # self.zoom_widget.setTickPosition(QSlider.TicksBelow)
        # self.zoom_widget.setMaximum(400)
        # self.zoom_widget.setValue(100)
        # self.zoom_widget.setMinimum(50)
        # self.zoom_widget.setPageStep(10)
        # self.zoom_widget.setGeometry(300,0, 300, 30)

        # self.zoom_widget.valueChanged.connect(self.set_zoom)
        #self.zoom_widget.valueChanged.connect(lambda v: self.update_overview_map())

        # self.view = QGraphicsView()
        # self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        #
        # self.overview_label = QLabel(self)
        # self.overview_label.setGeometry(-10, -10, 250, 250)
        # self.overview_label.setScaledContents(True)
        # self.last_time = time.time()


    def renew(self):
        "removes the whole graphics and add default"

        scene = MSMLGraphicsScene(self.mainframe, self)
        self.scene_node = SceneShape(self.mainframe, scene)
        self.scene_node.setPos(* self.mainframe.msml_pdata.get_task_position(self.scene_node))
        scene.addItem(self.scene_node)

        import msmlgui.shared, msml.exporter
        from msml.run import DefaultGraphBuilder



        m = self.mainframe.msml_model
        e = msml.exporter.get_exporter("nsofa")(m) # TODO use shared.msml_app
        m.exporter = e
        m.validate()


        graphbuilder = DefaultGraphBuilder(m,e)

        dag = graphbuilder.dag

        for t in self.mainframe.msml_model.workflow._tasks.values():
            assert isinstance(t,msml.model.Task)
            t.bind(msmlgui.shared.msml_app.alphabet)

            ts = TaskShape(t, self.mainframe, scene)
            ts.setPos(*self.mainframe.msml_pdata.get_task_position(t))

            self.mainframe.msml_vdata.task_map[t] = ts
            self.mainframe.msml_vdata.task_map[ts] = t

        for x,y in dag.edges_iter():
            if isinstance(x, msml.model.MSMLVariable): continue #TODO handle variables
            if isinstance(y, msml.exporter.Exporter): continue #TODO handle exporter


            a = self.mainframe.msml_vdata.task_map[x]
            b = self.mainframe.msml_vdata.task_map[y]

            ref = dag.get_edge_data(x,y)[0]['ref']

            sa = ref.linked_from.name
            sb = ref.linked_to.name

            cnnctd = GraphicsTaskArrowItem(a, sa, b, sb)

            scene.addItem(cnnctd)


        for a in self.mainframe.msml_pdata.annotations:
            ashape = AnnotationShape(a,scene)
            scene.addItem(ashape)

        self.setScene(scene)
        return scene

    def set_zoom(self, value):
        value /=100.0
        transform = QTransform(value, 0, 0, 0, value, 0, 0, 0, 1)
        self.setTransform(transform)


    def drawForeground(self, painter, rect):
        # run = time.time()
        # if run - self.last_time  > 1:
        #     self.view.setGeometry(self.geometry())
        #     self.view.setScene(self.scene())
        #     pixMap = QPixmap.grabWidget(self.view)
        #     pixMap = pixMap.scaled(250, 250, Qt.KeepAspectRatio)#, Qt.SmoothTransformation)
        #     self.overview_label.setPixmap(pixMap)
        #
        #     self.last_time = run

        QGraphicsView.drawForeground(self, painter, rect)


class MSMLGraphicsScene(QGraphicsScene):
    def __init__(self, mainframe, parent = None):
        super(QGraphicsScene, self).__init__(parent)
        assert mainframe is not None
        self.mainframe = mainframe
        self.selectionChanged.connect(self.onItemSelected)

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
        try:
            items = self.selectedItems()
            item = items[0]
            html = item.get_help()
            self.mainframe.webOperatorHelp.setHtml(html)

            if isinstance(item, TaskShape):
                self.mainframe.set_task_active_propertyeditor(item.task)

        except IndexError as e:
            pass


    def mouseDoubleClickEvent(self, event):
        QGraphicsScene.mouseDoubleClickEvent(self, event)


class HelpItem(object):
    def get_help(self):
        return "No help information"

class TaskShape(QGraphicsItemGroup, HelpItem):
    OUTER_RECT = QRectF(-100, -50, 200, 100)
    TEXT_POS = (-80,-40)
    TEXT_WIDTH = 160

    def __init__(self, task, mainframe,  parent = None):
        QGraphicsItemGroup.__init__(self, None,  parent)
        self.mainframe = mainframe
        self.task = task

        self.setAcceptDrops(True)
        self.setCursor(Qt.OpenHandCursor)

        self.outer_rect = QGraphicsRectItem(TaskShape.OUTER_RECT, self)
        self.addToGroup(self.outer_rect)

        self.text = QGraphicsTextItem(self.task.id, self)
        self.addToGroup(self.text)
        self.text.setPos(*TaskShape.TEXT_POS)
        self.text.setTextWidth(TaskShape.TEXT_WIDTH)
        self.text.setHtml(tpl_task_shape(i=self.task.id, op=self.task.name))

        self.inputs_boxes = {}
        self.outputs_boxes =  {}

        y, x, delta, sz  = -90, -40, 15, 10
        for idx, slot in enumerate(self.task.operator.input_names()):
            rect = QGraphicsRectItem( y + idx * delta, x - sz/2, sz, sz, self)
            rect.setBrush(QBrush(Qt.darkRed))
            self.addToGroup(rect)
            self.inputs_boxes[slot] = rect

        y, x, delta, sz  = 80, 40, 15, 10
        for idx, slot in enumerate(self.task.operator.output_names()):
            rect = QGraphicsRectItem(y - idx * delta, x-sz/2, sz, sz, self)
            rect.setBrush(QBrush(Qt.blue))
            self.addToGroup(rect)
            self.outputs_boxes[slot] = rect

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsFocusable)

    def get_help(self):
        return tpl_operator_help(o = self.task.operator)

    def dragEnterEvent(self, event):
        assert isinstance(event, QGraphicsSceneDragDropEvent)

    def dragLeaveEvent(self, event):
        assert isinstance(event, QGraphicsSceneDragDropEvent)

    def dropEvent(self, event):
        assert isinstance(event, QGraphicsSceneDragDropEvent)

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

    def boundingRect(self):
        extra = (self.pen().width() + 20) / 2.0

        return QRectF(self.line().p1(), QSizeF(self.line().p2().x() - self.line().p1().x(),
                      self.line().p2().y() - self.line().p1().y())) .normalized().adjusted(-extra, -extra, extra, extra)

    def shape(self):
        path = QGraphicsLineItem.shape()
        path.addPolygon(self.arrowHead)
        return path

class SceneShape(QGraphicsItemGroup, HelpItem):
    OUTER_RECT = QRectF(-100, -50 , 200, 100)

    def __init__(self, mainframe, parent = None):
        QGraphicsItemGroup.__init__(self, None, parent)
        self.mainframe = mainframe

        self.setAcceptDrops(True)
        self.setCursor(Qt.OpenHandCursor)

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsFocusable)

        self._render()


    def _render(self):
        self.outer_rect = QGraphicsRectItem(TaskShape.OUTER_RECT, self)
        self.addToGroup(self.outer_rect)

        self.text  = QGraphicsTextItem("Scene", self)
        self.addToGroup(self.text)
        self.text.setPos(*TaskShape.TEXT_POS)
        self.text.setTextWidth(TaskShape.TEXT_WIDTH)
        self.text.setHtml(tpl_scene_shape(scene = self.mainframe.msml_model.scene))

        self.inputs_boxes = {}
        self.outputs_boxes =  {}
        #TODO generate output boxes

    def get_help(self):
        return "#TODO"


class AnnotationShape(QGraphicsItemGroup, HelpItem):
    OUTER_RECT = QRectF(-100, -50 , 200, 100)

    def __init__(self, mainframe, msmlfile, parent = None):
        QGraphicsItemGroup.__init__(self, parent)
        self.msmlfile = msmlfile
        self.mainframe = mainframe

        self.setAcceptDrops(True)
        self.setCursor(Qt.OpenHandCursor)

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsFocusable)

        self._render()


    def _render(self):
        self.outer_rect = QGraphicsRectItem(TaskShape.OUTER_RECT, self)
        self.addToGroup(self.outer_rect)

        self.text  = QGraphicsTextItem("Scene", self)
        self.addToGroup(self.text)
        self.text.setPos(*TaskShape.TEXT_POS)
        self.text.setTextWidth(TaskShape.TEXT_WIDTH)
        self.text.setHtml(tpl_scene_shape(scene = self.msmlfile.scene))

        self.inputs_boxes = {}
        self.outputs_boxes =  {}
        #TODO generate output boxes

    def get_help(self):
        return "#TODO"


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
        rectA = self.taskA.outputs_boxes[self.slotA]
        rectB = self.taskB.inputs_boxes[self.slotB]

        assert isinstance(rectA, QGraphicsRectItem)
        assert isinstance(rectB, QGraphicsRectItem)

        centerA = self.taskA.mapRectToScene(rectA.rect()).center()
        centerB = self.taskB.mapRectToScene(rectB.rect()).center()

        half_y =  0.5 * abs(centerB.y() - centerA.y())

        print(half_y, centerB.y() , centerA.y())
        mid_one = QPointF(centerA.x(), centerA.y() + half_y)
        mid_two = QPointF(centerB.x(), centerA.y() + half_y)

        polygon = QPolygonF()
        polygon << centerA << mid_one << mid_two << centerB
        self.setPolygon(polygon)

    def paint(self, painter, option, widget=None):
        self._calc_polygon()
        QGraphicsPolygonItem.paint(self, painter, option, widget)



