from datetime import datetime, timedelta, timezone
import pytz
from werkzeug.security import generate_password_hash, check_password_hash

from utils.response import Response
from . import db
from apscheduler.schedulers.blocking import BlockingScheduler
from utils.auth_exceptions import *


def time_left(date1, date2):
    timezone = pytz.timezone('Asia/Jerusalem')
    if date1.tzinfo is None:
        date1 = timezone.localize(date1)
    if date2.tzinfo is None:
        date2 = timezone.localize(date2)
    difference = date2 - date1
    minute = timedelta(minutes=3)
    return difference <= minute





class VerifiedUsers(db.Model):
    email = db.Column(db.String(64), nullable=False, primary_key=True)
    date_send = db.Column(db.DateTime(), default=datetime.now())

    def save(self):
        db.session.add(self)
        db.session.commit()

    def remove(self):
        db.session.delete(self)
        db.session.commit()

    def update_field(self, field, value):
        if hasattr(self, field):
            setattr(self, field, value)
            self.save()
        else:
            raise AttributeError("Invalid field name.")

    @classmethod
    def get_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    def toJSON(self):
        return self.toDICT()

    @staticmethod
    def create_verified_user(_email):
        v = VerifiedUsers(email = _email,date_send = datetime.now())
        VerifiedUsers.update(v)



    @staticmethod
    def update(verification):
        old_code = VerifiedUsers.get_by_email(verification.email)
        if old_code:
            old_code.update_field('date_send', datetime.now())
        else:
            verification.save()







