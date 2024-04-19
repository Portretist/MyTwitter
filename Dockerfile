FROM python:3.10

WORKDIR /app

COPY requirements.txt /app
RUN pip3 install --upgrade pip -r requirements.txt

COPY main/. /app

EXPOSE 5000