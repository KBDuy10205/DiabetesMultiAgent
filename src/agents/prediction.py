from __future__ import annotations

import math
from pathlib import Path

FEATURES = ('Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age')
DEFAULT_MODEL = Path(__file__).resolve().parents[2] / 'output/model/diabetes_pipeline.joblib'


class PredictionAgent:
    """Input: one feature dict. Output: label, probability and model limitations."""

    def __init__(self, model_path=DEFAULT_MODEL, loader=None):
        self.model_path, self.loader = model_path, loader

    def run(self, features: dict) -> dict:
        if not isinstance(features, dict) or set(features) != set(FEATURES):
            raise ValueError(f'Expected exactly these features: {", ".join(FEATURES)}')
        for value in features.values():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError('Features must be finite non-negative numbers')
        import pandas as pd
        if self.loader is None:
            import joblib
            loader = joblib.load
        else:
            loader = self.loader
        model = loader(self.model_path)
        if list(model.classes_) != [0, 1]:
            raise ValueError('Model must expose binary classes [0, 1]')
        frame = pd.DataFrame([features], columns=FEATURES)
        probability = float(model.predict_proba(frame)[0][1])
        label = int(model.predict(frame)[0])
        if not math.isfinite(probability) or not 0 <= probability <= 1 or label not in (0, 1):
            raise ValueError('Invalid model output')
        return {'label': label, 'probability': probability, 'model': 'Pima pipeline',
                'limitation': 'Thử nghiệm học tập trên Pima; chưa xác nhận lâm sàng, không phải chẩn đoán.'}
