import { useEffect, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function App() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/health`)
      .then((res) => res.json())
      .then(setHealth)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>URL Shortener</h1>
      <p>Milestone 0 scaffolding — this page just proves the frontend can reach the backend.</p>
      {error && <p style={{ color: "red" }}>Failed to reach API: {error}</p>}
      {health && <pre>{JSON.stringify(health, null, 2)}</pre>}
    </div>
  );
}
