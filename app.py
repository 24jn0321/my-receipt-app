import os
from flask import Flask, request, render_template_string
from PIL import Image
import pytesseract
from pymongo import MongoClient
from datetime import datetime
import re

app = Flask(__name__)

# 你的 MongoDB 地址
MONGO_URI = "mongodb+srv://24jn0321:ZAtU3rP88qdSLexw@cluster0.lxjfxh5.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['receipt_db']
collection = db['items']

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><title>收据解析-轻量版</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; max-width: 500px; margin: auto; padding: 20px; background: #f0f2f5; }
        .card { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 10px; }
        .price { color: #d9534f; font-weight: bold; float: right; }
        .btn { background: #28a745; color: white; border: none; padding: 12px; width: 100%; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <h2>🧾 收据解析 (轻量优化版)</h2>
    <div class="card">
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/*" required>
            <button type="submit" class="btn" style="margin-top:10px;">开始解析</button>
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
            # 使用轻量引擎提取文本
            text = pytesseract.image_to_string(img, lang='eng+jpn')
            
            # 查找金额数字
            lines = text.split('\n')
            for line in lines:
                nums = re.findall(r'\d+', line)
                if nums:
                    price = nums[-1] # 取最后一段数字通常是金额
                    if 1 < len(price) < 6: # 简单过滤日期或电话
                        collection.insert_one({
                            "name": line[:15] or "未命名商品",
                            "price": int(price),
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
    
    items = list(collection.find().sort("_id", -1).limit(10))
    return render_template_string(HTML_TEMPLATE, items=items)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
