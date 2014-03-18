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


        QMetaObject.connectSlotsByName(self)

        # static models
        self.cboMaterialRegionElementsModel = MaterialElementsModel(self)
        self.cboMaterialRegionElements.setModel(self.cboMaterialRegionElementsModel )

        self.current_scene_object = None

    @pyqtSlot(str)
    def on_mesh_change(self, val):
        if self.current_scene_object:
            self.current_scene_object.mesh.mesh = val
            # TODO specify type

    def on_material_region_name_change(self, name):
        if self.current_scene_object:
            index = self.cboMaterialRegion.currentIndex()
            mat = self.current_scene_object.material[index]
            mat.id = name

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
            region = self.current_scene_object.material[index]
            #assert isinstance(self.tabMaterialRegionElementAttributes, QTreeWidget)
            #self.tabMaterialRegionElementAttributesModel = MaterialRegionElementsModel(self.model, self.current_scene_object, mat, self)
            #self.tabMaterialRegionElementAttributes.setModel(self.tabMaterialRegionElementAttributesModel)

            self.tabMaterialRegionElementAttributes.clear()
            for mat in region: self.append_material_region_entry(mat)


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
            item.setExpanded(True)
            root.addChild(item)

        root.setExpanded(True)
        self.tabMaterialRegionElementAttributes.addTopLevelItem(root)




    def on_material_region_add(self):
        if self.current_scene_object:
            mat = MaterialRegion(generate_name('mat_', '_region'))

            # DEBUG
            oe = ObjectElement({}, msml.env.current_alphabet.get("linearElasticMaterial"))
            mat.append(oe)
            #


            self.current_scene_object.material.append(mat)

            index = self.cboMaterialRegionModel.createIndex(0,0)

            self.cboMaterialRegionModel.rowsInserted.emit\
                (index, 0, len(self.current_scene_object.material))

            self.cboMaterialRegion.setCurrentIndex(len(self.current_scene_object.material)-1)


    def on_material_region_element_add(self):
        # TODO add element
        pass

    def on_material_region_remove(self):
        pass


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
        self.cboMeshModel = MeshModel(model, self)
        self.cboMesh.setModel(self.cboMeshModel)

        self.cboMesh.setCurrentIndex(self.cboMeshModel.lookafter(sceneobj.mesh.mesh))

        self.cboMaterialRegionModel = MaterialRegionModel(self.model, self.current_scene_object, self)
        self.cboMaterialRegion.setModel(self.cboMaterialRegionModel)


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

    edit.model = model

    edit.open()
    app.exec_()