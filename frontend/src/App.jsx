import { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";

import { Line, Pie, Bar } from "react-chartjs-2";

import {
  Chart as ChartJS,
  LineElement,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend
} from "chart.js";

ChartJS.register(
  LineElement,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend
);

function App() {

  const API = "http://localhost:8000";

  const [token, setToken] = useState(null);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isSignup, setIsSignup] = useState(false);

  const [result, setResult] = useState(null);
  const [liveData, setLiveData] = useState([]);

  const [history, setHistory] = useState([]);
  const [featureImportance, setFeatureImportance] = useState({});

  const [connected, setConnected] = useState(false);
  const [trainingStatus, setTrainingStatus] = useState("");

  const [globalAttack, setGlobalAttack] = useState(null);

  const wsRef = useRef(null);

  // ------------------------
  // GLOBAL ATTACK FEED
  // ------------------------

  useEffect(() => {

    const interval = setInterval(async () => {

      try {

        const res = await axios.get(`${API}/global-attacks`);

        setGlobalAttack(res.data);

      } catch {}

    }, 4000);

    return () => clearInterval(interval);

  }, []);

  // ------------------------
  // LOGIN
  // ------------------------

  const login = async () => {

    try {

      const form = new URLSearchParams();
      form.append("username", username);
      form.append("password", password);

      const res = await axios.post(`${API}/login`, form);

      setToken(res.data.access_token);

    } catch (err) {

      console.error(err);
      alert("Login failed");

    }

  };

  // ------------------------
  // SIGN UP
  // ------------------------

const signup = async () => {

  try {

    await axios.post(`${API}/register`, {
      username,
      password
    });

    // auto login after signup

    const form = new URLSearchParams();

    form.append("username", username);
    form.append("password", password);

    const loginRes = await axios.post(
      `${API}/login`,
      form
    );

    setToken(loginRes.data.access_token);

  } catch (err) {

    console.error(err);

    alert("Signup failed");

  }

};

  // ------------------------
  // LOAD ANALYTICS
  // ------------------------

  const loadAnalytics = async () => {

    if (!token) return;

    try {

      const headers = {
        Authorization: `Bearer ${token}`
      };

      const historyRes = await axios.get(
        `${API}/analytics/history`,
        { headers }
      );

      const featureRes = await axios.get(
        `${API}/model/feature-importance`,
        { headers }
      );

      setHistory(historyRes.data || []);
      setFeatureImportance(featureRes.data || {});

    } catch (e) {

      console.error("Analytics load failed", e);

    }

  };

  useEffect(() => {

    if (token) loadAnalytics();

  }, [token]);

  // ------------------------
  // LIVE MONITORING
  // ------------------------

  const startMonitoring = () => {

    if (connected) return;

    wsRef.current = new WebSocket(`${API.replace("http","ws")}/stream`);

    wsRef.current.onopen = () => {
      setConnected(true);
    };

    wsRef.current.onmessage = (event) => {

      const data = JSON.parse(event.data);

      setLiveData(prev => {
        const updated = [...prev, data.probability];
        return updated.slice(-20);
      });

      setResult(data);

    };

    wsRef.current.onclose = () => {
      setConnected(false);
      wsRef.current = null;
    };

  };

  const stopMonitoring = () => {

    if (wsRef.current) wsRef.current.close();

  };

  // ------------------------
  // TRAIN MODEL
  // ------------------------

  const retrainModel = async () => {

    try {

      const headers = {
        Authorization: `Bearer ${token}`
      };

      setTrainingStatus("Training started...");

      await axios.post(
        `${API}/model/retrain`,
        {},
        { headers }
      );

      setTrainingStatus("Training running in background");

      setTimeout(loadAnalytics, 5000);

    } catch {

      setTrainingStatus("Training failed");

    }

  };

  // ------------------------
  // ATTACK SIMULATION
  // ------------------------

  const simulateAttack = async (type) => {

    try {

      const headers = {
        Authorization: `Bearer ${token}`
      };

      const res = await axios.get(
        `${API}/simulate/${type}`,
        { headers }
      );

      setResult(res.data);

      setLiveData(prev => {
        const updated = [...prev, res.data.probability];
        return updated.slice(-20);
      });

      loadAnalytics();

    } catch {

      alert("Simulation failed");

    }

  };

  // ------------------------
  // DATASET UPLOAD
  // ------------------------

  const uploadDataset = async (event) => {

    try {

      const file = event.target.files[0];

      const formData = new FormData();
      formData.append("file", file);

      const headers = {
        Authorization: `Bearer ${token}`,
        "Content-Type": "multipart/form-data"
      };

      await axios.post(
        `${API}/upload`,
        formData,
        { headers }
      );

      alert("Dataset uploaded successfully");

    } catch {

      alert("Upload failed");

    }

  };

  // ------------------------
  // CHART DATA
  // ------------------------

  const lineChart = {

    labels: liveData.map((_, i) => i),

    datasets: [
      {
        label: "Malicious Probability",
        data: liveData,
        borderColor: "#ef4444",
        tension: 0.3
      }
    ]

  };

  const maliciousCount = history.filter(
    h => h.prediction === "MALICIOUS"
  ).length;

  const benignCount = history.length - maliciousCount;

  const pieData = {

    labels: ["Malicious", "Benign"],

    datasets: [
      {
        data: [maliciousCount, benignCount],
        backgroundColor: ["#ef4444", "#22c55e"]
      }
    ]

  };

  const featureNames = Object.keys(featureImportance || {});
  const featureValues = Object.values(featureImportance || {});

  const featureChart = {

    labels: featureNames,

    datasets: [
      {
        label: "Feature Importance",
        data: featureValues,
        backgroundColor: "#f59e0b"
      }
    ]

  };

  const probabilityPercent = result
    ? Math.round(result.probability * 100)
    : 0;

  const gaugeColor =
    probabilityPercent > 70 ? "#ef4444"
    : probabilityPercent > 40 ? "#f59e0b"
    : "#22c55e";

  // ------------------------
  // LOGIN PAGE
  // ------------------------

  if (!token) {

  return (

    <div className="center-screen">

      <div className="login-card">

        <h2>
          {isSignup ? "Create Account" : "AegisNet Login"}
        </h2>

        <input
          placeholder="Username"
          onChange={e => setUsername(e.target.value)}
        />

        <input
          type="password"
          placeholder="Password"
          onChange={e => setPassword(e.target.value)}
        />

        {

          isSignup

          ?

          <button onClick={signup}>
            Sign Up
          </button>

          :

          <button onClick={login}>
            Login
          </button>

        }

        <p
          style={{
            marginTop: "15px",
            cursor: "pointer",
            color: "#38bdf8"
          }}
          onClick={() => setIsSignup(!isSignup)}
        >

          {

            isSignup

            ?

            "Already have an account? Login"

            :

            "No account? Sign Up"

          }

        </p>

      </div>

    </div>

  );

}

  // ------------------------
  // DASHBOARD
  // ------------------------

  return (

    <div className="dashboard-container">

      <h1>🛡 AegisNet Security Dashboard</h1>

      {/* CONTROLS */}

      <div className="control-bar">

        <button onClick={startMonitoring}>
          Start Monitoring
        </button>

        <button onClick={stopMonitoring}>
          Stop Monitoring
        </button>

        <button onClick={retrainModel}>
          Train Model
        </button>

        <input
          type="file"
          onChange={uploadDataset}
        />

      </div>

      <p>{trainingStatus}</p>

      {/* ATTACK SIMULATION */}

      <div className="control-bar">

        <button onClick={() => simulateAttack("ddos")}>
          Simulate DDoS
        </button>

        <button onClick={() => simulateAttack("botnet")}>
          Simulate Botnet
        </button>

        <button onClick={() => simulateAttack("portscan")}>
          Simulate Port Scan
        </button>

      </div>

      <h2>Status: {result?.prediction || "Waiting..."}</h2>

      {/* DASHBOARD GRID */}

      <div className="dashboard-grid">

        <div className="card">

          <h3>🌍 Global Attack Monitor</h3>

          {globalAttack && (

            <div>

              <p><b>Country:</b> {globalAttack.country}</p>
              <p><b>Attack:</b> {globalAttack.attack}</p>
              <p><b>Time:</b> {globalAttack.time}</p>

            </div>

          )}

        </div>

        <div className="card">

          <h3>Threat Probability</h3>

          <div
            className="gauge"
            style={{
              background:
              `conic-gradient(${gaugeColor} ${probabilityPercent * 3.6}deg,#ddd 0deg)`
            }}
          >

            {probabilityPercent}%

          </div>

        </div>

        <div className="card">

          <h3>Live Threat Chart</h3>

          <Line data={lineChart} />

        </div>

        <div className="card">

          <h3>Attack Distribution</h3>

          <Pie data={pieData} />

        </div>

        <div className="card">

          <h3>Feature Importance</h3>

          {featureNames.length > 0 && (
            <Bar data={featureChart} />
          )}

        </div>

      </div>

      {/* HISTORY */}

      <div className="card full-width">

        <h2>Prediction History</h2>

        <table>

          <thead>

            <tr>
              <th>Timestamp</th>
              <th>Prediction</th>
              <th>Probability</th>
            </tr>

          </thead>

          <tbody>

            {history.slice(-10).map((row, i) => (

              <tr key={i}>

                <td>{row.timestamp}</td>
                <td>{row.prediction}</td>
                <td>{row.probability.toFixed(3)}</td>

              </tr>

            ))}

          </tbody>

        </table>

      </div>

    </div>

  );

}

export default App;