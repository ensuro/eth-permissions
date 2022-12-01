import re


def ellipsize(hexa):
    """Ellipsize a hex string

    >>> ellipsize("0x4d68Cf31d222270b18E406AFd6A42719a62a0785") -> "0x4d68...0785"
    """
    match = re.match(r"(0x[0-9a-fA-F]{4})([0-9a-fA-F]*?)([0-9a-fA-F]{4})$", hexa)
    if not match:
        raise ValueError(f"Expected a hex string beggining with 0x, got {hexa}")
    return match.expand(r"\1...\3")


class ExplorerAddress:
    EXPLORER_URL_TEMPLATE = "https://polygonscan.com/address/{address}"

    @classmethod
    def get(cls, address):
        return cls.EXPLORER_URL_TEMPLATE.format(address=address)
