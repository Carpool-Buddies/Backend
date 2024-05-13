from datetime import datetime, timedelta, timezone

from werkzeug.security import generate_password_hash, check_password_hash
from . import db

from utils.auth_exceptions import *


class VerificationCodes(db.Model):
    email = db.Column(db.String(64), nullable=False, primary_key=True)
    code = db.Column(db.Text())
    date_send = db.Column(db.DateTime(), default=datetime.utcnow())

    def save(self):
        try:

            db.session.add(self)
            db.session.commit()
        except Exception as e:
            pass

    @staticmethod
    def send_code(_verification_code):
        if VerificationCodes.get_by_email(_verification_code.email):
            old_code = VerificationCodes.get_by_email(_verification_code.email)
            old_code.update_field('code', _verification_code.code)
            old_code.update_field('date_send',datetime.utcnow())
        else:
            _verification_code.save()

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
