import os, cv2, time, threading, numpy as np
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from tensorflow.keras.models import load_model 
from ultralytics import YOLO
from datetime import datetime
from materials_utils import create_lookup_table, get_component_materials
from deconstruction_model import EfficientDeconstructionModel

# -----------------------------
# Config
# -----------------------------
IMG_SIZE = 224
CONF_THRESHOLD = 0.7
CLASS_INDICES = {"E-waste": 0, "Non-E-waste": 1}
CAPTURE_INTERVAL = 10  # seconds
UPLOAD_FOLDER = "static/uploads"
LOG_FILE = "detection_log.csv"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------
# Load models
# -----------------------------
model1 = load_model("models/ewaste_resnet50_model2.h5", compile=False)
model2 = YOLO("models/ewaste_yolov8_model.pt")
lookup_table = create_lookup_table()
decon_model = EfficientDeconstructionModel()
decon_model.load_model("models/efficient_deconstruction_model.pkl")

# -----------------------------
# FastAPI setup
# -----------------------------
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# -----------------------------
# Utility functions
# -----------------------------
def predict_ewaste(frame):
    img = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
    img_array = np.expand_dims(img, axis=0) / 255.0
    preds = model1.predict(img_array, verbose=0)
    conf = preds[0][CLASS_INDICES["E-waste"]]
    return ("E-waste" if conf >= CONF_THRESHOLD else "Non-E-waste", float(conf))

def predict_component(frame):
    results = model2.predict(frame, imgsz=224, conf=0.25, verbose=False)
    if not results:
        return "N/A", 0.0
    r = results[0]
    probs = r.probs
    top1 = probs.top1
    comp_name = r.names[top1]
    conf = float(probs.top1conf.item())
    return comp_name, conf

def predict_deconstruction(component, mat_info):
    materials = {mat: 1 for mat in mat_info.get("materials", [])}
    hazard = "High" if mat_info.get("hazard", 0) >= 2 else ("Medium" if mat_info.get("hazard", 0) == 1 else "Low")
    device_category = component if component != "N/A" else "Other"
    return decon_model.predict(device_category, materials, hazard)

def log_detection(data: dict):
    """Append detection results to CSV log"""
    header = ["timestamp","category","ewaste_conf","component","component_conf",
              "hazardous_level","materials","recommended_method","confidence","alternative_methods"]
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write(",".join(header) + "\n")
    with open(LOG_FILE, "a") as f:
        row = [
            data["timestamp"],
            data["category"],
            str(data["ewaste_confidence"]),
            data["component"],
            str(data["component_confidence"]),
            str(data["hazardous_level"]),
            "|".join(data["materials"]),
            data["deconstruction_method"]["recommended_method"],
            str(data["deconstruction_method"]["confidence"]),
            "|".join([m["method"] for m in data["deconstruction_method"]["alternative_methods"]])
        ]
        f.write(",".join(row) + "\n")

# -----------------------------
# Live camera + detection loop
# -----------------------------
cap = cv2.VideoCapture(1)
latest_result = {}  # shared between threads

def capture_loop():
    global latest_result
    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Camera not accessible")
            break

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        category, e_conf = predict_ewaste(frame)

        if category == "E-waste":
            component, comp_conf = predict_component(frame)
            mat_info = get_component_materials(component, lookup_table)
            decon_result = predict_deconstruction(component, mat_info)
        else:
            component, comp_conf = "N/A", 0.0
            mat_info = {"materials": [], "hazard": 0}
            decon_result = {"recommended_method": "N/A", "confidence": 0.0, "alternative_methods": []}

        latest_result = {
            "timestamp": timestamp,
            "category": category,
            "ewaste_confidence": round(e_conf * 100, 2),
            "component": component,
            "component_confidence": round(comp_conf * 100, 2),
            "hazardous_level": int(mat_info["hazard"]),
            "materials": mat_info["materials"],
            "deconstruction_method": {
                "recommended_method": decon_result["recommended_method"],
                "confidence": decon_result["confidence"],
                "alternative_methods": decon_result["alternative_methods"]
            }
        }

        log_detection(latest_result)
        print(f"[{timestamp}] {latest_result}")

        time.sleep(CAPTURE_INTERVAL)

threading.Thread(target=capture_loop, daemon=True).start()

# -----------------------------
# Video streaming generator
# -----------------------------
def gen_frames():
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Overlay detection label if available
        if latest_result:
            label = f"{latest_result['category']} ({latest_result['ewaste_confidence']}%)"
            if latest_result['component'] != "N/A":
                label += f" | {latest_result['component']} ({latest_result['component_confidence']}%)"
            cv2.putText(frame, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 255, 0) if "E-waste" in label else (0, 0, 255), 2)

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# -----------------------------
# Routes
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("dashboard2.html", {"request": request})

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(gen_frames(),
                             media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/latest_result")
async def latest_result_api():
    """Return latest detection info for dashboard live update"""
    if not latest_result:
        return JSONResponse(content={"status": "no data"})
    return JSONResponse(content=latest_result)

@app.get("/logs")
async def get_logs():
    if not os.path.exists(LOG_FILE):
        return JSONResponse(content={"logs": []})
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()
    return JSONResponse(content={"logs": lines})
if __name__ == "_main_":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5001, reload=True)
