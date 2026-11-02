FROM python:3.11-slim

WORKDIR /app

# 复制项目文件
COPY main.py /app/
COPY .env.example /app/

# 设置环境变量默认值
ENV PYTHONUNBUFFERED=1 \
    PORT=8796

# 暴露端口
EXPOSE 8796

# 运行健康探针
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8796/health')" || exit 1

# 启动服务
CMD ["python3", "main.py"]
