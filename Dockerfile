FROM python:3.11.3
COPY requirements.txt /bot/requirements.txt
RUN pip install --no-cache-dir -r /bot/requirements.txt
COPY . /bot/
WORKDIR /bot/
CMD ["python", "/bot/main.py"]
