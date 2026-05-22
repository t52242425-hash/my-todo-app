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
            background: url('https://c4.wallpaperflare.com/wallpaper/892/625/70/%E6%A4%8E%E5%90%8D%E7%9C%9F%E6%98%BC-%E3%81%8A%E9%9A%A3%E3%81%AE%E5%A4%A9%E4%BD%BF%E6%A7%98%E3%81%AB%E3%81%84%E3%81%A4%E3%81%AE%E9%96%93%E3%81%AB%E3%81%8B%E9%A7%84%E7%9B%AE%E4%BA%BA%E9%96%93%E3%81%AB%E3%81%95%E3%82%8C%E3%81%A6%E3%81%84%E3%81%9F%E4%BB%B件-hd-wallpaper-preview.jpg') no-repeat center center fixed;
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
            background: rgba(255, 255, 255, 0.8); 
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
            padding: 24px;
            box-sizing: border-box;
            border: 1px solid rgba(255, 255, 255, 0.25);
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

        /* 事項基本與登場動畫設定 */
        .task-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 16px;
            background-color: rgba(248, 250, 252, 0.9);
            border: 1px solid rgba(237, 242, 247, 0.5);
            border-radius: var(--border-radius);
            max-height: 80px; 
            opacity: 1;
            transform: scale(1);
            overflow: hidden;
            box-sizing: border-box;
            
            /* 平滑淡出的 Transition 核心 */
            transition: opacity 0.4s ease, 
                        transform 0.4s ease, 
                        max-height 0.4s ease, 
                        padding 0.4s ease, 
                        margin 0.4s ease;
            
            animation: slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-20px) scale(0.95);
                max-height: 0;
                padding-top: 0;
                padding-bottom: 0;
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
                max-height: 80px;
            }
        }

        /* 漸漸消失動畫樣式 */
        .task-item.fade-out {
            animation: none !important; 
            opacity: 0 !important;
            transform: scale(0.8) translateY(-15px) !important;
            max-height: 0 !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            border-color: transparent !important;
            pointer-events: none;
        }

        .task-text {
            font-size: 16px;
            word-break: break-all;
            padding-right: 10px;
            cursor: pointer;
            flex: 1;
        }

        .btn-delete {
            background-color: transparent;
            color: var(--danger);
            padding: 6px 12px;
            font-size: 14px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            transition: background-color 0.2s;
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
        
        <form id="add-form" class="input-group">
            <input type="text" id="new-task-input" placeholder="今天想完成什麼事呢？" required autocomplete="off">
            <button type="submit" class="btn btn-primary">新增</button>
        </form>

        <!-- 核心改變：我們徹底拿掉 HTML 裡的所有 onclick 事前綁定，改用全動態監聽 -->
        <div class="task-list" id="task-list-container">
            {% for task in tasks %}
            <div class="task-item" id="task-{{ task[0] }}" data-id="{{ task[0] }}">
                <span class="task-text">{{ task[1] }}</span>
                <button type="button" class="btn btn-delete">✕ 刪除</button>
            </div>
            {% else %}
            <div class="empty-state" id="empty-msg">
                ☕ 目前沒有待辦事項，休息一下吧！
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        // 1. 處理新增事項
        document.getElementById('add-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const input = document.getElementById('new-task-input');
            const taskText = input.value.trim();
            if (!taskText) return;

            input.value = '';

            const emptyMsg = document.getElementById('empty-msg');
            if (emptyMsg) emptyMsg.remove();

            fetch('/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: 'new_task=' + encodeURIComponent(taskText)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const container = document.getElementById('task-list-container');
                    const newItem = document.createElement('div');
                    newItem.className = 'task-item';
                    newItem.id = 'task-' + data.id;
                    newItem.setAttribute('data-id', data.id); // 埋入 ID 供動態查找
                    newItem.innerHTML = `
                        <span class="task-text">${escapeHtml(taskText)}</span>
                        <button type="button" class="btn btn-delete">✕ 刪除</button>
                    `;
                    container.insertBefore(newItem, container.firstChild);
                }
            });
        });

        // 2.【終極核心】事件代理人：直接在最外層大容器監聽點擊
        document.getElementById('task-list-container').addEventListener('click', function(e) {
            // 判斷點擊的是不是「文字」或「✕ 刪除按鈕」
            if (e.target.classList.contains('task-text') || e.target.classList.contains('btn-delete')) {
                e.stopPropagation();
                
                // 往上找到最靠近的 .task-item 祖先元素
                const taskItem = e.target.closest('.task-item');
                if (!taskItem) return;
                
                const taskId = taskItem.getAttribute('data-id');
                if (!taskId) return;

                // 如果已經在淡出了，就不要重複執行
                if (taskItem.classList.contains('fade-out')) return;

                // 立即悄悄發送刪除命令給後端資料庫
                fetch('/delete/' + taskId, { method: 'POST' });

                // 觸發前端淡出過渡效果
                taskItem.classList.add('fade-out');

                // 使用極度保險的雙重保障：優先採用 Transition 結束事件，如果卡住就用 setTimeout 備援
                let removed = false;
                function removeNode() {
                    if (removed) return;
                    removed = true;
                    taskItem.remove();
                    checkEmptyState();
                }

                taskItem.addEventListener('transitionend', removeNode, { once: true });
                setTimeout(removeNode, 450); // 備援機制：如果瀏覽器沒觸發事件，450毫秒後也絕對強制拔除
            }
        });

        function checkEmptyState() {
            const container = document.getElementById('task-list-container');
            if (container && container.querySelectorAll('.task-item').length === 0) {
                container.innerHTML = '<div class="empty-state" id="empty-msg">☕ 目前沒有待辦事項，休息一下吧！</div>';
            }
        }

        function escapeHtml(text) {
            return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
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
    new_id = None
    if task:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO github_tasks (task) VALUES (%s) RETURNING id;", (task,))
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "id": new_id})
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
