# File: database_setup.py
from app import app, db

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("Database tables created successfully in 'school_routes.db'.")