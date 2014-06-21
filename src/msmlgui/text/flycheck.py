__author__ = 'weigl'

from PyQt4.QtCore import Qt

import operator
from collections import namedtuple
from itertools import starmap

from msmlgui.shared import msml_app


ErrorEntry = namedtuple("ErrorEntry", "level message position")


def match_values(tokens, *values):
    if len(tokens) == len(values):
        return match_values_start(tokens, *values)
    return False


def match_values_start(tokens, *values):
    tokvals = map(operator.attrgetter("value"), tokens)
    return all(starmap(operator.eq, zip(tokvals, values)))


def group_elements(tokens):
    cache = []
    for t in tokens:
        if t.type == "PCDATA" and t.value.strip(" \n") == "":
            continue

        cache.append(t)
        if t.type in ("LONETAGCLOSE", "TAGCLOSE"):
            yield cache
            cache = []


def build_element(element_tokens):
    d = {}
    it = iter(element_tokens)
    next(it)

    tag = next(it)
    d['_tag'] = tag.value
    d[':tag'] = tag.lexpos

    attr_name = None
    attr_start = None
    attr_stop = None
    attr_value = None

    for t in it:
        if t.type == "TAGCLOSE": break

        if t.type == "TAGATTRNAME":
            attr_name = t.value
            attr_start = t.lexpos

        if t.type == "ATTRVALUE2STRING":
            attr_value = t.value

        if t.type == "ATTRVALUE2CLOSE":
            attr_stop = t.lexpos + 1

            d[attr_name] = attr_value
            d[":" + attr_name] = (attr_start, attr_stop)

    d[':tag'] = (tag.lexpos, t.lexpos + 1)

    return d


class OperatorChecker(object):
    def __init__(self):
        self.report = []
        self.activated = False

    def __call__(self, element_tokens):
        if not self.activated:
            self.activated = match_values(element_tokens, "<", "workflow", ">")
        elif match_values(element_tokens, "</", "workflow", ">"):
            self.activated = False
        else:
            element = build_element(element_tokens)
            self.check(element)


    def check(self, element):
        alphabet = msml_app.alphabet
        try:
            operator = alphabet.operators[element['_tag']]

            if 'id' not in element:
                self.report.append(ErrorEntry(1,
                                              "Task of %s does not have an <id> attribute" % operator.name,
                                              element[':tag']))

            for name, slot in operator.input.items():
                if name not in element:
                    self.report.append(
                        ErrorEntry(1, "task %s for operator %s misses input attribute %s " % (
                            element['id'], operator.name, name), element[':tag']))

            for name, slot in operator.parameters.items():
                if name not in element:
                    self.report.append(
                        ErrorEntry(1, "task %s for operator %s misses parameter attribute %s " % (
                            element['id'], operator.name, name), element[':tag']))

            for k in element:
                if k.startswith(":") or k.startswith("_") or k == "id":
                    continue

                if k not in operator.acceptable_names():
                    self.report.append(ErrorEntry(0, "attrib %s is unknown for operator %s in task %s" % (
                        k, operator.name, element['id']), element[":" + k]))

        except KeyError:
            self.report.append(
                ErrorEntry(1, "%s is not defiend in the alphabet" % element['_tag'], element[':tag']))


def find_errors(tokens):
    opc = OperatorChecker()

    groups = list(group_elements(tokens))

    for et in groups:
        # print build_element(et)
        opc(et)

    return opc.report


# #######################################################################################################################

TreeEntry = namedtuple("TreeEntry", "name position color icon")


class Overview(object):
    def __init__(self):
        self.variables = []
        self.tasks = []
        self.objects = []
        self.environment = []

    def add(self, seq, text, position, foreground=False, background=False, icon=False):
        from  PyQt4.QtGui import QTreeWidgetItem



        item = QTreeWidgetItem()

        item.setText(0, text)
        item.setData(0, Qt.UserRole, position)

        if foreground:
            item.setForeground(0, foreground)

        if background:
            item.setBackground(0, background)

        if icon:
            item.setIcon(0, icon)

        seq.append(item)
        return item

    def add_environment(self, *args, **kwargs):
        return self.add(self.environment, *args, **kwargs)

    def add_task(self, *args, **kwargs):
        return self.add(self.tasks, *args, **kwargs)

    def add_object(self, *args, **kwargs):
        return self.add(self.objects, *args, **kwargs)

    def add_variable(self, *args, **kwargs):
        return self.add(self.variables, *args, **kwargs)


