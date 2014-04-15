__author__ = 'Alexander Weigl'

from StringIO import StringIO

from msml.exporter.visitor import VisitorExporterFramework
from msml.model import *


class SceneTextBuilder(VisitorExporterFramework):
    def __init__(self, msml_file):
        VisitorExporterFramework.__init__(self, msml_file, None)

        self.visitor = self
        self.text = StringIO()

    def div_closer(self, *args):
        self.text.write("</div>")

    def div_start(self, name, *args):
        title = name.split('_')[-2]
        self.text.write("<div class='%s'><h3>%s</h3>" % (name, title))

    def __getattr__(self, item):
        # if item in self.__dict__:
        #     return self.__dict__[item]

        if item.endswith("_end"):
            return self.div_closer

        if item.endswith("_begin"):
            def fn(*args):
                self.div_start(item, *args)

            return fn

        if item.endswith('_element'):
            def fn(*args):
                element = args[-1]
                if isinstance(element, ObjectElement):
                    self.object_element(element)

            return fn

        return lambda *args: 0

    def object_element(self, element):
        self.text.write('<div class="element"><h4>{tag}</h4><table>'.format(
            tag=element.tag))

        for k, v in element.attributes.items():
            self.text.write("<tr><th>%s</th><td>%s</td></tr>" % (k, v))
        self.text.write("</table></div>")

    def object_mesh(self, _msml, _scene, _object, mesh):
        self.text.write('<div class="mesh"><h3>Mesh</h3><table>')
        self.text.write("<tr><th>%s</th><td>%s</td></tr>" % ("Id", mesh.id))
        self.text.write("<tr><th>%s</th><td>%s</td></tr>" % ('Mesh', mesh.mesh))
        self.text.write("<tr><th>%s</th><td>%s</td></tr></table>" % ('Type', mesh.type))

    def msml_begin(self, *args):
        self.text.write("""
        <html>
        <head>
        <style>
       .environment_begin,
        .variables_begin,
        .workflow_begin,
        .environment_simulation_begin {
            display: none;
        }

        table {with:100%}
        table:nth-child(odd) {
            backround: #424;
        }

        h1, h2, h3, h4 {
            background: #ccc;
            padding:0.2em;
            margin:0;
        }

        table:nth-child(even) {
            backround: #424;
        }

        th {text-align: right; width:30%; border-right: 1px dashed black; padding:1em;}
        div {
            margin-left:1.5em;
            border-left: 2px solid black;
            border-top: 1px solid black;
            border-bottom: 1px solid black;
        }

        </style>
        <body>
        """)

    def msml_end(self, *args):
        self.text.write("</body></html>")

    def scene_begin(self, _msml, scene):
        self.text.write('<div class="scene"> <h1>Scene</h1>')

    def object_begin(self, _msml, _scene, object):
        self.text.write('<div class="object"> <h2>Object: %s</h2>' % object.id)


def scene_to_text(msml):
    s = SceneTextBuilder(msml)
    s.visit()
    return s.text.getvalue()