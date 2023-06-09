import "./App.css";
import { Outlet, Route, Routes } from "react-router";
import Main from "./routes/Main";
import Log from "./routes/Log";


function App() {
  return (
    <div>
      <Routes>
        <Route path="/" element={<Outlet />}>
          <Route index element={<Main />} />
          <Route path="log/:name/:format" element={<Log />} />
          <Route path="*" element={<div>Error</div>} />
        </Route >
      </Routes >
    </div>
  );
}

export default App;
