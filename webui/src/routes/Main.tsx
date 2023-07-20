import React, { useEffect, useState } from "react";
import { jsonRpc } from "../utils/json_rpc";

function ShowInfo(name, node, log, stdoutLog, additional: React.JSX = null) {
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
  const logInfo = log && (
    <>
      <div>
        <b>Logs</b>
        <div>
          {log?.map((e) => (
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
          {stdoutLog?.map((e) => (
            <div key={e[0]}>
              <a href={`log/${btoa(e[0])}/stdout`}>stdout</a>
            </div>
          ))}
        </div>
      </div>
    </>
  );
  return (
    <div className="info" key={name}>
      {nameInfo}
      {httpInfo}
      {jrpcInfo}
      {grpcInfo}
      {logInfo}
      {additional}
    </div>
  );
}

function ShowInfos(nodes, logs, stdoutLogs, name) {
  return (
    <div className="infos">
      {Object.keys(nodes).map((index) =>
        ShowInfo(`${name}_${index}`, nodes[index], logs?.[`${name} ${index}`], stdoutLogs?.[`${name} ${index}`])
      )}
    </div>
  );
}

export default function Main() {
  const [vns, setVns] = useState({});
  const [danWallet, setDanWallets] = useState({});
  const [indexers, setIndexers] = useState({});
  const [node, setNode] = useState();
  const [wallet, setWallet] = useState();
  const [logs, setLogs] = useState({});
  const [stdoutLogs, setStdoutLogs] = useState({});
  const [connectorSample, setConnectorSample] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);

  useEffect(() => {
    jsonRpc("vns")
      .then((resp) => {
        setVns(resp);
        Object.keys(resp).map((index) => {
          jsonRpc("get_logs", `vn ${index}`)
            .then((resp) => {
              setLogs((state) => ({ ...state, [`vn ${index}`]: resp }));
            })
            .catch((error) => console.log(error));
          jsonRpc("get_stdout", `vn ${index}`)
            .then((resp) => {
              setStdoutLogs((state) => ({ ...state, [`vn ${index}`]: resp }));
            })
            .catch((error) => console.log(error));
        });
      })
      .catch((error) => {
        console.log(error);
      });
    jsonRpc("dan_wallets")
      .then((resp) => {
        setDanWallets(resp);
        Object.keys(resp).map((index) => {
          jsonRpc("get_logs", `dan ${index}`)
            .then((resp) => {
              setLogs((state) => ({ ...state, [`dan ${index}`]: resp }));
            })
            .catch((error) => console.log(error));
          jsonRpc("get_stdout", `dan ${index}`)
            .then((resp) => {
              setStdoutLogs((state) => ({ ...state, [`dan ${index}`]: resp }));
            })
            .catch((error) => console.log(error));
        });
      })
      .catch((error) => {
        console.log(error);
      });
    jsonRpc("indexers")
      .then((resp) => {
        setIndexers(resp);
        Object.keys(resp).map((index) => {
          jsonRpc("get_logs", `indexer ${index}`)
            .then((resp) => {
              setLogs((state) => ({ ...state, [`indexer ${index}`]: resp }));
            })
            .catch((error) => console.log(error));
          jsonRpc("get_stdout", `indexer ${index}`)
            .then((resp) => {
              setStdoutLogs((state) => ({ ...state, [`indexer ${index}`]: resp }));
            })
            .catch((error) => console.log(error));
        });
      })
      .catch((error) => {
        console.log(error);
      });
    jsonRpc("http_connector")
      .then((resp) => {
        setConnectorSample(resp);
      })
      .catch((error) => {
        console.log(error);
      });
    jsonRpc("get_logs", "node").then((resp) => {
      setLogs((state) => ({ ...state, node: resp }));
    });
    jsonRpc("get_logs", "wallet").then((resp) => {
      setLogs((state) => ({ ...state, wallet: resp }));
    });
    jsonRpc("get_logs", "miner").then((resp) => {
      setLogs((state) => ({ ...state, miner: resp }));
    });
    jsonRpc("get_stdout", "node").then((resp) => {
      setStdoutLogs((state) => ({ ...state, node: resp }));
    });
    jsonRpc("get_stdout", "wallet").then((resp) => {
      setStdoutLogs((state) => ({ ...state, wallet: resp }));
    });
    jsonRpc("get_stdout", "miner").then((resp) => {
      setStdoutLogs((state) => ({ ...state, miner: resp }));
    });
    jsonRpc("grpc_node").then((resp) => setNode({ grpc: resp }));
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
      <div className="label">Base layer</div>
      <div className="infos">
        {ShowInfo("node", node, logs?.["node"], stdoutLogs?.["node"])}
        {ShowInfo("wallet", wallet, logs?.["wallet"], stdoutLogs?.["wallet"])}
        {ShowInfo("miner", null, logs?.["miner"], stdoutLogs?.["miner"], <button onClick={() => jsonRpc("mine", 1)}>Mine</button>)}
      </div>
      <div>
        <div className="label">Validator Nodes</div>
        {ShowInfos(vns, logs, stdoutLogs, "vn")}
      </div>
      <div>
        <div className="label">Dan Wallets</div>
        {ShowInfos(danWallet, logs, stdoutLogs, "dan")}
      </div>
      <div>
        <div className="label">Indexers</div>
        {ShowInfos(indexers, logs, stdoutLogs, "indexer")}
      </div>
      <div className="label">Templates</div>
      <div className="infos">
        {ShowInfo(
          null,
          null,
          null,
          null,
          <>
            <input type="file" onChange={handleFileChange} />
            <button onClick={handleFileUpload}>Upload template</button>
          </>
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
