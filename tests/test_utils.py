import pytest
from collections import defaultdict
from datetime import timedelta
from eth_permissions.utils import ellipsize, ExplorerAddress, safe_serializer

def test_ellipsize_valid():
    assert ellipsize("0x4d68Cf31d222270b18E406AFd6A42719a62a0785") == "0x4d68...0785"

def test_ellipsize_invalid():
    with pytest.raises(ValueError, match="Expected a hex string beggining with 0x"):
        ellipsize("not-a-hex")

def test_explorer_address():
    addr = "0x1234567890123456789012345678901234567890"
    assert ExplorerAddress.get(addr) == f"https://polygonscan.com/address/{addr}"

class MockWithAsDict:
    def as_dict(self):
        return {"foo": "bar"}

def test_safe_serializer():
    assert safe_serializer(MockWithAsDict()) == {"foo": "bar"}

    result = safe_serializer({1, 2, 3})
    assert isinstance(result, list)
    assert len(result) == 3
    assert all(item in result for item in {1, 2, 3})

    # isinstance(obj, defaultdict)
    dd = defaultdict(set)
    dd["role1"].add("member1")
    dd["role1"].add("member2")
    result = safe_serializer(dd)
    assert result == {"role1": ["member1", "member2"]} or result == {"role1": ["member2", "member1"]}

    # isinstance(obj, timedelta)
    td = timedelta(hours=1, minutes=30)
    assert safe_serializer(td) == 5400

    # raise TypeError
    with pytest.raises(TypeError, match="is not serializable"):
        safe_serializer(object())
