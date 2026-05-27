from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    WebSocket,
    BackgroundTasks,
    UploadFile,
    File
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from pydantic import BaseModel

import pandas as pd
import numpy as np
import joblib
import glob
import os
import asyncio
import random
import subprocess
import logging

# ---------------------------------------------------
# BASIC SETUP
# ---------------------------------------------------

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="AegisNet IDS")

@app.get("/")
def root():
    return {
        "service": "AegisNet IDS",
        "status": "running",
        "docs": "/docs"
    }

# ---------------------------------------------------
# GLOBAL STATE
# ---------------------------------------------------

training_status = "idle"

GLOBAL_ATTACKS = [
    {"country": "China", "attack": "Botnet"},
    {"country": "Russia", "attack": "Port Scan"},
    {"country": "USA", "attack": "DDoS"},
    {"country": "Brazil", "attack": "Botnet"},
    {"country": "India", "attack": "Port Scan"},
]

# ---------------------------------------------------
# CORS
# ---------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------
# DATABASE
# ---------------------------------------------------

DATABASE_URL = "sqlite:///./aegisnet.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)

class PredictionLog(Base):
    __tablename__ = "prediction_logs"
    id = Column(Integer, primary_key=True)
    user = Column(String)
    prediction = Column(String)
    probability = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ---------------------------------------------------
# AUTH
# ---------------------------------------------------

SECRET_KEY = "aegisnet-secret"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password):
    return pwd_context.hash(password)

def verify_password(password, hashed):
    return pwd_context.verify(password, hashed)

def create_token(username):
    expire = datetime.utcnow() + timedelta(minutes=30)
    return jwt.encode(
        {"sub": username, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")

    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(401)

    return username

# ---------------------------------------------------
# MODEL LOADING
# ---------------------------------------------------

MODEL_DIR = os.path.join(
    os.path.dirname(__file__),
    "../models"
)

model_files = glob.glob(
    os.path.join(MODEL_DIR, "aegisnet_binary_*.pkl")
)

model = None
threshold = 0.5
selector = None
scaler = None
features = []

if model_files:

    latest_model = max(model_files, key=os.path.getctime)

    logging.info(f"Loading model: {latest_model}")

    bundle = joblib.load(latest_model)

    model = bundle["model"]
    threshold = bundle["threshold"]
    selector = bundle["selector"]
    scaler = bundle["scaler"]
    features = bundle["features"]

# ---------------------------------------------------
# SCHEMAS
# ---------------------------------------------------

class FlowFeatures(BaseModel):
    data: dict

class RegisterUser(BaseModel):
    username: str
    password: str

# ---------------------------------------------------
# USER ENDPOINTS
# ---------------------------------------------------

@app.post("/register")
def register(user: RegisterUser, db: Session = Depends(get_db)):

    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(400, "User exists")

    db_user = User(
        username=user.username,
        hashed_password=hash_password(user.password)
    )

    db.add(db_user)
    db.commit()

    return {"message": "User created"}

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.username == form_data.username
    ).first()

    if not user or not verify_password(
        form_data.password,
        user.hashed_password
    ):
        raise HTTPException(401)

    token = create_token(user.username)

    return {"access_token": token}

# ---------------------------------------------------
# ANALYTICS
# ---------------------------------------------------

@app.get("/analytics/history")
def analytics_history(db: Session = Depends(get_db)):

    logs = db.query(PredictionLog).all()

    return [
        {
            "timestamp": log.timestamp,
            "prediction": log.prediction,
            "probability": log.probability
        }
        for log in logs
    ]

# ---------------------------------------------------
# FEATURE IMPORTANCE
# ---------------------------------------------------

@app.get("/model/feature-importance")
def feature_importance():

    try:

        if model is None:
            return {}

        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        else:
            return {}

        length = min(len(features), len(importances))

        data = dict(
            sorted(
                zip(features[:length], importances[:length]),
                key=lambda x: x[1],
                reverse=True
            )[:20]
        )

        return data

    except Exception as e:

        print("Feature importance error:", e)

        return {}

# ---------------------------------------------------
# TRAIN MODEL
# ---------------------------------------------------

def retrain_model():

    global training_status

    training_status = "training"

    subprocess.run(["python", "training/train_binary.py"])

    training_status = "completed"

@app.post("/model/retrain")
def retrain(background_tasks: BackgroundTasks):

    background_tasks.add_task(retrain_model)

    return {"message": "training started"}

@app.get("/model/training-status")
def training_status_api():

    return {"status": training_status}

# ---------------------------------------------------
# SIMULATION
# ---------------------------------------------------

@app.get("/simulate/{attack_type}")
def simulate_attack(attack_type: str):

    prob = random.random()

    pred = "MALICIOUS" if prob >= threshold else "BENIGN"

    return {
        "attack_type": attack_type,
        "prediction": pred,
        "probability": prob
    }

# ---------------------------------------------------
# GLOBAL ATTACK MAP
# ---------------------------------------------------

@app.get("/global-attacks")
def global_attacks():

    attack = random.choice(GLOBAL_ATTACKS)

    return {
        "country": attack["country"],
        "attack": attack["attack"],
        "time": datetime.utcnow()
    }

# ---------------------------------------------------
# DATASET UPLOAD
# ---------------------------------------------------

@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):

    DATA_DIR = os.path.join(
        os.path.dirname(__file__),
        "../data"
    )

    os.makedirs(DATA_DIR, exist_ok=True)

    path = os.path.join(DATA_DIR, file.filename)

    with open(path, "wb") as f:
        f.write(await file.read())

    return {"message": "Dataset uploaded"}

# ---------------------------------------------------
# LIVE STREAM
# ---------------------------------------------------

@app.websocket("/stream")
async def stream_predictions(websocket: WebSocket):

    await websocket.accept()

    try:

        while True:

            prob = random.random()

            pred = "MALICIOUS" if prob >= threshold else "BENIGN"

            await websocket.send_json({
                "prediction": pred,
                "probability": prob
            })

            await asyncio.sleep(2)

    except Exception:
        logging.info("WebSocket disconnected")