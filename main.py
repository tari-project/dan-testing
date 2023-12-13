# pyright: reportUnboundVariable=false

from Processes.base_node import base_node
from Common.config import (
    TARI_BINS_FOLDER,
    TARI_DAN_BINS_FOLDER,
    BURN_AMOUNT,
    COLOR_RESET,
    CREATE_ACCOUNTS,
    DATA_FOLDER,
    DEFAULT_TEMPLATE_FUNCTION,
    DELETE_EVERYTHING_BUT_TEMPLATES_BEFORE,
    DELETE_TEMPLATES,
    DELETE_STDOUT_LOGS,
    SPAWN_INDEXERS,
    SPAWN_VNS,
    SPAWN_WALLETS,
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
from Processes.miner import miner
from Processes.signaling_server import SignalingServer
from Stats.stats import stats
from Processes.tari_connector_sample import TariConnectorSample
from Processes.template import Template
from Processes.template_server import Server
from Common.threads import threads
from Common.local_ip import local_ip
from Processes.wallet import wallet
from commands import Commands
from webui import JrpcWebuiServer
import os
import re
import shutil
import time
import traceback
import webbrowser
from Collections.validator_nodes import validator_nodes
from Collections.indexers import indexers
from Collections.dan_wallet_daemons import dan_wallets
from typing import Any

accounts: dict[str, Any] = {}


def cli_loop():
    global miner, tari_connector_sample, server, accounts
    commands = Commands(tari_connector_sample, server, signaling_server)
    server = JrpcWebuiServer(commands)
    try:
        while True:
            try:
                command = input("Command (press ctrl-c to exit or type 'help'): ")
            except:
                # this is for ctrl-c
                print("ctrl-c exiting...")
                break
            for_eval = command
            command = command.lower()
            try:
                if command == "help":
                    print("Commands available : ")
                    print("burn <public_key> <path = 'burn.json'>")
                    print("mine <number of blocks> - to mine blocks")
                    print("grpc <node|wallet> - to get grpc port of node or wallet")
                    print("jrpc <vn <id>|dan <id>|indexer> - to get jrpc port of vn with id <id>, dan wallet with id <id> or indexer")
                    print(
                        "http <vn <id>|dan <id>|indexer|connector|webui> - to get http address of vn with id <id>, dan with id <id>, indexer or connector (connector sample page), webui"
                    )
                    print(
                        "stop <node|wallet|indexer|vn <id>|dan <id>> - to stop node, wallet, indexer, vn with id or dan wallet with id, the command how to run it locally will be printed without the `-n` (non-interactive switch)"
                    )
                    print("live - list of things that are still running from this python (base node, wallet, ...)")
                    print("---")
                    print("All indices are zero based")
                elif command.startswith("burn"):
                    public_key = command.split()[1]
                    outfile = "burn.json"
                    if len(command.split()) > 2:
                        outfile = command.split()[2]
                    commands.burn(public_key, outfile, BURN_AMOUNT)

                elif command.startswith("mine"):
                    blocks = int(command.split()[1])
                    commands.mine(blocks)
                elif command.startswith("grpc"):
                    what = command.split()[1]
                    print(commands.grpc(what))
                elif command.startswith("jrpc vn"):
                    if r := re.match(r"jrpc vn (\d+)", command):
                        vn_id = int(r.group(1))
                        jrpc_port = commands.jrpc_vn(vn_id)
                        if jrpc_port:
                            print(jrpc_port)
                        else:
                            print(f"VN id ({vn_id}) is invalid, either it never existed or you already stopped it")
                elif command.startswith("jrpc dan"):
                    if r := re.match(r"jrpc dan (\d+)", command):
                        dan_id = int(r.group(1))
                        jrpc_port = commands.jrpc_dan(dan_id)
                        if jrpc_port:
                            print(jrpc_port)
                        else:
                            print(f"Dan id ({dan_id}) is invalid, either it never existed or you already stopped it")
                elif command.startswith("jrpc indexer"):
                    if r := re.match(r"jrpc indexer (\d+)", command):
                        indexer_id = int(r.group(1))
                        jrpc_port = commands.jrpc_indexer(indexer_id)
                        if jrpc_port:
                            print(jrpc_port)
                        else:
                            print(f"Indexer ({indexer_id}) is invalid, either it never existed or you already stopped it")
                elif command == ("jrpc signaling"):
                    url = f"http://{local_ip}:{signaling_server.json_rpc_port}"
                    print(url)
                elif command.startswith("http"):
                    if command.startswith("http vn"):
                        if r := re.match(r"http vn (\d+)", command):
                            vn_id = int(r.group(1))
                            http_address = commands.http_vn(vn_id)
                            if http_address:
                                print(http_address)
                                webbrowser.open(http_address)
                            else:
                                print(f"VN id ({vn_id}) is invalid, either it never existed or you already stopped it")
                    elif command.startswith("http dan"):
                        if r := re.match(r"http dan (\d+)", command):
                            dan_id = int(r.group(1))
                            http_address = commands.http_dan(dan_id)
                            if http_address:
                                print(http_address)
                                webbrowser.open(http_address)
                            else:
                                print(f"Dan id ({dan_id}) is invalid, either it never existed or you already stopped it")
                    elif command.startswith("http indexer"):
                        if r := re.match(r"http indexer (\d+)", command):
                            indexer_id = int(r.group(1))
                            http_address = commands.http_indexer(indexer_id)
                            if http_address:
                                print(http_address)
                                webbrowser.open(http_address)
                            else:
                                print(f"Indexer id ({indexer_id}) is invalid, either it never existed or you already stopped it")
                    elif command == "http connector":
                        if tari_connector_sample:
                            url = f"http://{local_ip}:{tari_connector_sample.http_port}"
                            print(url)
                            webbrowser.open(url)
                        else:
                            print("No tari connector sample")
                    elif command == "http webui":
                        url = f"http://{local_ip}:{server.webui.http_port}"
                        print(url)
                        webbrowser.open(url)
                    else:
                        print("Invalid http request")
                elif command.startswith("stop"):
                    what = command.split(maxsplit=1)[1]
                    if what == "node":
                        if base_node:
                            base_node.stop()
                    elif what == "wallet":
                        if wallet:
                            wallet.stop()
                    else:
                        # This should be 'VN <id>'
                        if r := re.match(r"vn (\d+)", what):
                            vn_id = int(r.group(1))
                            validator_nodes.stop(vn_id)
                        elif r := re.match(r"dan (\d+)", what):
                            dan_id = int(r.group(1))
                            dan_wallets.stop(dan_id)
                        elif r := re.match(r"indexer (\d+)", what):
                            indexer_id = int(r.group(1))
                            indexers.stop(indexer_id)
                        else:
                            print("Invalid stop command", command)
                        # which = what.split()
                elif command.startswith("start"):
                    what = command.split(maxsplit=1)[1]
                    if r := re.match(r"vn (\d+)", what):
                        vn_id = int(r.group(1))
                        validator_nodes.add_validator_node(vn_id)
                elif command == "live":
                    if "base_node" in locals():
                        print("Base node is running")
                    if "wallet" in locals():
                        print("Wallet is running")
                    validator_nodes.live()
                    dan_wallets.live()
                    indexers.live()
                elif command == "tx":
                    template.call_function(TEMPLATE_FUNCTION[0], dan_wallets.any_dan_wallet_daemon().jrpc_client, FUNCTION_ARGS)
                    pass
                elif command.startswith("eval"):
                    # In case you need for whatever reason access to the running python script
                    eval(for_eval[len("eval ") :])
                elif command == "stats":
                    print(stats)
                elif command == "exit":
                    break
                else:
                    print("Wrong command")
            except Exception as ex:
                print("Command errored:", ex)
                traceback.print_exc()
    except Exception as ex:
        print("Failed in CLI loop:", ex)
        traceback.print_exc()
    del server


# this is how many times we send the funds back and forth for each of two wallets
def stress_test(num_of_tx: int = 1, dry_run: bool = True):
    # The dry run is ignored for now, once there will be a change in the PR I will update this.
    global base_node, miner, tari_connector_sample, server
    global total_num_of_tx
    total_num_of_tx = 0

    def send_tx(account0: int, account1: int):
        global total_num_of_tx
        res_addr = "resource_0101010101010101010101010101010101010101010101010101010101010101"
        acc0, dan0 = accounts[account0]
        acc1, dan1 = accounts[account1]
        public_key0 = acc0["public_key"]
        public_key1 = acc1["public_key"]
        for i in range(num_of_tx):
            print(f"tx {account0} -> {account1} ({i})")
            # dan0.jrpc_client.confidential_transfer(acc0, 1, res_addr, public_key1, 2000)
            # dan1.jrpc_client.confidential_transfer(acc1, 1, res_addr, public_key0, 2000)
            dan0.jrpc_client.transfer(acc0, 2000, res_addr, public_key1, 2000, dry_run)
            total_num_of_tx += 1
            # dan_wallets[dst_id].jrpc_client.transfer(dst_account, 1, res_addr, src_public_key, 2000)

    # We will send back and forth between two wallets. So with n*2 wallets we have n concurrent TXs
    start = time.time()
    threads.set_semaphore_limit(0)
    for id in range(0, len(accounts.keys()) - 1, 2):
        id1 = list(accounts.keys())[id]
        id2 = list(accounts.keys())[id + 1]
        threads.add(send_tx, (id1, id2))

    threads.wait()

    total_time = time.time() - start

    if total_num_of_tx:
        print(f"Total number of Tx {total_num_of_tx}")
        print(f"Total time {total_time}")
        print(f"Number of concurrent TXs : {SPAWN_WALLETS//2}")
        print(f"Avg time for one TX {total_time/total_num_of_tx}")
    else:
        print("No TXs")


def print_step(step_name: str):
    print(f"{STEP_OUTER_COLOR}### {STEP_COLOR}{step_name.upper()} {STEP_OUTER_COLOR}###{COLOR_RESET}")


def check_executable(bins_folder: str, file_name: str):
    if not os.path.exists(os.path.join(bins_folder, file_name)) and not os.path.exists(os.path.join(bins_folder, f"{file_name}.exe")):
        print(f"Copy {file_name} executable to '{bins_folder}' here")
        exit()


try:
    if DELETE_EVERYTHING_BUT_TEMPLATES_BEFORE or DELETE_STDOUT_LOGS:
        if os.path.exists(DATA_FOLDER):
            for file in os.listdir(DATA_FOLDER):
                full_path = os.path.join(os.getcwd(), DATA_FOLDER, file)
                if os.path.isdir(full_path):
                    if DELETE_EVERYTHING_BUT_TEMPLATES_BEFORE:
                        if file != "templates" or DELETE_TEMPLATES:
                            shutil.rmtree(full_path)
                    else:
                        if re.match(r"stdout", file):
                            shutil.rmtree(full_path)
    if USE_BINARY_EXECUTABLE:
        print_step("!!! YOU ARE USING EXECUTABLE BINARIES AND NOT COMPILING THE CODE !!!")
        print_step(f"Tari folder {TARI_BINS_FOLDER}")
        print_step(f"Tari dan folder {TARI_DAN_BINS_FOLDER}")
        check_executable(TARI_BINS_FOLDER, "minotari_node")
        check_executable(TARI_BINS_FOLDER, "minotari_console_wallet")
        check_executable(TARI_BINS_FOLDER, "minotari_miner")
        check_executable(TARI_DAN_BINS_FOLDER, "tari_indexer")
        check_executable(TARI_DAN_BINS_FOLDER, "tari_dan_wallet_daemon")
        check_executable(TARI_DAN_BINS_FOLDER, "tari_dan_wallet_cli")
        check_executable(TARI_DAN_BINS_FOLDER, "tari_signaling_server")
        check_executable(TARI_DAN_BINS_FOLDER, "tari_validator_node")
        check_executable(TARI_DAN_BINS_FOLDER, "tari_validator_node_cli")
    try:
        os.mkdir(DATA_FOLDER)
    except:
        pass
    try:
        os.mkdir(os.path.join(DATA_FOLDER, "stdout"))
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
    base_node.start(local_ip)
    print_step("STARTING WALLET")
    # Start wallet
    wallet.start(base_node.get_address(), local_ip)
    # Set ports for miner
    miner.start(base_node.grpc_port, wallet.grpc_port, local_ip)
    # Mine some blocks
    miner.mine((SPAWN_VNS + SPAWN_INDEXERS + SPAWN_WALLETS) * 2 + 13)  # Make sure we have enough funds
    # Start VNs
    print_step("CREATING VNS")
    for vn_id in range(SPAWN_VNS):
        validator_nodes.add_validator_node(vn_id)
    validator_nodes.wait_for_sync()

    print_step("REGISTER THE VNS")
    # Register VNs
    validator_nodes.register()

    if SPAWN_INDEXERS > 0:
        print_step("STARTING INDEXERS")

        def spawn_indexer(id: int):
            indexers.add_indexer(id)
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
        indexers.wait_for_sync()
        # connections = indexer.jrpc_client.get_connections()
        # comms_stats = indexer.jrpc_client.get_comms_stats()
        # print(connections)
        # print(comms_stats)

    if SPAWN_INDEXERS == 0 and SPAWN_WALLETS > 0:  # type: ignore
        raise Exception("Can't create a wallet when there is no indexer")

    signaling_server_jrpc_port = None
    if STEPS_RUN_SIGNALLING_SERVER:
        print_step("Starting signalling server")
        signaling_server = SignalingServer(local_ip)
        signaling_server_jrpc_port = signaling_server.json_rpc_port
    print_step("CREATING DAN WALLETS DAEMONS")

    def create_wallet(dwallet_id: int, indexer_jrpc: int, signaling_server_jrpc: int):
        dan_wallets.add_dan_wallet_daemon(dwallet_id, indexer_jrpc, signaling_server_jrpc)

    for dwallet_id in range(SPAWN_WALLETS):
        if SPAWN_INDEXERS > 0 and signaling_server_jrpc_port:
            threads.add(
                create_wallet,
                (
                    dwallet_id,
                    indexers[dwallet_id % SPAWN_INDEXERS].json_rpc_port,
                    signaling_server_jrpc_port,
                ),
            )

    threads.wait()

    miner.mine(23)
    validator_nodes.wait_for_sync()
    indexers.wait_for_sync()

    def spawn_wallet(d_id: int):
        while True:
            try:
                dan_wallets[d_id].jrpc_client.auth()
                break
            except:
                time.sleep(1)
        print(f"Dan Wallet {d_id} created")

    for dwallet_id in dan_wallets:
        threads.add(spawn_wallet, (dwallet_id,))

    threads.wait()
    if STEPS_CREATE_TEMPLATE:
        # Publish template
        print_step("PUBLISHING TEMPLATE")
        for t in templates.values():
            t.publish_template(validator_nodes.any_node().json_rpc_port, server.port, local_ip)
        miner.mine(4)

        # Wait for the VNs to pickup the blocks from base layer
        # TODO wait for VN to download and activate the template
    validator_nodes.wait_for_sync()

    indexers.wait_for_sync()

    if STEPS_CREATE_ACCOUNT:
        print_step("CREATING ACCOUNTS")
        start = time.time()

        def create_account(i: int, amount: int):
            name = {"Name": f"TestAccount_{i}"}
            dan_wallet_jrpc = dan_wallets[i % SPAWN_WALLETS].jrpc_client
            print(f"Account {name["Name"]} creation started")
            dan_wallet_jrpc.create_free_test_coins(name, amount)
            print(f"Account {name["Name"]} created")

        threads.set_semaphore_limit(1)
        for i in range(CREATE_ACCOUNTS):
            threads.add(create_account, (i, 10000000))
        threads.wait()
        threads.set_semaphore_limit(10)

        for did in dan_wallets:
            while True:
                accs = dan_wallets[did].jrpc_client.accounts_list(0, CREATE_ACCOUNTS)["accounts"]
                print("accs", len(accs), end="\r")
                if len(accs) != CREATE_ACCOUNTS // SPAWN_WALLETS + (did < CREATE_ACCOUNTS % SPAWN_WALLETS and 1 or 0):
                    time.sleep(1)
                else:
                    break
            for acc in sorted(accs, key=lambda acc: acc["account"]["name"]):
                accounts[acc["account"]["name"]] = (acc, dan_wallets[did])
        print()
        # burns = {}
        # accounts = {}
        # BURN_AMOUNT = 10000
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
        # validator_nodes.wait_for_sync()
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
            template.call_function(method, dan_wallets.any_dan_wallet_daemon().jrpc_client, FUNCTION_ARGS, dump_into_account)

    if STEPS_RUN_TARI_CONNECTOR_TEST_SITE:
        if not STEPS_RUN_SIGNALLING_SERVER:
            print("Starting tari-connector test without signaling server is pointless!")
        else:
            print_step("Starting tari-connector test website")
            tari_connector_sample = TariConnectorSample(signaling_server_address=f"http://{local_ip}:{signaling_server.json_rpc_port}")
    else:
        tari_connector_sample = None
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
if "dan_wallets" in locals():
    del dan_wallets
if "indexers" in locals():
    del indexers
if "validator_nodes" in locals():
    del validator_nodes
if "wallet" in locals():
    del wallet
if "base_node" in locals():
    del base_node
if "server" in locals():
    del server
