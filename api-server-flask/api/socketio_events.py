from api import socketio
from flask import request
from flask_socketio import emit, join_room, leave_room
from models import Users
from services.notification_service import NotificationService
import jwt
from api.config import BaseConfig

@socketio.on('connect')
def handle_connect():
    token = request.args.get('token')
    try:
        decoded_token = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token['user_id']
        user = Users.query.get(user_id)
        if user:
            user.set_jwt_auth_active(True)
            user.save()
            join_room(user_id)
            emit('connected', {'message': 'User connected successfully'})
    except jwt.ExpiredSignatureError:
        emit('error', {'message': 'Token has expired'})
    except jwt.InvalidTokenError:
        emit('error', {'message': 'Invalid token'})

@socketio.on('disconnect')
def handle_disconnect():
    token = request.args.get('token')
    try:
        decoded_token = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token['user_id']
        user = Users.query.get(user_id)
        if user:
            user.set_jwt_auth_active(False)
            user.save()
            leave_room(user_id)
            emit('disconnected', {'message': 'User disconnected successfully'})
    except jwt.ExpiredSignatureError:
        emit('error', {'message': 'Token has expired'})
    except jwt.InvalidTokenError:
        emit('error', {'message': 'Invalid token'})

@socketio.on('message')
def handle_message(data):
    sender_id = data['sender_id']
    receiver_id = data['receiver_id']
    message = data['message']
    NotificationService.send_message_between_users(sender_id, receiver_id, message)

@socketio.on('notification')
def handle_notification(data):
    user_ids = data.get('user_ids')
    message = data['message']
    if user_ids:
        NotificationService.send_notification_to_group(user_ids, message)
    else:
        user_id = data['user_id']
        NotificationService.send_notification_to_user(user_id, message)
