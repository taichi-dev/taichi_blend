import bpy


option_types = {
    'int': bpy.props.IntProperty,
    'float': bpy.props.FloatProperty,
    'bool': bpy.props.BoolProperty,
    'str': bpy.props.StringProperty,
    'enum': bpy.props.EnumProperty,
    'vec_int_2': bpy.props.IntVectorProperty,
    'vec_int_3': bpy.props.IntVectorProperty,
    'vec_float_2': bpy.props.FloatVectorProperty,
    'vec_float_3': bpy.props.FloatVectorProperty,
    'search_object': bpy.props.StringProperty,
}


def get_words(string):
    words = []
    for word in string.split('_'):
        words.append(word.capitalize())
    return words


def register_socket(socket_system_name, socket_def, node_system):
    pass


def register_node(node_system_name, node_def, node_system):
    node_name_words = get_words(node_system_name)
    node_name = ' '.join(node_name_words)
    node_id = node_system.cap_prefix + '{}Node'.format(''.join(node_name_words))
    attributes = {}
    attributes['ns_wrapped'] = getattr(node_def, 'wrapped', None)
    attributes['bl_idname'] = node_system.prefix + '_{}_node'.format(node_system_name)
    attributes['bl_label'] = node_name
    inputs = []
    outputs = []
    options = []
    option_items = {}

    for attribute_name in dir(node_def):
        if attribute_name.startswith('_'):
            continue
        if attribute_name.startswith('input_'):
            input_def = getattr(node_def, attribute_name)
            inputs.append(input_def)
        if attribute_name.startswith('output_'):
            output_def = getattr(node_def, attribute_name)
            outputs.append(output_def)
        if attribute_name.startswith('option_'):
            option_def = getattr(node_def, attribute_name)
            option_id = attribute_name[len('option_') : ]
            options.append((option_def, option_id))

    attributes['ns_options'] = options

    def create_sockets(sockets_def, sockets):
        for system_name, socket_type in sockets_def:
            socket_id = node_system.prefix + '_{}_socket'.format(socket_type)
            name_words = get_words(system_name)
            name = ' '.join(name_words)
            socket = sockets.new(socket_id, name)
            socket.text = name
            socket.hide_value = True

    def init_node(self, context):
        create_sockets(inputs, self.inputs)
        create_sockets(outputs, self.outputs)
        self.width = 200

    attributes['init'] = init_node
    props = {}
    props_names = {}
    props_types = {}
    for (option_system_name, option_type), option_id in options:
        name_words = get_words(option_system_name)
        option_name = ' '.join(name_words)
        prop_class = option_types[option_type]
        if option_type in ['int', 'float', 'bool', 'str']:
            prop = prop_class(name=option_name)
        elif option_type.startswith('vec_'):
            size = int(option_type[-1])
            prop = prop_class(name=option_name, size=size)
        elif option_type == 'enum':
            items_def = getattr(node_def, 'items_' + option_id)
            option_items[option_id] = items_def
            items = []
            for item in items_def:
                item_id = item.upper()
                item_name = item.capitalize()
                item_description = ''
                items.append((item_id, item_name, item_description))
            prop = prop_class(name=option_name, items=items)
        elif option_type == 'search_object':
            prop = prop_class(name=option_name)
        else:
            assert False, option_type
        props[option_system_name] = prop
        props_types[option_system_name] = option_type
        props_names[option_system_name] = option_name

    attributes['ns_option_items'] = option_items

    def draw_buttons(self, context, layout):
        for attribute, prop in props.items():
            row = layout.row()
            row.label(text=props_names[attribute])
            prop_type = props_types[attribute]
            if prop_type == 'search_object':
                row.prop_search(self, attribute, bpy.data, 'objects', text='')
            else:
                row.prop(self, attribute, text='')

    attributes['draw_buttons'] = draw_buttons
    node_class = type(node_id, (node_system.base_node, ), attributes)
    node_class.__annotations__ = props
    bpy.utils.register_class(node_class)
    node_system.nodes.append(node_class)
    if not node_system.categories_def.get(node_def.category, None):
        node_system.categories_def[node_def.category] = []
    node_system.categories_def[node_def.category].append(attributes['bl_idname'])


def get_node_table(node_group):
    def get_table(node_group):
        nodes = []
        for key, node in node_group.nodes.items():
            inputs = []
            options = []
            for (opt_name, opt_type), opt_id in node.ns_options:
                if opt_name in node:
                    item = node[opt_name]
                else:
                    if opt_type == 'str' or opt_type.startswith('search_'):
                        item = ''
                    elif opt_type.startswith('vec_'):
                        item = (0,) * int(opt_type.split('_')[-1])
                    else:
                        item = 0
                if opt_type == 'enum':
                    item = node.ns_option_items[opt_id][item]
                elif opt_type.startswith('vec_'):
                    item = tuple(item[i] for i in range(len(item)))
                options.append(item)
            for name, socket in node.inputs.items():
                link_node = None
                link_socket = 0
                if len(socket.links):
                    link_node = socket.links[0].from_node
                    link_socket = socket.links[0].from_socket
                    link_socket = list(link_node.outputs).index(link_socket)
                    link_node = node_group.nodes.keys().index(link_node.name)
                inputs.append((link_node, link_socket))
            ninfo = node.ns_wrapped, node.name, tuple(inputs), tuple(options)
            nodes.append(ninfo)
        return nodes


    def construct_table(nodes):
        visited = [None for i in nodes]
        entered = [False for i in nodes]

        def dfs(i):
            if i is None:
                return None, [None]

            assert not entered[i], i
            if visited[i] is not None:
                return visited[i]

            entered[i] = True
            cons, name, inputs, options = nodes[i]
            args = []
            for j, k in inputs:
                ret, rets = dfs(j)
                args.append(rets[k])

            res = cons(tuple(args), options)
            visited[i] = res
            entered[i] = False
            return res

        for i in range(len(nodes)):
            dfs(i)

        table = {}
        for i, ninfo in enumerate(nodes):
            name = ninfo[1]
            ret, rets = visited[i]
            table[name] = ret
        return table

    return construct_table(get_table(node_group))
