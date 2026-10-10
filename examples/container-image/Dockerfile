FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --create-home app

COPY --chown=app:app app.py /app/app.py

USER app:app

CMD ["python", "-u", "/app/app.py"]
