from distutils.core import setup

try:
    import py2exe
except:
    pass


setup(name="msml-gui",
      version="0.1alpha",
      author="Alexander Weigl",
      author_email="uiduw@student.kit.edu",
      url="https://github.com/CognitionGuidedSurgery/msml-gui/",
      license="GNU General Public License (GPL) 3",
      packages=['msmlgui'],
      package_data={"src": ["*.ui"]},
      scripts=["src/__main__.py"],
      windows=[{"script": "bin/liftr"}],
      options={"py2exe": {"skip_archive": True, "includes": ["sip"]}})