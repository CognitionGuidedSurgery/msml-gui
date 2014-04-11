__author__ = 'weigl'

import random
import json
import msml.model


def random_position():
    p = lambda: random.randint(-20, 20)
    return p(), p()


def generate_name(prefix="task", suffix=""):
    chars = [chr(i) for i in range(65, 110)]
    sample = random.sample(chars, 5)
    rand = ''.join(sample)
    return prefix + rand + suffix


def msml_file_factory():
    return msml.model.MSMLFile()