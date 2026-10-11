import { useEffect, useState } from 'react';
import { checkHealth } from '../services/api';

export default function Navbar() {
  const [status, setStatus] = useState('checking');

  useEffect(() => {
    checkHealth()
      .then((r) => setStatus(r.status === 'mock' ? 'mock' : 'online'))
      .catch(() => setStatus('offline'));
  }, []);

  const labels = {
    checking: 'Checking server…',
    online: 'Server connected',
    offline: 'Server not reachable',
    mock: 'Demo data mode',
  };

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <div>
          <h1 className="brand">FormScan-Lite</h1>
          <p className="tagline">Read government documents in your language</p>
        </div>
        <span className={`status status-${status}`}>{labels[status]}</span>
      </div>
    </header>
  );
}
