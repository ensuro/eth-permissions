from hexbytes import HexBytes

from ens_permissions.roles import Component, Role, get_registry


def test_simple_role_hash():
    role = Role("LEVEL1_ROLE")
    assert role.hash == HexBytes("0xbf372ca3ebecfe59ac256f17697941bbe63302aced610e8b0e3646f743c7beb2")


def test_unknown_role():
    role = Role.from_hash(HexBytes("0x55435dd261a4b9b3364963f7738a7a662ad9c84396d64be3365284bb7f0a5041"))
    assert role.name == "UNKNOWN ROLE: 0x5543...5041"


def test_component():
    component = Component(HexBytes("0x8c5f6aEB655D687929a82c5d430Ec56abaDdc0c8"), "Test")
    assert str(component) == "Test"


def test_component_unknown_name():
    component = Component(HexBytes("0x8c5f6aEB655D687929a82c5d430Ec56abaDdc0c8"))
    assert str(component) == "Component<0x8c5f...c0c8>"


def test_component_role():
    component = Component(HexBytes("0x8c5f6aEB655D687929a82c5d430Ec56abaDdc0c8"), "Test")
    role = Role("POLICY_CREATOR_ROLE", component=component)
    assert role.hash == HexBytes("0x1ca1414ebf49990bc4f22652af37d8d535c4dc522f3557d79ede5d6b1c1c9ffb")
    assert str(role) == "Role:POLICY_CREATOR_ROLE@Test"


def test_registry():
    kr_names = ["GUARDIAN_ROLE", "LEVEL1_ROLE", "LEVEL2_ROLE", "LEVEL3_ROLE"]
    registry = get_registry()
    registry.add_roles([Role(name) for name in kr_names])

    assert (
        registry.get("0x0000000000000000000000000000000000000000000000000000000000000000")
        == Role.default_admin()
    )
    assert registry.get("0x55435dd261a4b9b3364963f7738a7a662ad9c84396d64be3365284bb7f0a5041") == Role(
        "GUARDIAN_ROLE"
    )
    assert registry.get("0x5ec196419322369c6bac572d883f4d990ae5ec82f7d93cdf89b85dbb05b63c27") == Role(
        "LEVEL3_ROLE"
    )
    assert registry.get("0xa82e22387fca439f316d78ca566f383218ab8ae1b3e830178c9c82cbd16749c0") == Role(
        "LEVEL2_ROLE"
    )
    assert registry.get("0xbf372ca3ebecfe59ac256f17697941bbe63302aced610e8b0e3646f743c7beb2") == Role(
        "LEVEL1_ROLE"
    )


def test_registry_with_components():
    kr_names = ["RESOLVER_ROLE", "PRICER_ROLE"]
    components = [Component(HexBytes("0x8c5f6aEB655D687929a82c5d430Ec56abaDdc0c8"), "TestRM")]

    registry = get_registry()
    registry.add_roles([Role(name) for name in kr_names])
    registry.add_components(components)

    assert (
        registry.get("0x0000000000000000000000000000000000000000000000000000000000000000")
        == Role.default_admin()
    )
    assert registry.get("0x92a19c77d2ea87c7f81d50c74403cb2f401780f3ad919571121efe2bdb427eb1") == Role(
        "RESOLVER_ROLE"
    )
    assert registry.get("0xc6823861ee2bb2198ce6b1fd6faf4c8f44f745bc804aca4a762f67e0d507fd8a") == Role(
        "PRICER_ROLE"
    )
    assert registry.get("0x1efef69cb7b7efbed1b57c9a070d0e45faca403bad919571121efe2bdb427eb1") == Role(
        "RESOLVER_ROLE", component=components[0]
    )
    assert registry.get("0x4add528a8b76da60a54e9da02ca189e5fe2a8574804aca4a762f67e0d507fd8a") == Role(
        "PRICER_ROLE", component=components[0]
    )
