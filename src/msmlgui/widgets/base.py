__author__ = 'weigl'

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import msml.model

from .shapes import *


def drange(start, stop, step):
    r = start
    while r < stop:
        yield r
        r += step


class MSMLGraphicsView(QGraphicsView):
    def __init__(self, mainframe, parent=None):
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
        self.scene_node.setPos(*self.mainframe.msml_pdata.get_task_position(self.scene_node))
        scene.addItem(self.scene_node)

        import msmlgui.shared, msml.exporter
        from msml.run import DefaultGraphBuilder

        m = self.mainframe.msml_model
        e = msml.exporter.get_exporter("nsofa")(m)  # TODO use shared.msml_app for getting exporter
        m.exporter = e
        m.validate()

        graphbuilder = DefaultGraphBuilder(m, e)

        dag = graphbuilder.dag

        # add TaskShapes
        for t in self.mainframe.msml_model.workflow._tasks.values():
            assert isinstance(t, msml.model.Task)
            t.bind(msmlgui.shared.msml_app.alphabet)

            ts = TaskShape(t, self.mainframe, scene)
            ts.setPos(*self.mainframe.msml_pdata.get_task_position(t))

            self.mainframe.msml_vdata.task_map[t] = ts
            self.mainframe.msml_vdata.task_map[ts] = t

        # add Variables
        for var in m.variables.values():
            if not var.name.startswith("_gen"):
                shape = VariableShape(var, self.mainframe)
                self.mainframe.msml_vdata.var_map[shape] = var
                self.mainframe.msml_vdata.var_map[var] = shape
                scene.addItem(shape)

        # add links
        for x, y in dag.edges_iter():
            #TODO better solution for this cascade
            if isinstance(x, msml.model.MSMLVariable):
                if x in self.mainframe.msml_vdata.var_map:
                    a = self.mainframe.msml_vdata.var_map[x]
                else:
                    continue
            else:
                a = self.mainframe.msml_vdata.task_map[x]

            if isinstance(y, msml.exporter.Exporter):
                b = self.scene_node
            else:
                b = self.mainframe.msml_vdata.task_map[y]

            ref = dag.get_edge_data(x, y)[0]['ref']

            sa = ref.linked_from.name
            sb = ref.linked_to.name

            if isinstance(x, msml.model.MSMLVariable) and isinstance(y, msml.model.Task):
                if sb in y.operator.parameter_names():
                    scene.removeItem(a)
                    continue

            cnnctd = GraphicsTaskArrowItem(a, sa, b, sb)
            scene.addItem(cnnctd)

        for a in self.mainframe.msml_pdata.annotations:
            ashape = AnnotationShape(a, scene)
            scene.addItem(ashape)

        self.setScene(scene)
        return scene

    def set_zoom(self, value):
        value /= 100.0
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
    def __init__(self, mainframe, parent=None):
        super(QGraphicsScene, self).__init__(parent)
        assert mainframe is not None
        self.mainframe = mainframe
        self.selectionChanged.connect(self.onItemSelected)

        self.line_mode = False
        self.line_shape = None
        self.from_task = None
        self.view = parent

        self.mCellSize = QRectF(0, 0, 25, 25)

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

        if event.modifiers() & Qt.AltModifier:
            point = event.scenePos()
            item = self.get_task_shape(point)
            if item:
                self.line_mode = True
                self.line_shape = GraphicsArrowItem(point.x(), point.y(), point.x() + 10, point.y() + 10)
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
                slotA, ok = QInputDialog.getItem(self.mainframe, "Output", "Output Slot", output_slots, 0, False)
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
        assert isinstance(event, QKeyEvent)
        if event.key() == 16777223:
            items = self.selectedItems()
            for i in items:
                self.removeItemSafely(i)

    def removeItemSafely(self, item):
        def remove_links(item):
            scene_items = self.items()
            for i in scene_items:
                if isinstance(i, GraphicsTaskArrowItem):
                    if item in (i.taskA, i.taskB):
                        self.removeItem(i)

        if isinstance(item, TaskShape) or isinstance(item, VariableShape):
            self.removeItem(item)
            remove_links(item)
        elif isinstance(item, SceneShape):
            print("SceneShape is not removeable")
        else:
            self.removeItem(item)

    def onItemSelected(self):
        try:
            items = self.selectedItems()
            item = items[0]
            html = item.get_help()
            self.mainframe.webOperatorHelp.setHtml(html)

            if isinstance(item, TaskShape):
                self.mainframe.set_property_model(item)

        except IndexError as e:
            pass


    def mouseDoubleClickEvent(self, event):
        QGraphicsScene.mouseDoubleClickEvent(self, event)


