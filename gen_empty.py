import taichi as ti
import numpy as np
import sys

n_frames = 250
output = sys.argv[1]

x = np.ones(1)
for frame in range(n_frames):
    print('generating frame', frame)
    writer = ti.PLYWriter(num_vertices=1)
    writer.add_vertex_pos(x, x, x)
    writer.export_frame(frame, output)
