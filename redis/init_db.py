from auth.auth import hash_password
from data import db as database
from data import models

def init():
    database.Base.metadata.create_all(bind=database.engine)

    db = database.SessionLocal()
    if not db.query(models.User).filter_by(username="admin").first():
        admin = models.User(
            username="admin",
            hashed_password=hash_password("secret"),
            age=30
        )
        db.add(admin)
        db.commit()
    db.close()

if __name__ == "__main__":
    init()
