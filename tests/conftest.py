import pytest

class FakeArgs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class FakeEvent:
    def __init__(self, event_name, block_number, log_index, **kwargs):
        self.event = event_name
        self.blockNumber = block_number
        self.logIndex = log_index
        if "roleId" not in kwargs:
            kwargs["roleId"] = 0
        self.args = FakeArgs(**kwargs)

class FakeProvider:
    def __init__(self, events=None):
        self.events = events or []
        class Eth:
            def contract(self, **kwargs): return self
        class W3:
            eth = Eth()
        self.w3 = W3()

    def get_events(self, contract_wrapper, event_names):
        return [e for e in self.events if e.event in event_names]

@pytest.fixture
def fake_event_cls():
    return FakeEvent

@pytest.fixture
def fake_provider_cls():
    return FakeProvider
