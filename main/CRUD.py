import os.path
from typing import Any, Dict, Tuple

from sqlalchemy import delete, select, update
from sqlalchemy.exc import NoResultFound
from werkzeug.utils import secure_filename

from .models import Follow, Image, Like, Tweet, User, db


class CRUD:
    result = {"result": True}

    def __init__(self):
        self.tasks = {
            "create": {
                "tweet": self.create_tweet,
                "image": self.add_image,
                "like": self.create_like,
                "follow": self.create_follow,
            },
            "read": {
                "user": self.get_user_information_by_id,
                "tweet": self.get_tweets_by_popular_followings,
            },
            "update": {
                "cur_user": self.update_current_user,
            },
            "delete": {
                "tweet": self.delete_tweet,
                "like": self.delete_like,
                "follow": self.delete_follow,
            },
        }

    def create_tweet(self, data: Dict) -> Dict:
        tweet_data = data["text"]
        tweet_author = data["author"]

        if len(data) > 2:
            tweet_media_ids = data["images"]
            tweet_media_ids = [str(num) for num in tweet_media_ids]
            tweet_media_ids = ",".join(tweet_media_ids)
            tweet = Tweet(
                text=tweet_data, attachments=tweet_media_ids, author=tweet_author
            )
        else:
            tweet = Tweet(text=tweet_data, author=tweet_author)

        db.session.add(tweet)
        db.session.commit()
        cur_res = self.result.copy()
        db.session.refresh(tweet)
        cur_res["tweet_id"] = tweet.id

        return cur_res

    def add_image(self, data: Tuple) -> Dict:
        image = data[0]
        if image.content_type == "image/jpeg":
            filename = f"{str(data[1])}_{secure_filename(image.filename)}"
            path_to_file = os.path.abspath(os.path.join("static", "images", filename))
            img = Image(data=path_to_file, owner_id=data[1])
            with open(path_to_file, "wb") as file:
                file.write(image.read())
            db.session.add(img)
            db.session.commit()
            cur_res = self.result.copy()
            db.session.refresh(img)
            cur_res["media_id"] = img.id

            return cur_res
        else:
            raise TypeError("Only JPEG images are allowed")

    def create_like(self, data: Dict) -> Dict:
        tweet_id = data["tweet_id"]
        user = data["cur_user"]

        try:
            test = db.session.execute(
                select(Like.user_id).where(
                    Like.tweet_id == tweet_id, Like.user_id == user
                )
            ).fetchone()[0]
            if test == user:
                raise PermissionError("You have already liked this tweet")
        except TypeError:
            like = Like(tweet_id=tweet_id, user_id=user)
            db.session.add(like)
            db.session.commit()
            db.session.refresh(like)
            like_id = like.id
            cur_likes = db.session.execute(
                select(Tweet.likes).where(Tweet.id == tweet_id)
            ).fetchone()[0]
            cur_likes = self._add_id_to_string(cur_likes, like_id)

            db.session.execute(
                update(Tweet).where(Tweet.id == tweet_id).values(likes=cur_likes)
            )
            db.session.commit()

            return self.result

    def create_follow(self, data: Dict) -> Dict:
        follower_id = data["cur_user"]
        following_id = data["following_id"]
        if follower_id != following_id:
            try:
                test = db.session.execute(
                    select(Follow.following_id).where(
                        Follow.following_id == following_id,
                        Follow.follower_id == follower_id,
                    )
                ).fetchone()
                if test[0] == following_id:
                    raise PermissionError("You have already following on this user")

            except TypeError:
                follow = Follow(follower_id=follower_id, following_id=following_id)
                db.session.add(follow)

                try:
                    follower_followings = db.session.execute(
                        select(User.followings).where(User.id == follower_id)
                    ).fetchone()[
                        0
                    ]  # Кто подписывается
                    following_followers = db.session.execute(
                        select(User.followings).where(User.id == following_id)
                    ).fetchone()[
                        0
                    ]  # На кого подписываются
                except TypeError:
                    raise IndexError(f"User with id {following_id} does not exist")

                follower_followings = self._add_id_to_string(
                    follower_followings, following_id
                )  # Кто подписывается
                following_followers = self._add_id_to_string(
                    following_followers, follower_id
                )  # На кого подписываются

                db.session.execute(
                    update(User)
                    .where(User.id == follower_id)
                    .values(followings=follower_followings)
                )  # Кто подписывается
                db.session.execute(
                    update(User)
                    .where(User.id == following_id)
                    .values(followers=following_followers)
                )  # На кого подписываются

                db.session.commit()
                return self.result

        raise PermissionError("You can't follow yourself")

    def delete_tweet(self, data: Dict) -> Dict:
        tweet_id = data["tweet_id"]
        cur_user_id = data["cur_user"]

        response_data = db.session.execute(
            select(Tweet.author, Tweet.likes).where(Tweet.id == tweet_id)
        ).fetchone()
        tweet_author, tweet_likes = response_data

        if int(tweet_author) == cur_user_id:
            tweet_likes = list(
                map(
                    lambda item: int(item),
                    filter(lambda item: item.isdigit(), tweet_likes),
                )
            )
            [
                db.session.execute(delete(Like).where(Like.id == like_id))
                for like_id in tweet_likes
            ]
            db.session.commit()
            db.session.execute(delete(Tweet).where(Tweet.id == tweet_id))
            db.session.commit()

            return self.result

        raise PermissionError("You do not have permission to delete this tweet")

    def delete_like(self, data: Dict) -> Dict:
        like_id = db.session.execute(
            select(Like.id).where(
                Like.tweet_id == data["tweet_id"] and Like.user_id == data["cur_user"]
            )
        ).fetchone()[0]
        tweet_id = db.session.execute(
            select(Like.tweet_id).where(Like.id == like_id)
        ).fetchone()[0]
        tweet_likes = db.session.execute(
            select(Tweet.likes).where(Tweet.id == tweet_id)
        ).fetchone()[0]

        try:
            new_likes = self._remove_id_from_string(tweet_likes, like_id)
        except ValueError:
            raise ValueError("This tweet does not have any like")

        db.session.execute(
            update(Tweet).where(Tweet.id == tweet_id).values(likes=new_likes)
        )
        db.session.execute(delete(Like).where(Like.id == like_id))
        db.session.commit()

        return self.result

    def delete_follow(self, data: Dict) -> Dict:
        follower_id = data["cur_user"]
        following_id = data["following_id"]

        follower_followings = db.session.execute(
            select(User.followings).where(User.id == follower_id)
        ).fetchone()[
            0
        ]  # Кто подписывается
        following_followers = db.session.execute(
            select(User.followers).where(User.id == following_id)
        ).fetchone()[
            0
        ]  # На кого подписываются

        try:
            follower_followings = self._remove_id_from_string(
                follower_followings, following_id
            )  # Кто подписывается
            following_followers = self._remove_id_from_string(
                following_followers, follower_id
            )  # На кого подписываются
        except ValueError:
            raise ValueError("You don't follow on this user")

        db.session.execute(
            update(User)
            .where(User.id == follower_id)
            .values(followings=follower_followings)
        )  # Кто подписывается
        db.session.execute(
            update(User)
            .where(User.id == follower_id)
            .values(followings=following_followers)
        )  # На кого подписываются

        db.session.execute(
            delete(Follow).where(
                Follow.following_id == following_id
                and Follow.follower_id == follower_id
            )
        )

        db.session.commit()

        return self.result

    def get_tweets_by_popular_followings(self, data: Dict) -> Dict:
        user_id = data["cur_user"]
        with db.session.no_autoflush:
            all_followings = (
                db.session.execute(select(User.followings).where(User.id == user_id))
                .fetchone()[0]
                .split(",")
            )

            try:
                all_followings = [
                    self.get_user_information_by_id({"cur_user": int(id)})["user"]
                    for id in all_followings
                    if id != ""
                ]
            except ValueError:
                raise ValueError("You don't follow on any user")

            tweets = []
            for following in all_followings:
                tweets.append(self._get_tweet_by_author(following))

            tweets.sort(key=lambda tweet: len(tweet.likes), reverse=True)
            cur_res = self.result.copy()
            cur_res["tweets"] = [tweet.to_json() for tweet in tweets]
        return cur_res

    def get_user_information_by_id(self, user_data: Dict):
        user_id = user_data["cur_user"]
        keys = ("id", "name", "followers", "followings")

        try:
            values = db.session.execute(
                select(User.name, User.followers, User.followings).where(
                    User.id == user_id
                )
            ).fetchall()[0]
        except NoResultFound:
            raise IndexError(f"User with id {user_id} does not exist")

        name, followers, followings = values
        values = user_id, name, followers, followings
        info = {keys[i]: values[i] for i in range(len(keys))}
        cur_res = self.result.copy()
        cur_res["user"] = info
        return cur_res

    def update_current_user(self, api_key: int) -> Dict:
        user_id = db.session.execute(
            select(User.id).where(User.api_key == api_key)
        ).fetchone()[0]
        return {"cur_user": user_id, "api_key": api_key}

    def _get_tweet_by_author(self, author_info: Dict) -> Dict:
        tweet = db.session.execute(
            select(Tweet).where(Tweet.author == author_info["id"])
        ).fetchone()[0]
        tweet.author = {"id": tweet.author, "name": author_info["name"]}
        likes = tweet.likes
        attachments = tweet.attachments
        if likes:
            likes = [
                self._get_like_info_by_id(int(like_id))
                for like_id in likes.split(",")
                if like_id != ""
            ]
            tweet.likes = likes
        if attachments:
            attachments = [
                self._get_image_link_by_id(int(image_id))
                for image_id in attachments.split(",")
            ]
            tweet.attachments = attachments

        return tweet

    def _get_image_link_by_id(self, image_id: int) -> str:
        try:
            return db.session.execute(
                select(Image.data).where(Image.id == image_id)
            ).fetchone()[0]
        except NoResultFound:
            raise ValueError(f"Image with id {image_id} does not exist")

    def _get_like_info_by_id(self, like_id: int) -> Dict:
        with db.session.no_autoflush:
            user_id = db.session.execute(
                select(Like.user_id).where(Like.id == like_id)
            ).fetchone()[0]
            username = db.session.execute(
                select(User.name).where(User.id == user_id)
            ).fetchone()[0]
        return {"user_id": user_id, "name": username}

    def _add_id_to_string(self, string: str, id: int) -> str:
        if string == "There's no one here yet":
            string = ""
        string += str(id) + ","
        return string

    def _remove_id_from_string(self, string: str, id: int) -> str:
        if string != "There's no one here yet":
            string = string.split(",")
            string.remove(str(id))
            if len(string) > 1:
                string = ",".join(string)
            else:
                string = "There's no one here yet"
            return string

        raise ValueError


crud = CRUD()


def core(data: Any, task: str, object: str):
    try:
        func = crud.tasks[task][object]
        return func(data)
    except Exception as e:
        return {
            "result": False,
            "error_type": e.__class__.__name__,
            "error_message": str(e),
        }, 500
