import os
import logging
import pathlib
import hashlib
import json
import sqlite3
from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(debug = True)
logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
dbpath = pathlib.Path(__file__).parent.resolve() / "db" / "mercari.sqlite3"
origins = [ os.environ.get('FRONT_URL', "http://localhost:3000") ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET","POST","PUT","DELETE"],
    allow_headers=["*"],
)

conn = sqlite3.connect(dbpath)

# create the item table
def create_items_table(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_id INTEGER,
            image_filename TEXT NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    """)
    conn.commit()

def create_category_table(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    conn.commit()

# creaste the tables
create_category_table(conn) 
create_items_table(conn)



                  
@app.get("/")
def root():
    return {"message": "Hello, world!"}

@app.get("/items")
def get_items():
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()
    cursor.execute(("""
        SELECT items.id, items.name, category.name, items.image_filename
        FROM items
        INNER JOIN category ON items.category_id = category.id
    """))
    items = cursor.fetchall()
    list_items = []
    for i in items:
        item = {
            "id": i[0],
            "name": i[1],
            "category": i[2],
            "image_filename": i[3]
        }
        list_items.append(item)
        
    return {"items": list_items}


@app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = File(...)):
    logger.info(f"Receive item: {name}, category: {category}, image: {image.filename}")
    
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()
    
    # hash image url and save image

    image_file = image.file.read()
    image_hash = hashlib.sha256(image_file).hexdigest()
    image_filename = f"{image_hash}.jpg"
    image_path = images / image_filename
    
    with open(image_path, 'wb') as f:
        f.write(image_file)
        
    
    cursor.execute("SELECT id FROM category WHERE name = ?", (category,))
    category_id = cursor.fetchone()
    if category_id is None:
        try:
            cursor.execute("INSERT INTO category (name) VALUES (?)", (category,))
            conn.commit()
            category_id = cursor.fetchone()[0]
        except sqlite3.IntegrityError:
            cursor.execute("SELECT id FROM category WHERE name = ?", (category,))
            category_id = cursor.fetchone()[0]
    else:
        category_id = category_id[0]
    
    # Insert item into items table
    cursor.execute("INSERT INTO items (name, category_id, image_filename) VALUES (?, ?, ?)",
                   (name, category_id, image_filename,))
    conn.commit()

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
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    items = cursor.fetchone()
    
    if items is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"item": items[0], "name": items[1], "category": items[2], "image": items[3]}

@app.get("/search")
def search_item(keyword: str):
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()
    keyword_search = f"%{keyword}%"
    cursor.execute('''
        SELECT items.id, items.name, category.name, items.image_filename
        FROM items
        INNER JOIN category ON items.category_id = category.id 
        WHERE items.name LIKE ?
                   ''', (keyword_search,))
    items = cursor.fetchall()
    
    list_items = []
    for i in items:
        item = {
            "id": i[0],
            "name": i[1],
            "category": i[2],
            "image_filename": i[3]
        }
        list_items.append(item)
        
    return {"items": list_items}