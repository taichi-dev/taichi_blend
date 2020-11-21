from . import *


if __name__ == '__main__':
    ini = A.specify_meta(C.float[512, 512], A.gaussian_dist([256, 256], 6, 8))
    pos = A.double_buffer(A.get_meta(ini))
    vel = A.double_buffer(A.get_meta(ini))
    A.bind_source(pos, A.advect_position(pos, vel, 0.1))
    A.bind_source(vel, A.laplacian_step(pos, vel, 1))
    init = A.merge_tasks(A.copy_field(pos, ini),
            A.copy_field(vel, A.constant_field(0)))
    step = A.repeat_task(A.merge_tasks(pos, vel), 8)
    vis = A.mix_value(A.pack_vector(pos, A.field_gradient(pos)),
            A.constant_field(1), 0.5, 0.5)
    init.run()
    gui = A.canvas_visualize(vis, step)
    gui.run()
