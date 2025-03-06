from imapclient import IMAPClient
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
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # 这里是授权码，而不是邮箱密码！
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.126.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 30))

# === 数据库配置（Render 只能用 `/tmp/` 目录存储临时数据） ===
DB_FILE = "emails.db"

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
    """ 轮询邮箱，检查未读邮件 """
    while True:
        try:
            print("🔍 正在检查新邮件...")

            with IMAPClient(IMAP_SERVER, port=IMAP_PORT, use_uid=True, ssl=True) as mail:
                # **使用 AUTHENTICATE 方式登录**
                mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
                print("✅ 登录成功！")

                # 获取邮箱文件夹，确保 "INBOX" 存在
                folders = mail.list_folders()
                print(f"📂 服务器上的文件夹: {folders}")

                # 选择收件箱
                mail.select_folder("INBOX")

                # 搜索未读邮件
                messages = mail.search(["UNSEEN"])
                print(f"📬 未读邮件数: {len(messages)}")

                for msg_id in messages:
                    msg_data = mail.fetch(msg_id, ["RFC822"])
                    msg = email.message_from_bytes(msg_data[msg_id][b"RFC822"])

                    # 解析邮件标题
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8", errors="ignore")

                    print(f"📩 新邮件: {subject}")

                    # 标记为已读
                    mail.add_flags(msg_id, ["\\Seen"])

        except Exception as e:
            print(f"❌ 发生错误: {e}")

        time.sleep(CHECK_INTERVAL)

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
