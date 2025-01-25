FROM python:3.13-alpine

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ARG VERSION="undefined"
ENV VERSION=${VERSION}

COPY . .

CMD ["python", "-u", "main.py"]
