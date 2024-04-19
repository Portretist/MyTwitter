from typing import Any, Dict

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False)
    api_key = db.Column(db.String(200), nullable=False)

    followers = db.Column(db.String, default="There's no one here yet")
    followings = db.Column(db.String, default="There's no one here yet")


class Image(db.Model):
    __tablename__ = "image"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data = db.Column(db.String, nullable=False)

    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"))


class Tweet(db.Model):
    __tablename__ = "tweet"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.String, nullable=False)
    attachments = db.Column(db.String)
    likes = db.Column(db.String, default="There's no one here yet")

    author = db.Column(db.Integer, db.ForeignKey("user.id"))

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Like(db.Model):
    __tablename__ = "like"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    tweet_id = db.Column(db.Integer, db.ForeignKey("tweet.id"))


class Follow(db.Model):
    __tablename__ = "follow"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    follower_id = db.Column(db.Integer, db.ForeignKey("user.id"))  # кто подписывается
    following_id = db.Column(
        db.Integer, db.ForeignKey("user.id")
    )  # на кого подписываются
