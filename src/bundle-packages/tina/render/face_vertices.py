from . import *


@A.register
class FaceVertices(IField):
    '''
    Name: face_vertices
    Category: render
    Inputs: verts:f faces:f
    Output: faverts:f
    '''

    def __init__(self, verts, faces):
        assert isinstance(verts, IField)
        assert isinstance(faces, IField)

        self.verts = verts
        self.faces = faces
        self.meta = MEdit(FMeta(faces), vdims=None)

    @ti.func
    def _subscript(self, I):
        indices = self.faces[I]
        return tuple(ti.subscript(self.verts, i) for i in indices)
