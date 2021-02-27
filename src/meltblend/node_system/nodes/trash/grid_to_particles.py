class Def:
    category = 'gather'

    input_1 = ('grid sampler', 'sampler')
    input_2 = ('particle_attribute_field_storage', 'field')

    output_1 = ('grid_field_storage', 'field')

    option_1 = ('stencil_type', 'enum')

    items_1 = ('b-spline', )
