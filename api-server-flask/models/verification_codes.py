from datetime import datetime, timedelta, timezone
import pytz
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

from utils.auth_exceptions import *


def time_left(date1, date2):
    israel_timezone = pytz.timezone('Israel')
    new_date = israel_timezone.localize(date1)
    difference = date2 - new_date
    minute = timedelta(minutes=3)
    return difference <= minute


class VerificationCodes(db.Model):
    email = db.Column(db.String(64), nullable=False, primary_key=True)
    code = db.Column(db.Text())
    date_send = db.Column(db.DateTime(), default=datetime.now(pytz.timezone('Israel')))

    def save(self):
        db.session.add(self)
        db.session.commit()

    def remove(self):
        db.session.delete(self)
        db.session.commit()


    @staticmethod
    def send_code(_verification_code):
        _verification_code.hash_code()
        old_code = VerificationCodes.get_by_email(_verification_code.email)
        if old_code:
            old_code.update_field('code', _verification_code.code)
            old_code.update_field('date_send', datetime.now(pytz.timezone('Israel')))
        else:
            _verification_code.save()

    @staticmethod
    def verify_user(_email, _code):
        user_code = VerificationCodes.get_by_email(_email)
        if user_code:
            is_correct_code = user_code.check_code(_code)
            if not is_correct_code:
                raise Exception("Code is incorrect")
            user_code.remove()
            in_time = time_left(user_code.date_send, datetime.now(pytz.timezone('Israel')))
            if not in_time:
                raise Exception("The code is expired")
            return True
        else:
            raise Exception("User is not exist")

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

    def hash_code(self):
        self.code = generate_password_hash(str(self.code))

    def check_code(self, new_code):
        return check_password_hash(self.code, new_code)
