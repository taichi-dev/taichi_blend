from . import *


@A.register
def FMeta(field):
    '''
    Name: get_meta
    Category: meta
    Inputs: field:f
    Output: meta:m
    '''
    assert isinstance(field, IField)

    return field.meta


Def = FMeta
