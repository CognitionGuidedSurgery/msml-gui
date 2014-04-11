__author__ = 'weigl'

import json
import msml.model
from .util import random_position

class Annotation(object):
    def __init__(self, pos = (0,0), text = ""):
        self.text = text
        self.pos = pos

class UiPersistentData(object):
    def __init__(self):
        self.task_positions = {}
        self.annotations = []

    def get_task_position(self, task):
        import msmlgui.widgets
        if isinstance(task, msmlgui.widgets.TaskShape):
            task = task.task

        if isinstance(task, msmlgui.widgets.SceneShape):
            task = "__scene__"

        if isinstance(task, msml.model.Task):
            task = task.id

        return self.task_positions.get(task, random_position())

    def store(self, filename):
        with open(filename, 'w') as fp:
            json.dump(self, fp)

    @staticmethod
    def load(filename):
        try:
            with open(filename) as fp:
                return json.load(fp)
        except IOError as e:
            print(e)
            return UiPersistentData()

    @staticmethod
    def load_from_msml(filename):
        f = filename.dirname() / filename.namebase + ".ui.json"
        return UiPersistentData.load(f)


class UiVolatileData(object):
    def __init__(self):
        self.task_map = {}
