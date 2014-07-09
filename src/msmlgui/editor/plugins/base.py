__author__ = 'Alexander Weigl'

from abc import *
from path import path

from pluginbase import PluginSource, PluginBase

plugin_base = PluginBase(package='msmlgui.editor.plugins')

plugin_source = plugin_base.make_plugin_source(
    searchpath=[path(__file__).dirname()])


def initialize_sources():
    with plugin_source:
        from msmlgui.editor.plugins import flycheck
        flycheck.install()

