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
    <meta charset="UTF-8"><title>收据解析-HF版</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; max-width: 500px; margin: auto; padding: 20px; background: #fdfdfd; }
        .card { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px; border-left: 5px solid #28a745; }
        .price { color: #d9534f; font-weight: bold; float: right; font-size: 1.2em; }
        .btn { background: #333; color: white; border: none; padding: 15px; width: 100%; border-radius: 8px; font-size: 1em; cursor: pointer; }
    </style>
</head>
<body>
    <h2 style="text-align: center;">🧾 收据解析系统</h2>
    <div class="card" style="border-left: 5px solid #333;">
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/*" required style="display: block; margin-bottom: 10px;">
            <button type="submit" class="btn">📷 上传并识别</button>
        </form>
    </div>
    <h3 style="margin-top: 20px;">📜 最近识别记录</h3>
    {% for item in items %}
    <div class="card">
        <span class="price">¥{{ item.price }}</span>
        <div style="font-weight: bold; margin-bottom: 5px;">{{ item.name }}</div>
        <div style="font-size: 0.8em; color: gray;">{{ item.date }}</div>
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
            # 识别日语和英语
            text = pytesseract.image_to_string(img, lang='jpn+eng')
            lines = text.split('\n')
            for line in lines:
                nums = re.findall(r'\d+', line)
                if nums:
                    price = nums[-1]
                    if 1 < len(price) < 6:
                        collection.insert_one({
                            "name": line[:20].strip() or "商品项",
                            "price": int(price),
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
    items = list(collection.find().sort("_id", -1).limit(10))
    return render_template_string(HTML_TEMPLATE, items=items)

if __name__ == '__main__':
    # 注意：Hugging Face 必须使用 7860 端口
    app.run(host='0.0.0.0', port=7860)
