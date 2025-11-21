FROM python:3.13-alpine as builder

WORKDIR /app

RUN apk add --no-cache binutils ffmpeg

COPY requirements.txt .
RUN pip install --no-cache-dir pyinstaller
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pyinstaller --onefile --name tomsg_bot --clean --noconfirm main.py

FROM alpine:3.21

RUN apk add --no-cache ffmpeg

COPY --from=builder /app/dist/tomsg_bot /

ARG VERSION="undefined@Dockerfile"
ENV VERSION=${VERSION}

ENTRYPOINT ["/tomsg_bot"]
