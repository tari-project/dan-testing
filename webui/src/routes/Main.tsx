import React, { useEffect, useState } from 'react'
import { jsonRpc } from '../utils/json_rpc';

function ShowInfo(index, node, log, stdoutLog) {
  console.log(node)
  return (
    <div className="info" key={index}>
      <div><pre></pre><b>Index</b>{index}</div>
      <div><b>HTTP</b><a href={`http://${node.http}`}>{`http://${node.http}`}</a></div>
      <div><b>JRPC</b><span className='select'>http://{node.jrpc}</span></div>
      <div>
        <b>Logs</b>
        <div>{log?.map((e) => <div><a href={`log/${btoa(e[0])}/normal`}>{e[1]} - {e[2]}</a></div>)}</div>
      </div>
      <div>
        <div>{stdoutLog?.map((e) => <div><a href={`log/${btoa(e[0])}/stdout`}>stdout</a></div>)}</div>
      </div>
    </div >
  );
}

function ShowInfos(nodes, logs, stdoutLogs, name) {
  return (
    <div className='infos'>
      {Object.keys(nodes).map((index) =>
        ShowInfo(index, nodes[index], logs?.[`${name} ${index}`], stdoutLogs?.[`${name} ${index}`])
      )}
    </div>
  );
}

export default function Main() {
  const [vns, setVns] = useState({});
  const [danWallet, setDanWallets] = useState({});
  const [indexers, setIndexers] = useState({});
  const [logs, setLogs] = useState({});
  const [stdoutLogs, setStdoutLogs] = useState({});

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
  }, []);
  return (
    <div className="main">
      <div><div className="label">Validator Nodes</div>
        {ShowInfos(vns, logs, stdoutLogs, "vn")}
      </div>
      <div><div className="label">Dan Wallets</div>
        {ShowInfos(danWallet, logs, stdoutLogs, "dan")}
      </div>
      <div><div className="label">Indexers</div>
        {ShowInfos(indexers, logs, stdoutLogs, "indexer")}
      </div>
    </div>
  );
}
