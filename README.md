# Ecommerce Django Project

[![Deployment Status](https://img.shields.io/badge/deployed-on_render-00bfff.svg)](https://ecommerce-y6ab.onrender.com/)

## Overview

This is a secure and feature-rich ecommerce web application built with Django 3.2.14 and Python 3. It covers user authentication, product catalog browsing, shopping cart, order management, and payment processing integrated with Razorpay.

## Features

- User registration, login, password reset flows
- Product listing and detailed views
- Shopping cart and checkout process
- Razorpay payment gateway integration
- Order tracking and profile management
- Admin dashboard for product & order management
- Email notifications for account activation and payment updates

## Technologies Used

- Django 3.2.14
- Python 3.12
- SQLite (default local DB)
- Bootstrap CSS and JS
- Razorpay Payment Gateway
- SMTP Email via Gmail

## Installation

1. Clone the repository:
git clone https://github.com/NakkaAnthanakshmi/ecommerce-django.git
cd ecommerce-django

2. Create and activate a virtual environment:
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

3. Install dependencies:
pip install -r requirements.txt

4. Set environment variables:
Create a `.env` file or set environment variables for:
- `SECRET_KEY`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`

5. Apply database migrations:
python manage.py migrate

6. Collect static files:
python manage.py collectstatic

7. Run the development server:
python manage.py runserver

## Deployment

The app is deployed on Render at:

https://ecommerce-y6ab.onrender.com/

## Contribution

Feel free to open issues or submit pull requests to improve the application.






