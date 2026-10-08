import "../styles/footer.css";

function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="footer">
      <div className="footer-container">
        <div>
          <h3>TensorForge 2.0</h3>

          <p>
            Customer Support Ticket Classification & Routing System
          </p>
        </div>

        <div className="footer-right">
          <span>Phase 2 — MVP</span>
          <span>© {currentYear} Team Project</span>
        </div>
      </div>
    </footer>
  );
}

export default Footer;