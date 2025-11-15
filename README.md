# Telegram ToDo/Reminder Bot


Simple Telegram bot that stores reminders in MySQL and notifies users at scheduled times using APScheduler.


## Setup
1. Copy `.env.example` to `.env` and fill values.
2. Build image: `docker build -t telegram-todo-bot:latest .`
3. Run locally with docker-compose: `docker compose up --build`


## Production / AKS
- Push image to ACR, create Kubernetes secret with `DATABASE_URL` and `TELEGRAM_TOKEN`, then apply k8s manifests in `k8s/`.


Notes:
- For production, prefer Azure Database for MySQL (Flexible Server) and DO NOT store credentials in image.
- If you run multiple bot replicas, run the scheduler as a single replica (see `deployment-scheduler.yaml`) to avoid duplicate notifications.