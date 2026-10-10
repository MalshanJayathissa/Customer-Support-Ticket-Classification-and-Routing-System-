import { Link, useLocation } from "react-router-dom";
import "../styles/navbar.css";

function Navbar() {
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <nav className="navbar">

      <div className="navbar-brand">
        <Link to="/">
          TensorForge 2.0
        </Link>
      </div>

      <div className="navbar-links">

        <Link
          to="/"
          className={isActive("/") ? "active" : ""}
        >
          Home
        </Link>

        <Link
          to="/predict"
          className={isActive("/predict") ? "active" : ""}
        >
          Predict
        </Link>

        <Link
          to="/batch"
          className={isActive("/batch") ? "active" : ""}
        >
          Batch
        </Link>

        <Link
          to="/dashboard"
          className={isActive("/dashboard") ? "active" : ""}
        >
          Dashboard
        </Link>

        <Link
          to="/about"
          className={isActive("/about") ? "active" : ""}
        >
          About
        </Link>

      </div>

    </nav>
  );
}

export default Navbar;