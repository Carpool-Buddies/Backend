from flask_socketio import emit
from models import Users, Notification, Message
from api.socketio_init import socketio

class NotificationService:
    @staticmethod
    def send_notification_to_user(user_id, message):
        """Send a notification to a single user"""
        user = Users.query.get(user_id)
        if user:
            if user.jwt_auth_active:
                emit('notification', {'message': message, 'user_id': user_id}, room=user_id)
            else:
                notification = Notification(user_id=user_id, message=message)
                notification.save()

    @staticmethod
    def send_notification_to_group(user_ids, message):
        """Send a notification to a group of users"""
        for user_id in user_ids:
            user = Users.query.get(user_id)
            if user:
                if user.jwt_auth_active:
                    emit('notification', {'message': message, 'user_id': user_id}, room=user_id)
                else:
                    notification = Notification(user_id=user_id, message=message)
                    notification.save()

    @staticmethod
    def send_message_between_users(sender_id, receiver_id, message):
        """Send a message between two users"""
        sender = Users.query.get(sender_id)
        receiver = Users.query.get(receiver_id)
        if sender and receiver:
            if receiver.jwt_auth_active:
                emit('message', {'message': message, 'sender_id': sender_id, 'receiver_id': receiver_id}, room=receiver_id)
            else:
                msg = Message(sender_id=sender_id, receiver_id=receiver_id, message=message)
                msg.save()

    @staticmethod
    def handle_login_notifications(user_id):
        """Fetch and send stored notifications and messages on user login"""
        notifications = Notification.query.filter_by(user_id=user_id, seen=False).all()
        for notification in notifications:
            socketio.emit('notification', {'message': notification.message, 'user_id': user_id}, room=user_id)
            notification.seen = True
            notification.save()

        messages = Message.query.filter_by(receiver_id=user_id, seen=False).all()
        for message in messages:
            socketio.emit('message', {'message': message.message, 'sender_id': message.sender_id, 'receiver_id': user_id}, room=user_id)
            message.seen = True
            message.save()
