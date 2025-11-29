import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

class EfficientDeconstructionModel:
    """Efficient model to select optimal deconstruction method for e-waste"""
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
        self.feature_names = []
        self.deconstruction_methods = [
            "Automated_Shredding",
            "Manual_Disassembly_General",
            "Manual_Disassembly_Battery_Safe",
            "Robotic_Screen_Removal",
            "Circuit_Board_Preprocessing",
            "Hazmat_Specialized_Handling"
        ]
        self.materials = [
            'ABS_Plastic', 'PVC_Plastic', 'Aluminum', 'Copper', 'Steel',
            'Lithium_Battery', 'Lead_Battery', 'Circuit_Boards',
            'LCD_Screen', 'CRT_Glass', 'Lead_Components', 'Mercury_Components'
        ]
        self.device_categories = ['Laptop', 'Smartphone', 'Desktop', 'Tablet', 'Monitor', 'Printer', 'Router', 'Gaming_Console', 'Other']
        self.hazard_levels = ['Low', 'Medium', 'High']

    def prepare_features(self, device_category, materials, hazard_level):
        features = []
        for cat in self.device_categories:
            features.append(1 if device_category==cat else 0)
        for level in self.hazard_levels:
            features.append(1 if hazard_level==level else 0)
        for material in self.materials:
            features.append(materials.get(material,0))
        return np.array(features).reshape(1,-1)

    def predict(self, device_category, materials, hazard_level):
        features = self.prepare_features(device_category, materials, hazard_level)
        pred = self.model.predict(features)[0]
        conf = np.max(self.model.predict_proba(features)[0])
        # Get top 3 alternative methods
        probs = self.model.predict_proba(features)[0]
        alt_methods = list(zip(self.model.classes_, probs))
        alt_methods.sort(key=lambda x:x[1], reverse=True)
        alt_methods = [{"method":m, "probability":p} for m,p in alt_methods[:3]]
        return {"recommended_method": pred, "confidence": conf, "alternative_methods": alt_methods}

    def load_model(self, filepath="models/efficient_deconstruction_model.pkl"):
        data = joblib.load(filepath)
        self.model = data["model"]
        self.feature_names = data["feature_names"]
        self.materials = data["materials"]
        self.device_categories = data["device_categories"]
        self.hazard_levels = data["hazard_levels"]
        self.deconstruction_methods = data["deconstruction_methods"]
