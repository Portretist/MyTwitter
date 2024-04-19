import io
import os


def test_get_user_info_by_wrong_id(client):
    response = client.get("/api/users/117")
    assert response.json["result"] is False


def test_get_user_info_by_id(client):
    response = client.get("/api/users/1")
    assert response.json["result"] is True
    assert response.json["user"]["name"] == "test_user_1"


def test_get_user_info_by_api_key(client):
    response = client.get("/api/users/me?api_key=test_2")
    assert response.json["result"] is True
    assert response.json["user"]["name"] == "test_user_2"


def test_get_user_info_by_wrong_api_key(client):
    response = client.get("/api/users/me?api_key=test")
    assert response.json["result"] is False


def test_get_tweet_from_user_followings_by_author_followers_count(client):
    response = client.get("/api/tweets?api_key=test_2")
    assert response.json["result"] is True


def test_get_tweet_from_user_followings_without_followings(client):
    response = client.get("/api/tweets?api_key=test_4")
    assert response.json["result"] is False
    print(response.json)
    assert response.json["error_message"] == "You don't follow on any user"


def test_create_new_tweet_and_add_to_database(client):
    response = client.post(
        "/api/tweets?api_key=test_2",
        json={"tweet_data": "new_test_tweet", "tweet_media_ids": [1]},
    )
    assert response.json["result"] is True
    assert response.json["tweet_id"] == 4


def test_create_new_tweet_and_add_to_database_without_data(client):
    response = client.post("/api/tweets?api_key=test_2")
    assert response.json["result"] is False


def test_save_user_image_in_db(client):
    image = "test_image.jpg"
    data = {"image": (open("./tests/" + image, "rb"), image)}
    response = client.post("/api/media?api_key=test_1", data=data)
    assert response.json["result"] is True
    assert response.json["media_id"] == 1
    os.remove(os.path.join("static", "images", f"1_{image}"))


def test_save_user_image_in_db_with_wrong_content_type(client):
    image = "test_image.txt"
    data = {"image": (io.BytesIO(b"some bite"), image)}
    response = client.post("/api/media?api_key=test_1", data=data)
    assert response.json["result"] is False
    assert response.json["error_message"] == "Only JPEG images are allowed"


def test_add_like_to_tweet(client):
    response = client.post("/api/tweets/1/likes?api_key=test_1")
    assert response.json["result"] is True


def test_add_like_to_tweet_with_wrong_id(client):
    response = client.post("/api/tweets/172/likes?api_key=test_1")
    assert response.json["result"] is False


def test_add_double_like_to_tweet(client):
    response = client.post("/api/tweets/1/likes?api_key=test_1")
    response = client.post("/api/tweets/1/likes?api_key=test_1")
    assert response.json["result"] is False
    assert response.json["error_message"] == "You have already liked this tweet"


def test_following_on_user(client):
    response = client.post("/api/users/2/follow?api_key=test_1")
    assert response.json["result"] is True


def test_double_following_on_user(client):
    response = client.post("/api/users/2/follow?api_key=test_1")
    response = client.post("/api/users/2/follow?api_key=test_1")
    assert response.json["result"] is False
    assert response.json["error_message"] == "You have already following on this user"


def test_follow_yourself(client):
    response = client.post("/api/users/1/follow?api_key=test_1")
    assert response.json["result"] is False
    assert response.json["error_message"] == "You can't follow yourself"


def test_delete_tweet_by_tweet_id(client):
    response = client.delete("/api/tweets/1?api_key=test_1")
    assert response.json["result"] is True


def test_delete_tweet_by_tweet_id_with_wrong_api_key(client):
    response = client.delete("/api/tweets/1?api_key=test_2")
    assert response.json["result"] is False
    assert response.json["error_type"] == PermissionError.__name__
    assert (
        response.json["error_message"]
        == "You do not have permission to delete this tweet"
    )


def test_remove_like_from_tweet(client):
    response = client.delete("/api/tweets/1/likes?api_key=test_2")
    assert response.json["result"] is True


def test_remove_like_from_tweet_without_likes(client):
    response = client.delete("/api/tweets/3/likes?api_key=test_1")
    assert response.json["result"] is False


def test_unfollowing_from_user(client):
    response = client.delete("/api/users/1/follow?api_key=test_2")
    assert response.json["result"] is True


def test_unfollowing_from_user_without_follow_on_it(client):
    response = client.delete("/api/users/2/follow?api_key=test_3")
    assert response.json["result"] is False
    assert response.json["error_message"] == "You don't follow on this user"
