from flasgger import Swagger
from flask import Flask, request


def create_app():
    app = Flask(__name__)

    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = "postgresql+psycopg2://tweetereshka:tweetereshka@db/tweetereshka"
    # app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql+psycopg2://tweetereshka:tweetereshka@localhost/tweetereshka'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    from .CRUD import core
    from .models import db

    CUR_USER = {
        "cur_user": None,
        "api_key": None,
    }  # Кэш данных по текущему пользователю, перед вызовом функции проведит проверку на совпадение переданного ключа, с лежащим по ключу "api_key"

    db.init_app(app)
    with app.app_context():
        db.create_all()

    @app.route("/api/users/me", methods=["GET"])
    def get_user_info_by_api_key():
        global CUR_USER
        CUR_USER = _check_cur_user(request.args.get("api_key"))

        return core(CUR_USER, "read", "user")

    @app.route("/api/users/<int:id>", methods=["GET"])
    def get_user_info_by_id(id):
        return core({"cur_user": id}, "read", "user")

    @app.route("/api/tweets", methods=["GET", "POST"])
    def tweets():
        global CUR_USER
        CUR_USER = _check_cur_user(request.args.get("api_key"))

        if request.method == "GET":
            return core(CUR_USER, "read", "tweet")

        elif request.method == "POST":
            try:
                tweet_data, tweet_media_ids = request.json.get(
                    "tweet_data"
                ), request.json.get("tweet_media_ids")
                data = {"text": tweet_data, "author": CUR_USER["cur_user"]}
                if tweet_media_ids is not None:
                    data["images"] = tweet_media_ids

                return core(data, "create", "tweet")
            except Exception as e:
                return {
                    "result": False,
                    "error_type": e.__class__.__name__,
                    "error_message": str(e),
                }, 500

    @app.route("/api/tweets/<int:id>", methods=["DELETE"])
    def delete_tweets(id):
        global CUR_USER
        CUR_USER = _check_cur_user(request.args.get("api_key"))

        data = {"tweet_id": id, "cur_user": CUR_USER["cur_user"]}
        return core(data, "delete", "tweet")

    @app.route("/api/media", methods=["POST"])
    def images():
        global CUR_USER
        CUR_USER = _check_cur_user(request.args.get("api_key"))

        img_file = request.files["image"]
        data = (img_file, CUR_USER["cur_user"])
        return core(data, "create", "image")

    @app.route("/api/tweets/<int:id>/likes", methods=["POST", "DELETE"])
    def likes(id):
        global CUR_USER
        CUR_USER = _check_cur_user(request.args.get("api_key"))
        data = {"tweet_id": id, "cur_user": CUR_USER["cur_user"]}

        if request.method == "POST":
            return core(data, "create", "like")

        elif request.method == "DELETE":
            return core(data, "delete", "like")

    @app.route("/api/users/<int:id>/follow", methods=["POST", "DELETE"])
    def follows(id):
        global CUR_USER
        CUR_USER = _check_cur_user(request.args.get("api_key"))
        data = {"cur_user": CUR_USER["cur_user"], "following_id": id}

        if request.method == "POST":
            return core(data, "create", "follow")

        elif request.method == "DELETE":
            return core(data, "delete", "follow")

    def _check_cur_user(api_key):
        if api_key != CUR_USER["api_key"]:
            return core(api_key, "update", "cur_user")

    Swagger(app, template_file="swagger.json")

    return app
