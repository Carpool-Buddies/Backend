# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from api import app, db
from apscheduler.schedulers.background import BackgroundScheduler
from services.auth_service import AuthService
import atexit


@app.shell_context_processor
def make_shell_context():
    return {"app": app,
            "db": db
            }


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(AuthService.send_clean_database, 'cron', hour=0, minute=10)
    scheduler.start()
    app.scheduler = scheduler
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    app.run(debug=True, host="0.0.0.0")
