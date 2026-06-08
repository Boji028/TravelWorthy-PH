from app import create_app
import sqlite3

app = create_app()
with app.app_context():
    conn = sqlite3.connect('instance/travel_agency.db')
    try:
        conn.execute("ALTER TABLE visa_countries ADD COLUMN requirements_pdf VARCHAR(300)")
        conn.commit()
        print('visa_countries table updated!')
    except Exception as e:
        print(f'Note: {e}')
    conn.close()