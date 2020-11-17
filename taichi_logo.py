import taichi as ti

n = 32
m = 8
img = ti.Vector.field(4, float, shape=(n, n))


white = ti.Vector(ti.hex_to_rgb(0xe3e3e3) + (1,))
black = ti.Vector(ti.hex_to_rgb(0x000000) + (0,))


@ti.func
def taichi_logo(pos, scale=1 / 1.11):
    p = (pos - 0.5) / scale + 0.5
    ret = -1
    if not (p - 0.50).norm_sqr() <= 0.555**2:
        if ret == -1:
            ret = 0
    if not (p - 0.50).norm_sqr() <= 0.48**2:
        if ret == -1:
            ret = 1
    if (p - ti.Vector([0.50, 0.25])).norm_sqr() <= 0.08**2:
        if ret == -1:
            ret = 1
    if (p - ti.Vector([0.50, 0.75])).norm_sqr() <= 0.08**2:
        if ret == -1:
            ret = 0
    if (p - ti.Vector([0.50, 0.25])).norm_sqr() <= 0.25**2:
        if ret == -1:
            ret = 0
    if (p - ti.Vector([0.50, 0.75])).norm_sqr() <= 0.25**2:
        if ret == -1:
            ret = 1
    if p[0] < 0.5:
        if ret == -1:
            ret = 1
    else:
        if ret == -1:
            ret = 0
    return 1 - ret


@ti.kernel
def paint():
    for i, j in img:
        cnt = 0
        for k, l in ti.ndrange(m, m):
            cnt += taichi_logo(ti.Vector([i + k / m, j + l / m]) / n)
        val = cnt / m**2
        ret = val * black + (1 - val) * white
        img[i, j] += ret


paint()
ti.imshow(img)
ti.imwrite(img, 'src/node_system/taichi_logo.png')
