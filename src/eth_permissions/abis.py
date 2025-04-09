OZ_ACCESS_CONTROL = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "role", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "account", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
        ],
        "name": "RoleGranted",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "role", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "account", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
        ],
        "name": "RoleRevoked",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "role", "type": "bytes32"},
            {"indexed": True, "internalType": "bytes32", "name": "previousAdminRole", "type": "bytes32"},
            {"indexed": True, "internalType": "bytes32", "name": "newAdminRole", "type": "bytes32"},
        ],
        "name": "RoleAdminChanged",
        "type": "event",
    },
]

OZ_ACCESS_MANAGER = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint64", "name": "roleId", "type": "uint64"},
            {"indexed": True, "internalType": "address", "name": "account", "type": "address"},
            {"indexed": False, "internalType": "uint32", "name": "delay", "type": "uint32"},
            {"indexed": False, "internalType": "uint48", "name": "since", "type": "uint48"},
            {"indexed": False, "internalType": "bool", "name": "newMember", "type": "bool"},
        ],
        "name": "RoleGranted",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint64", "name": "roleId", "type": "uint64"},
            {"indexed": True, "internalType": "address", "name": "account", "type": "address"},
        ],
        "name": "RoleRevoked",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint64", "name": "roleId", "type": "uint64"},
            {"indexed": True, "internalType": "uint64", "name": "guardian", "type": "uint64"},
        ],
        "name": "RoleGuardianChanged",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint64", "name": "roleId", "type": "uint64"},
            {"indexed": True, "internalType": "uint64", "name": "admin", "type": "uint64"},
        ],
        "name": "RoleAdminChanged",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint64", "name": "roleId", "type": "uint64"},
            {"indexed": False, "internalType": "string", "name": "label", "type": "string"},
        ],
        "name": "RoleLabel",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "target", "type": "address"},
            {"indexed": False, "internalType": "bytes4", "name": "selector", "type": "bytes4"},
            {"indexed": True, "internalType": "uint64", "name": "roleId", "type": "uint64"},
        ],
        "name": "TargetFunctionRoleUpdated",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint64", "name": "roleId", "type": "uint64"},
            {"indexed": False, "internalType": "uint32", "name": "delay", "type": "uint32"},
            {"indexed": False, "internalType": "uint48", "name": "since", "type": "uint48"},
        ],
        "name": "RoleGrantDelayChanged",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "target", "type": "address"},
            {"indexed": False, "internalType": "bool", "name": "closed", "type": "bool"},
        ],
        "name": "TargetClosed",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "target", "type": "address"},
            {"indexed": False, "internalType": "uint32", "name": "delay", "type": "uint32"},
            {"indexed": False, "internalType": "uint48", "name": "since", "type": "uint48"},
        ],
        "name": "TargetAdminDelayUpdated",
        "type": "event",
    },
]
