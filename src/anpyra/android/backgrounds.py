"""Native background layers, image loading/fit and gradient bytecode emission."""

import struct

from ..compiler.ir import ApplyScreenBackground, IfBool, IfCompare, NewScreen, SetTextColor
from ..components.screen import alpha_byte, parse_color
from .dalvik import OP_INVOKE_DIRECT, OP_INVOKE_STATIC, OP_INVOKE_VIRTUAL, emit_const, emit_invoke
from .dex_types import FieldKey, MethodKey

FRAME = "Landroid/widget/FrameLayout;"
VIEW = "Landroid/view/View;"
CONTEXT = "Landroid/content/Context;"
DRAWABLE = "Landroid/graphics/drawable/Drawable;"
COLOR = "Landroid/graphics/drawable/ColorDrawable;"
GRADIENT = "Landroid/graphics/drawable/GradientDrawable;"
ORIENTATION = "Landroid/graphics/drawable/GradientDrawable$Orientation;"
LAYER = "Landroid/graphics/drawable/LayerDrawable;"
IMAGE_VIEW = "Landroid/widget/ImageView;"
SCALE_TYPE = "Landroid/widget/ImageView$ScaleType;"
FRAME_PARAMS = "Landroid/widget/FrameLayout$LayoutParams;"
LAYOUT_PARAMS = "Landroid/view/ViewGroup$LayoutParams;"
ASSETS = "Landroid/content/res/AssetManager;"
STREAM = "Ljava/io/InputStream;"
BITMAP = "Landroid/graphics/Bitmap;"
BITMAP_FACTORY = "Landroid/graphics/BitmapFactory;"
STRING = "Ljava/lang/String;"
VERSION = "Landroid/os/Build$VERSION;"
SDK_FIELD = FieldKey(VERSION, "SDK_INT", "I")
ORIENTATIONS = {
    "top_bottom": "TOP_BOTTOM",
    "bottom_top": "BOTTOM_TOP",
    "left_right": "LEFT_RIGHT",
    "right_left": "RIGHT_LEFT",
    "tl_br": "TL_BR",
    "tr_bl": "TR_BL",
    "bl_tr": "BL_TR",
    "br_tl": "BR_TL",
}
SCALES = {
    "cover": "CENTER_CROP",
    "contain": "FIT_CENTER",
    "fill": "FIT_XY",
    "center": "CENTER",
    "inside": "CENTER_INSIDE",
    "fit_start": "FIT_START",
    "fit_end": "FIT_END",
}


def background_methods() -> dict[str, MethodKey]:
    return {
        "color_constructor": MethodKey(COLOR, "<init>", "V", ("I",)),
        "gradient_constructor": MethodKey(GRADIENT, "<init>", "V", (ORIENTATION, "[I")),
        "gradient_type": MethodKey(GRADIENT, "setGradientType", "V", ("I",)),
        "gradient_center": MethodKey(GRADIENT, "setGradientCenter", "V", ("F", "F")),
        "gradient_radius": MethodKey(GRADIENT, "setGradientRadius", "V", ("F",)),
        "layer_constructor": MethodKey(LAYER, "<init>", "V", ("[" + DRAWABLE,)),
        "drawable_alpha": MethodKey(DRAWABLE, "setAlpha", "V", ("I",)),
        "view_background": MethodKey(VIEW, "setBackground", "V", (DRAWABLE,)),
        "view_alpha": MethodKey(VIEW, "setAlpha", "V", ("F",)),
        "context_assets": MethodKey(CONTEXT, "getAssets", ASSETS, ()),
        "asset_open": MethodKey(ASSETS, "open", STREAM, (STRING,)),
        "bitmap_decode": MethodKey(BITMAP_FACTORY, "decodeStream", BITMAP, (STREAM,)),
        "stream_close": MethodKey(STREAM, "close", "V", ()),
        "image_constructor": MethodKey(IMAGE_VIEW, "<init>", "V", (CONTEXT,)),
        "image_bitmap": MethodKey(IMAGE_VIEW, "setImageBitmap", "V", (BITMAP,)),
        "image_scale": MethodKey(IMAGE_VIEW, "setScaleType", "V", (SCALE_TYPE,)),
        "image_alpha": MethodKey(IMAGE_VIEW, "setImageAlpha", "V", ("I",)),
        "layout_constructor": MethodKey(FRAME_PARAMS, "<init>", "V", ("I", "I")),
        "frame_add_image": MethodKey(FRAME, "addView", "V", (VIEW, "I", LAYOUT_PARAMS)),
    }


def background_fields(operations) -> tuple[FieldKey, ...]:
    fields = set()
    for op in operations:
        if isinstance(op, (NewScreen, SetTextColor)):
            fields.add(SDK_FIELD)
        if isinstance(op, (IfBool, IfCompare)):
            fields.update(background_fields((*op.then_ops, *op.else_ops)))
        elif isinstance(op, ApplyScreenBackground):
            if op.background.gradient is not None:
                fields.add(
                    FieldKey(
                        ORIENTATION, ORIENTATIONS[op.background.gradient.direction], ORIENTATION
                    )
                )
            if op.background.image is not None:
                fields.add(FieldKey(SCALE_TYPE, SCALES[op.background.image.fit], SCALE_TYPE))
    return tuple(fields)


