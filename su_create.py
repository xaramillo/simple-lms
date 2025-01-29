from app import User, db
admin = User(username='admin')
admin.set_password('password123')
db.session.add(admin)
db.session.commit()