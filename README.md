# MailWatcher (Docker Version)

MailWatcher 是一个 Python Flask 应用，使用 Docker 在 Render 上部署，监听 `lushi78778@126.com` 邮箱的邮件，并在网页上显示邮件的主题。

## 📂 目录结构
```
MailWatcher_Docker/
│── mailwatcher.py      # 监听邮件 & Flask Web 服务器
│── .env                # 存储邮箱账号、密码等（不会上传）
│── .gitignore          # 忽略 .env，防止敏感信息泄露
│── Dockerfile          # Docker 配置文件
│── .dockerignore       # 忽略无用文件
│── requirements.txt    # 依赖列表（Flask, python-dotenv）
│── README.md           # 项目说明
```

## 📌 安装依赖
```bash
pip install -r requirements.txt
```

## 🔍 运行项目（本地测试）
```bash
python mailwatcher.py
```

## 🐳 Docker 运行（本地）
```bash
docker build -t mailwatcher .
docker run -p 10000:10000 --env-file .env mailwatcher
```

## 🚀 在 Render 上部署
1. 登录 [Render](https://dashboard.render.com/)
2. 选择 "New Web Service" → "Deploy from Dockerfile"
3. 绑定 GitHub 仓库
4. 添加环境变量 (`EMAIL_ACCOUNT`, `EMAIL_PASSWORD`, `IMAP_SERVER` 等)
5. 部署并访问 `https://your-app-name.onrender.com/`

## 🌐 访问 Web 界面
部署完成后，打开：
```
http://127.0.0.1:10000/  (本地运行)
https://your-app-name.onrender.com/ (Render 运行)
```
即可查看最近 20 封邮件的主题，每 **5 秒自动刷新**。
