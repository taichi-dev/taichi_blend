'''NumPy mesh helpers'''

import numpy as np


def meshgrid(n):
    def _face(x, y):
        return np.array([(x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1)])

    def _edge1(x, y):
        return np.array([(x, y), (x + 1, y)])

    def _edge2(x, y):
        return np.array([(x, y), (x, y + 1)])

    n_particles = n**2
    n_edges1 = (n - 1) * n
    n_edges2 = (n - 1) * n
    n_faces = (n - 1)**2
    xi = np.arange(n)
    yi = np.arange(n)
    xs = np.linspace(0, 1, n)
    ys = np.linspace(0, 1, n)
    pos = np.array(np.meshgrid(xs, ys)).swapaxes(0, 2).reshape(n_particles, 2)
    faces = _face(*np.meshgrid(xi[:-1], yi[:-1])).swapaxes(0, 1).swapaxes(1, 2).swapaxes(2, 3)
    faces = (faces[1] * n + faces[0]).reshape(n_faces, 4)
    edges1 = _edge1(*np.meshgrid(xi[:-1], yi)).swapaxes(0, 1).swapaxes(1, 2).swapaxes(2, 3)
    edges2 = _edge2(*np.meshgrid(xi, yi[:-1])).swapaxes(0, 1).swapaxes(1, 2).swapaxes(2, 3)
    edges1 = (edges1[1] * n + edges1[0]).reshape(n_edges1, 2)
    edges2 = (edges2[1] * n + edges2[0]).reshape(n_edges2, 2)
    edges = np.concatenate([edges1, edges2], axis=0)
    pos = np.concatenate([pos, np.zeros((n_particles, 1))], axis=1)
    uv = pos[faces, :2].reshape(faces.shape[1] * faces.shape[0], 2)
    return pos, edges, faces, uv
