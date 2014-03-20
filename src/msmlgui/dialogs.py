__author__ = 'Alexander Weigl'
__date__ = "2014-03-09"

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import PyQt4.uic
from path import path

from msml.model import *

PKG_DIR = path(__file__).parent


ELEMENT_TYPE = 0x01
ATTRIBUTE_TYPE = 0x02


# TODO add/remove objects
# TODO model for cboMesh
# TODO check for txtMesh

# TODO Material:
# TODO model for cboRegion
# TODO add/remove regions
# TODO model for cboIndexGroup
# TODO model for elements
# TODO model for table of attributes elements

def generate_name(prefix = "task", suffix = ""):
    import random
    chars = [chr(i) for i in range(65, 65+26)]
    rand =''.join(random.sample(chars, 5))
    return prefix + rand + suffix


class SceneEditor(QDialog):
    def __init__(self, parent=None, flags=0):
        QDialog.__init__(self, parent)
        PyQt4.uic.loadUi(PKG_DIR / "scene_editor.ui", self)

        # no changes allowed -> select object first
        self.scrollAreaWidgetContents.setEnabled(False)

        # general
        self.btnSceneObjectAdd.clicked.connect(self.add_scene_object)
        self.btnSceneObjectRemove.clicked.connect(self.remove_scene_object)
        self.listScene.activated.connect(self.on_listScene_activated)
        self.cboMesh.currentIndexChanged.connect(self.on_mesh_change)

        ## material region
        self.cboMaterialRegion.editTextChanged.connect(self.on_material_region_name_change)
        self.cboMaterialRegion.currentIndexChanged.connect(self.on_material_region_change)
        self.btnMaterialRegionAdd.clicked.connect(self.on_material_region_add)
        self.btnMaterialRegionRemove.clicked.connect(self.on_material_region_remove)
        self.btnMaterialRegionElementAdd.clicked.connect(self.on_material_region_element_add)
        #self.tabMaterialRegionElementAttributes.itemDoubleClicked.connect(self.on_material_region_element_edit_column)
        self.tabMaterialRegionElementAttributes.itemChanged.connect(self.on_material_region_element_edit_changed)


        # constraints
        self.btnConstraintAdd.clicked.connect(self.on_constraint_add)
        self.btnConstraintRemove.clicked.connect(self.on_constraint_remove)

        self.accepted.connect(self.on_accept)

        QMetaObject.connectSlotsByName(self)

        # static models

        self.tabConstraints.setItemDelegateForColumn(0, NoEditDelegate(self))
        self.tabMaterialRegionElementAttributes.setItemDelegateForColumn(0, NoEditDelegate(self))

        alphabet = msml.env.current_alphabet

        get_elements = lambda tp: filter(lambda x: isinstance(x, tp), alphabet.object_attributes.values())

        for e in get_elements(OAMaterial):
            self.cboMaterialRegionElements.addItem(e.name, e)

        for e in get_elements(OAConstraint):
            self.cboConstraints.addItem(e.name, e)

        for e in get_elements(ObjectAttribute):
            self.cboOutputs.addItem(e.name, e)

        self.current_scene_object = None

    def on_accept(self):
        from yaml import load, dump
        try:
            from yaml import CLoader as Loader, CDumper as Dumper
        except ImportError:
            from yaml import Loader, Dumper

        print(dump(self.model, Dumper=Dumper))

    @pyqtSlot(str)
    def on_mesh_change(self, val):
        if self.current_scene_object:
            self.current_scene_object.mesh.mesh = val
            # TODO specify type

    def on_material_region_name_change(self, name):
        if self.current_scene_object:
            try:
                index = self.cboMaterialRegion.currentIndex()
                mat = self.current_scene_object.material[index]
                mat.id = name
            except IndexError as e:
                pass

