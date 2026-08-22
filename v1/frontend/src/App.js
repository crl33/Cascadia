import { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "@/pages/Dashboard";
import Roadmap from "@/pages/Roadmap";

function App() {
    useEffect(() => {
        // Force dark cinematic mode globally
        document.documentElement.classList.add("dark");
        document.documentElement.style.colorScheme = "dark";
    }, []);

    return (
        <div className="App">
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/roadmap" element={<Roadmap />} />
                </Routes>
            </BrowserRouter>
        </div>
    );
}

export default App;
