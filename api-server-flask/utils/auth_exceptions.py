class EmailValidationError(Exception):
    """Exception raised for errors in the email format."""

    def __init__(self, message=None):
        if message is None:
            message = "Invalid email format."
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

class EmailAlreadyExistsError(Exception):
    """Exception raised when an email already exists in the database."""

    def __init__(self, email):
        self.email = email
        super().__init__(self.__str__())
        self.send_email_notification()

    def __str__(self):
        return f"Email {self.email} already exists."

    def send_email_notification(self):
        # TODO: Placeholder for email sending logic
        print(f"Sending email notification to {self.email}.")

class InvalidBirthdayError(Exception):
    """Exception raised for errors in the birthday format or value."""

    def __init__(self, message=None):
        if message is None:
            message = "Invalid birthday provided."
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

class PasswordValidationError(Exception):
    """Exception raised for password validation errors with a specific message."""

    def __init__(self, message=None):
        if message is None:
            message = "Invalid password format"
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

class PhoneNumberValidationError(Exception):
    """Exception raised for phone number validation errors with a specific message."""

    def __init__(self, message=None):
        if message is None:
            message = "Invalid phone number format"
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class TooManyLoginAttemptsError(Exception):
    """Exception raised when too many login attempts are detected."""

    def __init__(self, message="Too many login attempts. Please try again later."):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

