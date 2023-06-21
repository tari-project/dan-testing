# pyright: reportUnboundVariable=false

from base_node import BaseNode
from config import (
    BURN_AMOUNT,
    COLOR_RESET,
    CREATE_ACCOUNTS_PER_WALLET,
    DATA_FOLDER,
    DEFAULT_TEMPLATE_FUNCTION,
    DELETE_EVERYTHING_BEFORE,
    DELETE_STDOUT_LOGS,
    LISTEN_ONLY_ON_LOCALHOST,
    SPAWN_INDEXERS,
    SPAWN_VNS,
    SPAWN_WALLETS_PER_INDEXER,
    STEP_COLOR,
    STEP_OUTER_COLOR,
    STEPS_CREATE_ACCOUNT,
    STEPS_CREATE_TEMPLATE,
    STEPS_RUN_SIGNALLING_SERVER,
    STEPS_RUN_TARI_CONNECTOR_TEST_SITE,
    STRESS_TEST,
    TEMPLATES,
    USE_BINARY_EXECUTABLE,
)
from dan_wallet_daemon import DanWalletDaemon
from indexer import Indexer
from miner import Miner
from signaling_server import SignalingServer
from stats import stats
from tari_connector_sample import TariConnectorSample
from template import Template
from template_server import Server
from threads import threads
from validator_node import ValidatorNode
from wallet import Wallet
import base64
import json
import os
import re
import shutil
import socket
import time
import traceback
import webbrowser

local_ip = "127.0.0.1"
if not LISTEN_ONLY_ON_LOCALHOST:
    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        temp_socket.connect(("10.255.255.255", 1))
        local_ip = temp_socket.getsockname()[0]
    except socket.error:
        local_ip = "127.0.0.1"
        exit()
    finally:
        temp_socket.close()

print(local_ip)


