import os
import psycopg2
from flask import Flask, render_template_string, request, redirect, jsonify

app = Flask(__name__)

# 取得在 Render 設定的雲端資料庫網址
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS github_tasks (
            id SERIAL PRIMARY KEY,
            task TEXT NOT NULL,
            is_completed BOOLEAN DEFAULT FALSE
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

if DATABASE_URL:
    try:
        init_db()
    except Exception as e:
        print(f"Database init error: {e}")

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
            --shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: url('data:image/jpeg;base64,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') no-repeat center center fixed;
            background-size: cover;
            color: var(--text-main);
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center; 
            min-height: 100vh;
            box-sizing: border-box;
        }

        .container {
            width: 100%;
            max-width: 480px;
            background: rgba(255, 255, 255, 0.5); 
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
            padding: 24px;
            box-sizing: border-box;
            border: 1px solid rgba(255, 255, 255, 0.2);
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
            background: rgba(255, 255, 255, 0.6);
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
            background-color: rgba(248, 250, 252, 0.7);
            border: 1px solid rgba(237, 242, 247, 0.5);
            border-radius: var(--border-radius);
            transition: all 0.3s ease;
        }

        .task-item.completed {
            opacity: 0.5;
        }
        
        .task-item.completed .task-text {
            text-decoration: line-through;
            color: var(--text-muted);
        }

        .task-text {
            font-size: 16px;
            word-break: break-all;
            padding-right: 10px;
            cursor: pointer;
            flex: 1;
            transition: all 0.2s;
        }

        .btn-delete {
            background-color: transparent;
            color: var(--danger);
            padding: 6px 12px;
            font-size: 14px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
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
        <h2>📝 雲端同步待辦清單</h2>
        
        <form method="POST" action="/add" class="input-group">
            <input type="text" name="new_task" placeholder="今天想完成什麼事呢？" required autocomplete="off">
            <button type="submit" class="btn btn-primary">新增</button>
        </form>

        <div class="task-list" id="task-list-container">
            {% for task in tasks %}
            <div class="task-item {% if task[2] %}completed{% endif %}" id="task-{{ task[0] }}">
                <span class="task-text" onclick="toggleTask({{ task[0] }})">{{ task[1] }}</span>
                <button type="button" class="btn btn-delete" onclick="deleteTask({{ task[0] }})">✕ 完成</button>
            </div>
            {% else %}
            <div class="empty-state" id="empty-msg">
                ☕ 目前沒有待辦事項，休息一下吧！
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        // 點擊文字：切換劃掉特效
        function toggleTask(taskId) {
            const taskElement = document.getElementById('task-' + taskId);
            taskElement.classList.toggle('completed');
            fetch('/toggle/' + taskId, { method: 'POST' });
        }

        // 點擊刪除：讓畫面上的項目直接消失
        function deleteTask(taskId) {
            const taskElement = document.getElementById('task-' + taskId);
            if (taskElement) {
                taskElement.remove(); // 讓網頁上的元素立刻消失
            }
            
            // 同步通知後台資料庫刪除
            fetch('/delete/' + taskId, { method: 'POST' })
            .then(() => {
                const container = document.getElementById('task-list-container');
                // 如果刪到沒東西了，顯示喝咖啡的提示
                if (container.children.length === 0) {
                    container.innerHTML = '<div class="empty-state" id="empty-msg">☕ 目前沒有待辦事項，休息一下吧！</div>';
                }
            });
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    if not DATABASE_URL:
        return "請在 Render 設定 DATABASE_URL 環境變數"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, task, is_completed FROM github_tasks ORDER BY id DESC;")
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
        cur.execute("INSERT INTO github_tasks (task) VALUES (%s);", (task,))
        conn.commit()
        cur.close()
        conn.close()
    return redirect("/")

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM github_tasks WHERE id = %s;", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True})

@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE github_tasks SET is_completed = NOT is_completed WHERE id = %s;", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
