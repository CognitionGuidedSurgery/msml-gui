__author__ = 'weigl'

import operator
from collections import namedtuple
from itertools import starmap

from msmlgui.shared import msml_app


ErrorEntry = namedtuple("ErrorEntry", "level message position")


def match_values(tokens, *values):
    if len(tokens) == len(values):
        tokvals = map(operator.attrgetter("value"), tokens)
        return all(starmap(operator.eq, zip(tokvals, values)))
    return False


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
                    "Task of %s does not have an <id> attribute" % operator.name, element[':tag']))


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
                    self.report.append(ErrorEntry(0,"attrib %s is unknown for operator %s in task %s" % (
                        k, operator.name, element['id']), element[":"+k]))

        except KeyError:
            self.report.append(
                ErrorEntry(1, "%s is not defiend in the alphabet" % element['_tag'], element[':tag']))






def find_errors(tokens):
    opc = OperatorChecker()

    groups = list(group_elements(tokens))

    for et in groups:
        #print build_element(et)
        opc(et)

    return opc.report


if __name__ == '__main__':
    with open("/org/share/home/weigl/workspace/msml/examples/BunnyExample/bunnyCGAL.msml.xml") as fp:
        content = fp.read()
        import msmlgui.text.xmllexer

        toks = msmlgui.text.xmllexer.tokenize(content)
        print find_errors(toks)
