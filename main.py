import os, cv2, numpy as np
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from tensorflow.keras.models import load_model
from ultralytics import YOLO
from materials_utils import create_lookup_table, get_component_materials
from deconstruction_model import EfficientDeconstructionModel

IMG_SIZE = 224
CONF_THRESHOLD = 0.7
CLASS_INDICES = {"E-waste": 0, "Non-E-waste": 1}

# Load models
model1 = load_model("models/ewaste_resnet50_model2.h5", compile=False)
model2 = YOLO("models/ewaste_yolov8_model.pt")
lookup_table = create_lookup_table()
decon_model = EfficientDeconstructionModel()
decon_model.load_model("models/efficient_deconstruction_model.pkl")

# FastAPI setup
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------
# Utility functions
# -----------------------------
async def read_imagefile(file: UploadFile) -> np.ndarray:
    contents = await file.read()  # ✅ await file read
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image")
    return img

def predict_ewaste(frame):
    img = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
    img_array = np.expand_dims(img, axis=0)/255.0
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

# -----------------------------
# Routes
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        frame = await read_imagefile(file)
        save_path = os.path.join(UPLOAD_FOLDER, file.filename)
        cv2.imwrite(save_path, frame)

        category, e_conf = predict_ewaste(frame)

        if category == "E-waste":
            component, comp_conf = predict_component(frame)
            mat_info = get_component_materials(component, lookup_table)
            decon_result = predict_deconstruction(component, mat_info)
        else:
            component, comp_conf = "N/A", 0.0
            mat_info = {"materials": [], "hazard": 0}
            decon_result = {"recommended_method": "N/A", "confidence": 0.0, "alternative_methods": []}

        return JSONResponse(content={
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
            },
            "image_url": f"/static/uploads/{file.filename}"
        })

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
if __name__ == "_main_":
    import uvicorn
    uvicorn.run("main2:app", host="127.0.0.1", port=5002, reload=True)
