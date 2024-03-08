import React, { useEffect, useState } from "react";
import { jsonRpc } from "../utils/json_rpc";

enum Executable {
  BaseNode = 1,
  Wallet = 2,
  Miner = 3,
  ValidatorNode = 4,
  Indexer = 5,
  DanWallet = 6,
  Templates = 7,
  TemplateWeb = 8,
}

async function jsonRpc2(address: string, method: string, params: any = null) {
  let id = 0;
  id += 1;
  let response = await fetch(address, {
    method: "POST",
    body: JSON.stringify({
      method: method,
      jsonrpc: "2.0",
      id: id,
      params: params,
    }),
    headers: {
      "Content-Type": "application/json",
    },
  });
  let json = await response.json();
  if (json.error) {
    throw json.error;
  }
  return json.result;
}

function ExtraInfoVN({
  name,
  url,
  setRow,
  addTxToPool,
  autoRefresh,
  state,
  horizontal,
}: {
  name: String;
  url: string;
  setRow: any;
  addTxToPool: any;
  autoRefresh: boolean;
  state: any;
  horizontal: boolean;
}) {
  const [bucket, setBucket] = useState(null);
  const [epoch, setEpoch] = useState(null);
  const [height, setHeight] = useState(null);
  const [pool, setPool] = useState([]);
  const [copied, setCopied] = useState(false);
  const [missingTxStates, setMissingTxStates] = useState({}); // {tx_id: [vn1, vn2, ...]}
  const [publicKey, setPublicKey] = useState(null);
  const [peerId, setPeerId] = useState(null);
  const [tick, setTick] = useState(0);
  useEffect(() => {
    if (autoRefresh) {
      const timer = setInterval(() => {
        setTick(tick + 1);
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [tick, autoRefresh]);
  useEffect(() => {
    jsonRpc2(url, "get_epoch_manager_stats")
      .then((resp) => {
        setRow(resp.committee_shard.shard + 1);
        setBucket(resp.committee_shard.shard);
        setHeight(resp.current_block_height);
        setEpoch(resp.current_epoch);
      })
      .catch((resp) => {
        console.error("err", resp);
      });
    jsonRpc2(url, "get_tx_pool").then((resp) => {
      setPool(resp.tx_pool);
      addTxToPool(resp.tx_pool.map((tx) => tx.transaction.id).sort());
    });
    jsonRpc2(url, "get_identity").then((resp) => {
      setPublicKey(resp.public_key);
      setPeerId(resp.peer_id);
    });
    let missing_tx = new Set();
    for (let k in state) {
      if (k != name && state[k].length > 0) {
        missing_tx = new Set([...missing_tx, ...state[k]]);
      }
    }
    let my_txs = new Set(state[name]);
    missing_tx = new Set([...missing_tx].filter((tx) => !my_txs.has(tx)));
    const promises = Array.from(missing_tx).map((tx) =>
      jsonRpc2(url, "get_transaction", [tx])
        .then((resp) => {
          return resp.transaction;
        })
        .catch((resp) => {
          throw { resp, tx };
        })
    );
    Promise.allSettled(promises).then((results) => {
      let newState = {};
      for (let result of results) {
        if (result.status == "fulfilled") {
          const resp = result.value;
          newState[resp.transaction.id] = {
            known: true,
            abort_details: resp.abort_details,
            final_decision: resp.final_decision,
          };
        } else {
          newState[result.reason.tx] = { known: false };
        }
      }
      if (JSON.stringify(newState) != JSON.stringify(missingTxStates)) {
        setMissingTxStates(newState);
      }
    });
    // for (let tx of missing_tx) {
    //   jsonRpc2(url, "get_transaction", [tx]).then((resp) => {
    //     setMissingTxStates((state) => ({ ...state, [tx]: { known: true, abort_details: resp.transaction.abort_details, final_decision: resp.transaction.final_decision } }));
    //     // console.log(resp);
    //   }).catch((resp) => { setMissingTxStates((state) => ({ ...state, [tx]: { know: false } })); });
    // }
  }, [tick, state]);
  const shorten = (str: string) => {
    if (str.length > 20) {
      return str.slice(0, 3) + "..." + str.slice(-3);
    }
    return str;
  };
  useEffect(() => {
    if (copied) {
      setTimeout(() => setCopied(false), 1000);
    }
  }, [copied]);
  const copyToClipboard = (str: string) => {
    setCopied(true);
    navigator.clipboard.writeText(str);
  };
  const showMissingTx = (missingTxStates) => {
    if (Object.keys(missingTxStates).length == 0) {
      return null;
    }
    return (
      <>
        <hr />
        <h3>Transaction from others TXs pools</h3>
        <div
          style={{
            display: "grid",
            gridAutoFlow: horizontal ? "column" : "row",
            gridTemplateRows: horizontal ? "auto auto auto auto" : "auto",
            gridTemplateColumns: horizontal ? "auto" : "auto auto auto auto",
          }}
        >
          <b>Tx Id</b>
          <b>Known</b>
          <b>Abort details</b>
          <b>Final decision</b>
          {Object.keys(missingTxStates).map((tx) => {
            const { known, abort_details, final_decision } = missingTxStates[tx];
            return (
              <>
                <div onClick={() => copyToClipboard(tx)}>{(copied && "Copied") || shorten(tx)}</div>
                <div style={{ color: known ? "green" : "red" }}>
                  <b>{(known && "Yes") || "No"}</b>
                </div>
                <div>{abort_details || <i>unknown</i>}</div>
                <div>{final_decision || <i>unknown</i>}</div>
              </>
            );
          })}
        </div>
      </>
    );
  };
  const showPool = (pool) => {
    if (pool.length == 0) {
      return null;
    }
    return (
      <>
        <hr />
        <h3>Pool transaction</h3>
        <div
          style={{
            display: "grid",
            gridAutoFlow: horizontal ? "column" : "row",
            gridTemplateRows: horizontal ? "auto auto auto auto auto" : "auto",
            gridTemplateColumns: horizontal ? "auto" : "auto auto auto auto auto",
          }}
        >
          <b>Tx Id</b>
          <b>Ready</b>
          <b>Local_Decision</b>
          <b>Remote_Decision</b>
          <b>Stage</b>
          {pool.map((tx) => (
            <>
              <div onClick={() => copyToClipboard(tx.transaction.id)}>
                {(copied && "Copied") || shorten(tx.transaction.id)}
              </div>
              <div>{(tx.is_ready && "Yes") || "No"}</div>
              <div>{tx.local_decision || "_"}</div>
              <div>{tx.remote_decision || "_"}</div>
              <div>{tx.stage}</div>
            </>
          ))}
        </div>
      </>
    );
  };
  return (
    <div style={{ whiteSpace: "nowrap" }}>
      <hr />
      <div
        style={{
          display: "grid",
          gridAutoFlow: "column",
          gridTemplateColumns: "auto auto",
          gridTemplateRows: "auto auto auto auto auto",
        }}
      >
        <div>
          <b>Bucket</b>
        </div>
        <div>
          <b>Height</b>
        </div>
        <div>
          <b>Epoch</b>
        </div>
        <div>
          <b>Public key</b>
        </div>
        <div>
          <b>Peer id</b>
        </div>
        <div>{bucket}</div>
        <div>{height}</div>
        <div>{epoch}</div>
        <div>{publicKey}</div>
        <div>{peerId}</div>
      </div>
      {showPool(pool)}
      {showMissingTx(missingTxStates)}
    </div>
  );
}

function ShowInfo(params: any) {
  let { children, executable, name, node, logs, stdoutLogs, showLogs, autoRefresh, updateState, state, horizontal } =
    params;
  const [row, setRow] = useState(1);
  const [unprocessedTx, setUnprocessedTx] = useState([]);
  const nameInfo = name && (
    <div>
      <pre></pre>
      <b>Name</b>
      {name}
    </div>
  );
  const jrpcInfo = node?.jrpc && (
    <div>
      <b>JRPC</b>
      <span className="select">http://{node.jrpc}</span>
    </div>
  );
  const grpcInfo = node?.grpc && (
    <div>
      <b>GRPC</b>
      <span className="select">http://{node.grpc}</span>
    </div>
  );
  const httpInfo = node?.http && (
    <div>
      <b>HTTP</b>
      <a href={`http://${node.http}`}>{`http://${node.http}`}</a>
    </div>
  );
  const logInfo = logs && (
    <>
      <div>
        <b>Logs</b>
        <div>
          {logs?.map((e) => (
            <div key={e[0]}>
              <a href={`log/${btoa(e[0])}/normal`}>
                {e[1]} - {e[2]}
              </a>
            </div>
          ))}
        </div>
      </div>
      <div>
        <div>
          {stdoutLogs?.map((e) => (
            <div key={e[0]}>
              <a href={`log/${btoa(e[0])}/stdout`}>stdout</a>
            </div>
          ))}
        </div>
      </div>
    </>
  );
  const addTxToPool = (tx: any) => {
    updateState({ name: name, state: tx });
  };
  return (
    <div className="info" key={name} style={{ gridRow: row }}>
      {nameInfo}
      {httpInfo}
      {jrpcInfo}
      {grpcInfo}
      {showLogs && logInfo}
      {executable === Executable.ValidatorNode && node?.jrpc && (
        <ExtraInfoVN
          name={name}
          url={`http://${node.jrpc}`}
          setRow={(new_row) => {
            if (new_row != row) setRow(new_row);
          }}
          addTxToPool={addTxToPool}
          autoRefresh={autoRefresh}
          state={state}
          horizontal={horizontal}
        />
      )}
      {children}
    </div>
  );
}

function ShowInfos(params: any) {
  let { nodes, executable, logs, stdoutLogs, showLogs, autoRefresh, horizontal } = params;
  const [state, setState] = useState({});
  const updateState = (partial_state: any) => {
    if (JSON.stringify(state[partial_state.name]) != JSON.stringify(partial_state.state)) {
      setState((state) => ({ ...state, [partial_state.name]: partial_state.state }));
    }
  };
  console.log(nodes);
  return (
    <div className="infos" style={{ display: "grid" }}>
      {Object.values(nodes).map((item: any) => (
        <ShowInfo
          key={item.name}
          executable={executable}
          name={item.name}
          node={item}
          logs={logs?.[item.name]}
          stdoutLogs={stdoutLogs?.[item.name]}
          showLogs={showLogs}
          autoRefresh={autoRefresh}
          updateState={updateState}
          state={state}
          horizontal={horizontal}
        />
      ))}
    </div>
  );
}

export default function Main() {
  const [vns, setVns] = useState({});
  const [baseNodes, setBaseNodes] = useState({});
  const [baseWallets, setBaseWallets] = useState({});
  const [danWallet, setDanWallets] = useState({});
  const [indexers, setIndexers] = useState({});
  const [node, setNode] = useState();
  const [wallet, setWallet] = useState();
  const [logs, setLogs] = useState({});
  const [stdoutLogs, setStdoutLogs] = useState({});
  const [connectorSample, setConnectorSample] = useState(null);
  const [templateWeb, setTemplateWeb] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [showLogs, setShowLogs] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [horizontal, setHorizontal] = useState(false);

  useEffect(() => {
    const getLogs = (name: string) =>
      jsonRpc("get_logs", name)
        .then((resp) => setLogs((state) => ({ ...state, [name]: resp })))
        .catch((error) => console.log(error));
    const getStdout = (name: string) =>
      jsonRpc("get_stdout", name)
        .then((resp) => setStdoutLogs((state) => ({ ...state, [name]: resp })))
        .catch((error) => console.log(error));
    const getAll = (items: Array<{ name: string }>) =>
      Object.values(items).map((item) => {
        getLogs(item.name);
        getStdout(item.name);
      });
    const get = (name: string, setFunction: any) => {
      jsonRpc(name)
        .then((resp) => {
          setFunction(resp);
          getAll(resp);
        })
        .catch((error) => console.log(error));
    };
    get("vns", setVns);
    get("dan_wallets", setDanWallets);
    get("indexers", setIndexers);
    get("base_nodes", setBaseNodes);
    get("base_wallets", setBaseWallets);
    jsonRpc("http", "TariConnector")
      .then((resp) => setConnectorSample(resp))
      .catch((error) => console.log(error));
    jsonRpc("http", "TemplateWeb")
      .then((resp) => setTemplateWeb(resp))
      .catch((error) => console.log(error));
    getLogs("miner");
    getStdout("miner");
  }, []);
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
  };

  const handleFileUpload = () => {
    let address = import.meta.env.VITE_DAEMON_JRPC_ADDRESS || "localhost:9000";
    const formData = new FormData();
    formData.append("file", selectedFile);
    fetch(`http://${address}/upload_template`, { method: "POST", body: formData }).then((resp) => {
      console.log("resp", resp);
    });
  };
  return (
    <div className="main">
      <button onClick={() => setShowLogs(!showLogs)}>{(showLogs && "Hide") || "Show"} logs</button>
      <button onClick={() => setAutoRefresh(!autoRefresh)}>{(autoRefresh && "Disable") || "Enable"} autorefresh</button>
      <button onClick={() => setHorizontal(!horizontal)}>Swap rows/columns</button>
      <div className="infos">
        <ShowInfo
          executable={Executable.Miner}
          name="miner"
          node={null}
          logs={logs?.["miner"]}
          stdoutLogs={stdoutLogs?.["miner"]}
          showLogs={showLogs}
          horizontal={horizontal}
        >
          <button onClick={() => jsonRpc("mine", 1)}>Mine</button>
        </ShowInfo>
      </div>
      <div>
        <div className="label">Base Nodes</div>
        <ShowInfos
          nodes={baseNodes}
          executable={Executable.BaseNode}
          logs={logs}
          stdoutLogs={stdoutLogs}
          showLogs={showLogs}
          autoRefresh={autoRefresh}
          horizontal={horizontal}
        />
      </div>
      <div>
        <div className="label">Base Wallets</div>
        <ShowInfos
          nodes={baseWallets}
          executable={Executable.BaseWallet}
          logs={logs}
          stdoutLogs={stdoutLogs}
          showLogs={showLogs}
          autoRefresh={autoRefresh}
          horizontal={horizontal}
        />
      </div>
      <div>
        <div className="label">Validator Nodes</div>
        <ShowInfos
          nodes={vns}
          executable={Executable.ValidatorNode}
          logs={logs}
          stdoutLogs={stdoutLogs}
          showLogs={showLogs}
          autoRefresh={autoRefresh}
          horizontal={horizontal}
        />
      </div>
      <div>
        <div className="label">Dan Wallets</div>
        <ShowInfos
          nodes={danWallet}
          executable={Executable.DanWallet}
          logs={logs}
          stdoutLogs={stdoutLogs}
          showLogs={showLogs}
          autoRefresh={autoRefresh}
          horizontal={horizontal}
        />
      </div>
      <div>
        <div className="label">Indexers</div>
        <ShowInfos
          nodes={indexers}
          executable={Executable.Indexer}
          logs={logs}
          stdoutLogs={stdoutLogs}
          showLogs={showLogs}
          autoRefresh={autoRefresh}
          horizontal={horizontal}
        />
      </div>
      <div className="label">Templates</div>
      <div className="infos">
        <ShowInfo executable={Executable.Templates} horizontal={horizontal}>
          <input type="file" onChange={handleFileChange} />
          <button onClick={handleFileUpload}>Upload template</button>
        </ShowInfo>
        {templateWeb && (
          <ShowInfo executable={Executable.TemplateWeb} horizontal={horizontal}>
            <div id="templates">
              <a href={templateWeb}>Template web</a>
            </div>
          </ShowInfo>
        )}
      </div>

      {connectorSample && (
        <div className="label">
          <a href={connectorSample}>Connector sample</a>
        </div>
      )}
    </div>
  );
}
