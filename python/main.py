import os
import logging
import pathlib
import hashlib
import json
import sqlite3
from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware


class App:
    def __init__(self, dbpath, db_setup_path, images_path):
        self.app = FastAPI(debug=True)
        self.logger = logging.getLogger("uvicorn")
        self.logger.level = logging.INFO
        self.images = images_path
        self.dbpath = dbpath
        self.db_setup_path = db_setup_path
        self.origins = [os.environ.get('FRONT_URL', "http://localhost:3000")]

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"],
        )
        self.conn = sqlite3.connect(dbpath)
        with open(db_setup_path, 'r') as f:
            file = f.read()

        self.cursor = self.conn.cursor()
        self.cursor.executescript(file)
        self.conn.commit()

    def root(self):
        return {"message": "Hello, world!"}

    def get_items(self):
        self.conn = sqlite3.connect(self.dbpath)
        self.cursor = self.conn.cursor()
        self.cursor.execute(("""
            SELECT items.id, items.name, category.name, items.image_filename
            FROM items
            INNER JOIN category ON items.category_id = category.id
        """))
        items = self.cursor.fetchall()
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

    def add_item(self, name: str = Form(...), category: str = Form(...), image: UploadFile = File(...)):
        self.logger.info(f"Receive item: {name}, category: {category}, image: {image.filename}")

        self.conn = sqlite3.connect(self.dbpath)
        self.cursor = self.conn.cursor()

        # hash image url and save image

        image_file = image.file.read()
        image_hash = hashlib.sha256(image_file).hexdigest()
        image_filename = f"{image_hash}.jpg"
        image_path = self.images / image_filename

        with open(image_path, 'wb') as f:
            f.write(image_file)

        self.cursor.execute("SELECT id FROM category WHERE name = ?", (category,))
        category_id = self.cursor.fetchone()
        if category_id is None:
            try:
                self.cursor.execute("INSERT INTO category (name) VALUES (?)", (category,))
                self.conn.commit()
                category_id = self.cursor.lastrowid  # get the last inserted ID
            except sqlite3.IntegrityError:
                self.cursor.execute("SELECT id FROM category WHERE name = ?", (category,))
                category_id = self.cursor.fetchone()[0]
        else:
            category_id = category_id[0]

        # Insert item into items table
        self.cursor.execute("INSERT INTO items (name, category_id, image_filename) VALUES (?, ?, ?)",
                            (name, category_id, image_filename,))
        self.conn.commit()

        return {"message": f"item received: {name}, category: {category}, image: {image_filename} "}

    async def get_image(self, image_filename):
        # Create image path
        image = self.images / image_filename

        if not image_filename.endswith(".jpg"):
            raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

        if not image.exists():
            self.logger.debug(f"Image not found: {image}")
            image = self.images / "default.jpg"

        return FileResponse(image)

    def get_item_withID(self, item_id: int):
        self.conn = sqlite3.connect(self.dbpath)
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        items = self.cursor.fetchone()

        if items is None:
            raise HTTPException(status_code=404, detail="Item not found")

        return {"item": items[0], "name": items[1], "category": items[2], "image": items[3]}

    def search_item(self, keyword: str):
        self.conn = sqlite3.connect(self.dbpath)
        self.cursor = self.conn.cursor()
        keyword_search = f"%{keyword}%"
        self.cursor.execute('''
            SELECT items.id, items.name, category.name, items.image_filename
            FROM items
            INNER JOIN category ON items.category_id = category.id 
            WHERE items.name LIKE ?
                       ''', (keyword_search,))
        items = self.cursor.fetchall()

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


# Usage
dbpath = pathlib.Path(__file__).parent.parent.resolve() / "db" / "mercari.sqlite3"
db_setup_path = pathlib.Path(__file__).parent.parent.resolve() / "db" / "items.db"
images_path = pathlib.Path(__file__).parent.resolve() / "images"

app_instance = App(dbpath, db_setup_path, images_path)

app = app_instance.app

app.get("/")(app_instance.root)
app.get("/items")(app_instance.get_items)
app.post("/items")(app_instance.add_item)
app.get("/images/{image_filename}")(app_instance.get_image)
app.get("/items/{item_id}")(app_instance.get_item_withID)
app.get("/search")(app_instance.search_item)

def main():
    dbpath = pathlib.Path(__file__).parent.parent.resolve() / "db" / "mercari.sqlite3"
    db_setup_path = pathlib.Path(__file__).parent.parent.resolve() / "db" / "items.db"
    images_path = pathlib.Path(__file__).parent.resolve() / "images"

    app_instance = App(dbpath, db_setup_path, images_path)

    app = app_instance.app
    app.get("/")(app_instance.root)
    app.get("/items")(app_instance.get_items)
    app.post("/items")(app_instance.add_item)
    app.get("/images/{image_filename}")(app_instance.get_image)
    app.get("/items/{item_id}")(app_instance.get_item_withID)
    app.get("/search")(app_instance.search_item)

    return app

app = main()
