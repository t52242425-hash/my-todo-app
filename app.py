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
            background: url('https://c4.wallpaperflare.com/wallpaper/892/625/70/%E6%A4%8E%E5%90%8D%E7%9C%9F%E6%98%BC-%E3%81%8A%E9%9A%A3%E3%81%AE%E5%A4%A9%E4%BD%BF%E6%A7%98%E3%81%AB%E3%81%84%E3%81%A4%E3%81%AE%E9%96%93%E3%81%AB%E3%81%8B%E9%A7%84%E7%9B%AE%E4%BA%BA%E9%96%93%E3%81%AB%E3%81%95%E3%82%8C%E3%81%A6%E3%81%84%E3%81%9F%E4%BB%B6-hd-wallpaper-preview.jpg') no-repeat center center fixed;
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

        .task-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 16px;
            background-color: rgba(248, 250, 252, 0.9);
            border: 1px solid rgba(237, 242, 247, 0.5);
            border-radius: var(--border-radius);
            transition: all 0.2s ease;
        }

        .task-text {
            font-size: 16px;
            word-break: break-all;
            padding-right: 10px;
            cursor: pointer;
            flex: 1;
            transition: all 0.2s;
        }

        .delete-form {
            margin: 0;
            padding: 0;
            display: inline;
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
            <div class="task-item" id="task-{{ task[0] }}">
                <!-- 1. 點擊文字本身：觸發立刻蒸發消失 -->
                <span class="task-text" onclick="dismissTask({{ task[0] }})">{{ task[1] }}</span>
                
                <!-- 2. 點擊刪除按鈕：觸發立刻蒸發消失，並防範手機表單跳轉 -->
                <form method="POST" action="/delete/{{ task[0] }}" class="delete-form" onsubmit="return dismissTaskWithForm(event, {{ task[0] }})">
                    <button type="submit" class="btn btn-delete">✕ 刪除</button>
                </form>
            </div>
            {% else %}
            <div class="empty-state" id="empty-msg">
                ☕ 目前沒有待辦事項，休息一下吧！
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        // 核心功能：讓指定的代辦項目一瞬間在地球上消失
        function removeElementFromScreen(taskId) {
            const taskElement = document.getElementById('task-' + taskId);
            if (taskElement) {
                taskElement.remove(); // 畫面秒刪
            }
            
            // 檢查如果全部都刪光了，自動補上喝咖啡的優雅提示
            const container = document.getElementById('task-list-container');
            if (container && container.querySelectorAll('.task-item').length === 0) {
                container.innerHTML = '<div class="empty-state" id="empty-msg">☕ 目前沒有待辦事項，休息一下吧！</div>';
            }
        }

        // 點擊文字：畫面秒消失，後台默默去雲端執行刪除
        function dismissTask(taskId) {
            removeElementFromScreen(taskId);
            fetch('/delete/' + taskId, { method: 'POST' });
        }

        // 點擊按鈕：攔截表單的重整行為，畫面秒消失，後台默默送出請求
        function dismissTaskWithForm(event, taskId) {
            event.preventDefault(); // 阻止網頁頓一下或重新整理
            removeElementFromScreen(taskId);
            fetch('/delete/' + taskId, { method: 'POST' });
            return false;
        }
    </script>
</body>
</html>