def cli_loop():
    global wallet, base_node, miner, dan_wallets, indexers, validator_nodes, tari_connector_sample, server
    try:
        while True:
            try:
                command = input("Command (press ctrl-c to exit or type 'help'): ")
            except:
                # this is for ctrl-c
                print("ctrl-c exiting...")
                break
            for_eval = command
            command.lower()
            try:
                if command == "help":
                    print("Commands available : ")
                    print("burn <public_key> <path = 'burn.json'>")
                    print("mine <number of blocks> - to mine blocks")
                    print("grpc <node|wallet> - to get grpc port of node or wallet")
                    print("jrpc <vn <id>|dan <id>|indexer> - to get jrpc port of vn with id <id>, dan wallet with id <id> or indexer")
                    print(
                        "http <vn <id>|dan <id>|indexer|connector> - to get http address of vn with id <id>, dan with id <id>, indexer or connector (connector sample page)"
                    )
                    print(
                        "kill <node|wallet|indexer|vn <id>|dan <id>> - to kill node, wallet, indexer, vn with id or dan wallet with id, the command how to run it locally will be printed without the `-n` (non-interactive switch)"
                    )
                    print("live - list of things that are still running from this python (base node, wallet, ...)")
                    print("---")
                    print("All indices are zero based")
                elif command.startswith("burn"):
                    public_key = command.split()[1]
                    public_key = bytes(int(public_key[i : i + 2], 16) for i in range(0, len(public_key), 2))
                    print_step(f"BURNING {BURN_AMOUNT}")
                    burn = wallet.grpc_client.burn(BURN_AMOUNT, public_key)
                    os.mkdir("output")
                    outfile = "burn.json"
                    if len(command.split()) > 2:
                        outfile = command.split()[2]

                    with open("output/" + outfile, "w") as f:
                        claim_proof = {
                            "commitment": base64.b64encode(burn.commitment).decode("utf-8"),
                            "range_proof": base64.b64encode(burn.range_proof).decode("utf-8"),
                            "reciprocal_claim_public_key": base64.b64encode(burn.reciprocal_claim_public_key).decode("utf-8"),
                            "ownership_proof": {
                                "u": base64.b64encode(burn.ownership_proof.u).decode("utf-8"),
                                "v": base64.b64encode(burn.ownership_proof.v).decode("utf-8"),
                                "public_nonce": base64.b64encode(burn.ownership_proof.public_nonce).decode("utf-8"),
                            },
                        }

                        json.dump(claim_proof, f)
                    print("written to file", outfile)

                elif command.startswith("mine"):
                    blocks = int(command.split()[1])
                    miner.mine(blocks)  # Mine the register TXs
                elif command.startswith("grpc"):
                    what = command.split()[1]
                    match what:
                        case "node":
                            print(base_node.grpc_port)
                        case "wallet":
                            print(wallet.grpc_port)
                        case _:
                            pass
                elif command.startswith("jrpc vn"):
                    if r := re.match(r"jrpc vn (\d+)", command):
                        vn_id = int(r.group(1))
                        if vn_id in validator_nodes:
                            print(validator_nodes[vn_id].json_rpc_port)
                        else:
                            print(f"VN id ({vn_id}) is invalid, either it never existed or you already killed it")
                elif command.startswith("jrpc dan"):
                    if r := re.match(r"jrpc dan (\d+)", command):
                        dan_id = int(r.group(1))
                        if dan_id in dan_wallets:
                            print(dan_wallets[dan_id].json_rpc_port)
                        else:
                            print(f"dan id ({dan_id}) is invalid, either it never existed or you already killed it")
                elif command.startswith("jrpc indexer"):
                    if r := re.match(r"jrpc indexer (\d+)", command):
                        indexer_id = int(r.group(1))
                        if indexer_id in indexers:
                            print(indexers[indexer_id].json_rpc_port)
                elif command.startswith("http"):
                    if command.startswith("http vn"):
                        if r := re.match(r"http vn (\d+)", command):
                            vn_id = int(r.group(1))
                            if vn_id in validator_nodes:
                                url = f"http://{validator_nodes[vn_id].http_ui_address}"
                                print(url)
                                webbrowser.open(url)
                            else:
                                print(f"VN id ({vn_id}) is invalid, either it never existed or you already killed it")
                    elif command.startswith("http dan"):
                        if r := re.match(r"http dan (\d+)", command):
                            dan_id = int(r.group(1))
                            if dan_id in dan_wallets:
                                url = f"http://localhost:{dan_wallets[dan_id].http_client.http_port}"
                                print(url)
                                webbrowser.open(url)
                            else:
                                print(f"DAN id ({dan_id}) is invalid, either it never existed or you already killed it")
                    elif command.startswith("http indexer"):
                        if r := re.match(r"http indexer (\d+)", command):
                            indexer_id = int(r.group(1))
                            if indexer_id in indexers:
                                url = f"http://{indexers[indexer_id].http_ui_address}"
                                print(url)
                                webbrowser.open(url)
                            else:
                                print(f"Indexer id ({indexer_id}) is invalid, either it never existed or you already killed it")
                    elif command == ("http signaling"):
                        url = f"http://localhost:{signaling_server.json_rpc_port}"
                        print(url)
                    elif command == ("http connector"):
                        url = f"http://localhost:{tari_connector_sample.http_port}"
                        print(url)
                        webbrowser.open(url)
                    else:
                        print("Invalid http request")
                elif command.startswith("kill"):
                    what = command.split(maxsplit=1)[1]
                    match what:
                        case "node":
                            if base_node:
                                print(f'To run base node : {" ".join(base_node.exec).replace("-n ", "")}')
                                del base_node
                        case "wallet":
                            if wallet:
                                print(f'To run the wallet : {" ".join(wallet.exec).replace("-n ", "")}')
                                del wallet
                        case _:
                            # This should be 'VN <id>'
                            if r := re.match(r"vn (\d+)", what):
                                vn_id = int(r.group(1))
                                if vn_id in validator_nodes:
                                    del validator_nodes[vn_id]
                                else:
                                    print(f"VN id ({vn_id}) is invalid, either it never existed or you already killed it")
                            elif r := re.match(r"dan (\d+)", what):
                                dan_id = int(r.group(1))
                                if dan_id in dan_wallets:
                                    del dan_wallets[dan_id]
                                else:
                                    print(f"DanWallet id ({dan_id}) is invalid, either it never existed or you already killed it")
                            elif r := re.match(r"indexer (\d+)", what):
                                indexer_id = int(r.group(1))
                                if indexer_id in indexers:
                                    del indexers[indexer_id]
                                else:
                                    print(f"Indexer id ({dan_id}) is invalid, either it never existed or you already killed it")
                            else:
                                print("Invalid kill command", command)
                            # which = what.split()
                elif command == "live":
                    if "base_node" in locals():
                        print("Base node is running")
                    if "wallet" in locals():
                        print("Wallet is running")
                    for vn_id in validator_nodes:
                        print(f"VN<{vn_id}> is running")
                    for daemon_id in dan_wallets:
                        print(f"DanWallet<{daemon_id}> is running")
                    for indexer_id in indexers:
                        print(f"Indexer<{indexer_id}> is running")
                elif command == "tx":
                    template.call_function(TEMPLATE_FUNCTION[0], next(iter(dan_wallets.values())).jrpc_client, FUNCTION_ARGS)
                    pass
                elif command.startswith("eval"):
                    # In case you need for whatever reason access to the running python script
                    eval(for_eval[len("eval ") :])
                elif command == "stats":
                    print(stats)
                else:
                    print("Wrong command")
            except Exception as ex:
                print("Command errored:", ex)
                traceback.print_exc()
    except Exception as ex:
        print("Failed in CLI loop:", ex)
        traceback.print_exc()


