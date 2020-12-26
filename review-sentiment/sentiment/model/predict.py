import uuid
from typing import List

import torch
from pydantic import BaseModel
from transformers import BertForSequenceClassification, BertTokenizer

from .model import get


class Prediction(BaseModel):
    prediction_id: uuid.UUID
    prediction: List[float]


def predict(text: str,
            model: BertForSequenceClassification = get.model,
            tokenizer: BertTokenizer = get.tokenizer) -> Prediction:
    model_input = torch.tensor([tokenizer.encode(text, add_special_tokens=False)], dtype=torch.int64)
    model_output = model(model_input)
    prediction = torch.softmax(model_output[0], dim=1)

    print(prediction)

    return Prediction(prediction_id=uuid.uuid4(),
                      prediction=list(map(float, prediction[0].tolist())))