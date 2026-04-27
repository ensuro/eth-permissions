class FakeEvent:
    def __init__(self, event_name, block_number, log_index, **kwargs):
        self.event = event_name
        self.blockNumber = block_number
        self.logIndex = log_index
        if "roleId" not in kwargs:
            kwargs["roleId"] = 0
        self.args = type("FakeArgs", (), kwargs)()


class FakeProvider:
    def __init__(self, events=None):
        self.events = events or []
        self.w3 = FakeW3()

    def get_events(self, contract_wrapper, event_names):
        return [e for e in self.events if e.event in event_names]


class FakeW3:
    class Eth:
        @staticmethod
        def contract(**kwargs):
            return None

    eth = Eth()
