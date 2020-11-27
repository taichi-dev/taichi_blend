# 8x8 blocked triangle rasterizer by @archibate <1931127624@qq.com>
#
# Many soft renderer tutorials uses a loop over each triangles.
# In this way when triangles are big, e.g. almost full of the screen,
# each iteration will have to fill a very large area of frame buffer.
#
# This might be okay for single-threaded CPU, but become extremely slow
# when applied to GPU since each GPU thread has to fill the entire screen.
# It also forces us to perform expensive atomics on the depth buffer.
# That explains why early Taichi THREE become so slow for a simple cube.
# So is there any solution for **rasterization on GPU compute shaders**?
#
# I searched the web and find nothing. Maybe waiting for my innovation?
# So here's my cool idea: **rasterize on a 8x8 smaller buffer first**,
# then launch another kernel over the 8x8 smaller buffer, and determine
# the detailed border of triangles in this pass. This also relief pixel
# shaders from atomics on depth buffers which harms performance.
#
# TODO: is it possible to have multiple layers for higher resoluion?

import taichi as ti
import numpy as np

def V(*xs):
  return ti.cast(ti.Vector(xs), float)

@ti.data_oriented
class Rasterizer:
  def __init__(self):
    self.N = 512  # image resolution
    self.E = 64   # num of triangles
    self.S = 8    # raster block size
    self.F = 32   # max overlaps per block

    self.tri = ti.Matrix.field(3, 3, float)  # vertex positions of each triangle
    self.trc = ti.Matrix.field(3, 3, float)  # vertex colors of each triangle
    self.img = ti.Vector.field(3, float)     # color frame buffer
    self.imd = ti.field(float)               # percise depth buffer
    self.tmp = ti.field(int)                 # raster block buffer
    self.tmd = ti.field(float)               # blocked depth buffer
    self.tml = ti.field(int)                 # num elements per block

    ti.root.dense(ti.ij, self.N).place(self.img)
    ti.root.dense(ti.ij, self.N).place(self.imd)
    ti.root.dense(ti.i, self.E).place(self.tri)
    ti.root.dense(ti.i, self.E).place(self.trc)
    ti.root.dense(ti.i, self.F).dense(ti.jk, self.N//self.S).place(self.tmp)
    ti.root.dense(ti.ij, self.N//self.S).place(self.tmd)
    ti.root.dense(ti.ij, self.N//self.S).place(self.tml)

  @ti.func
  def calcuvw(self, p, a, b, c):    # u, v, w is the distance to edge BC, CA, AB
    u = (p - c).cross((b - c).normalized())
    v = (p - a).cross((c - a).normalized())
    w = (p - b).cross((a - b).normalized())
    return V(u, v, w)

  @ti.func
  def calcmn(self, p, a, b, c):    # m, n is the barycenter coordinate to edge BC, CA
    r = 1 / (a - c).cross(b - c)
    m = (p - c).cross(b - c) * r
    n = (p - a).cross(c - a) * r
    return V(m, n)

  @ti.func
  def makexy2uvw(self, a, b, c):   # make a matrix that converts (x, y, 1) to (u, v, w)
    x = self.calcuvw(V(1, 0), a, b, c)
    y = self.calcuvw(V(0, 1), a, b, c)
    t = self.calcuvw(V(0, 0), a, b, c)
    return ti.Matrix.cols([x - t, y - t, t])

  @ti.func
  def makexy2mn(self, a, b, c):    # make a matrix that converts (x, y, 1) to (m, n)
    x = self.calcmn(V(1, 0), a, b, c)
    y = self.calcmn(V(0, 1), a, b, c)
    t = self.calcmn(V(0, 0), a, b, c)
    return ti.Matrix.cols([x - t, y - t, t])

  @ti.func
  def getverts(self, f):           # TODO: support slicing matrices in Taichi..
      return [ti.Vector([f[i, j] for j in range(f.m)]) for i in range(f.n)]

  @ti.kernel
  def raster(self):    # 8x8 rough rasterization
    for q in ti.grouped(self.tml):
      self.tml[q] = 0
      self.tmd[q] = 1e6
    # TODO: use brensel instead of barycent for raster
    for e in self.tri:
      aa, bb, cc = self.getverts(self.tri[e])
      a, b, c = V(aa.x, aa.y), V(bb.x, bb.y), V(cc.x, cc.y)
      xy2uvw = self.makexy2uvw(a, b, c)      # xy-to-distance matrix
      pmin = max(0, int(ti.floor(min(a, b, c) / self.S)))
      pmax = min(self.N//self.S, int(ti.ceil(max(a, b, c) / self.S) + 1))
      for q in ti.grouped(ti.ndrange(*zip(pmin, pmax))):
        p = q * self.S + self.S//2
        uvw = xy2uvw @ V(p.x, p.y, 1)
        if all(uvw > -self.S) or all(uvw < self.S):
          l = ti.atomic_add(self.tml[q], 1)
          self.tmp[l, q] = e  # append an element

  @ti.kernel
  def promote(self):   # percise rasterization
    for q in ti.grouped(self.tml):
      for l in range(self.tml[q]):
        e = self.tmp[l, q]
        aa, bb, cc = self.getverts(self.tri[e])
        a, b, c = V(aa.x, aa.y), V(bb.x, bb.y), V(cc.x, cc.y)
        xy2mn = self.makexy2mn(a, b, c)  # xy-to-barycenter matrix
        for s in ti.grouped(ti.ndrange(self.S, self.S)):
          p = q * self.S + s
          mn = xy2mn @ V(p.x, p.y, 1)    # convert to barycenter coordinate
          mno = V(mn.x, mn.y, 1 - mn.x - mn.y)
          if all(mno > 0) or all(mno < 0):
            depth = mno.x * aa.z + mno.y * bb.z + mno.z * cc.z
            if self.imd[p] > depth:
              # we don't need atomics here as only this thread is accessing [p]
              self.imd[p] = depth
              clra, clrb, clrc = self.getverts(self.trc[e])
              clr = mno.x * clra + mno.y * clrb + mno.z * clrc  # interpolate colors
              self.img[p] = clr

  def render(self):
    self.img.fill(0)
    self.imd.fill(1e6)
    self.raster()
    self.promote()

class Main(Rasterizer):
  def main(self):
    print('[Hint] Press SPACE to randomize triangles')
    gui = ti.GUI('raster', self.N, fast_gui=True)
    gui.fps_limit = None
    self.tri[0] = [(0, 0, 128), (512, 0, 128), (256, 512, 128)]
    self.trc[0] = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
    self.tri[1] = [(256, 0, 0), (512, 512, 128), (0, 512, 256)]
    self.trc[1] = [(0, 1, 1), (1, 0, 1), (1, 1, 0)]
    while gui.running and not gui.get_event(gui.ESCAPE):
      if gui.is_pressed(gui.SPACE):
        self.tri.from_numpy(np.random.rand(self.E, 3, 3).astype(np.float32) * self.N)
        self.trc.from_numpy(np.random.rand(self.E, 3, 3).astype(np.float32))
      self.render()
      gui.set_image(self.img)
      gui.show()

if __name__ == '__main__':
  ti.init(ti.gpu)
  Main().main()
