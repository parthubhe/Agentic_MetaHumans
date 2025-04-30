import shutil
import torch
from transformers import AutoTokenizer, AutoModel
import os
#import numpy as np
#import random
class BERTClass(torch.nn.Module):
    def __init__(self):
        super(BERTClass, self).__init__()
        # Load the RoBERTa model from the local folder to avoid repeated downloads
        self.roberta = AutoModel.from_pretrained(r"D:\Metahuman Chatbot\Multiclass_Classifier\roberta-base")
        self.fc = torch.nn.Linear(768, 5)

    def forward(self, ids, mask, token_type_ids):
        _, features = self.roberta(ids, attention_mask=mask, token_type_ids=token_type_ids, return_dict=False)
        output = self.fc(features)
        return output


# Instantiate and load the trained emotion model
emotion_model = BERTClass()
MODEL_PATH = r"D:\Metahuman Chatbot\Multiclass_Classifier\MulticlassSentimentClassifier_files\model.bin"
emotion_model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu')))

# Load the tokenizer from the local folder
emotion_tokenizer = AutoTokenizer.from_pretrained(r"D:\Metahuman Chatbot\Multiclass_Classifier\roberta-base")

# Mapping from classifier output indices to emotion labels
classifier_class_names = {
    0: "Anger",
    1: "Fear",
    2: "Joy",
    3: "Sadness",
    4: "Surprise"
}


def analyze_text_emotion(text):
    encoding = emotion_tokenizer.encode_plus(
        text,
        add_special_tokens=True,
        max_length=128,
        truncation=True,
        padding='max_length',
        return_tensors='pt'
    )
    input_ids = encoding['input_ids']
    attention_mask = encoding['attention_mask']
    token_type_ids = encoding.get('token_type_ids')
    if token_type_ids is None:
        token_type_ids = torch.zeros_like(input_ids)

    emotion_model.eval()
    with torch.no_grad():
        outputs = emotion_model(input_ids, attention_mask, token_type_ids)

    probabilities = torch.sigmoid(outputs)
    predicted_probabilities = probabilities.tolist()[0]
    predicted_probabilities_dict = {
        classifier_class_names[i]: predicted_probabilities[i]
        for i in range(len(classifier_class_names))
    }
    return predicted_probabilities_dict


def predict_emotion(text):
    prob_dict = analyze_text_emotion(text)
    predicted_label = max(prob_dict, key=prob_dict.get)
    return prob_dict, predicted_label


def generate_emotion_payload_from_probabilities(prob_dict):
    mapping = {
        "Anger": "anger",
        "Fear": "fear",
        "Joy": "joy",
        "Sadness": "sadness",
        "Surprise": "amazement"
    }
    emotions_payload = {
        "amazement": 0,
        "anger": 0,
        "cheekiness": 0,
        "disgust": 0,
        "fear": 0,
        "grief": 0,
        "joy": 0,
        "outofbreath": 0,
        "pain": 0,
        "sadness": 0,
    }
    for key, a2f_key in mapping.items():
        if key in prob_dict:
            emotions_payload[a2f_key] = prob_dict[key]
    payload = {
        "a2f_instance": "/World/audio2face/CoreFullface",
        "emotions": emotions_payload,
    }
    return payload

