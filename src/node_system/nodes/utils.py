import bpy

from . import base


option_types = {
    'int': bpy.props.IntProperty,
    'enum': bpy.props.EnumProperty,
    'vec_int_2': bpy.props.IntVectorProperty,
    'search_object': bpy.props.StringProperty
}


def get_words(string):
    words = []
    for word in string.split('_'):
        words.append(word.capitalize())
    return words


def register_node(node_system_name, node_def, node_system):
    node_name_words = get_words(node_system_name)
    node_name = ' '.join(node_name_words)
    node_id = 'TaichiBlend{}Node'.format(''.join(node_name_words))
    attributes = {}
    attributes['bl_idname'] = 'taichi_blend_{}_node'.format(node_system_name)
    attributes['bl_label'] = node_name
    inputs = []
    outputs = []
    options = []

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

    def create_sockets(sockets_def, sockets):
        for system_name, socket_type in sockets_def:
            socket_id = 'taichi_blend_{}_socket'.format(socket_type)
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
        if option_type == 'int':
            prop = prop_class(name=option_name)
        elif option_type.startswith('vec'):
            size = int(option_type[-1])
            prop = prop_class(name=option_name, size=size)
        elif option_type == 'enum':
            items_def = getattr(node_def, 'items_' + option_id)
            items = []
            for item in items_def:
                item_id = item.upper()
                item_name = item.capitalize()
                item_description = ''
                items.append((item_id, item_name, item_description))
            prop = prop_class(name=option_name, items=items)
        elif option_type == 'search_object':
            prop = prop_class(name=option_name)
        props[option_system_name] = prop
        props_types[option_system_name] = option_type
        props_names[option_system_name] = option_name

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
    node_class = type(node_id, (base.TaichiBlendBaseNode, ), attributes)
    node_class.__annotations__ = props
    bpy.utils.register_class(node_class)
    node_system.nodes.append(node_class)
    if not node_system.categories_def.get(node_def.category, None):
        node_system.categories_def[node_def.category] = []
    node_system.categories_def[node_def.category].append(attributes['bl_idname'])
