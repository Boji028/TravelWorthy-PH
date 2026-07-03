from app import create_app, db
from models.visa import VisaCountry

app = create_app()
with app.app_context():
    db.create_all()
    print("Visa table created!")
