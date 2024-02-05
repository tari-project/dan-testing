import re
from typing import Optional
from enum import Enum


def parse(what: str) -> tuple[Optional[str], Optional[int]]:
    match = re.match(r"(Miner)", what)
    if match:
        return
    match = re.match(r"(BaseNode|BaseWallet|AssetWallet|ValidatorNode)_(\d+)", what)
    if not match:
        return ("_", None)
    print(match.groups())
    if len(match.groups()) == 2:
        return (match.group(1), None)
    return (match.group(1), int(match.group(2)))


print(parse("Miner"))
print(parse("BaseNode_0"))
print(parse("BaseNode_1"))
print(parse("ValidatorNode_0"))
print(parse("AssetWallet_0"))
print(parse("Indexer_0"))

# from Processes.base_wallet import GrpcWallet
# from Processes.base_node import GrpcBaseNode
# from Processes.dan_wallet_daemon import JrpcDanWalletDaemon

# grpc = GrpcWallet("127.0.0.1:18008")
# # print(grpc.get_balance())
# # print(grpc.check_connectivity())
# # print(grpc.get_address().address.hex())


# grpc = GrpcBaseNode("127.0.0.1:18006")
# print(grpc.get_public_addresses())


# # jrpc = JrpcDanWalletDaemon("http://127.0.0.1:18013")
# # jrpc.auth()
# # print(jrpc.get_all_tx_by_status())
