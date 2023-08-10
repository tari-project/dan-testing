import os
from typing import Any

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


def is_boolstring(value: str):
    return value.lower() in ["false", "true", "0", "1"]


def is_boolstring_true(value: str):
    return value.lower() in ["true", "1"]


def get_env_or_default(env_name: str, default: Any, validation: Any = None) -> Any:
    if env_name in os.environ:
        if validation:
            if not validation(os.environ[env_name]):
                print(f"Value {COLOR_BRIGHT_RED}{os.environ[env_name]}{COLOR_RESET} for {COLOR_BRIGHT_BLUE}{env_name}{COLOR_RESET} is not valid!")
                exit()
        return os.environ[env_name]
    return default


WEBUI_PORT = get_env_or_default("DAN_TESTING_WEBUI_PORT", "auto")
DATA_FOLDER = get_env_or_default("DAN_TESTING_DATA_FOLDER", "Data")
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
REDIRECT_CARGO_INSTALL_CARGO_GENERATE_STDOUT = True
REDIRECT_TEMPLATE_STDOUT = True
REDIRECT_DAN_WALLET_WEBUI_STDOUT = True
REDIRECT_SIGNALING_STDOUT = True
NETWORK = "localnet"
SPAWN_VNS = int(get_env_or_default("DAN_TESTING_SPAWN_VNS", 1))
print("SPAWN_VNS", SPAWN_VNS)
SPAWN_INDEXERS = int(get_env_or_default("DAN_TESTING_SPAWN_INDEXERS", 1))
print("SPAWN_INDEXERS", SPAWN_INDEXERS)
SPAWN_WALLETS = int(get_env_or_default("DAN_TESTING_SPAWN_WALLETS", 1))
print("SPAWN_WALLETS", SPAWN_WALLETS)
CREATE_ACCOUNTS = int(get_env_or_default("DAN_TESTING_CREATE_ACCOUNTS", 2))
print("CREATE_ACCOUNTS", CREATE_ACCOUNTS)
# Any one of the templates from `wasm_template`
TEMPLATES = get_env_or_default("DAN_TESTING_TEMPLATES", "fungible,swap")
# Specify args e.g. mint=10000,10001,1. Start the value with "w:" to choose Workspace arg, specify multiples with | e.g. fungible::mint=w:0|fungible::mint=10000,10001,1
# use ! to dump the buckets into the account
# DEFAULT_TEMPLATE_FUNCTION = "mint"
DEFAULT_TEMPLATE_FUNCTION = get_env_or_default(
    "DAN_TESTING_DEFAULT_TEMPLATE_FUNCTION",
    'fungible::mint=Amount(1000000),"token1"|fungible::mint=Amount(2000),"token2"',
)
BURN_AMOUNT = int(get_env_or_default("DAN_TESTING_BURN_AMOUNT", 1000000))
NO_FEES = is_boolstring_true(get_env_or_default("DAN_TESTING_NO_FEES", "true", is_boolstring))

USE_BINARY_EXECUTABLE = "DAN_TESTING_USE_BINARY_EXECUTABLE" in os.environ
STEPS_CREATE_ACCOUNT = is_boolstring_true(get_env_or_default("DAN_TESTING_STEPS_CREATE_ACCOUNT", "true", is_boolstring))
STEPS_CREATE_TEMPLATE = is_boolstring_true(get_env_or_default("DAN_TESTING_STEPS_CREATE_TEMPLATE", "true", is_boolstring))
STEPS_RUN_TARI_CONNECTOR_TEST_SITE = "DAN_TESTING_STEPS_RUN_TARI_CONNECTOR_TEST_SITE" in os.environ
STEPS_RUN_SIGNALLING_SERVER = True
LISTEN_ONLY_ON_LOCALHOST = True

# If this is False, the cli_loop will be called instead
STRESS_TEST = is_boolstring_true(get_env_or_default("DAN_TESTING_STEPS_STRESS_TEST", "false", is_boolstring))