def emit_background(
    op,
    assembler,
    registers,
    this_register,
    type_indexes,
    string_indexes,
    method_indexes,
    field_indexes,
    methods,
    scratch,
    argument_base,
):
    background = op.background
    a, b, c, value, index, extra, background_view = scratch

    def invoke(name, args, opcode=OP_INVOKE_VIRTUAL):
        key = methods[name]
        types = key.parameters if opcode == OP_INVOKE_STATIC else (key.owner, *key.parameters)
        emit_invoke(
            assembler,
            opcode,
            method_indexes[key],
            args,
            types,
            argument_base,
            f"{key.owner}->{key.name}",
        )

    def create(register, descriptor):
        assembler.emit("new_instance", register, type_indexes[descriptor], descriptor, size=2)

    def floating(register, number):
        emit_const(assembler, register, struct.unpack("<I", struct.pack("<f", number))[0])

    if background.color is None and background.gradient is None and background.image is None:
        return
    create(background_view, FRAME)
    invoke("frame_constructor", (background_view, this_register), OP_INVOKE_DIRECT)
    floating(value, background.effective_opacity)
    invoke("view_alpha", (background_view, value))

    layers = []
    if background.color is not None:
        create(a, COLOR)
        emit_const(assembler, value, parse_color(background.color))
        invoke("color_constructor", (a, value), OP_INVOKE_DIRECT)
        layers.append(a)
    if background.gradient is not None:
        gradient = background.gradient
        emit_const(assembler, 1, len(gradient.colors))
        assembler.emit("new_array", 0, 1, type_indexes["[I"], "[I", size=2)
        for position, color in enumerate(gradient.colors):
            emit_const(assembler, value, parse_color(color))
            emit_const(assembler, index, position)
            assembler.emit("aput", value, 0, index, size=2)
        field = FieldKey(ORIENTATION, ORIENTATIONS[gradient.direction], ORIENTATION)
        assembler.emit("sget_object", c, field_indexes[field], field.name, size=2)
        create(b, GRADIENT)
        invoke("gradient_constructor", (b, c, 0), OP_INVOKE_DIRECT)
        if gradient.kind != "linear":
            emit_const(assembler, value, {"radial": 1, "sweep": 2}[gradient.kind])
            invoke("gradient_type", (b, value))
            floating(value, gradient.center[0])
            floating(index, gradient.center[1])
            invoke("gradient_center", (b, value, index))
            if gradient.kind == "radial":
                floating(value, gradient.radius)
                invoke("gradient_radius", (b, value))
        layers.append(b)
    if layers:
        emit_const(assembler, 1, len(layers))
        assembler.emit("new_array", 0, 1, type_indexes["[" + DRAWABLE], "[" + DRAWABLE, size=2)
        for position, layer in enumerate(layers):
            emit_const(assembler, index, position)
            assembler.emit("aput_object", layer, 0, index, size=2)
        create(c, LAYER)
        invoke("layer_constructor", (c, 0), OP_INVOKE_DIRECT)
        invoke("view_background", (background_view, c))
    if background.image is not None:
        if op.image_asset is None:
            raise ValueError(
                "resolve screen image assets before DEX generation; use anpyra check/build"
            )
        image = background.image
        invoke("context_assets", (this_register,))
        assembler.emit("move_result_object", a, size=1)
        assembler.emit(
            "const_string", value, string_indexes[op.image_asset], op.image_asset, size=2
        )
        invoke("asset_open", (a, value))
        assembler.emit("move_result_object", index, size=1)
        invoke("bitmap_decode", (index,), OP_INVOKE_STATIC)
        assembler.emit("move_result_object", extra, size=1)
        invoke("stream_close", (index,))
        create(a, IMAGE_VIEW)
        invoke("image_constructor", (a, this_register), OP_INVOKE_DIRECT)
        invoke("image_bitmap", (a, extra))
        field = FieldKey(SCALE_TYPE, SCALES[image.fit], SCALE_TYPE)
        assembler.emit("sget_object", b, field_indexes[field], field.name, size=2)
        invoke("image_scale", (a, b))
        emit_const(assembler, value, alpha_byte(image.opacity))
        invoke("image_alpha", (a, value))
        create(extra, FRAME_PARAMS)
        emit_const(assembler, value, -1)
        invoke("layout_constructor", (extra, value, value), OP_INVOKE_DIRECT)
        emit_const(assembler, value, 0)
        invoke("frame_add_image", (background_view, a, value, extra))
    create(extra, FRAME_PARAMS)
    emit_const(assembler, value, -1)
    invoke("layout_constructor", (extra, value, value), OP_INVOKE_DIRECT)
    emit_const(assembler, value, 0)
    invoke("frame_add_image", (registers[op.receiver], background_view, value, extra))
