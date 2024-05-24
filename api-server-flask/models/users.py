from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from . import db

from utils.auth_exceptions import *


class Users(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.Text())
    first_name = db.Column(db.String(32), nullable=False)
    last_name = db.Column(db.String(32), nullable=False)
    phone_number = db.Column(db.String(32), nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    jwt_auth_active = db.Column(db.Boolean())
    approved = db.Column(db.Boolean())
    date_joined = db.Column(db.DateTime(), default=datetime.now())

    def __repr__(self):
        return f"User {self.email}"

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def register_user(user):
        if Users.get_by_email(user.email):
            raise EmailAlreadyExistsError(user.email)

        new_user = Users(
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone_number=user.phone_number,
            birthday=datetime.strptime(user.birthday, "%Y-%m-%d")
        )
        new_user.set_password(user.password)
        new_user.save()

        return new_user

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def update_email(self, new_email):
        self.email = new_email

    def update_field(self, field, value):
        if hasattr(self, field):
            setattr(self, field, value)
            self.save()
        else:
            raise AttributeError("Invalid field name.")

    def check_jwt_auth_active(self):
        return self.jwt_auth_active

    def set_jwt_auth_active(self, set_status):
        self.jwt_auth_active = set_status

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)

    @classmethod
    def get_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    def toDICT(self):
        cls_dict = {}
        cls_dict['_id'] = self.id
        cls_dict['email'] = self.email

        return cls_dict

    def toJSON(self):
        return self.toDICT()

    def update_user_details(self, new_details):
        """
        Updates the user details with new information.

        Parameters:
        - new_details: dict, a dictionary containing the updated details for the user

        Raises:
        - Exception: If an error occurs during the update process
        """
        try:
            for key, value in new_details.items():
                if key == "password":
                    self.set_password(value)
                # if key == "birthday":
                #     value = datetime.strptime(value, '%Y-%m-%d')
                setattr(self, key, value)
            self.save()
        except Exception as e:
            print(f"Error updating user details: {str(e)}")
            db.session.rollback()
            raise Exception("Failed to update user details") from e
