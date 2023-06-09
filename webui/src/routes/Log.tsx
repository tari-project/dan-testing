import React, { useEffect, useState } from "react";
import { useParams } from "react-router";
import { jsonRpc } from "../utils/json_rpc";

export default function Log() {
  const { name } = useParams<{ name: string }>();
  const { format } = useParams<{ format: string }>();
  const [content, setContent] = useState(undefined);
  useEffect(() => {
    jsonRpc("get_file", atob(name))
      .then((resp) => {
        console.log(format)
        if (format == "normal") {
          resp = resp.replace(/(\d{4}-\d{2}-\d{2} \d+:\d{2}:\d{2}.\d+)/gi, '<span class="time">$1</span>')
          resp = resp.replace(/(\[tari::.*?\])/gi, '<span class="target">$1</span>')
        } else {
          resp = resp.replace(/\n(\d+:\d+)/gi, '\n<span class="time">$1</span>')
        }
        resp = resp.replace(/(INFO|ERROR|WARN|DEBUG)/g, '<span class="$1">$1</span>')
        resp = resp.replace(/\/\/ (.*)/gi, '// <span class="file">$1</span>')
        setContent(resp);
      })
      .catch((error) => {
        console.log("error", error);
      });
  }, []);
  if (content === undefined) {
    return <div>Loading file</div>
  }
  if (content === "") {
    return <div>File is empty</div>
  }
  return (
    < pre
      dangerouslySetInnerHTML={{
        __html: content,
      }
      }
    />
  );
}
