import os
from flask import Flask, request, render_template_string
from PIL import Image
import pytesseract
from pymongo import MongoClient
from datetime import datetime
import re

app = Flask(__name__)

# MongoDB 连接
MONGO_URI = "mongodb+srv://24jn0321:ZAtU3rP88qdSLexw@cluster0.lxjfxh5.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['receipt_db']
collection = db['items']

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><title>轻量版收据解析</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; max-width: 500px; margin: auto; padding: 20px; background: #f4f7f9; }
        .card { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .price { color: #e74c3c; font-weight: bold; float: right; }
        .btn { background: #28a745; color: white; border: none; padding: 12px; width: 100%; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <h2>📜 轻量版解析器 (RAM 优化)</h2>
    <div class="card">
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/*" required>
            <button type="submit" class="btn" style="margin-top:10px;">上传解析</button>
        </form>
    </div>
    {% for item in items %}
    <div class="card">
        <span>{{ item.name }}</span><span class="price">¥{{ item.price }}</span>
        <div style="font-size:0.8em; color:gray;">{{ item.date }}</div>
    </div>
    {% endfor %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            img = Image.open(file.stream)
            # 使用轻量级引擎解析日语和英语
            text = pytesseract.image_to_string(img, lang='jpn+eng')
            
            # 简单的金额提取逻辑
            lines = text.split('\n')
            for line in lines:
                if any(c.isdigit() for c in line):
                    price = ''.join(filter(str.isdigit, line))
                    if price and len(price) < 7: # 过滤掉电话号码等长数字
                        collection.insert_one({
                            "name": line[:15], "price": int(price),
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
    
    items = list(collection.find().sort("_id", -1).limit(10))
    return render_template_string(HTML_TEMPLATE, items=items)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
