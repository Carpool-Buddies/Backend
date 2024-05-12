class EmailValidationError(Exception):
    """Exception raised for errors in the email format."""
    pass

class EmailAlreadyExistsError(Exception):
    """Exception raised when an email already exists in the database."""
    pass

class InvalidBirthdayError(Exception):
    """Exception raised for errors in the birthday format or value."""
    pass

class PasswordValidationError(Exception):
    """Exception raised for password validation errors with a specific message."""
    pass

class PhoneNumberValidationError(Exception):
    """Exception raised for password validation errors with a specific message."""
    pass


