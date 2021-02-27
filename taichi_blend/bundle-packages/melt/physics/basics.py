from . import *


@A.register
def LaplacianBlur(x):
    '''
    Name: laplacian_blur
    Category: stencil
    Inputs: source:f
    Output: result:f
    '''
    return A.mix_value(x, A.field_laplacian(A.clamp_sample(x)), 1, 1)


@A.register
def LaplacianStep(pos, vel, kappa):
    '''
    Name: laplacian_step
    Category: physics
    Inputs: pos:f vel:f kappa:c
    Output: vel:f
    '''
    return A.mix_value(vel, A.field_laplacian(A.boundary_sample(pos)), 1, kappa)


@A.register
def AdvectPosition(pos, vel, dt):
    '''
    Name: advect_position
    Category: physics
    Inputs: pos:f vel:f dt:c
    Output: pos:f
    '''
    return A.mix_value(pos, vel, 1, dt)
