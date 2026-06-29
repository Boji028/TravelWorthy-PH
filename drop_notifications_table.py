from app import create_app, db

app = create_app()
with app.app_context():
    db.session.execute(db.text('DROP TABLE IF EXISTS inquiry_notifications'))
    db.session.commit()
    print("Dropped inquiry_notifications table.")