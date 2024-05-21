from datetime import datetime, timedelta


class LoginAttemptTracker:
    def __init__(self):
        self.attempts = {}

    def register_attempt(self, email):
        if email not in self.attempts:
            self.attempts[email] = []
        self.attempts[email].append(datetime.now())

    def get_attempts(self, email):
        if email not in self.attempts:
            return 0
        now = datetime.now()
        self.attempts[email] = [attempt for attempt in self.attempts[email] if now - attempt < timedelta(minutes=15)]
        return len(self.attempts[email])

    def clear_attempts(self, email):
        if email in self.attempts:
            del self.attempts[email]
