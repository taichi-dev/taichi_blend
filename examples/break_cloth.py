__import__('importlib').reload(__import__('reblend'))
from reblend import *
import taichi as ti
import taichi_glsl as tl

ti.init(arch=ti.cpu)

dt = 4e-4
steps = 58
stiffness = 2e3
damping = 9e-3
resistance = 0.3
gravity = 2
tolerance = 0.63
mass_scale = 0.2
cloth_height = 1.5
ball_radius = 0.5
ground_height = -0.5

cloth = bpy.data.collections['Cloth'].objects[0].data
_pos = to_numpy(cloth.vertices, 'co').astype(np.float32)
_edges = to_numpy(cloth.edges, 'vertices').astype(np.int32)
_faces = to_numpy(cloth.polygons, 'vertices').astype(np.int32)

ball = bpy.data.collections['Ball'].objects[0].data
ball_vertices = to_numpy(ball.vertices, 'co').astype(np.float32)
ball_edges = to_numpy(ball.edges, 'vertices').astype(np.int32)
ball_faces = to_numpy(ball.polygons, 'vertices').astype(np.int32)

_pos[:, 2] += cloth_height
pos = ti.Vector.field(3, float, _pos.shape[0])
vel = ti.Vector.field(3, float, _pos.shape[0])
edges = ti.Vector.field(2, int, _edges.shape[0])
rest = ti.field(float, _edges.shape[0])
ball_pos = ti.Vector.field(3, float, ())
ball_vel = ti.Vector.field(3, float, ())

ball_pos[None] = [0.12, -0.06, 2.8]
pos.from_numpy(_pos)
edges.from_numpy(_edges)


@ti.kernel
def init():
    for e in edges:
        p, q = edges[e]
        disp = pos[q] - pos[p]
        rest[e] = disp.norm()

@ti.kernel
def substep():
    for e in edges:
        if rest[e] >= 1e3:
            continue
        p, q = edges[e]
        disp = pos[q] - pos[p]
        disv = vel[q] - vel[p]
        k = disp.norm() - rest[e]
        if k > rest[e] * tolerance:
            rest[e] = 1e4
        acc = disp * k / rest[e]**2
        acc += disv * damping
        vel[p] += stiffness * acc * dt
        vel[q] -= stiffness * acc * dt
    for p in pos:
        vel[p].z -= gravity * dt
        new_vel = tl.ballBoundReflect(pos[p], vel[p], ball_pos[None], ball_radius + 0.037, 6)
        dv = vel[p] - new_vel
        ball_vel[None] += dv * mass_scale / pos.shape[0]
        vel[p] = new_vel
        if pos[p].z <= ground_height and vel[p].z < 0:
            vel[p].z = 0
        if pos[p].z == cloth_height:
            if (pos[p].x == -1 or pos[p].x == 1) or (pos[p].y == -1 or pos[p].y == 1):
                vel[p] *= 0
        vel[p] *= ti.exp(-dt * resistance)
        pos[p] += vel[p] * dt
    ball_vel[None].z -= gravity * dt
    ball_pos[None] += ball_vel[None] * dt
    if ball_pos[None].z <= ball_radius + ground_height and ball_vel[None].z < 0:
        ball_vel[None].z *= -0.6


def get_edges():
    cols = np.extract(_rest >= 1e3, np.arange(_rest.shape[0]))
    return np.delete(_edges, cols, axis=0)

def get_faces():
    endpoint0 = _pos[_faces[:, 0]]
    endpoint1 = _pos[_faces[:, 1]]
    endpoint2 = _pos[_faces[:, 2]]
    endpoint3 = _pos[_faces[:, 3]]
    areas = np.sqrt(np.sum(np.cross(endpoint0 - endpoint1, endpoint0 - endpoint2, axis=1)**2, axis=1))
    areas += np.sqrt(np.sum(np.cross(endpoint3 - endpoint0, endpoint3 - endpoint2, axis=1)**2, axis=1))
    cols = np.extract(areas >= 1.63 * ((1 + tolerance) * _rest_average)**2, np.arange(_faces.shape[0]))
    return np.delete(_faces, cols, axis=0)
    
init()
_rest = rest.to_numpy()
_rest_average = np.average(_rest)
for i, (cloth, ball) in enumerate(zip(object_frames('p_sequence'), object_frames('q_sequence'))):
    print('rendering frame', i)
    for s in range(steps):
        substep()
    _pos = pos.to_numpy()
    _rest = rest.to_numpy()
    cloth = new_mesh('p_seq', _pos, [], get_faces())
    set_object_frame('p_sequence', i, cloth)
    ball = new_mesh('q_seq', ball_vertices + ball_pos.to_numpy().reshape(1, 3), ball_edges, ball_faces)
    set_object_frame('q_sequence', i, ball)
