import os
from flask import Flask, request, jsonify, render_template_string
import easyocr
import cv2
import numpy as np
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- 这里填入你刚才拿到的完整地址 ---
MONGO_URI = "mongodb+srv://24jn0321:ZAtU3rP88qdSLexw@cluster0.lxjfxh5.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['receipt_db']
collection = db['items']

reader = easyocr.Reader(['ja', 'en']) # 支持日语和英语

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
            results = reader.readtext(img)
            
            # 简单的逻辑：提取包含数字的行作为金额，提取“◎”
            for i, (bbox, text, prob) in enumerate(results):
                if any(char.isdigit() for char in text):
                    price = ''.join(filter(str.isdigit, text))
                    name = results[i-1][1] if i > 0 else "未知商品"
                    collection.insert_one({
                        "name": name,
                        "price": int(price),
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
    
    items = list(collection.find().sort("_id", -1).limit(10))
    return f"<h1>解析结果</h1>" + "".join([f"<div>{i['name']}: ¥{i['price']} ({i['date']})</div>" for i in items]) + '<form method="post" enctype="multipart/form-data"><input type="file" name="file"><button>上传解析</button></form>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)