def stress_test():
    global wallet, base_node, miner, dan_wallets, indexers, validator_nodes, tari_connector_sample, server

    num_of_tx = 10  # this is how many times we send the funds back and forth for each of two wallets

    def send_tx(src_id: int, dst_id: int):
        src_account = dan_wallets[src_id].jrpc_client.accounts_list()[("accounts")][0]
        dst_account = dan_wallets[dst_id].jrpc_client.accounts_list()[("accounts")][0]
        res_addr = [1] * 32
        src_public_key = src_account["public_key"]
        dst_public_key = dst_account["public_key"]
        for i in range(num_of_tx):
            print(f"tx {src_id} -> {dst_id} ({i})")
            dan_wallets[src_id].jrpc_client.confidential_transfer(src_account, 1, res_addr, dst_public_key, 1)
            dan_wallets[dst_id].jrpc_client.confidential_transfer(dst_account, 1, res_addr, src_public_key, 1)
            dan_wallets[src_id].jrpc_client.transfer(src_account, 1, res_addr, dst_public_key, 1)
            dan_wallets[dst_id].jrpc_client.transfer(dst_account, 1, res_addr, src_public_key, 1)

    # We will send back and forth between two wallets. So with n*2 wallets we have n concurrent TXs
    start = time.time()
    for i in range(SPAWN_WALLETS_PER_INDEXER // 2):
        threads.add(send_tx, (i * 2, i * 2 + 1))

    threads.wait()

    total_time = time.time() - start

    total_num_of_tx = SPAWN_WALLETS_PER_INDEXER // 2 * num_of_tx * 2
    print(f"Total number of Tx {total_num_of_tx}")
    print(f"Total time {total_time}")
    print(f"Number of concurrent TXs : {SPAWN_WALLETS_PER_INDEXER//2}")
    print(f"Avg time for one TX {total_time/total_num_of_tx}")


def print_step(step_name: str):
    print(f"{STEP_OUTER_COLOR}### {STEP_COLOR}{step_name} {STEP_OUTER_COLOR}###{COLOR_RESET}")


def check_executable(file_name: str):
    if not os.path.exists(f"./{file_name}") and not os.path.exists(f"./{file_name}.exe"):
        print(f"Copy {file_name} executable in here")
        exit()


def wait_for_vns_to_sync():
    print("Waiting for VNs to sync to", base_node.grpc_client.get_tip())
    # We have to check if VNs are already running their jrpc server
    while True:
        try:
            while any(
                vn.jrpc_client.get_epoch_manager_stats()["current_block_height"] != base_node.grpc_client.get_tip() - 3
                for vn in validator_nodes.values()
            ):
                print(
                    [vn.jrpc_client.get_epoch_manager_stats()["current_block_height"] for vn in validator_nodes.values()],
                    base_node.grpc_client.get_tip() - 3,
                    end="\033[K\r",
                )
                time.sleep(1)
            break
        except:
            time.sleep(1)
    print("done\033[K")


try:
    if DELETE_EVERYTHING_BEFORE or DELETE_STDOUT_LOGS:
        try:
            shutil.rmtree(DATA_FOLDER)
        except:
            pass
        # for file in os.listdir(os.getcwd()):
        #     full_path = os.path.join(os.getcwd(), file)
        #     if os.path.isdir(full_path):
        #         if DELETE_EVERYTHING_BEFORE:
        #             if re.match(
        #                 r"(config|data|base_node|log|peer_db|miner|vn_\d+|wallet|dan_wallet_daemon_\d+|templates|stdout|signaling_server|indexer_\d+)",
        #                 file,
        #             ):
        #                 shutil.rmtree(full_path)
        #         else:
        #             if re.match(r"stdout", file):
        #                 shutil.rmtree(full_path)
    if USE_BINARY_EXECUTABLE:
        print_step("YOU ARE USING EXECUTABLE BINARIES AND NOT COMPILING THE CODE !!!")
        check_executable("tari_base_node")
        check_executable("tari_console_wallet")
        check_executable("tari_miner")
        check_executable("tari_indexer")
        check_executable("tari_dan_wallet_daemon")
        check_executable("tari_dan_wallet_cli")
        check_executable("tari_signaling_server")
        check_executable("tari_validator_node")
        check_executable("tari_validator_node_cli")
    try:
        os.mkdir(f"./{DATA_FOLDER}")
        os.mkdir(f"./{DATA_FOLDER}/stdout")
    except:
        pass

    # Step 1, start the http server for serving wasm files.
    print_step("STARTING HTTP SERVER")
    server = Server()
    server.run()
    templates: dict[str, Template] = {}
    if STEPS_CREATE_TEMPLATE:
        print_step("GENERATING TEMPLATE")
        # Generate template
        for t in TEMPLATES.split(","):
            templates[t] = Template(t)
    print_step("STARTING BASE NODE")
    # Start base node
    base_node = BaseNode(local_ip)
    print_step("STARTING WALLET")
    # Start wallet
    wallet = Wallet(base_node.get_address(), local_ip)
    # Set ports for miner
    miner = Miner(base_node.grpc_port, wallet.grpc_port, local_ip)
    # Mine some blocks
    miner.mine((SPAWN_VNS + SPAWN_INDEXERS * SPAWN_WALLETS_PER_INDEXER) * 2 + 13)  # Make sure we have enough funds
    # Start VNs
    print_step("CREATING VNS")
    validator_nodes: dict[int, ValidatorNode] = {}
    for vn_id in range(SPAWN_VNS):
        vn = ValidatorNode(
            base_node.grpc_port, wallet.grpc_port, vn_id, local_ip, [validator_nodes[vn_id].get_address() for vn_id in validator_nodes]
        )
        validator_nodes[vn_id] = vn
    wait_for_vns_to_sync()

    print_step("REGISTER THE VNS")
    # Register VNs
    for vn_id in validator_nodes:
        validator_nodes[vn_id].register(local_ip)
        # Uncomment next line if you want to have only one registeration per block
        # miner.mine(1)

        # Wait until they are all in the mempool
    i = 0
    print("Waiting for X tx's in mempool.", end="")
    while i < 10:
        if base_node.grpc_client.get_mempool_size() < len(validator_nodes) + 1:
            print(".", end="")
            time.sleep(1)
        else:
            break
        i += 1
    print("done")
    # Mining till the VNs are part of the committees
    miner.mine(20)  # Mine the register TXs
    time.sleep(1)

    indexers: dict[int, Indexer] = {}
    if SPAWN_INDEXERS > 0:
        print_step("STARTING INDEXERS")

        def spawn_indexer(id: int):
            indexers[id] = Indexer(id, base_node.grpc_port, local_ip, [validator_nodes[vn_id].get_address() for vn_id in validator_nodes])
            time.sleep(1)
            # force the indexer to connect to a VN. It will not find this substate, but it needs to contact the VN
            # to start comms
            try:
                indexers[id].jrpc_client.get_substate("component_d082c9cfb6507e302d5e252f43f4c008924648fc9bff18eaca5820a87808fc42", 0)
            except:
                pass

        for id in range(SPAWN_INDEXERS):
            threads.add(spawn_indexer, (id,))

        threads.wait()
        # connections = indexer.jrpc_client.get_connections()
        # comms_stats = indexer.jrpc_client.get_comms_stats()
        # print(connections)
        # print(comms_stats)

    dan_wallets: dict[int, DanWalletDaemon] = {}

    if SPAWN_INDEXERS == 0 and SPAWN_WALLETS_PER_INDEXER > 0:  # type: ignore
        raise Exception("Can't create a wallet when there is no indexer")

    signaling_server_jrpc_port = None
    if STEPS_RUN_SIGNALLING_SERVER:
        print_step("Starting signalling server")
        signaling_server = SignalingServer(local_ip)
        signaling_server_jrpc_port = signaling_server.json_rpc_port
    print_step("CREATING DAN WALLETS DAEMONS")

    def create_wallet(dwallet_id: int, indexer_jrpc: int, signaling_server_jrpc: int):
        dan_wallets[dwallet_id] = DanWalletDaemon(dwallet_id, indexer_jrpc, signaling_server_jrpc, local_ip)

    for indexer_id in range(SPAWN_INDEXERS):
        for dwallet_id in range(SPAWN_WALLETS_PER_INDEXER):
            # vn_id = min(SPAWN_VNS - 1, dwallet_id)
            if indexers and signaling_server_jrpc_port:
                threads.add(
                    create_wallet,
                    (
                        dwallet_id + indexer_id * SPAWN_WALLETS_PER_INDEXER,
                        indexers[indexer_id].json_rpc_port,
                        signaling_server_jrpc_port,
                    ),
                )

    threads.wait()

    miner.mine(23)
    wait_for_vns_to_sync()

    def spawn_wallet(d_id: int):
        while True:
            try:
                dan_wallets[d_id].jrpc_client.auth()
                break
            except:
                time.sleep(1)
        print(f"Dan Wallet {d_id} created")

    for indexer_id in range(SPAWN_INDEXERS):
        for d_id in range(SPAWN_WALLETS_PER_INDEXER):
            print("....")
            threads.add(spawn_wallet, (d_id + indexer_id * SPAWN_WALLETS_PER_INDEXER,))

    threads.wait()
    if STEPS_CREATE_TEMPLATE:
        # Publish template
        print_step("PUBLISHING TEMPLATE")
        for t in templates.values():
            t.publish_template(next(iter(validator_nodes.values())).json_rpc_port, server.port, local_ip)
        miner.mine(4)

        # Wait for the VNs to pickup the blocks from base layer
        # TODO wait for VN to download and activate the template
    wait_for_vns_to_sync()

    if STEPS_CREATE_ACCOUNT:
        print_step("CREATING ACCOUNTS")
        start = time.time()

        def create_account(i: int, id: int, amount: int):
            name = {"Name": f"TestAccount_{i+id*CREATE_ACCOUNTS_PER_WALLET}"}
            dan_wallet_jrpc = dan_wallets[id].jrpc_client
            print(f"Account {name} creation started")
            dan_wallet_jrpc.create_free_test_coins(name, amount)
            print(f"Account {name} created")

        for i in range(CREATE_ACCOUNTS_PER_WALLET):
            for id in dan_wallets:
                threads.add(create_account, (i, id, 12345))
        threads.wait()

        # burns = {}
        # accounts = {}
        # print_step(f"BURNING {BURN_AMOUNT}")
        # for id in dan_wallets:
        #     dan_wallet_jrpc = dan_wallets[id].jrpc_client
        #     account = dan_wallet_jrpc.accounts_list(0, 1)["accounts"][0]
        #     accounts[id] = account
        #     public_key = account["public_key"]
        #     burns[id] = wallet.grpc_client.burn(BURN_AMOUNT, bytes.fromhex(public_key))
        #     del dan_wallet_jrpc
        #     del public_key
        #     del account
        # # Wait for the burn to be in the mempool
        # print("Waiting for all burns to be in mempool.", end="")
        # while base_node.grpc_client.get_mempool_size() != len(dan_wallets):
        #     print(".", end="")
        #     time.sleep(1)
        # miner.mine(4)  # Mine the burns
        # print("done")
        # print("Wait until they are all mined.", end="")
        # while base_node.grpc_client.get_mempool_size() != 0:
        #     print(".", end="")
        #     miner.mine(1)  # Mine the burns
        #     time.sleep(1)
        # print("done")
        # miner.mine(3)  # mine 3 more blocks to have confirmation
        # wait_for_vns_to_sync()
        # time.sleep(10)
        # print_step("CLAIM BURN")
        # for id in dan_wallets:
        #     dan_wallet_jrpc = dan_wallets[id].jrpc_client
        #     dan_wallet_jrpc.claim_burn(burns[id], accounts[id])
        #     del dan_wallet_jrpc
        # print_step("CHECKING THE BALANCE")
        # for id in dan_wallets:
        #     # Claim the burn
        #     for id in dan_wallets:
        #         dan_wallet_jrpc = dan_wallets[id].jrpc_client
        #         while (
        #             dan_wallet_jrpc.get_balances(accounts[id])["balances"][0]["balance"]
        #             + dan_wallet_jrpc.get_balances(accounts[id])["balances"][0]["confidential_balance"]
        #             == 0
        #         ):
        #             time.sleep(1)
        #         del dan_wallet_jrpc

        # print_step("BURNED AND CLAIMED")

    if STEPS_CREATE_TEMPLATE:
        print_step("Creating template")

        # Call the function
        for function in DEFAULT_TEMPLATE_FUNCTION.split("|"):
            TEMPLATE_FUNCTION = function.split("=")
            FUNCTION_ARGS = len(TEMPLATE_FUNCTION) > 1 and TEMPLATE_FUNCTION[1].split(",") or []

            print(TEMPLATE_FUNCTION)
            print(FUNCTION_ARGS)
            template_name = TEMPLATE_FUNCTION[0].split("::")
            template = templates[template_name[0]]
            dump_into_account = "!" in template_name[1]
            method = template_name[1].replace("!", "")
            template.call_function(method, next(iter(dan_wallets.values())).jrpc_client, FUNCTION_ARGS, dump_into_account)

    if STEPS_RUN_TARI_CONNECTOR_TEST_SITE:
        if not STEPS_RUN_SIGNALLING_SERVER:
            print("Starting tari-connector test without signaling server is pointless!")
        else:
            print_step("Starting tari-connector test website")
            tari_connector_sample = TariConnectorSample(signaling_server_address=f"http://{local_ip}:{signaling_server.json_rpc_port}")
    if STRESS_TEST:
        stress_test()
    print(stats)
    cli_loop()
except Exception as ex:
    print("Failed setup:", ex)
    traceback.print_exc()
except KeyboardInterrupt:
    print("ctrl-c pressed during setup")

if "tari_connector_sample" in locals():
    del tari_connector_sample
if "signaling_server" in locals():
    del signaling_server
if "DanWallets" in locals():
    del dan_wallets
if "indexers" in locals():
    del indexers
if "VNs" in locals():
    del validator_nodes
if "wallet" in locals():
    del wallet
if "base_node" in locals():
    del base_node
if "server" in locals():
    del server
