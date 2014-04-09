__author__ = 'Alexander Weigl <uiduw@student.kit.edu>'

from msml.frontend import App
from functools import partial

from jinja2 import Environment, PackageLoader

jenv = Environment(loader= PackageLoader(__name__))
msml_app = App()

def render_template(tpl_name, **kwargs):
    return jenv.get_template(tpl_name).render(**kwargs)

tpl_operator_help = partial(render_template, "operator_help.html")
tpl_task_shape = partial(render_template, "task_shape.html")
tpl_scene_shape = partial(render_template, "scene_shape.html")
tpl_scene_help= partial(render_template, "scene_help.html")


def generate_name(prefix = "task", suffix = ""):
    import random
    chars = [chr(i) for i in range(65, 110)]
    rand =''.join(random.sample(chars, 5))
    return prefix + rand + suffix