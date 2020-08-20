import taichi as ti
import numpy as np

n_grid = 128
n_particles = n_grid**2
n_faces = (n_grid - 1)**2
n_frames = 250
output = '/tmp/grid2d.ply'

def face(x, y):
    return np.array([(x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1)])

for frame in range(n_frames):
    print('generating frame', frame)
    xs = np.linspace(0, 1, n_grid)
    ys = np.linspace(0, 1, n_grid)
    pos = np.array(np.meshgrid(xs, ys)).swapaxes(0, 2).reshape(n_particles, 2)
    indices = face(*np.meshgrid(np.arange(n_grid - 1), np.arange(n_grid - 1))).swapaxes(0, 1).swapaxes(1, 2).swapaxes(2, 3)
    indices = (indices[0] * n_grid + indices[1]).reshape(n_faces, 4)
    pos = np.concatenate([pos, np.zeros((n_particles, 1))], axis=1)
    writer = ti.PLYWriter(num_vertices=n_particles, num_faces=n_faces,
            face_type='quad')
    writer.add_vertex_pos(pos[:, 0], pos[:, 1], pos[:, 2])
    writer.add_faces(indices)
    writer.export_frame(frame, output)
