import { Link } from "react-router-dom";
import "../styles/navbar.css";

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">TensorForge 2.0</Link>
      </div>

      <div className="navbar-links">
        <Link to="/">Home</Link>
        <Link to="/predict">Predict</Link>
        <Link to="/batch">Batch</Link>
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/about">About</Link>
      </div>
    </nav>
  );
}

export default Navbar;