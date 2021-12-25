FROM python:3.8.5-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
RUN apk add --update --no-cache gcc python3-dev jpeg-dev zlib-dev musl-dev libc-dev linux-headers
RUN apk add --update postgresql-dev
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . /app

WORKDIR /app

COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]