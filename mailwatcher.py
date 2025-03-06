import imaplib
import email
import sqlite3
import threading
import time
import os
from email.header import decode_header
from flask import Flask, render_template_string
from dotenv import load_dotenv

# === 加载 .env 文件 ===
load_dotenv()
EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.126.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 30))

# === 数据库配置（Render 只能用 `/tmp/` 目录存储临时数据） ===
DB_FILE = "/tmp/emails.db"

# === Flask Web 服务器 ===
app = Flask(__name__)

def init_db():
    """ 初始化 SQLite 数据库 """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_email(subject):
    """ 保存邮件标题到数据库（避免重复） """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM emails WHERE subject = ?", (subject,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO emails (subject) VALUES (?)", (subject,))
        conn.commit()
    conn.close()

def get_emails():
    """ 获取数据库中的邮件标题（最近 20 封） """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT subject FROM emails ORDER BY id DESC LIMIT 20")
    emails = cursor.fetchall()
    conn.close()
    return [email[0] for email in emails]

def check_new_email():
    """ 每隔一段时间轮询邮箱，获取新邮件 """
    while True:
        try:
            print("🔍 正在检查新邮件...")
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
            mail.select("inbox")

            # 搜索所有未读邮件
            status, messages = mail.search(None, "UNSEEN")

            if status == "OK":
                for num in messages[0].split():
                    status, msg_data = mail.fetch(num, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])

                            # 解析邮件标题
                            subject, encoding = decode_header(msg["Subject"])[0]
                            if isinstance(subject, bytes) and encoding:
                                subject = subject.decode(encoding)

                            print(f"📩 新邮件: {subject}")
                            save_email(subject)

                    mail.store(num, "+FLAGS", "\\Seen")  # 标记邮件为已读

            mail.logout()
        except Exception as e:
            print(f"❌ 发生错误: {e}")

        time.sleep(CHECK_INTERVAL)  # 等待指定时间后再检查

@app.route("/")
def index():
    emails = get_emails()
    html_template = """
    <!DOCTYPE html>
    <html lang="zh">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📬 邮件监听 - MailWatcher</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; background-color: #f4f4f4; }
            h1 { color: #333; }
            ul { list-style-type: none; padding: 0; }
            li { padding: 10px; border-bottom: 1px solid #ccc; background: #fff; margin: 5px; }
        </style>
        <script>
            setTimeout(() => location.reload(), 5000); // 每5秒刷新页面
        </script>
    </head>
    <body>
        <h1>📬 监听的邮件主题</h1>
        <ul>
            {% for email in emails %}
                <li>{{ email }}</li>
            {% endfor %}
        </ul>
    </body>
    </html>
    """
    return render_template_string(html_template, emails=emails)

def start_listener():
    """ 启动邮件监听线程 """
    init_db()
    listener_thread = threading.Thread(target=check_new_email, daemon=True)
    listener_thread.start()

start_listener()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)  # Render 需要运行在端口 10000
