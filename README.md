LifeFlow – Vijayawada Blood Bank Management System

CSP Lab Project | 3rd Year Data Science | Community Service Project

A complete full-stack web application for managing blood banks in Vijayawada with real branch data, inventory tracking, donor management, hospital orders, eligibility checker, and Machine Learning prediction.

Theme

Blood Red (#C41E3A) + Black + Gold accent

Logo

Red medical cross + red blood drop (included in static/images/logo.png)

Features





Real Registration + Login (SQLite + Flask-Login)



Home Dashboard with live stats & Chart.js graphs



Capacity & In-Stock (12 real Vijayawada blood banks + 50 bags)



Appointments & Donor details (CRUD + Search)



Hospital Orders (Pending / Completed tracking)



Donor Eligibility Checker (Indian guidelines)



ML Prediction page (Random Forest on RFM model)



Admin Dashboard



Public Donor Registration form



Full CRUD on Inventory, Appointments, Orders, Donors



Search & Filter on all tables



Beautiful responsive Bootstrap 5 UI



Datasets





blood_bank_branches.csv – 12 real blood banks in Vijayawada



inventory.csv, donors.csv, appointments.csv, orders.csv – 50+ realistic sample records for the sample branch (Vijaya Sri Blood Bank)



Tech Stack





Backend: Python Flask + SQLAlchemy + Flask-Login



Database: SQLite (file-based, no extra install)



Frontend: HTML5 + Bootstrap 5 + Custom CSS + Chart.js



ML: scikit-learn (Random Forest)



Data: Pandas





How to Run in VS Code (Clear Step-by-Step)



1. Prerequisites





Python 3.9 or higher installed



VS Code installed



(Optional) Git



2. Open Project





Download / extract the LifeFlow_BloodBank folder



Open VS Code → File → Open Folder → select LifeFlow_BloodBank



3. Create Virtual Environment (Recommended)

Open VS Code Terminal (Ctrl + ~ or View → Terminal) and run:

python -m venv venv

Activate it:





Windows:

venv\Scripts\activate





Mac / Linux:

source venv/bin/activate



4. Install Dependencies

pip install -r requirements.txt



5. Run the Application

python app.py

You will see:

Admin created: admin / admin123
Branches loaded
Inventory loaded
...
 * Running on http://127.0.0.1:5000



6. Open in Browser

Go to: http://127.0.0.1:5000

7. Login Credentials (Pre-created)







Username



Password



Role





admin



admin123



admin

You can also register new users from the Register page.

8. Public Donor Form

Direct link: http://127.0.0.1:5000/donor_register





Project Structure

LifeFlow_BloodBank/
├── app.py                 # Main Flask application
├── requirements.txt
├── README.md
├── data/                  # CSV datasets
│   ├── blood_bank_branches.csv
│   ├── inventory.csv
│   ├── donors.csv
│   ├── appointments.csv
│   └── orders.csv
├── models/                # ML model (auto-generated)
├── instance/              # SQLite database (auto-created)
├── static/
│   ├── css/style.css
│   ├── images/logo.png
│   └── js/
└── templates/             # All HTML pages
    ├── base.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── capacity.html
    ├── appointments.html
    ├── orders.html
    ├── donors.html
    ├── eligibility.html
    ├── prediction.html
    ├── about.html
    ├── admin.html
    └── donor_register.html



Pages Overview





Login / Register – Secure authentication



Home (Dashboard) – Stats + Blood type chart + Quick actions



Capacity & Stock – All Vijayawada branches + Inventory CRUD



Appointments – Schedule & manage donor appointments



Orders – Hospital blood requests tracking



Donors – Full donor database with eligibility



Eligibility – Interactive checker



Prediction – ML-based “will donate again?” predictor



Admin – User & system stats (admin only)



About – Project info



Public Donor Registration



Notes for Presentation





Show the real Vijayawada blood bank list first



Demonstrate live CRUD (add a bag / appointment / order)



Run Eligibility check live



Show ML Prediction with different Recency values



Highlight the community impact of the CSP project



Troubleshooting





Port already in use → change port=5000 to port=5001 in app.py



Module not found → make sure venv is activated and pip install -r requirements.txt ran successfully



Database errors → delete instance/lifeflow.db and re-run python app.py



Made with ❤️ for Vijayawada | CSP Lab 2026
