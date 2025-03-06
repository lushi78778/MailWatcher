# 使用 Python 3.9 作为基础镜像
FROM python:3.9

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 安装 Python 依赖
RUN pip install -r requirements.txt

# 运行 Flask 应用
CMD ["gunicorn", "-b", "0.0.0.0:10000", "mailwatcher:app"]
