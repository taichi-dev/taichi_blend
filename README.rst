Taichi Blend
============

Taichi Blender intergration for creating physic-based animations.

将 Taichi 集成进 Blender，从而创作基于物理的动画。


How to install
--------------

1. Clone the repo and build the add-on:

.. code-block:: bash

    git clone https://github.com/taichi-dev/taichi_blend.git --depth=1
    cd taichi_blend
    make bundle

This should create the file ``build/Taichi-Blend.zip``.

2. Start your Blender, and follow these steps:

   Edit -> Preferences -> Add-ons -> Install

3. In the pop-up installation window, select the file ``build/Taichi-Blend.zip`` we just built.

4. Then you should see an item named ``Physics: Taichi Blend``, click the check on the left side to enable it.

5. Go to the ``Scripting`` module and try ``import taichi as ti`` to confirm that installation is complete.

If you encounter any problems, please report by `opening an issue <https://github.com/taichi_blend/issues>`_, many thanks!


安装指南
--------

1. 克隆该项目，并构建其插件：

.. code-block:: bash

    git clone https://github.com/taichi-dev/taichi_blend.git --depth=1
    cd taichi_blend
    make bundle

进行该操作后，你将得到文件 ``build/Taichi-Blend.zip`` 。

2. 启动 Blender，在菜单栏中如下步骤操作：

   编辑 -> 偏好设置 -> 插件 -> 安装

3. 在弹出的安装窗口中，选择我们刚刚构建好的 ``build/Taichi-Blend.zip`` 。

4. 然后你应该可以看见一个 ``Physics: Taichi Blend`` 的项目，点击它左边的勾选框，以启用它。

5. 前往 ``Scripting`` 模块， 试着输入 ``import taichi as ti`` 来确认安装是否正确完成。


如果遇到任何问题，请开一个 Issue 来报告，十分感谢！


How to play
-----------

TODO: WIP


使用指南
--------

TODO: 施工中
