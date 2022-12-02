from dataclasses import dataclass
from itertools import zip_longest

from hexbytes import HexBytes
from web3 import Web3

from .utils import ellipsize


@dataclass
class Component:
    address: HexBytes
    name: str = None

    def __str__(self):
        if self.name:
            return self.name
        return f"Component<{ellipsize(self.address.hex())}>"


class Role:
    def __init__(self, name, component: Component = None):
        self.name = name
        self.component = component
        self._role_hash = HexBytes(Web3.keccak(text=name).hex())

    @classmethod
    def from_hash(cls, hash: HexBytes, component: Component = None):
        ret = cls(name=f"UNKNOWN ROLE: {ellipsize(hash.hex())}", component=component)
        ret._role_hash = hash
        return ret

    @classmethod
    def default_admin(cls):
        ret = cls("DEFAULT_ADMIN_ROLE")
        ret._role_hash = HexBytes("0x" + "0" * 64)
        return ret

    @property
    def hash(self) -> HexBytes:
        if not getattr(self, "_hash", None):
            if self.component is None:
                self._hash = self._role_hash
            else:
                self._hash = HexBytes(
                    bytes(
                        [
                            cbyte ^ rbyte
                            for cbyte, rbyte in zip_longest(
                                self.component.address, self._role_hash, fillvalue=0
                            )
                        ]
                    )
                )
        return self._hash

    def __str__(self):
        ret = f"Role:{self.name}"
        if self.component:
            ret += f"@{self.component}"
        return ret

    def __repr__(self):
        return f"Role('{self.name}')"

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Role):
            return False
        return self.hash == __o.hash


class Registry:
    def __init__(self):
        self._map = {}
        self.add(Role.default_admin())

    def add_roles(self, roles):
        for role in roles:
            self.add(role)

    def add_components(self, components):
        for component in components:
            for role in list(self._map.values()):
                self.add(Role(role.name, component=component))

    def add(self, role):
        self._map[role.hash] = role

    def get(self, hash):
        if isinstance(hash, str):
            hash = HexBytes(hash)
        return self._map.get(hash, Role.from_hash(hash))


# def get_known_roles(known_role_names, known_components=None) -> list:
#     known_roles = [Role(name) for name in known_role_names]
#     known_roles.append(Role.default_admin())

#     if known_components:
#         for name in known_role_names:
#             known_roles += [Role(name, component=component) for component in known_components]

#     return known_roles


# def get_known_roles_map(known_role_names, known_components=None) -> dict:
#     known_roles = get_known_roles(known_role_names, known_components)
#     return {role.hash: role for role in known_roles}


_registry = None


def get_registry():
    global _registry
    if _registry is None:
        _registry = Registry()
    return _registry
