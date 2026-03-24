import pytest
from hexbytes import HexBytes
from eth_permissions.access_control import Component, Role, Registry, get_registry

def test_registry_with_components():
    kr_names = ["RESOLVER_ROLE", "PRICER_ROLE"]
    components = [Component(HexBytes("0x8c5f6aEB655D687929a82c5d430Ec56abaDdc0c8"), "TestRM")]
    registry = get_registry()
    registry.add_roles([Role(name) for name in kr_names])
    registry.add_components(components)
    
    res_role_hash = "0x1efef69cb7b7efbed1b57c9a070d0e45faca403bad919571121efe2bdb427eb1"
    assert registry.get(res_role_hash) == Role("RESOLVER_ROLE", component=components[0])

def test_component_to_json():
    addr = "0x8c5f6aEB655D687929a82c5d430Ec56abaDdc0c8"
    comp = Component(HexBytes(addr), "Test")
    assert comp.to_json() == {"address": addr.lower(), "name": "Test"}

def test_role_to_json():
    role = Role("LEVEL1_ROLE")
    json_data = role.to_json()
    assert json_data["name"] == "LEVEL1_ROLE"
    assert json_data["component"] is None

def test_registry_tail_matching():
    registry = Registry()
    base_role = Role("BASE_ROLE")
    registry.add(base_role)
    base_hash = base_role.hash
    tail = base_hash[-12:]
    fake_hash = HexBytes(bytes([0]*20) + tail)
    recovered = registry.get(fake_hash)
    assert recovered.name == "BASE_ROLE"
    assert recovered.component is not None
    assert recovered.component.address == HexBytes(base_hash.hex()[:-24])

def test_role_repr():
    comp = Component(HexBytes("0x1234567890123456789012345678901234567890"), "Comp")
    role = Role("TEST", component=comp)
    assert repr(role) == "Role('TEST')@Comp"
    assert repr(Role("TEST")) == "Role('TEST')"

def test_registry_get_unknown():
    registry = Registry()
    unknown_hash = HexBytes("0x" + "f" * 64)
    recovered = registry.get(unknown_hash)
    assert recovered.name.startswith("UNKNOWN ROLE:")

def test_role_equality():
    role1 = Role("LEVEL1_ROLE")
    role2 = Role("LEVEL1_ROLE")
    assert role1 == role2
    assert role1 != object()
    assert hash(role1) == hash(role2)
