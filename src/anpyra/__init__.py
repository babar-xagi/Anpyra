"""Anpyra: Python source to native Android bytecode."""

from .api import Activity, TextView
from .build import BuildResult, build_apk, build_project
from .compiler.frontend import CompileError, compile_file, compile_source
from .components import (
    Background,
    Border,
    Button,
    ButtonState,
    ButtonStyle,
    ChatSession,
    Column,
    Font,
    Gradient,
    Icon,
    Image,
    Row,
    Screen,
    ScrollView,
    Shadow,
    StyleError,
    TextInput,
    TextStyle,
)
from .config import AppConfig, ConfigError, Project, load_project

__version__ = "0.1.3"
__all__ = [
    "Column",
    "Row",
    "ScrollView",
    "TextInput",
    "ChatSession",
    "Button",
    "ButtonStyle",
    "ButtonState",
    "Border",
    "Icon",
    "Font",
    "Shadow",
    "TextStyle",
    "Screen",
    "Background",
    "Image",
    "Gradient",
    "StyleError",
    "Activity",
    "TextView",
    "AppConfig",
    "Project",
    "ConfigError",
    "CompileError",
    "BuildResult",
    "load_project",
    "build_project",
    "build_apk",
    "compile_source",
    "compile_file",
]
