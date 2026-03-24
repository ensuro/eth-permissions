import pytest
from hexbytes import HexBytes
from eth_utils import to_checksum_address
from eth_permissions.chaindata import AccessControlEventStream, AccessManagerEventStream
from eth_permissions.access_manager import AccessManager, Role
from unittest.mock import patch

@patch("eth_permissions.chaindata.ETHWrapper.connect")
def test_stream_snapshot_simple(mock_connect, fake_event_cls, fake_provider_cls):
    role_hash = HexBytes("0xbf372ca3ebecfe59ac256f17697941bbe63302aced610e8b0e3646f743c7beb2")
    member = to_checksum_address("0x1111111111111111111111111111111111111111")
    events = [
        fake_event_cls("RoleGranted", 1, 1, role=role_hash, account=member, sender=member),
        fake_event_cls("RoleRevoked", 2, 1, role=role_hash, account=member, sender=member),
        fake_event_cls("RoleGranted", 3, 1, role=role_hash, account=member, sender=member),
    ]
    provider = fake_provider_cls(events)
    stream = AccessControlEventStream("0xContract", provider=provider)
    snapshot = stream.snapshot
    assert len(snapshot) == 1
    assert snapshot[0]["role"].hash == role_hash

@patch("eth_permissions.chaindata.ETHWrapper.connect")
def test_stream_state_reconstruction_complex(mock_connect, fake_event_cls, fake_provider_cls):
    role_id = 0x55435dd261a4b9b3
    target_addr = to_checksum_address("0x8c5f6aEB655D687929a82c5d430Ec56abaDdc0c8")
    member_addr = to_checksum_address("0x2222222222222222222222222222222222222222")
    selector = HexBytes("0xabcdef12")
    events = [
        fake_event_cls("RoleLabel", 1, 1, roleId=role_id, label="MANAGER_ROLE"),
        fake_event_cls("RoleGranted", 1, 2, roleId=role_id, account=member_addr, delay=0),
        fake_event_cls("TargetFunctionRoleUpdated", 2, 1, roleId=role_id, target=target_addr, selector=selector),
        fake_event_cls("RoleAdminChanged", 3, 1, roleId=role_id, admin=0),
        fake_event_cls("TargetClosed", 4, 1, roleId=role_id, target=target_addr, closed=True),
    ]
    provider = fake_provider_cls(events)
    stream = AccessManagerEventStream("0xContract", provider=provider)
    with patch.object(AccessManagerEventStream, "_get_events", return_value=events):
        snapshot = stream.snapshot
    assert snapshot.roles[role_id].label == "MANAGER_ROLE"
    assert snapshot.get_target(target_addr).closed is True

@patch("eth_permissions.chaindata.ETHWrapper.connect")
def test_stream_comparison_engine(mock_connect, fake_event_cls, fake_provider_cls):
    role_id = 123
    events = [fake_event_cls("RoleLabel", 1, 1, roleId=role_id, label="OLD_LABEL")]
    provider = fake_provider_cls(events)
    stream = AccessManagerEventStream("0xContract", provider=provider)
    with patch.object(AccessManagerEventStream, "_get_events", return_value=events):
        target_am = AccessManager()
        target_am.label_role(Role(role_id), "NEW_LABEL")
        target_am.set_role_admin(Role(role_id), Role(10))
        differences = stream.compare(target_am)
    
    ops = {op.op for op in differences}
    assert "labelRole" in ops
    assert "setRoleAdmin" in ops

@patch("eth_permissions.chaindata.ETHWrapper.connect")
def test_stream_extra_logic(mock_connect, fake_event_cls, fake_provider_cls):
    role_id = 1
    member = to_checksum_address("0x1111111111111111111111111111111111111111")
    events = [fake_event_cls("RoleGranted", 1, 1, roleId=role_id, account=member, delay=0)]
    provider = fake_provider_cls(events)
    stream = AccessManagerEventStream("0xContract", provider=provider)
    with patch.object(AccessManagerEventStream, "_get_events", return_value=events):
        assert stream.snapshot_dict["roles"][role_id]["members"][0]["address"] == member
        
        # Test revocation detection
        target_am = AccessManager() # No members
        diffs = stream.compare(target_am)
        assert any(op.op == "revokeRole" for op in diffs)

@patch("eth_permissions.chaindata.ETHWrapper.connect")
def test_stream_revoke_warning(mock_connect, fake_event_cls, fake_provider_cls):
    role_hash = HexBytes("0x" + "1" * 64)
    events = [fake_event_cls("RoleRevoked", 1, 1, role=role_hash, account="0x0", sender="0x0")]
    stream = AccessControlEventStream("0x0", provider=fake_provider_cls(events))
    with pytest.warns(UserWarning, match="can't remove ungranted role"):
        _ = stream.snapshot
