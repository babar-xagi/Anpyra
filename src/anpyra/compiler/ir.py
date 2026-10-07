# Adapted from the user-provided PyAndroid experiments for Anpyra.
from __future__ import annotations

from dataclasses import dataclass

from ..components.button import ButtonDesign
from ..components.screen import Background


@dataclass(frozen=True)
class CallSuperOnCreate:
    pass


@dataclass(frozen=True)
class LoadConst:
    target: str
    type_name: str
    value: str | int | bool


@dataclass(frozen=True)
class IntBinary:
    target: str
    left_var: str
    operator: str
    right_var: str


@dataclass(frozen=True)
class CallFunction:
    target: str
    function_name: str
    args: tuple[str, ...]


@dataclass(frozen=True)
class ReturnValue:
    value_var: str


@dataclass(frozen=True)
class NewTextView:
    target: str


@dataclass(frozen=True)
class NewButton:
    target: str


@dataclass(frozen=True)
class NewLayout:
    target: str
    kind: str


@dataclass(frozen=True)
class AddLayoutChild:
    receiver: str
    view: str
    width: object = "match_parent"
    height: object = "wrap_content"
    weight: float = 0
    margin: tuple = (0, 0, 0, 0)


@dataclass(frozen=True)
class NewTextInput:
    target: str
    hint: str
    password: bool = False
    hint_color: int | None = None


@dataclass(frozen=True)
class BindChatSession:
    target: str
    key_input: str
    message_input: str
    transcript: str
    status: str
    send_button: str
    clear_button: str
    model: str


@dataclass(frozen=True)
class AppField:
    name: str
    type_name: str
    persist: bool = False


@dataclass(frozen=True)
class StoreAppField:
    name: str
    value_var: str


@dataclass(frozen=True)
class InitAppField:
    name: str
    value: str | int | bool


@dataclass(frozen=True)
class BindClick:
    button: str
    handler: str


@dataclass(frozen=True)
class CallEvent:
    handler: str


@dataclass(frozen=True)
class EventExpr:
    kind: str
    type_name: str
    value: object = None
    args: tuple = ()


@dataclass(frozen=True)
class EventAssign:
    kind: str
    name: str
    value: EventExpr


@dataclass(frozen=True)
class EventAction:
    receiver: str | None
    method: str
    args: tuple = ()


@dataclass(frozen=True)
class EventIf:
    condition: EventExpr
    then_ops: tuple
    else_ops: tuple


@dataclass(frozen=True)
class EventReturn:
    pass


@dataclass(frozen=True)
class EventHandler:
    name: str
    operations: tuple
    local_types: tuple


@dataclass(frozen=True)
class ApplyButtonDesign:
    receiver: str
    design: ButtonDesign
    icon_asset: str | None = None


@dataclass(frozen=True)
class SetButtonProperty:
    receiver: str
    property: str
    value: float | bool
    value_var: str | None = None


@dataclass(frozen=True)
class SetText:
    receiver: str
    value_var: str


@dataclass(frozen=True)
class SetContentView:
    view: str


@dataclass(frozen=True)
class NewScreen:
    target: str


@dataclass(frozen=True)
class SetScreenContent:
    receiver: str
    view: str


@dataclass(frozen=True)
class SetScrollContent:
    receiver: str
    view: str


@dataclass(frozen=True)
class ApplyScreenBackground:
    receiver: str
    background: Background
    image_asset: str | None = None


@dataclass(frozen=True)
class SetTextColor:
    receiver: str
    color: int


@dataclass(frozen=True)
class SetTextStyle:
    receiver: str
    property: str
    value: object
    font_asset: str | None = None


@dataclass(frozen=True)
class IfBool:
    condition_var: str
    then_ops: tuple["IROp", ...]
    else_ops: tuple["IROp", ...]


@dataclass(frozen=True)
class IfCompare:
    left_var: str
    operator: str
    right_var: str
    then_ops: tuple["IROp", ...]
    else_ops: tuple["IROp", ...]


IROp = (
    CallSuperOnCreate
    | LoadConst
    | IntBinary
    | CallFunction
    | ReturnValue
    | NewTextView
    | NewButton
    | NewLayout
    | AddLayoutChild
    | NewTextInput
    | BindChatSession
    | StoreAppField
    | InitAppField
    | BindClick
    | CallEvent
    | ApplyButtonDesign
    | SetButtonProperty
    | SetText
    | SetContentView
    | NewScreen
    | SetScreenContent
    | SetScrollContent
    | ApplyScreenBackground
    | SetTextColor
    | SetTextStyle
    | IfBool
    | IfCompare
)


@dataclass(frozen=True)
class FunctionIR:
    name: str
    parameters: tuple[tuple[str, str], ...]
    return_type: str
    operations: tuple[IROp, ...]
    symbol_types: tuple[tuple[str, str], ...]

    def pretty(self) -> str:
        params = ", ".join(f"{n}: {t}" for n, t in self.parameters)
        lines = [
            f"FunctionIR {self.name}({params}) -> {self.return_type}",
            "  symbols:",
        ]
        for name, typ in self.symbol_types:
            lines.append(f"    {name}: {typ}")
        lines.append("  operations:")
        for op in self.operations:
            lines.append(f"    {op!r}")
        return "\n".join(lines)


@dataclass(frozen=True)
class AppIR:
    package: str
    class_name: str
    label: str
    functions: tuple[FunctionIR, ...]
    operations: tuple[IROp, ...]
    symbol_types: tuple[tuple[str, str], ...]
    app_fields: tuple[AppField, ...] = ()
    handlers: tuple[EventHandler, ...] = ()

    @property
    def qualified_activity(self) -> str:
        return f"{self.package}.{self.class_name}"

    @property
    def class_descriptor(self) -> str:
        return "L" + self.qualified_activity.replace(".", "/") + ";"

    def pretty(self) -> str:
        lines = [f"AppIR(package={self.package!r}, class={self.class_name!r})"]
        if self.app_fields or self.handlers:
            lines.append("  Activity fields:")
            lines.extend(f"    {field!r}" for field in self.app_fields)
            lines.append("  event handlers:")
            lines.extend(f"    {handler!r}" for handler in self.handlers)
        lines.append("  functions:")
        for fn in self.functions:
            for line in fn.pretty().splitlines():
                lines.append("    " + line)
        lines.append("  on_create symbols:")
        for name, typ in self.symbol_types:
            lines.append(f"    {name}: {typ}")
        lines.append("  on_create operations:")

        def walk(ops, indent):
            pad = " " * indent
            for op in ops:
                if isinstance(op, IfBool):
                    lines.append(f"{pad}IfBool(condition_var={op.condition_var!r})")
                    lines.append(f"{pad}  then:")
                    walk(op.then_ops, indent + 4)
                    lines.append(f"{pad}  else:")
                    walk(op.else_ops, indent + 4)
                elif isinstance(op, IfCompare):
                    lines.append(
                        f"{pad}IfCompare(left_var={op.left_var!r}, operator={op.operator!r}, right_var={op.right_var!r})"
                    )
                    lines.append(f"{pad}  then:")
                    walk(op.then_ops, indent + 4)
                    lines.append(f"{pad}  else:")
                    walk(op.else_ops, indent + 4)
                else:
                    lines.append(f"{pad}{op!r}")

        walk(self.operations, 4)
        return "\n".join(lines)
