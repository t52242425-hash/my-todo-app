import os
import psycopg2
from flask import Flask, render_template_string, request, jsonify, send_from_directory

app = Flask(__name__)

# 取得資料庫網址
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# 讓 Flask 可以直接讀取根目錄下的 preview.jpg
@app.route('/preview.jpg')
def serve_image():
    return send_from_directory('.', 'preview.jpg')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的質感待辦清單</title>
    <style>
        :root {
            --primary: #4a6fa5;
            --danger: #e53e3e;
            --border-radius: 12px;
            --bg-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            /* 直接指向根目錄的 preview.jpg */
            background: url('/preview.jpg') no-repeat center center fixed;
            background-size: cover;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center; 
            min-height: 100vh;
        }
        .container {
            width: 100%;
            max-width: 480px;
            background: rgba(255, 255, 255, 0.8); 
            backdrop-filter: blur(12px);
            border-radius: var(--border-radius);
            box-shadow: var(--bg-shadow);
            padding: 24px;
        }
        h2 { margin-top: 0; margin-bottom: 24px; font-size: 24px; }
        .input-group { display: flex; gap: 10px; margin-bottom: 24px; }
        input[type="text"] { flex: 1; padding: 12px 16px; border: 1.5px solid #e2e8f0; border-radius: var(--border-radius); background: rgba(255, 255, 255, 0.6); }
        .btn { padding: 12px 20px; border: none; border-radius: var(--border-radius); font-weight: 600; cursor: pointer; }
        .btn-primary { background-color: var(--primary); color: white; }
        .task-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 16px;
            background-color: rgba(248, 250, 252, 0.9);
            margin-bottom: 12px;
            border-radius: var(--border-radius);
            animation: slideIn 0.35s ease-out forwards;
        }
        .task-text { cursor: pointer; flex: 1; transition: 0.2s; }
        .completed { text-decoration: line-through; opacity: 0.5; }
        .run-fade-out { pointer-events: none; animation: itemFadeOut 0.4s forwards; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes itemFadeOut { to { opacity: 0; transform: scale(0.9); max-height: 0; padding: 0; margin: 0; } }
        .btn-delete { color: var(--danger); background: none; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h2>📝 雲端同步待辦清單</h2>
        <form id="add-form" class="input-group">
            <input type="text" id="new-task-input" placeholder="今天想完成什麼事呢？" required autocomplete="off">
            <button type="submit" class="btn btn-primary">新增</button>
        </form>
        <div class="task-list" id="task-list-container">
            {% for task in tasks %}
            <div class="task-item" id="task-{{ task[0] }}">
                <span class="task-text" onclick="executeDelete({{ task[0] }})">{{ task[1] }}</span>
                <button type="button" class="btn btn-delete" onclick="executeDelete({{ task[0] }})">✕ 刪除</button>
            </div>
            {% endfor %}
        </div>
    </div>
    <script>
        document.getElementById('add-form').addEventListener('submit', function(e) {
            e.preventDefault();
            const input = document.getElementById('new-task-input');
            const taskText = input.value.trim();
            fetch('/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: 'new_task=' + encodeURIComponent(taskText)
            })
            .then(res => res.json())
            .then(data => { if (data.success) location.reload(); });
            input.value = '';
        });
        function executeDelete(taskId) {
            const taskItem = document.getElementById('task-' + taskId);
            const taskText = taskItem.querySelector('.task-text');
            taskText.classList.add('completed');
            taskItem.classList.add('run-fade-out');
            fetch('/delete/' + taskId, { method: 'POST' })
            .then(() => { setTimeout(() => taskItem.remove(), 400); });
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    if not DATABASE_URL: return "請在 Render 設定 DATABASE_URL"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, task FROM github_tasks ORDER BY id DESC;")
    tasks = cur.fetchall()
    cur.close()
    conn.close()
    return render_template_string(HTML_TEMPLATE, tasks=tasks)

@app.route("/add", methods=["POST"])
def add_task():
    task = request.form.get("new_task")
    if task:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO github_tasks (task) VALUES (%s) RETURNING id;", (task,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM github_tasks WHERE id = %s;", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
