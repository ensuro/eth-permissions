import pytest
from datetime import timedelta
from eth_utils import to_checksum_address
from eth_permissions.access_manager import AccessManager, Role, Target, RoleMember

def test_access_manager_basic_operations():
    am = AccessManager()
    role_id = 1
    addr = to_checksum_address("0x1111111111111111111111111111111111111111")
    am.label_role(Role(role_id), "POOL_ROLE")
    am.grant_role(Role(role_id), addr, execution_delay=timedelta(seconds=60))
    assert am.roles[role_id].label == "POOL_ROLE"
    assert len(am.get_role_members(Role(role_id))) == 1

def test_access_manager_hierarchy():
    am = AccessManager()
    am.set_role_admin(Role(1), Role(0))
    am.set_role_guardian(Role(1), Role(2))
    assert am.get_role_admin(Role(1)).id == 0
    assert am.get_role_guardian(Role(1)).id == 2

def test_access_manager_time_and_delay_integrity():
    am = AccessManager()
    role_id = 1
    target_addr = to_checksum_address("0x4444444444444444444444444444444444444444")
    member_addr = to_checksum_address("0x5555555555555555555555555555555555555555")
    exec_delay = timedelta(minutes=30)
    am.grant_role(Role(role_id), member_addr, execution_delay=exec_delay)
    am.set_target_admin_delay(Target(target_addr), timedelta(hours=12))
    member = next(m for m in am.get_role_members(Role(role_id)) if m.address == member_addr)
    assert member.execution_delay == exec_delay
    assert am.get_target(target_addr).admin_delay == timedelta(hours=12)

def test_access_manager_dataclass_serialization():
    role = Role(id=0x123, label="TEST", grant_delay=timedelta(hours=1))
    assert role.as_dict()["id"] == 0x123
    new_role = Role.from_dict(role.as_dict())
    assert new_role == role
    
    target_addr = to_checksum_address("0xfe84d0393127919301b752824dd96d291d0e0841")
    target = Target(address=target_addr, closed=True)
    assert target.as_dict()["address"] == target_addr

def test_access_manager_equality_and_hashes():
    role = Role(1)
    assert role != "not a role"
    target = Target(to_checksum_address("0x1111111111111111111111111111111111111111"))
    assert target != "not a target"
    assert RoleMember(target.address) != "not a member"

def test_access_manager_misc_queries():
    am = AccessManager()
    role = Role(1)
    target = Target(to_checksum_address("0x1111111111111111111111111111111111111111"))
    am.set_target_function_role(target, {"0xabcdef12"}, role)
    assert am.get_role(1).id == 1
    assert am.get_role_guardian(role) == am.ADMIN_ROLE
    assert "0xabcdef12" in am.get_all_target_selectors(target)
    
    role_targets = am.get_all_role_targets(role)
    assert target in role_targets
