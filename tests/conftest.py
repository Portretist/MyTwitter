import pytest

from main.routes import create_app
from main.models import User, Like, Follow, Tweet, db as _db


@pytest.fixture
def app():
    _app = create_app()
    _app.config["TESTING"] = True
    _app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = "postgresql+psycopg2://tweetereshka:tweetereshka@localhost/tweetereshka"
    with _app.app_context():
        _db.create_all()

        user_1 = User(name="test_user_1", api_key="test_1", followers="2,3,")
        user_2 = User(name="test_user_2", api_key="test_2", followings="1,3,")
        user_3 = User(
            name="test_user_3", api_key="test_3", followers="2,", followings="1,"
        )
        user_4 = User(name="test_user_4", api_key="test_4")
        _db.session.add_all([user_1, user_2, user_3, user_4])
        _db.session.commit()

        tweet_1 = Tweet(text="test_tweet_1", author=user_1.id, likes="1,2,")
        tweet_2 = Tweet(text="test_tweet_2", author=user_3.id, likes="3,")
        tweet_3 = Tweet(text="test_tweet_3", author=user_2.id)
        _db.session.add_all([tweet_1, tweet_2, tweet_3])
        _db.session.commit()

        like_1 = Like(user_id=user_2.id, tweet_id=tweet_1.id)
        like_2 = Like(user_id=user_3.id, tweet_id=tweet_1.id)
        like_3 = Like(user_id=user_2.id, tweet_id=tweet_2.id)
        follow = Follow(follower_id=user_2.id, following_id=user_1.id)
        _db.session.add_all([like_1, like_2, like_3, follow])
        _db.session.commit()

        yield _app
        _db.session.close()
        _db.drop_all()


@pytest.fixture
def client(app):
    client = app.test_client()
    yield client
