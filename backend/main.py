from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import numpy as np
import faiss
import cv2
import os
import pickle
import tensorflow as tf
from tensorflow.keras.applications.inception_resnet_v2 import InceptionResNetV2, preprocess_input
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import Model
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change "*" to ["http://localhost:3000"] for stricter security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure image storage folder exists
IMAGE_FOLDER = "static/images"
FEATURES_FILE = "static/features.pkl"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/static/{image_name}")
async def get_image(image_name: str):
    image_path = f"static/images/{image_name}"
    return FileResponse(image_path)

@app.get("/")
async def root():
    return {"message": "Image Search API is running"}

# FAISS index for similarity search
index = faiss.IndexFlatL2(1536)

# Load Inception-ResNet-v2 model for feature extraction
physical_devices = tf.config.list_physical_devices('GPU')
if physical_devices:
    tf.config.experimental.set_memory_growth(physical_devices[0], True)

base_model = InceptionResNetV2(weights="imagenet", include_top=False, pooling="avg")
feature_extractor = Model(inputs=base_model.input, outputs=base_model.output)

def load_image_paths(folder):
    return [os.path.join(folder, img) for img in os.listdir(folder) if img.endswith((".jpg", ".png", ".jpeg"))]

def extract_features(image_path):
    img = image.load_img(image_path, target_size=(299, 299))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)
    with tf.device('/GPU:0'):
        features = feature_extractor.predict_on_batch(img_array)
    return features.reshape(1, -1).astype("float32")

def save_features():
    with open(FEATURES_FILE, "wb") as f:
        pickle.dump((image_db, feature_vectors), f)

def load_features():
    if os.path.exists(FEATURES_FILE):
        with open(FEATURES_FILE, "rb") as f:
            return pickle.load(f)
    return [], np.zeros((0, 1536), dtype="float32")

def sync_image_database():
    global image_db, feature_vectors, index
    current_images = load_image_paths(IMAGE_FOLDER)
    if set(current_images) != set(image_db):
        image_db = current_images
        feature_vectors = np.array([extract_features(img) for img in image_db])
        if len(feature_vectors) > 0:
            feature_vectors = np.vstack(feature_vectors)
        else:
            feature_vectors = np.zeros((0, 1536), dtype="float32")
        index.reset()
        if feature_vectors.size > 0:
            index.add(feature_vectors)
        save_features()

image_db, feature_vectors = load_features()
sync_image_database()

if feature_vectors.size > 0:
    index.add(feature_vectors)

@app.post("/search")
async def search(file: UploadFile = File(...)):
    file_path = os.path.join(IMAGE_FOLDER, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    
    # Perform similarity search
    query_vector = extract_features(file_path)
    distances, indices = index.search(query_vector, 5)
    
    # Set a similarity threshold (adjust as needed)
    similarity_threshold = 500  # Lower values mean higher similarity
    similar_images = [os.path.basename(image_db[i]) for i, d in zip(indices[0], distances[0]) if i < len(image_db) and d < similarity_threshold]
    
    if not similar_images:
        return JSONResponse({"similar_images": []})
    
    return JSONResponse({"similar_images": similar_images})
