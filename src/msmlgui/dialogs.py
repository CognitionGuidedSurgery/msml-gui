__author__ = 'Alexander Weigl'
__date__ = "2014-03-09"

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import PyQt4.uic
from path import path

from msml.model import *

PKG_DIR = path(__file__).parent

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
    chars = [chr(i) for i in range(65, 110)]
    rand =''.join(random.sample(chars, 5))
    return prefix + rand + suffix


class SceneEditor(QDialog):
    def __init__(self, parent=None, flags=0):
        QDialog.__init__(self, parent)
        PyQt4.uic.loadUi(PKG_DIR / "scene_editor.ui", self)

        # general
        self.btnSceneObjectAdd.clicked.connect(self.add_scene_object)
        self.btnSceneObjectRemove.clicked.connect(self.remove_scene_object)

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

        self.cboMeshModel = MeshSelection(model, self)
        self.cboMesh.setModel(self.cboMeshModel)


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



class MeshSelection(QStringListModel):
    def __init__(self, msmlfile, parent=None):
        QStringListModel.__init__(self, parent)
        assert isinstance(msmlfile, MSMLFile)

        list = QStringList()

        for value in get_output_slots(msmlfile, type="mesh"):
            list << value

        self.setStringList(list)



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
            return QVariant(o.name)
        return QVariant()

    def rowCount(self, parent  = QModelIndex()):
        return len(self.msmlobj.material)

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

class MaterialRegionElements(QAbstractListModel):
    def __init__(self, msmlfile, msmlobj, material, parent=None):
        QAbstractListModel.__init__(self, parent)
        assert isinstance(msmlfile, MSMLFile)
        assert isinstance(msmlobj, SceneObject)
        assert isinstance(material, MaterialRegion)

        self.msmlfile = msmlfile
        self.sceneobj = msmlobj
        self.region = material

        alphabet = msml.env.current_alphabet
        oattr = filter( lambda x: isinstance(x, OAMaterial), alphabet.object_attributes)

        self.elements = oattr
        self.activated = dict()

        for m in material:
            assert isinstance(m, ObjectElement)
            self.activated[m.object_attribute] = True

    def data(self, index = QModelIndex(), role = Qt.DisplayRole):
        if index.isValid():
            o = self.elements[index.row()]
            if role == Qt.DisplayRole:
                return QVariant(o.name)
            elif role == Qt.FontRole:
                font = QAbstractListModel.data(index, role)
                if font and o in self.activated:
                    return font.setWeight(QFont.Bold)
        return QVariant()

    def rowCount(self, parent  = QModelIndex()):
        return len(self.msmlobj.material)



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
