import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { initMonitoring } from "./utils/monitoring";

initMonitoring();

createRoot(document.getElementById("root")!).render(<App />);
