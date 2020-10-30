class Def:
    category = 'scatter'

    input_1 = ('particle_attribute_sampler', 'sampler')
    input_2 = ('grid_field_storage', 'field')

    output_1 = ('grid_field_storage', 'field')

    option_1 = ('stencil_type', 'enum')

    items_1 = ('b-spline', )
