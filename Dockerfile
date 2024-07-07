FROM python:3.12.4-slim

RUN apt-get update && \
    apt-get install -y git && \
    git config --global user.name "AI Bot" && \
    git config --global user.email "noreply@aibot.com"

RUN pip install poetry==1.8.3

RUN poetry config virtualenvs.create false

WORKDIR /code

COPY ./pyproject.toml ./README.md ./poetry.lock* ./bootstrap.sh ./

COPY ./package[s] ./packages

RUN poetry install  --no-interaction --no-ansi --no-root

COPY ./app ./app

RUN poetry install --no-interaction --no-ansi

# Start app
EXPOSE 5000
ENTRYPOINT ["/code/bootstrap.sh"]
