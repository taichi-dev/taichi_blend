class Def:
    category = 'sampler'

    input_1 = ('lhs_sampler', 'sampler')
    input_2 = ('rhs_sampler', 'sampler')

    output_1 = ('result_sampler', 'sampler')

    option_1 = ('operation_type', 'enum')

    items_1 = ('add', 'sub', 'mul')
