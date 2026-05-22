import json
import os
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
DATA_FILE = "todo_list.json"


# 讀取檔案功能
def load_tasks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# 儲存檔案功能
def save_tasks(tasks):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)


# 💡 簡易的網頁畫面（HTML）
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的質感待辦清單</title>
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
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
        }

        .container {
            width: 100%;
            max-width: 480px;
            background: var(--card-bg);
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
            padding: 24px;
            margin-top: 20px;
            box-sizing: border-box;
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
<link rel="manifest" href="/manifest.json">
"""



# 網頁路由 1：首頁（秀出所有待辦事項）
@app.route("/")
def index():
    tasks = load_tasks()
    return render_template_string(HTML_TEMPLATE, tasks=tasks)


# 網頁路由 2：新增事項
@app.route("/add", methods=["POST"])
def add_task():
    task = request.form.get("new_task")
    if task and task.strip():
        tasks = load_tasks()
        tasks.append(task.strip())
        save_tasks(tasks)
    return index()


# 網頁路由 3：刪除/完成事項
@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    tasks = load_tasks()
    if 0 <= task_id < len(tasks):
        tasks.pop(task_id)
        save_tasks(tasks)
    return index()


# 啟動伺服器（允許外網連線）
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