#    def on_material_region_element_edit_column(self, item, column):
#        assert isinstance(item, QTreeWidgetItem)
#        self.tabMaterialRegionElementAttributes.editItem(item, column)

    def on_material_region_element_edit_changed(self, item, column):
        # TODO get
        data, key = item.data(column, Qt.UserRole).toPyObject()
        newdata = item.data(column, Qt.DisplayRole).toPyObject()
        data[key] = newdata


    @pyqtSlot(int)
    def on_material_region_change(self, index):
        if self.current_scene_object:
            region = self.cboMaterialRegion.itemData(index).toPyObject()
            #assert isinstance(self.tabMaterialRegionElementAttributes, QTreeWidget)
            #self.tabMaterialRegionElementAttributesModel = MaterialRegionElementsModel(self.model, self.current_scene_object, mat, self)
            #self.tabMaterialRegionElementAttributes.setModel(self.tabMaterialRegionElementAttributesModel)

            self.tabMaterialRegionElementAttributes.clear()
            for mat in region:
                self.append_material_region_entry(mat)


    def append_material_region_entry(self, entry):
        "appends and ObjectElement entry in the current tabMaterialRegionElementAttributes TreeWidget"


        meta   = entry.meta
        values = entry.attributes

        root = QTreeWidgetItem([meta.name,meta.description], ELEMENT_TYPE)
        b = QBrush(Qt.lightGray)
        root.setData(0, Qt.BackgroundRole, b)
        root.setData(1, Qt.BackgroundRole, b)


        for name, param in meta.parameters.items():
            item = QTreeWidgetItem(ATTRIBUTE_TYPE)
            item.setData(0, Qt.DisplayRole, name)
            item.setData(1, Qt.DisplayRole, entry.get(name, "<not/set>"))

            #item.setData(1, Qt.EditRole, str(entry.get(name, "<not/set>")))
            item.setData(1, Qt.UserRole, (entry.attributes, name))

            item.setFirstColumnSpanned(True)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            item.setToolTip(0, str(param))
            root.addChild(item)
            item.setExpanded(True)

        self.tabMaterialRegionElementAttributes.addTopLevelItem(root)
        root.setExpanded(True)




    def on_material_region_add(self):
        if self.current_scene_object:
            mat = MaterialRegion(generate_name('mat_', '_region'))

            # DEBUG
            oe = ObjectElement({}, msml.env.current_alphabet.get("linearElasticMaterial"))
            mat.append(oe)
            #

            self.current_scene_object.material.append(mat)
            self.cboMaterialRegion.addItem(mat.id, mat)
            self.cboMaterialRegion.setCurrentIndex(len(self.current_scene_object.material)-1)

    def on_material_region_remove(self):
        if self.current_scene_object:
            idx = self.cboMaterialRegion.currentIndex()
            region = self.cboMaterialRegion.itemData(idx).toPyObject()
            midx  = self.current_scene_object.material.index(region)
            del self.current_scene_object.material[midx]
            self.cboMaterialRegion.removeItem(idx)


    def on_material_region_element_add(self):
        if self.current_scene_object:
            region_idx = self.cboMaterialRegion.currentIndex()
            region = self.current_scene_object.material[region_idx]

            attrib_idx = self.cboMaterialRegionElements.currentIndex()
            attrib = self.cboMaterialRegionElements.itemData(attrib_idx).toPyObject()
            oe = ObjectElement({}, attrib)
            region.append(oe)
            self.append_material_region_entry(oe)

    def on_listScene_activated(self, index):
        assert isinstance(index,QModelIndex)
        sceneobj = self.model.scene[index.row()]
        self.activate_scene_object(sceneobj)

    def activate_scene_object(self, sceneobj):
        assert isinstance(sceneobj, SceneObject)

        self.scrollAreaWidgetContents.setEnabled(True)
        self.current_scene_object = sceneobj

        self.txtName.setText(sceneobj.id)

        # mesm model
        self.cboMeshModel = MeshModel(self._model, self)
        self.cboMesh.setModel(self.cboMeshModel)

        self.cboMesh.setCurrentIndex(self.cboMeshModel.lookafter(sceneobj.mesh.mesh))

        #self.cboMaterialRegionModel = MaterialRegionModel(self.model, self.current_scene_object, self)
        #self.cboMaterialRegion.setModel(self.cboMaterialRegionModel)
        self.cboMaterialRegion.clear()
        for region in self.current_scene_object.material:
            self.cboMaterialRegion.addItem(region.name, region)

        ## constraints
        def find_cset(step):
            for s in self.current_scene_object.constraints:
                if s.for_step == step.name:
                    return s
            oc = ObjectConstraints(generate_name("cset_"), step.name)
            self.current_scene_object.constraints.append(oc)
            return oc

        self.tabConstraints.clear()
        self.constraints_treewidgets = {}
        hbrush = QBrush(Qt.lightGray)
        for step in self.model.env.simulation:
            w = QTreeWidgetItem(5)

            w.setData(0, Qt.DisplayRole, step.name)
            w.setData(1, Qt.DisplayRole, "%d/%d" %(step.dt, step.iterations))
            w.setData(0, Qt.BackgroundRole, hbrush)
            w.setData(1, Qt.BackgroundRole, hbrush)
            self.constraints_treewidgets[step.name] = w
            self.tabConstraints.addTopLevelItem(w)

            w.setData(0, Qt.UserRole, find_cset(step))
            w.setExpanded(True)
            w.setFirstColumnSpanned(True)


        for cset in self.current_scene_object.constraints:
            self.append_constraint_set(cset)


    def on_constraint_add(self):
        if self.current_scene_object:
            attrib = self.cboConstraints.itemData(
                self.cboConstraints.currentIndex()).toPyObject()
            oe = ObjectElement({}, attrib)

            root = self.tabConstraints.currentItem()
            while root.parent() and root.parent() != self.tabConstraints:
                root = root.parent()

            if root:
                self.append_constraint(oe, root)

                seq = root.data(0, Qt.UserRole).toPyObject()
                seq.constraints.append(oe)


    def on_constraint_remove(self):
        pass

    def append_constraint_set(self, cset):
        root = self.constraints_treewidgets[cset.for_step]
        assert isinstance(cset, ObjectConstraints)
        for c in cset.constraints:
            self.append_constraint(c, root)

    def append_constraint(self, c, root):
        assert isinstance(c, ObjectElement)

        v = QTreeWidgetItem(6)
        v.setData(0, Qt.DisplayRole, c.meta.name)
        v.setData(1, Qt.DisplayRole, c.meta.description)
        root.addChild(v)
        v.setExpanded(True)

        for p in c.meta.parameters.values():
            u = QTreeWidgetItem(7)
            v.addChild(u)

            u.setData(0,Qt.DisplayRole, p.name)
            u.setData(1,Qt.DisplayRole, c.attributes.get(p.name, ""))
            u.setData(1,Qt.UserRole, (c.attributes, p.name))

            u.setFlags(v.flags() | Qt.ItemIsEditable)
            u.setExpanded(True)



    def remove_scene_object(self):
        indexes = self.listScene.selectedIndexes()
        idx = indexes[0].row()

        del self.model.scene[idx]

        i = self.listSceneModel.createIndex(idx, 0)
        self.listScene.dataChanged(i,i)

    def add_scene_object(self):
        new = SceneObject(generate_name("obj"))
        self._model.scene.append(new)
        i = QModelIndex()
        last = len(self._model.scene) - 1
        self.listScene.rowsInserted(i, last, last + 1)


    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, model):
        assert isinstance(model, MSMLFile)
        self._model = model #TODO Working Copy
        self.listSceneModel = SceneObjectModel(model)
        self.listScene.setModel(self.listSceneModel)

