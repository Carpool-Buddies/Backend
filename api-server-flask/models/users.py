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
    approved = db.Column(db.Boolean(), default=False) #TODO: Change this to date and reapproved evrey year
    date_joined = db.Column(db.DateTime(), default=datetime.now())

    def __repr__(self):
        return f"User {self.email}"

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def register_user(_email, _password, _first_name, _last_name, _phone_number, _birthday):
        if Users.get_by_email(_email):
            raise EmailAlreadyExistsError(_email)

        new_user = Users(
            email=_email,
            first_name=_first_name,
            last_name=_last_name,
            phone_number=_phone_number,
            birthday=datetime.strptime(_birthday, "%Y-%m-%d")
        )
        new_user.set_password(_password)
        new_user.save()

        return new_user

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def update_email(self, new_email):
        self.email = new_email

    def approve(self):
        self.approved = True
        db.session.commit()

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

    def to_profile(self):
        return {"id": self.id,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "phone_number": self.phone_number,
                "approved": self.approved,
                "birthday": self.birthday
                }

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
                elif key == "birthday":
                    # Convert the birthday to a date object
                    value = value.date()
                    setattr(self, key, value)
                else:
                    setattr(self, key, value)
            self.save()
        except Exception as e:
            print(f"Error updating user details: {str(e)}")
            db.session.rollback()
            raise Exception("Failed to update user details") from e

    # def update_user_details(self, new_details):
    #     """
    #     Updates the user details with new information.
    #
    #     Parameters:
    #     - new_details: dict, a dictionary containing the updated details for the user
    #
    #     Raises:
    #     - Exception: If an error occurs during the update process
    #     """
    #     try:
    #         for key, value in new_details.items():
    #             if key == "password":
    #                 self.set_password(value)
    #             # if key == "birthday":
    #             #     value = datetime.strptime(value, '%Y-%m-%d')
    #             else:
    #                 setattr(self, key, value)
    #         self.save()
    #     except Exception as e:
    #         print(f"Error updating user details: {str(e)}")
    #         db.session.rollback()
    #         raise Exception("Failed to update user details") from e
