"""DEX method signatures, listings and build-result records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProtoKey:
    return_type: str
    parameters: tuple[str, ...]


@dataclass(frozen=True)
class MethodKey:
    owner: str
    name: str
    return_type: str
    parameters: tuple[str, ...]


@dataclass(frozen=True)
class FieldKey:
    owner: str
    name: str
    type_name: str


@dataclass(frozen=True)
class MethodListing:
    name: str
    registers: tuple[tuple[str, str, int], ...]
    code_units: int
    assembly: tuple[str, ...]


@dataclass(frozen=True)
class DexBuild:
    data: bytes
    register_map: tuple[tuple[str, str, int], ...]
    code_units: int
    assembly_listing: tuple[str, ...]
    methods: tuple[MethodListing, ...]
