__author__ = 'Alexander Weigl <uiduw@student.kit.edu>'

from lxml import etree

from msml.exporter.visitor import *


def Sub(root, tagname, **kwargs):
    def parse(v):
        if isinstance(v, type):
            return v.__name__
        return str(v)

    str_kwargs = {k: parse(v) for k, v in kwargs.items()
                  if v is not None}
    return etree.SubElement(root, tagname, str_kwargs)


def object_element(parent, tag, attributes):
    def parse(v):
        if isinstance(v, Reference):
            return "${%s.%s}" % (v.task, v.slot)
        if isinstance(v, Constant):
            return v.value
        return v

    attribs = {str(k): parse(v) for k, v in attributes.items() if k != "__tag__"}
    return Sub(parent, tag, **attribs)


class XmlBuilder(VisitorExporterFramework):
    def __init__(self, msml_file):
        VisitorExporterFramework.__init__(self, msml_file, None)
        Visitor.__init__(self, self)
        self.visitor = self

    def to_xml(self):
        return self.visit()

    def __object_element(self, parent, element):
        assert isinstance(element, ObjectElement)
        return object_element(parent, element.tag, element.attributes)

    def write_export_file(self, msml_file_path, product):
        pass

    def scene_begin(self, _msml, scene):
        return Sub(_msml, "scene")

    def object_sets_begin(self, _msml, _scene, _object, sets):
        return Sub(_object, "sets")

    def object_sets_elements_begin(self, _msml, _scene, _object, _object_sets, elements):
        return Sub(_object_sets, "elements")

    def object_sets_nodes_begin(self, _msml, _scene, _object, _object_sets, nodes):
        return Sub(_object_sets, 'nodes')

    def object_sets_surfaces_begin(self, _msml, _scene, _object, _object_sets, surfaces):
        return Sub(_object_sets, "surfaces")

    def object_sets_surfaces_element(self, _msml, _scene, _object, _object_sets, _surfaces, surface):
        return self.__object_element(_object_sets, surface)

    def object_sets_nodes_element(self, _msml, _scene, _object, _object_sets, _nodes, node):
        return self.__object_element(_object_sets, node)

    def object_sets_elements_element(self, _msml, _scene, _object, _object_sets, _elements, element):
        return self.__object_element(_object_sets, element)

    def object_output_begin(self, _msml, _scene, _object, outputs):
        return Sub(_object, "output")

    def object_output_element(self, _msml, _scene, _object, _output, output):
        return self.__object_element(_output, output)

    def object_mesh(self, _msml, _scene, _object, mesh):
        assert isinstance(mesh, Mesh)
        return Sub(_object, mesh.type, id=mesh.id, mesh=mesh.mesh)

    def object_material_region_begin(self, _msml, _scene, _object, _material, region):
        assert isinstance(region, MaterialRegion)
        return Sub(_material, "region",
                   id=region.id)

    def object_material_region_element(self, _msml, _scene, _object, _material, _region, element):
        return self.__object_element(_region, element)


    def object_material_begin(self, _msml, _scene, _object, materials):
        return Sub(_object, "material")

    def object_constraints_begin(self, _msml, _scene, _object, constraints):
        return Sub(_object, "constraints")

    def object_constraint_element(self, _msml, _scene, _object, _constraints, _constraint, element):
        return self.__object_element(_constraint, element)

    def object_constraint_begin(self, _msml, _scene, _object, _constraints, constraint):
        assert isinstance(constraint, ObjectConstraints)
        return Sub(_constraints, "constraint", name=constraint.name, forStep=constraint.for_step)

    def object_begin(self, _msml, _scene, object):
        return Sub(_scene, "object", id=object.id)

    def msml_begin(self, msml_file):
        return etree.Element("msml")
        # TODO Add namespace attributes
        # xmlns:msml="http://sfb125.de/msml"
        # xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        # xsi:schemaLocation="http://sfb125.de/msml

    def environment_solver(self, _msml, _environment, solver):
        return Sub(_environment, "solver",
                   dampingRayleighRatioMass=solver.dampingRayleighRatioMass,
                   preconditioner=solver.preconditioner,
                   dampingRayleighRatioStiffness=solver.dampingRayleighRatioStiffness,
                   linearSolver=solver.linearSolver,
                   timeIntegration=solver.timeIntegration,
                   processingUnit=solver.processingUnit)

    def environment_simulation_begin(self, _msml, _environment, simulation):
        return Sub(_environment, "simulation")

    def environment_simulation_element(self, _msml, _environment, _simulation, step):
        return Sub(_simulation, "step", dt=step.dt, name=step.name,
                   iterations=step.iterations)

    def environment_begin(self, _msml, env):
        return Sub(_msml, "environment")

    def variables_begin(self, _msml, variables):
        return Sub(_msml, "variables")

    def variables_element(self, _msml, _variables, variable):
        assert isinstance(variable, MSMLVariable)
        if variable.name.startswith("_gen"):
            return None

        return Sub(_variables, "var", format=variable.format, name=variable.name, value=variable.value,
                   type=variable.type)

    def workflow_begin(self, _msml, workflow):
        return Sub(_msml, "workflow")

    def workflow_element(self, _msml, _workflow, task):
        a = dict(task.attributes)
        a['id'] = task.id
        return object_element(_workflow, task.name, a)


__all__ = ['to_xml']


def to_xml(msml_file):
    b = XmlBuilder(msml_file)
    return b.to_xml()


import codecs


def save_xml(fp, xml):
    r = etree.ElementTree(xml)
    with codecs.open(fp, 'w', 'utf-8') as fp:
        r.write(fp, pretty_print=True)
