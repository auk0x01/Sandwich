from app import app, db, User
import os

with app.app_context():
    db.create_all()
    admin = User('admin', 'admin@sandwich', os.environ['ADMIN_PASSWORD'])
    db.session.add(admin)
    db.session.commit()
