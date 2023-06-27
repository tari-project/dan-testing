import os
from typing import Any


def get_env_or_default(env_name: str, default: Any):
    if env_name in os.environ:
        return os.environ[env_name]
    return default


DATA_FOLDER = "Data"
TARI_BINS_FOLDER = get_env_or_default("TARI_BINS_FOLDER", "bins")
TARI_DAN_BINS_FOLDER = get_env_or_default("TARI_DAN_BINS_FOLDER", "bins")
DELETE_EVERYTHING_BUT_TEMPLATES_BEFORE = True
DELETE_STDOUT_LOGS = True
DELETE_TEMPLATES = False
REDIRECT_BASE_NODE_STDOUT = True
REDIRECT_WALLET_STDOUT = True
REDIRECT_MINER_STDOUT = True
# how many VNs should print to console
REDIRECT_VN_FROM_INDEX_STDOUT = 0
# how many dan wallets should print to console
REDIRECT_DAN_WALLET_STDOUT = 0
# The register vn cli is redirected as VN, this is for the publish template etc.
REDIRECT_VN_CLI_STDOUT = True
REDIRECT_INDEXER_STDOUT = True
# This is for the cargo generate and compilation for the template
REDIRECT_TEMPLATE_STDOUT = True
REDIRECT_DAN_WALLET_WEBUI_STDOUT = True
REDIRECT_SIGNALING_STDOUT = True
NETWORK = "localnet"
SPAWN_VNS = 1
SPAWN_INDEXERS = 1
SPAWN_WALLETS_PER_INDEXER = 2
CREATE_ACCOUNTS_PER_WALLET = 1
# Any one of the templates from `wasm_template`
TEMPLATES = "fungible,swap"
# Specify args e.g. mint=10000,10001,1. Start the value with "w:" to choose Workspace arg, specify multiples with | e.g. fungible::mint=w:0|fungible::mint=10000,10001,1
# use ! to dump the buckets into the account
# DEFAULT_TEMPLATE_FUNCTION = "mint"
DEFAULT_TEMPLATE_FUNCTION = 'fungible::mint=Amount(1000000),"token1"|fungible::mint=Amount(2000),"token2"'
BURN_AMOUNT = 1000000
NO_FEES = True

USE_BINARY_EXECUTABLE = "DAN_TESTING_USE_BINARY_EXECUTABLE" in os.environ
STEPS_CREATE_ACCOUNT = True
STEPS_CREATE_TEMPLATE = True
STEPS_RUN_TARI_CONNECTOR_TEST_SITE = True
STEPS_RUN_SIGNALLING_SERVER = True
LISTEN_ONLY_ON_LOCALHOST = True

COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_MAGENTA = "\033[95m"
COLOR_CYAN = "\033[96m"
COLOR_RESET = "\033[0m"

COLOR_BRIGHT_RED = "\033[91;1m"
COLOR_BRIGHT_GREEN = "\033[92;1m"
COLOR_BRIGHT_YELLOW = "\033[93;1m"
COLOR_BRIGHT_BLUE = "\033[94;1m"
COLOR_BRIGHT_MAGENTA = "\033[95;1m"
COLOR_BRIGHT_CYAN = "\033[96;1m"

NAME_COLOR = COLOR_BRIGHT_YELLOW
EXEC_COLOR = COLOR_BRIGHT_GREEN
PORT_COLOR = COLOR_BRIGHT_CYAN
STEP_COLOR = COLOR_BRIGHT_YELLOW
STEP_OUTER_COLOR = COLOR_BRIGHT_GREEN

# If this is False, the cli_loop will be called instead
STRESS_TEST = False
