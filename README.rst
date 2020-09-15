Taichi Blend
============

Taichi Blender intergration for creating physic-based animations.


Examples: https://github.com/taichi-dev/taichi_blend/tree/master/examples.
Taichi repo: https://github.com/taichi-dev/taichi.
Taichi documentation: https://taichi.readthedocs.io/en/stable.
Taichi 中文文档: https://taichi.readthedocs.io/zh_CN/latest.
Taichi forum: https://forum.taichi.graphics.


How to install
--------------

1. Goto the Blender ``Scripting`` window, type these commands into the shell:

.. code-block:: python

   import sys
   import platform
   major = sys.version_info.major
   minor = sys.version_info.minor
   assert major == 3 and minor in [6, 7, 8], "Only Python 3.6/3.7/3.8 is supported"

   ver = str(major) + str(minor)

   if sys.platform.lower().startswith('win'):
      plat = 'win'
   elif sys.platform.lower().startswith('linux'):
      plat = 'linux'
   else:
      assert 0, "Invalid platform: {}".format(sys.platform)

   file = 'Taichi-Blend-{}-py{}.zip'.format(plat, ver)
   print('You should download', file)


It may shows, for example:

.. code-block:: none

   You should download Taichi-Blend-win-py37.zip

2. Go to the `release page <https://github.com/taichi-dev/taichi_blend/releases>`_,
   choose one of the ZIP files to download, according to the ``You should download`` printed above.
   Download ``Taichi-Blend-win.zip`` for Windows users for example.

3. Go back to the Blender, and follow these steps:

   Edit -> Preferences -> Add-ons -> Install

4. In the pop-up installation window, select the file ``Taichi-Blend.zip`` we just download.

5. Then you should see an item named ``Physics: Taichi Blend``, click the check on the left side to enable it.

6. Try ``import taichi as ti`` in the shell to confirm that installation is complete.

If you encounter any problems, please report by `opening an issue <https://github.com/taichi-dev/taichi_blend/issues>`_, many thanks!


How to play
-----------

1. Create a new ``General`` scene in Blender, delete the default ``Cube``.

2. Go to the ``Scripting`` window, press ``New`` to create a new script (text).

3. Paste some `example scripts <https://github.com/taichi-dev/taichi_blend/tree/master/examples>`_ to the editor.

4. Press the play button to run the script. Blender may stuck a while for the first launch.

5. Go back to ``Layout`` window. Press SPACE and you should see particles to move. May stuck a while at first frame.

Included packages
-----------------

Installing this bundle (``Taichi-Blend.zip``) will allows you to use these packages:

* ``taichi`` - the Taichi programming langurage `[repo] <https://github.com/taichi-dev/taichi>`_ `[doc] <https://taichi.readthedocs.io/en/stable>`_
* ``taichi_glsl`` - some handy helper functions for Taichi `[repo] <https://github.com/taichi-dev/taichi_glsl>`_ `[doc] <https://taichi-glsl.readthedocs.io>`_
* ``taichi_elements`` - a high-performance MPM solver written in Taichi `[repo] <https://github.com/taichi-dev/taichi_elements>`_ `[doc] <https://taichi-elements.readthedocs.io>`_
* ``numblend`` - utilities to interface Blender with NumPy