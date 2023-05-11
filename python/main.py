import os
import logging
import pathlib
import hashlib
import json
from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [ os.environ.get('FRONT_URL', "http://localhost:3000") ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET","POST","PUT","DELETE"],
    allow_headers=["*"],
)



                  
@app.get("/")
def root():
    return {"message": "Hello, world!"}

@app.get("/items")
def get_items():
    # Load items.json
    try:
        with open('items.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


@app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = File(...)):
    logger.info(f"Receive item: {name}, category: {category}, image: {image.filename}")

    # hash image url and save image

    image_file = image.file.read()
    image_hash = hashlib.sha256(image_file).hexdigest()
    image_filename = f"{image_hash}.jpg"
    image_path = images / image_filename
    
    with open(image_path, 'wb') as f:
        f.write(image_file)
        
    
    # Load items.json
    try:
        with open('items.json', 'r') as f:
            items = json.load(f)
    except FileNotFoundError:
        items = {"items": []}

    # Append the new item to the list
    items['items'].append({"name": name, "category": category, "image": image_filename})

    # Save items.json
    with open('items.json', 'w') as f:
        json.dump(items, f)

    return {"message": f"item received: {name}, category: {category}, image: {image_filename} "}

@app.get("/image/{image_filename}")
async def get_image(image_filename):
    # Create image path
    image = images / image_filename

    if not image_filename.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)

@app.get("/items/{item_id}")
def get_item_withID(item_id:int):
    try:
        with open('items.json', 'r') as f:
            items = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return items['items'][item_id]