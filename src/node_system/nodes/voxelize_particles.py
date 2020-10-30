class Def:
    category = 'scatter'

    input_1 = ('particle position sampler', 'sampler')
    input_2 = ('weight per particle scalar', 'value')

    output_1 = ('voxel_field_storage', 'field')

    option_1 = ('stencil_type', 'enum')

    items_1 = ('gaussian', )
