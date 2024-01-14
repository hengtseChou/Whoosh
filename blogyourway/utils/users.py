import bcrypt
from flask import Request, flash, render_template, request
from flask_login import UserMixin

from blogyourway.config import ENV
from blogyourway.services.logging import Logger, LoggerUtils, logger
from blogyourway.services.mongo import Database, mongodb
from blogyourway.utils.common import FormValidator, get_today


class User(UserMixin):
    # user id is set as username
    def __init__(self, user_data):
        for key, value in user_data.items():
            if key == "username":
                self.id = value
                self.username = value
                continue
            setattr(self, key, value)


###################################################################

# user registration

###################################################################


class NewUserSetup:
    def __init__(self, request: Request, db_handler: Database, logger: Logger):
        self._regist_form = request.form.to_dict()
        self._request = request
        self._db_handler = db_handler
        self._logger = logger

    def _form_validated(self, validator: FormValidator) -> bool:
        if not validator.validate_email(self._regist_form["email"]):
            return False
        if not validator.validate_password(self._regist_form["password"]):
            return False
        if not validator.validate_username(self._regist_form["username"]):
            return False
        if not validator.validate_blogname(self._regist_form["blogname"]):
            return False
        return True

    def _no_duplicates(self) -> bool:
        for field in ["email", "username", "blogname"]:
            if self._db_handler.user_login.exists(field, self._regist_form[field]):
                flash(
                    f"{field.capitalize()} is already used. Please try another one.",
                    category="error",
                )
                LoggerUtils.registration_failed(
                    logger=self._logger,
                    request=self._request,
                    msg=f"{field} {self._regist_form[field]} already used",
                )
                return True
        return False

    def _create_user_login(self, username: str, email: str, hashed_password: str) -> dict:
        new_user_login = {"username": username, "email": email, "password": hashed_password}
        return new_user_login

    def _create_user_info(self, username: str, email: str, blogname: str) -> dict:
        new_user_info = {
            "username": username,
            "email": email,
            "blogname": blogname,
            "cover_url": "",
            "profile_img_url": "",
            "short_bio": "",
            "social_links": [],
            "change_log_enabled": False,
            "gallery_enabled": True,
            "created_at": get_today(env=ENV),
        }
        return new_user_info

    def _create_user_about(self, username: str) -> dict:
        new_user_about = {"username": username, "about": "", "about_views": 0}
        return new_user_about

    def _create_user_views(self, username: str) -> dict:
        new_user_views = {"username": username, "unique_visitors": []}
        return new_user_views

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hashing user input password.

        Args:
            password (str): a string of plain text password.

        Returns:
            str: a string of the hashed password encoded back to utf-8.
        """

        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12))
        hashed_pw = hashed_pw.decode("utf-8")
        return hashed_pw

    def create_user(self):
        validator = FormValidator()

        if not self._form_validated(validator=validator):
            return render_template("register.html")

        if self._no_duplicates():
            return render_template("register.html")

        hashed_pw = self._hash_password(self._regist_form["password"])
        new_user_login = self._create_user_login(
            self._regist_form["username"], self._regist_form["email"], hashed_pw
        )
        new_user_info = self._create_user_info(
            self._regist_form["username"],
            self._regist_form["email"],
            self._regist_form["blogname"],
        )
        new_user_about = self._create_user_about(self._regist_form["username"])
        new_user_views = self._create_user_views(self._regist_form["username"])

        self._db_handler.user_login.insert_one(new_user_login)
        self._db_handler.user_info.insert_one(new_user_info)
        self._db_handler.user_about.insert_one(new_user_about)
        self._db_handler.user_views.insert_one(new_user_views)

        return self._regist_form["username"]


def create_user(request: request) -> str:
    user_registration = NewUserSetup(request, mongodb, logger)
    return user_registration.create_user()


###################################################################

# deleting user

###################################################################


class UserDeletionSetup:
    def __init__(self, username: str, db_handler: Database, logger: Logger) -> None:
        self._user_to_be_deleted = username
        self._db_handler = db_handler
        self._logger = logger

    def _get_posts_uid_by_user(self) -> list:
        target_posts = self._db_handler.post_info.find({"author": self._user_to_be_deleted})
        target_posts_uid = [post["post_uid"] for post in target_posts]

        return target_posts_uid

    def _remove_all_posts(self):
        self._db_handler.post_info.delete_many({"author": self._user_to_be_deleted})
        self._db_handler.post_content.delete_many({"author": self._user_to_be_deleted})
        self._logger.debug(f"Deleted all posts written by user {self._user_to_be_deleted}.")

    def _remove_all_related_comments(self, post_uids: list):
        for post_uid in post_uids:
            self._db_handler.comment.delete_many({"post_uid": post_uid})
        self._logger.debug(f"Deleted relevant comments from user {self._user_to_be_deleted}.")

    def _remove_related_metrics(self):
        pass

    def _remove_all_user_data(self):
        self._db_handler.user_login.delete_one({"username": self._user_to_be_deleted})
        self._db_handler.user_info.delete_one({"username": self._user_to_be_deleted})
        self._db_handler.user_about.delete_one({"username": self._user_to_be_deleted})
        self._db_handler.user_views.delete_one({"username": self._user_to_be_deleted})

        self._logger.debug(f"Deleted user information for user {self._user_to_be_deleted}.")

    def start_deletion_process(self):
        target_posts_uid = self._get_posts_uid_by_user()
        self._remove_all_posts()
        self._remove_all_related_comments(target_posts_uid)
        # this place should includes removing metrics data for the user
        self._remove_related_metrics()
        self._remove_all_user_data()


def delete_user(username):
    user_deletion = UserDeletionSetup(username=username, db_handler=mongodb, logger=logger)
    user_deletion.start_deletion_process()
