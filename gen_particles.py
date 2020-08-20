import taichi as ti
import numpy as np

n_particles = 8192
n_frames = 250
output = '/tmp/particles.ply'

for frame in range(n_frames):
    print('generating frame', frame)
    pos = np.random.rand(n_particles, 3) * 2 - 1
    writer = ti.PLYWriter(num_vertices=n_particles)
    writer.add_vertex_pos(pos[:, 0], pos[:, 1], pos[:, 2])
    writer.export_frame(frame, output)
