import { motion } from "framer-motion";
import { FiWifi, FiGithub } from "react-icons/fi";
import "../styles/layout.css";

export default function Footer() {
  return (
    <motion.footer
      className="footer glass"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
    >
      <div className="footer-brand">
        <span className="footer-logo"><FiWifi /></span>
        <div>
          <strong>Smart WiFi Bandwidth Sharing</strong>
          <p className="text-dim">Game Theory based fair bandwidth allocation system</p>
        </div>
      </div>

      <div className="footer-credits">
        <span>Developed by</span>
        <div className="footer-names">
          <span className="dev-chip">👨‍💻 Sujeetha</span>
          
        </div>
        
      </div>

      <div className="footer-links">
        <a href="https://github.com/sujeethas2024-netizen/smart-wifi-bandwidth-sharing" target="_blank" rel="noreferrer" title="GitHub">
          <FiGithub />
        </a>
      </div>
    </motion.footer>
  );
}