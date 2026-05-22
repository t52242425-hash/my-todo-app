import json
import os
from flask import Flask, jsonify, redirect, render_template_string, request

app = Flask(__name__)
DATA_FILE = "todo_list.json"


def load_tasks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_tasks(tasks):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)


# 這裡就是我們新改的網頁外觀，裡面已經完美融入了 manifest 連動！
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的質感待辦清單</title>
    <!-- 修正：這行身分證連動必須安穩地躺在 head 標籤裡面 -->
    <link rel="manifest" href="/manifest.json">
    <style>
        :root {
            --bg-color: #f4f6f9;
            --card-bg: #ffffff;
            --text-main: #2d3748;
            --text-muted: #a0aec0;
            --primary: #4a6fa5;
            --primary-hover: #3b5c88;
            --danger: #e53e3e;
            --danger-light: #fff5f5;
            --border-radius: 12px;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            /* 修正：換成全新、100% 純英文無錯字的椎名真晝高畫質壁紙網址 */
            background: url('https://c4.wallpaperflare.com/wallpaper/892/625/70/%E6%A4%8E%E5%90%8D%E7%9C%9F%E6%98%BC-%E3%81%8A%E9%9A%A3%E3%81%AE%E5%A4%A9%E4%BD%BF%E6%A7%98%E3%81%AB%E3%81%84%E3%81%A4%E3%81%AE%E9%96%93%E3%81%AB%E3%81%8B%E9%A7%84%E7%9B%AE%E4%BA%BA%E9%96%93%E3%81%AB%E3%81%95%E3%82%8C%E3%81%A6%E3%81%84%E3%81%9F%E4%BB%B6-hd-wallpaper-preview.jpg') no-repeat center center fixed;
            background-size: cover;
            
            color: var(--text-main);
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            
            /* 這裡幫 pricing 居中，卡片就會漂亮地浮在畫面正中間 */
            align-items: center; 
            min-height: 100vh;
            box-sizing: border-box;
        }

        .container {
            width: 100%;
            max-width: 480px;
            
            /* 關鍵修正 1：原本是 #ffffff(純白)，改成帶有 0.85 透明度的白 */
            background: rgba(255, 255, 255, 0.85); 
            
            /* 關鍵修正 2：毛玻璃核心！讓卡片背後的真晝圖片產生高質感模糊，文字才會清晰 */
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            
            border-radius: var(--border-radius);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15); /* 讓陰影稍微加深，增加懸浮感 */
            padding: 24px;
            margin-top: 20px;
            box-sizing: border-box;
            
            /* 加上輕微的白色細邊框，看起來更精緻 */
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        h2 {
            margin-top: 0;
            margin-bottom: 24px;
            font-size: 24px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .input-group {
            display: flex;
            gap: 10px;
            margin-bottom: 24px;
        }

        input[type="text"] {
            flex: 1;
            padding: 12px 16px;
            border: 1.5px solid #e2e8f0;
            border-radius: var(--border-radius);
            font-size: 16px;
            outline: none;
            transition: border-color 0.2s;
        }

        input[type="text"]:focus {
            border-color: var(--primary);
        }

        .btn {
            padding: 12px 20px;
            border: none;
            border-radius: var(--border-radius);
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-primary {
            background-color: var(--primary);
            color: white;
        }

        .btn-primary:hover {
            background-color: var(--primary-hover);
        }

        .task-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .task-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 16px;
            background-color: #f8fafc;
            border: 1px solid #edf2f7;
            border-radius: var(--border-radius);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .task-item:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        }

        .task-text {
            font-size: 16px;
            word-break: break-all;
            padding-right: 10px;
        }

        .btn-delete {
            background-color: transparent;
            color: var(--danger);
            padding: 6px 12px;
            font-size: 14px;
            border-radius: 8px;
        }

        .btn-delete:hover {
            background-color: var(--danger-light);
        }

        .empty-state {
            text-align: center;
            color: var(--text-muted);
            padding: 40px 0;
            font-size: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>📝 待辦事項清單</h2>
        
        <form method="POST" action="/add" class="input-group">
            <input type="text" name="new_task" placeholder="今天想完成什麼事呢？" required autocomplete="off">
            <button type="submit" class="btn btn-primary">新增</button>
        </form>

        <div class="task-list">
            {% for task in tasks %}
            <div class="task-item">
                <span class="task-text">{{ task }}</span>
                <form method="POST" action="/delete/{{ loop.index0 }}" style="margin: 0;">
                    <button type="submit" class="btn btn-delete">✓ 完成</button>
                </form>
            </div>
            {% else %}
            <div class="empty-state">
                ☕ 目前沒有待辦事項，休息一下吧！
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""


@app.route("/")
def index():
    tasks = load_tasks()
    return render_template_string(HTML_TEMPLATE, tasks=tasks)


@app.route("/add", methods=["POST"])
def add_task():
    task = request.form.get("new_task")
    if task:
        tasks = load_tasks()
        tasks.append(task)
        save_tasks(tasks)
    return redirect("/")


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    tasks = load_tasks()
    if 0 <= task_id < len(tasks):
        tasks.pop(task_id)
        save_tasks(tasks)
    return redirect("/")


# 這裡負責把身分證資訊用正確的 json 格式丟回給手機瀏覽器
@app.route("/manifest.json")
def manifest():
    return jsonify(
        {
            "short_name": "我的清單",
            "name": "我的質感待辦清單 App",
            "icons": [
                {
                    "src": "https://cdn-icons-png.flaticon.com/512/9063/9063163.png",
                    "type": "image/png",
                    "sizes": "512x512",
                }
            ],
            "start_url": "/",
            "background_color": "#f4f6f9",
            "theme_color": "#4a6fa5",
            "display": "standalone",
            "orientation": "portrait",
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
