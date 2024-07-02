from api import app, db, socketio
from apscheduler.schedulers.background import BackgroundScheduler

from models import Users
from services.auth_service import AuthService
import atexit
import jwt
from api.config import BaseConfig

@app.shell_context_processor
def make_shell_context():
    return {"app": app, "db": db}

def check_token_expiry():
    users = Users.query.all()
    for user in users:
        if user.jwt_auth_active:
            token = jwt.encode({'email': user.email, 'user_id': user.id}, BaseConfig.SECRET_KEY)
            try:
                jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                user.set_jwt_auth_active(False)
                db.session.commit()
                socketio.emit('disconnect', {'user_id': user.id})

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(AuthService.send_clean_database, 'cron', hour=0, minute=10)
    scheduler.add_job(check_token_expiry, 'interval', minutes=5)
    scheduler.start()
    app.scheduler = scheduler
    atexit.register(lambda: scheduler.shutdown())
    socketio.run(app, debug=True, host="0.0.0.0", allow_unsafe_werkzeug=True)