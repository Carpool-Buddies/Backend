class Response:
    def __init__(self, success, message, status_code, data=None):
        self.success = success
        self.message = message
        self.status_code = status_code
        self.data = data

    def to_dict(self):
        response = {
            "success": self.success,
            "msg": self.message
        }
        if self.data:
            response.update(self.data)
        return response

    def to_tuple(self):
        return self.to_dict(), self.status_code
