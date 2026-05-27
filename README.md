# 🛡️ AegisNet

### Adaptive Network Intrusion Detection System (IDS)

AegisNet is a machine learning–powered Intrusion Detection System designed to detect malicious network activity in real time using cybersecurity traffic analysis, threat simulation, and live monitoring dashboards.

Built using:

* **FastAPI** for backend APIs
* **React + Vite** for frontend dashboard
* **LightGBM / ML pipeline** for intrusion detection
* **WebSockets** for real-time monitoring
* **Chart.js** for live analytics visualization

---

# 🚀 Features

## ✅ Real-Time Threat Monitoring

* Live WebSocket-based monitoring stream
* Continuous threat probability updates
* Real-time attack analytics

## ✅ Machine Learning Intrusion Detection

* Binary malicious/benign traffic classification
* Trained on CIC-IDS2017 cybersecurity dataset
* Feature preprocessing + scaling pipeline
* Model versioning support

## ✅ Interactive Security Dashboard

* Threat probability gauge
* Live threat trend graph
* Attack distribution analytics
* Feature importance visualization
* Prediction history tracking

## ✅ Attack Simulation Engine

Simulate:

* DDoS attacks
* Botnet traffic
* Port scanning activity

Useful for:

* cybersecurity demonstrations
* SOC dashboard simulation
* IDS testing workflows

## ✅ Live Global Threat Feed

Simulated global attack monitoring:

* China → Botnet
* Russia → Port Scan
* USA → DDoS

Provides a Security Operations Center (SOC)-style monitoring experience.

## ✅ Authentication System

* User registration
* JWT authentication
* Login-protected dashboard

## ✅ Dataset Uploading

Upload datasets directly from the UI for future retraining workflows.

---

# 🧠 Tech Stack

| Layer          | Technology  |
| -------------- | ----------- |
| Frontend       | React, Vite |
| Backend        | FastAPI     |
| ML Framework   | LightGBM    |
| Database       | SQLite      |
| Realtime       | WebSockets  |
| Charts         | Chart.js    |
| Authentication | JWT         |
| Dataset        | CIC-IDS2017 |

---

# 📂 Project Structure

```bash
AegisNet/
│
├── backend/
│   ├── main.py
│   ├── model_loader.py
│   ├── predictor.py
│   └── schemas.py
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── training/
│   ├── preprocess.py
│   └── train_binary.py
│
├── models/
│   └── aegisnet_binary_*.pkl
│
├── data/
│   └── .gitkeep
│
├── requirements.txt
├── Dockerfile
└── README.md
```

---

# ⚙️ Installation

## 1️⃣ Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/AegisNet.git
cd AegisNet
```

---

## 2️⃣ Backend Setup

```bash
python -m venv venv
```

### Activate Virtual Environment

### Windows

```bash
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Backend

```bash
uvicorn backend.main:app --reload
```

Backend runs at:

```bash
http://localhost:8000
```

---

## 3️⃣ Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

```bash
http://localhost:5173
```

---

# 🧪 Training the Model

Run:

```bash
python training/train_binary.py
```

The trained model will be saved inside:

```bash
models/
```

---

# 📊 Dataset

This project uses the:

### CIC-IDS2017 Dataset

Contains:

* benign traffic
* DDoS attacks
* botnet traffic
* brute force attacks
* port scans
* infiltration traffic

---

# 🔐 Authentication

AegisNet uses:

* JWT access tokens
* password hashing
* protected API routes

---

# 🌍 Future Roadmap (v0.2.0)

Planned upgrades:

* autonomous threat intelligence engine
* geolocation-based attack mapping
* SIEM integrations
* anomaly detection
* explainable AI threat reasoning
* live packet capture support
* advanced SOC visualization
* multi-model ensemble detection
* Docker Compose deployment
* cloud deployment pipeline

---

# 📌 Current Version

```bash
v0.1.0
```

---

# 👨‍💻 Author

Vedant
Cybersecurity + AI/ML Developer

---

# ⚠️ Disclaimer

This project is intended for:

* educational purposes
* cybersecurity research
* IDS experimentation

Not intended for production enterprise deployment yet.