class NoEditDelegate(QStyledItemDelegate):
    def __init__(self, parent = None):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, QWidget, QStyleOptionViewItem, QModelIndex):
        return None


class SceneObjectModel(QAbstractListModel):
    def __init__(self, msmlfile, parent=None):
        QAbstractListModel.__init__(self, parent)
        assert isinstance(msmlfile, MSMLFile)

        self.msmlfile = msmlfile

    def data(self, index = QModelIndex(), role = Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            o = self.msmlfile.scene[index.row()]
            assert isinstance(o, SceneObject)
            return QVariant(o.id)
        return QVariant()

    def rowCount(self, parent  = QModelIndex()):
        return len(self.msmlfile.scene)


class MeshModel(QStringListModel):
    def __init__(self, msmlfile, parent=None):
        QStringListModel.__init__(self, parent)
        assert isinstance(msmlfile, MSMLFile)

        self.list = QStringList()

        self.values = []
        for value in get_output_slots(msmlfile, type="mesh"):
            self.list << value
            self.values.append(value)

        self.setStringList(self.list)

    def lookafter(self, value):
        if value in self.values:
            return self.values.index(value)
        elif value:
            self.values.append(value)
            self.list << value
            self.setStringList(list)
            return len(self.list) - 1
        else:
            return -1


class MaterialRegionModel(QAbstractListModel):
    def __init__(self, msmlfile, msmlobj, parent=None):
        QAbstractListModel.__init__(self, parent)
        assert isinstance(msmlfile, MSMLFile)
        assert isinstance(msmlobj, SceneObject)

        self.msmlfile = msmlfile
        self.msmlobj = msmlobj

    def data(self, index = QModelIndex(), role = Qt.DisplayRole):
        if index.isValid():
            o = self.msmlobj.material[index.row()]
            return QVariant(o.id)
        return QVariant()

    def rowCount(self, parent  = QModelIndex()):
        return len(self.msmlobj.material)


class MaterialElementsModel(QAbstractListModel):
    def __init__(self, parent = None):
        QAbstractListModel.__init__(self, parent)

        alphabet = msml.env.current_alphabet
        oattr = alphabet.object_attributes.values()
        self.elements = filter(lambda x: isinstance(x, OAMaterial), oattr)

    def data(self, index = QModelIndex(), role = Qt.DisplayRole):
        if index.isValid():
            o = self.elements[index.row()]
            return QVariant(o.name)
        return QVariant()

    def rowCount(self, parent  = QModelIndex()):
        return len(self.elements)


class MaterialRegionIndexGroupModel(QStringListModel):
    def __init__(self, msmlfile, msmlobj, material, parent=None):
        QStringListModel.__init__(self, parent)
        assert isinstance(msmlfile, MSMLFile)
        assert isinstance(msmlobj, SceneObject)
        assert isinstance(material, MaterialRegion)

        list = QStringList()

        for value in get_output_slots(msmlfile, type = "indexgroup"):
            list << value

        self.setStringList(list)

import msml.env


import collections
TreeNode = collections.namedtuple("TreeNode", "t,d")


#
# class MaterialRegionElementsModel(QAbstractItemModel):
#     def __init__(self, msmlfile, msmlobj, material, parent=None):
#         QAbstractListModel.__init__(self, parent)
#         assert isinstance(msmlfile, MSMLFile)
#         assert isinstance(msmlobj, SceneObject)
#         assert isinstance(material, MaterialRegion)
#
#         self.msmlfile = msmlfile
#         self.sceneobj = msmlobj
#         self.region = material
#
#         self._memory = {}
#
#     def interalize(self, index, type, data):
#         t = TreeNode(type,data)
#         idx = index.internalId()
#         self._memory[idx] = t
#         #
#         # if t in self._memory:
#         #     return self._memory.index(t)
#         # else:
#         #     self._memory.append(t)
#         #     return len(self._memory) - 1
#
#     def outeralize(self, idx):
#         if isinstance(idx, int):
#             return self._memory[id]
#         else:
#             idx = idx.internalId()
#             return self._memory[idx]
#
#
#     def parent(self, index = QModelIndex()):
#         if not index.isValid():
#             return QModelIndex()
#
#         node = self.outeralize(index)
#         if node.t == 'element':
#             return QModelIndex()
#         else:
#             index = self.createIndex(0, 0)
#             return index
#
#
#     def index(self, row, column, parent = QModelIndex()):
#         if not self.hasIndex(row, column, parent):
#             return QModelIndex()
#
#         index = self.createIndex(row, column)
#         if not parent.isValid(): # parent is root !
#             element = self.region[row]
#             self.interalize(index, 'element', element)
#             return index
#         else:
#             node = self.outeralize(parent)
#             data = node.d.object_attribute.parameters[row]
#             self.interalize(index, 'attributes', data)
#             return index
#
#         return QModelIndex()
#
#     def data(self, index = QModelIndex(), role = Qt.DisplayRole):
#         if index.isValid():
#             node = self.outeralize(index)
#             col = index.column()
#
#             if node.t== 'element':
#                 return node.d.name
#             elif node.t == 'attribtues':
#                 return QVariant("test")
#
#
#     def rowCount(self, parent  = QModelIndex()):
#         if not parent.isValid():
#             return len(self.region)
#         else:
#             node = self.outeralize(parent)
#             if node.t == 'root':
#                 return len(self.region)
#             elif node.t == 'element':
#                 return len(node.d.object_attribute.parameters)
#             return 0
#
#     def columnCount(self, index = QModelIndex()):
#         return 2
#
#     def headerData(self, section, orientation = Qt.Horizontal, role = Qt.DisplayRole):
#         header = ["Attribut", "Value"]
#         if orientation == Qt.Horizontal and role == Qt.DisplayRole:
#             return header[section]
#         return QVariant()
#

def get_output_slots(msmlfile, type=None):
    assert isinstance(msmlfile, MSMLFile)
    for task in msmlfile.workflow._tasks.values():
        taskname = task.id
        for slot, info in task.operator.output.items():
            #TODO check type
            yield "%s.%s" % (taskname, slot)


class EnvEditor(QDialog):
    def __init__(self, parent=None, flags=0):
        QDialog.__init__(self, parent)
        PyQt4.uic.loadUi(PKG_DIR / "env_editor.ui", self)


import msml.env
import msml.frontend
if __name__ == "__main__":
    msml.env.load_user_file()
    msml.env.current_alphabet = msml.frontend.alphabet({'<paths>':[], 'alphabet': 'a', '--xsd-file':False, '-S': True})

    import msmlgui.rcc

    import sys
    app = QApplication(sys.argv)

    edit = SceneEditor()
    model  = MSMLFile()

    t1 = Task("test",{'id':"abc"})
    t1.operator = msml.env.current_alphabet.get('surfaceExtract')
    model.workflow.add_task(t1)

    model.env.simulation.add_step("initial", 0.05, 1000)
    model.env.simulation.add_step("first", 0.05, 1000)
    model.env.simulation.add_step("second", 0.05, 1000)


    edit.model = model

    edit.open()
    app.exec_()