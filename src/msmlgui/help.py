__author__ = 'Alexander Weigl'

from .shared import msml_app
from .helper.template import *
import UserDict

class Chainmap(UserDict.DictMixin):
    """Combine multiple mappings for sequential lookup.

    For example, to emulate Python's normal lookup sequence:

        import __builtin__
        pylookup = Chainmap(locals(), globals(), vars(__builtin__))
    """

    def __init__(self, *maps):
        self._maps = maps

    def __getitem__(self, key):
        for mapping in self._maps:
            try:
                return mapping[key]
            except KeyError:
                pass
        raise KeyError(key)


class OperatorDocumenationMap(UserDict.DictMixin):
    def __getitem__(self, item):
        operator = msml_app.alphabet.operators[item]
        return tpl_operator_help(o=operator)


class ElementOperatorDocumentationMap(UserDict.DictMixin):
    def __getitem__(self, item):
        element = msml_app.alphabet.object_attributes[item]
        return tpl_attribute_help(a=element)


class GoogleFallbackDocumentation(UserDict.DictMixin):
    def __getitem__(self, item):
        return "http://msml.readthedocs.org/en/latest/search.html?q=%s&check_keywords=yes&area=default"%item

_fixedKey = {}
_database = Chainmap(_fixedKey, OperatorDocumenationMap(),ElementOperatorDocumentationMap(), GoogleFallbackDocumentation())

__all__ = ['get_help']

def get_help(key):
    """

    :param key:
    :return:
    :rtype: str
    """
    return _database[key]



