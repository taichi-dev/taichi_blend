Taichi Blend
============

Taichi Blender intergration for creating physic-based animations.

将 Taichi 集成进 Blender，从而创作基于物理的动画。


Examples: https://github.com/taichi-dev/taichi_blend/tree/master/examples.
Taichi repo: .
Taichi documentation: 
Taichi 中文文档: https://taichi.readthedocs.io/zh_CN/latest.
Taichi forum: https://forum.taichi.graphics.


How to install
--------------

1. Go to the `release page <https://github.com/taichi-dev/taichi_blend/releases>`_,
   choose one of the ZIP files to download, according to your system.
   Download ``Taichi-Blend-win.zip`` for Windows users for example.

2. Start your Blender, and follow these steps:

   Edit -> Preferences -> Add-ons -> Install

3. In the pop-up installation window, select the file ``Taichi-Blend.zip`` we just download.

4. Then you should see an item named ``Physics: Taichi Blend``, click the check on the left side to enable it.

5. Go to the ``Scripting`` module and try ``import taichi as ti`` to confirm that installation is complete.

If you encounter any problems, please report by `opening an issue <https://github.com/taichi_blend/issues>`_, many thanks!


安装指南
--------

1. 前往 `发布页面 <https://github.com/taichi-dev/taichi_blend/releases>`_ ，
   选择符合你操作系统的那个 ZIP 文件来下载。
   比如 Windows 用户，请下载 ``Taichi-Blend-win.zip`` 。

2. 启动 Blender，在菜单栏中如下步骤操作：

   编辑 -> 偏好设置 -> 插件 -> 安装

3. 在弹出的安装窗口中，选择我们刚刚下载的 ``Taichi-Blend.zip`` 。

4. 然后你应该可以看见一个 ``Physics: Taichi Blend`` 的项目，点击它左边的勾选框，以启用它。

5. 前往 ``Scripting`` 模块， 试着输入 ``import taichi as ti`` 来确认安装是否正确完成。


如果遇到任何问题，请 `开一个 Issue <https://github.com/taichi_blend/issues>`_ 来报告，十分感谢！


Included packages
-----------------

Installing this bundle (``Taichi-Blend.zip``) will allows you to use these packages:

* ``taichi`` - the Taichi programming langurage [[repo]](https://github.com/taichi-dev/taichi) [[doc]](https://taichi.readthedocs.io/en/stable)
* ``taichi_glsl`` - some handy helper functions for Taichi [[repo]](https://github.com/taichi-dev/taichi_glsl) [[doc]](https://taichi-glsl.readthedocs.io)
* ``taichi_elements`` - a high-performance MPM solver written in Taichi [[repo]](https://github.com/taichi-dev/taichi_elements) [[doc]](https://taichi-elements.readthedocs.io)
* ``numblend`` - utilities to interface Blender with NumPy


整合包内容
----------

安装了该整合包 (``Taichi-Blend.zip``) 后，你将可以使用下列 Python 包：

* ``taichi`` - Taichi 编程语言 [[项目主页]](https://github.com/taichi-dev/taichi) [[中文文档]](https://taichi.readthedocs.io/zh_CN/latest)
* ``taichi_glsl`` - Taichi 一些有用的扩展函数 [[项目主页]](https://github.com/taichi-dev/taichi_glsl) [[英文文档]](https://taichi-glsl.readthedocs.io)
* ``taichi_elements`` - 用 Taichi 写的一个高性能 MPM 求解器 [[项目主页]](https://github.com/taichi-dev/taichi_elements) [[英文文档]](https://taichi-elements.readthedocs.io)
* ``numblend`` - 在 Blender 和 NumPy 之间搭建桥梁的工具
