# r4a1221021/flaskproject1-2/FlaskProject1-2-b35aea4865849d4948fb8a1e18280a969282046f/models.py

import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ユーザーとグループの中間テーブル (変更なし)
user_group_association = db.Table('user_group_association',
                                  db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                                  db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
                                  )


class User(UserMixin, db.Model):
    """ ユーザーモデル """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    requests = db.relationship('SupportRequest', backref='author', lazy=True)
    sos_signals = db.relationship('SOSSignal', backref='author', lazy=True)
    chat_messages = db.relationship('ChatMessage', backref='author', lazy=True)
    community_posts = db.relationship('CommunityPost', backref='author', lazy=True)
    groups = db.relationship('Group', secondary=user_group_association, lazy='subquery',
                             backref=db.backref('members', lazy=True))
    group_chat_messages = db.relationship('GroupChatMessage', backref='author', lazy=True)
    # shelter_logs relationship removed

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --- その他のモデル (変更なし) ---
class SupportRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    priority = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class SOSSignal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class CommunityPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.now)
    chat_messages = db.relationship('GroupChatMessage', backref='group', lazy=True)

class GroupChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)


# --- 修正: 避難所モデル (シンプル版) ---
class Shelter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    capacity = db.Column(db.Integer, nullable=False) # 収容可能人数
    # current_occupancy, latitude, longitude, logs relationship removed

# --- 削除: ShelterLog モデル ---
# class ShelterLog(db.Model): ... は削除