class FindVariables(object):
    def __init__(self, overview):
        self.overview = overview

    def __call__(self, tokens):
        if tokens[1].value == "var":  # and tokens[1].type == "TAGNAME"
            element = build_element(tokens)

            name = "%s : (%s,%s)" % (element['name'], element['physical'], element['logical'],)
            position = element[':tag'][0]

            self.overview.add_variable(name, position)


class FindObjectOutput(object):
    def __init__(self, overview):
        self.overview = overview
        self.activated_object = False
        self.activated_output = False

    def __call__(self, tokens):
        if not self.activated_output and match_values_start(tokens, "<", "object"):
            self.activated_object = True
        elif self.activated_object and match_values(tokens, "</", "object", ">"):
            self.activated_object = False
        else:
            if not self.activated_output and match_values(tokens, "<", "output", ">"):
                self.activated_output = True
            elif self.activated_output and match_values(tokens, "</", "output", ">"):
                self.activated_output = False
            elif self.activated_object and self.activated_output:
                element = build_element(tokens)

                print "object output"

                name = "%s : (%s,%s)" % (element['id'], "n/a", "n/a")
                position = element[':tag'][0]

                self.overview.add_variable(name, position)


class FindObjects(object):
    def __init__(self, overview):
        self.overview = overview

    def __call__(self, tokens):
        if match_values_start(tokens, "<", "object"):
            element = build_element(tokens)

            name = "%s" % (element['id'],)
            position = element[':tag'][0]

            self.overview.add_object(name, position)


class FindEnvironment(object):
    def __init__(self, overview):
        self.overview = overview
        self.in_env = False

    def __call__(self, tokens):
        if not self.in_env and match_values(tokens, "<", "environment", ">"):
            self.in_env = True
        elif self.in_env and match_values(tokens, "</", "environment", ">"):
            self.in_env = False
        elif self.in_env:
            element = build_element(tokens)

            for k, v in element.items():
                if k.startswith("_") or k.startswith(":"):
                    continue

                name = "%s: %s = %s" % (element['_tag'], k, v)
                position = element[':' + k][0]

                self.overview.add_environment(name, position)


class FindTasks(object):
    def __init__(self, overview):
        self.overview = overview
        self.in_wf = False

    def __call__(self, tokens):
        if not self.in_wf and match_values(tokens, "<", "workflow", ">"):
            self.in_wf = True
        elif self.in_wf and match_values(tokens, "</", "workflow", ">"):
            self.in_wf = False
        elif self.in_wf:

            print("task")

            element = build_element(tokens)

            _id = element.get('id',"n/a")

            name = "%s: %s" % (_id, element["_tag"],)
            position = element[':tag'][0]


            try:
                operator = msml_app.alphabet.operators[element["_tag"]]

                for o in operator.output_names():
                    self.overview.add_variable(
                        "%s.%s" % (_id, o),
                        position
                    )

                foreground = False
            except KeyError:
                foreground = Qt.darkRed


            self.overview.add_task(name, position, foreground = foreground)


def build_overview(tokens):
    overview = Overview()

    var = FindVariables(overview)
    oo = FindObjectOutput(overview)
    fo = FindObjects(overview)
    env = FindEnvironment(overview)
    tk = FindTasks(overview)

    actions = [var, oo, fo, env,tk]

    for group in list(group_elements(tokens)):
        for a in actions:
            a(group)

    return overview


if __name__ == '__main__':
    with open("/org/share/home/weigl/workspace/msml/examples/BunnyExample/bunnyCGAL.msml.xml") as fp:
        content = fp.read()
        import msmlgui.text.xmllexer

        toks = msmlgui.text.xmllexer.tokenize(content)
        print find_errors(toks)
