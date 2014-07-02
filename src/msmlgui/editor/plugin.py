__author__ = 'weigl'

from abc import *
from path import path

from pluginbase import PluginSource, PluginBase


@ABCMeta
class Plugin(object):
    @abstractmethod
    def visitMainWindows(self):
        pass


def createPluginManager( additional_paths = list() ):

    system = path(__file__).dirname() / 'plugins'
    paths = additional_paths + [system]

    # Build the manager
    simplePluginManager = PluginManager()
    # Tell it the default place(s) where to find plugins
    simplePluginManager.setPluginPlaces(system)

    simplePluginManager.setCategoriesFilter({
       "Playback" : IPlaybackPlugin,
       "SongInfo" : ISongInfoPlugin,
       "Visualization" : IVisualisation,
       })



    # Load all plugins
    simplePluginManager.collectPlugins()

    # Activate all loaded plugins
    for pluginInfo in simplePluginManager.getAllPlugins():
       simplePluginManager.activatePluginByName(pluginInfo.name)
