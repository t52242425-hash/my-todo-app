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
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的手機待辦清單</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 500px; margin: 30px auto; padding: 20px; }
        h2 { color: #333; }
        .task-item { display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #ddd; align-items: center; }
        button { background-color: #ff4d4d; color: white; border: none; padding: 5px 10px; cursor: pointer; border-radius: 3px; }
        input[type="text"] { padding: 8px; width: 70%; }
        .add-btn { background-color: #4CAF50; padding: 8px; }
    </style>
</head>
<body>
    <h2>📝 我的待辦清單</h2>

    <form method="POST" action="/add">
        <input type="text" name="new_task" placeholder="輸入想新增的事項..." required>
        <button type="submit" class="add-btn">新增</button>
    </form>

    <div style="margin-top: 20px;">
        {% for task in tasks %}
        <div class="task-item">
            <span>{{ loop.index }}. {{ task }}</span>
            <form method="POST" action="/delete/{{ loop.index0 }}" style="margin: 0;">
                <button type="submit">完成</button>
            </form>
        </div>
        {% else %}
        <p>目前沒有待辦事項，太棒了！</p>
        {% endfor %}
    </div>
</body>
</html>
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