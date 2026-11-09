# Stockroom — Retail Management System

A clean Django retail operations MVP for inventory, point-of-sale checkout, sales history, and stock alerts.

## Included
- Secure Django admin login and product/category management
- Inventory list with SKU, cost, price, active status, stock, and reorder levels
- Point of sale screen with cash, card, and transfer payment methods
- Atomic checkout that prevents overselling and decrements stock
- Dashboard with today’s revenue, transaction count, low-stock alerts, and recent sales
- PostgreSQL-ready settings, WhiteNoise static files, Gunicorn, and Render Blueprint deployment

## Local setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
./build.sh
python manage.py createsuperuser
python manage.py runserver
```
Open http://127.0.0.1:8000/admin/ to sign in, then use the dashboard.

## Render deployment
Push this repository to GitHub, create a new Render Blueprint from the repository, and select `render.yaml`. Render provisions the web service and PostgreSQL database. After the first deploy, create a superuser from the Render shell:
```bash
python manage.py createsuperuser
```
