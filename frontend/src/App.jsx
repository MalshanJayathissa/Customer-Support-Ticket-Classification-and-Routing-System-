import { BrowserRouter, Routes, Route } from "react-router-dom";

import Navbar from "./components/Navbar";
import Footer from "./components/Footer";

import Home from "./pages/Home";
import Predict from "./pages/Predict";
import BatchPredict from "./pages/BatchPredict";
import Dashboard from "./pages/Dashboard";
import About from "./pages/About";

import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">

        <Navbar />

        <div className="app-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/predict" element={<Predict />} />
            <Route path="/batch" element={<BatchPredict />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </div>

        <Footer />

      </div>
    </BrowserRouter>
  );
}

export default App;