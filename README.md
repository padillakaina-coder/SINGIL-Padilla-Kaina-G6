# SINGIL
Baka Nakalimutan Mo? SINGIL Lang! A web-based personal borrowing and repayment tracking system built with Django and Supabase (PostgreSQL).

## Features
**Account feature (Project Development 1)**
- Registration with validation and hashed passwords
- Login and logout
- Role-based dashboards (Registered User and Administrator)
- Profile view and edit

**Core feature (Project Development 2): Borrowing and Lending Transaction Recording with Repayments**
- Keep a list of people you lend to or borrow from
- Add, view, edit and delete borrowing and lending transactions
- Record full or partial repayments; the remaining balance is calculated automatically
- Each transaction gets a status: Pending, Due Soon, Overdue, Partially Paid or Paid
- The user dashboard shows total owed, total receivable and recent transactions
- The administrator dashboard shows counts only, never transaction details

## Setup
1. Clone the repository and create a virtual environment.
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your Supabase PostgreSQL values.
4. `python manage.py migrate`
5. `python manage.py createsuperuser` (this account becomes the Administrator)
6. `python manage.py runserver`

## Branches
- `main`: stable code only
- `develop`: integration branch
- `feature/*`: one branch per feature, merged by pull request

## Documentation
The PD2 completion report is in the `docs/` folder.