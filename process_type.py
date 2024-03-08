from typing import Optional


def is_base_node(what: str) -> bool:
    return what.startswith("BaseNode")


def is_base_wallet(what: str) -> bool:
    return what.startswith("BaseWallet")


def is_asset_wallet(what: str) -> bool:
    return what.startswith("AssetWallet")


def is_validator_node(what: str) -> bool:
    return what.startswith("ValidatorNode")


def is_miner(what: str) -> bool:
    return what.startswith("Miner")


def is_indexer(what: str) -> bool:
    return what.startswith("Indexer")


def is_signaling_server(what: str) -> bool:
    return what.startswith("SignalingServer")


def is_connector(what: str) -> bool:
    return what.startswith("TariConnector")


def is_template_web(what: str) -> bool:
    return what.startswith("TemplateWeb")


def get_index(what: str) -> Optional[int]:
    try:
        _, id = what.split("_")
        return int(id)
    except:
        return None
