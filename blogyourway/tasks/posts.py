from dataclasses import asdict
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from flask_login import current_user

from blogyourway.forms.posts import EditPostForm, NewPostForm
from blogyourway.models.posts import PostContent, PostInfo
from blogyourway.mongo import Database, mongodb
from blogyourway.tasks.utils import UIDGenerator, process_tags

###################################################################

# create new post

###################################################################


class NewPostSetup:
    def __init__(self, post_uid_generator: UIDGenerator, db_handler: Database) -> None:
        self._post_uid = post_uid_generator.generate_post_uid()
        self._db_handler = db_handler

    def _create_post_info(self, form: NewPostForm, author_name: str) -> dict:
        new_post_info = PostInfo(
            post_uid=self._post_uid,
            title=form.title.data,
            subtitle=form.subtitle.data,
            author=author_name,
            tags=process_tags(form.tags.data),
            custom_slug=form.custom_slug.data,
            cover_url=form.cover_url.data,
        )
        return asdict(new_post_info)

    def _create_post_content(self, form: NewPostForm, author_name: str) -> dict:
        new_post_content = PostContent(
            post_uid=self._post_uid, author=author_name, content=form.editor.data
        )
        return asdict(new_post_content)

    def _increment_tags_for_user(self, new_post_info: dict) -> None:
        username = new_post_info.get("author")
        tags = new_post_info.get("tags")
        tags_increments = {f"tags.{tag}": 1 for tag in tags}
        self._db_handler.user_info.make_increments(
            filter={"username": username}, increments=tags_increments, upsert=True
        )

    def create_post(self, author_name: str, form: NewPostForm) -> str | None:

        new_post_info = self._create_post_info(author_name=author_name, form=form)
        new_post_content = self._create_post_content(author_name=author_name, form=form)

        self._db_handler.post_info.insert_one(new_post_info)
        self._db_handler.post_content.insert_one(new_post_content)
        self._increment_tags_for_user(new_post_info)

        return self._post_uid


def create_post(form: NewPostForm) -> str:
    uid_generator = UIDGenerator(db_handler=mongodb)

    new_post_setup = NewPostSetup(post_uid_generator=uid_generator, db_handler=mongodb)
    new_post_uid = new_post_setup.create_post(author_name=current_user.username, form=form)
    return new_post_uid


###################################################################

# updating a post

###################################################################


class PostUpdateSetup:
    def __init__(self, db_handler: Database) -> None:
        self._db_handler = db_handler

    def _update_tags_for_user(self, post_uid: str, new_tags: dict) -> None:
        post_info = self._db_handler.post_info.find_one({"post_uid": post_uid})
        author = post_info.get("author")
        old_tags = post_info.get("tags")
        tags_reduction = {f"tags.{tag}": -1 for tag in old_tags}
        self._db_handler.user_info.make_increments(
            filter={"username": author}, increments=tags_reduction
        )
        tags_increment = {f"tags.{tag}": 1 for tag in new_tags}
        self._db_handler.user_info.make_increments(
            filter={"username": author}, increments=tags_increment, upsert=True
        )

    def update_post(self, post_uid: str, form: EditPostForm) -> None:

        updated_post_info = {
            "title": form.title.data,
            "subtitle": form.subtitle.data,
            "tags": process_tags(form.tags.data),
            "cover_url": form.cover_url.data,
            "custom_slug": form.custom_slug.data,
            "last_updated": datetime.now(timezone.utc),
        }
        updated_post_content = {"content": form.editor.data}

        self._update_tags_for_user(post_uid, updated_post_info.get("tags"))
        self._db_handler.post_info.update_values(
            filter={"post_uid": post_uid}, update=updated_post_info
        )
        self._db_handler.post_content.update_values(
            filter={"post_uid": post_uid}, update=updated_post_content
        )


def update_post(post_uid: str, form: EditPostForm) -> None:
    post_update_setup = PostUpdateSetup(db_handler=mongodb)
    post_update_setup.update_post(post_uid=post_uid, form=form)


###################################################################

# formatter for posts that are saved as markdown

###################################################################


class HTMLFormatter:
    def __init__(self, html: str):
        """Format markdown strings for additional styles for different pages.

        Args:
            html (str): a string that is already html.
        """

        self.__soup = BeautifulSoup(html, "html.parser")

    def add_padding(self):
        blocks = self.__soup.find_all(
            lambda tag: tag.name not in ["figure", "img"], recursive=False
        )
        for block in blocks:
            current_class = block.get("class", [])
            current_class.append("py-2")
            block["class"] = current_class

        return self

    def change_headings(self):
        small_headings = self.__soup.find_all("h3")
        for head in small_headings:
            head.name = "h5"

        medium_headings = self.__soup.find_all("h2")
        for head in medium_headings:
            head.name = "h3"

        big_headings = self.__soup.find_all("h1")
        for head in big_headings:
            head.name = "h2"
            current_class = head.get("class", [])
            # current_class.append("fw-bold")
            # current_class.append("border-bottom")
            head["class"] = current_class

        return self

    def modify_figure(self, max_width="100%"):
        # center image and modify size
        imgs = self.__soup.find_all(["img"])
        for img in imgs:
            current_style = img.get("style", "")
            new_style = f"{current_style} display: block; margin: 0 auto; max-width: {max_width}; min-width: 30%; height: auto;"
            img["style"] = new_style
            # img["loading"] = "lazy"
            img_src = img["src"]
            img["src"] = ""
            img["data-src"] = img_src
            current_class = img.get("class", [])
            current_class.append("lazyload")
            img["class"] = current_class

        # center caption
        captions = self.__soup.find_all(["figcaption"])
        for caption in captions:
            current_style = caption.get("style", "")
            new_style = f"{current_style} text-align: center"
            caption["style"] = new_style
            current_class = img.get("class", [])
            current_class.append("my-2")
            img["class"] = current_class

        return self

    def to_string(self) -> str:
        return str(self.__soup)


def html_to_post(html: str) -> str:
    formatter = HTMLFormatter(html)
    post = formatter.add_padding().change_headings().modify_figure().to_string()

    return post


def html_to_about(html: str) -> str:
    formatter = HTMLFormatter(html)
    about = formatter.add_padding().change_headings().modify_figure().to_string()

    return about


###################################################################

# blogpost pagination

###################################################################


###################################################################

# post utilities

###################################################################


class PostUtils:
    def __init__(self, db_handler: Database):
        self._db_handler = db_handler

    # def get_all_post_uid(self) -> list[str]:
    #     all_post_info = self._db_handler.post_info.find({})
    #     all_post_uid = [post_info.get("post_uid") for post_info in all_post_info]
    #     return all_post_uid

    # def get_all_author(self) -> list[str]:
    #     all_post_info = self._db_handler.post_info.find({})
    #     all_author = [post_info.get("author") for post_info in all_post_info]
    #     return all_author

    # def get_all_last_update(self) -> list[str]:
    #     all_post_info = self._db_handler.post_info.find({})
    #     all_last_updated = [post_info.get("last_updated") for post_info in all_post_info]
    #     return all_last_updated
    def get_all_posts_info(self, include_archive=False) -> list[dict]:
        if include_archive:
            result = self._db_handler.post_info.find({}).as_list()
        else:
            result = (self._db_handler.post_info.find({"archived": False})).as_list()
        return result

    def find_featured_posts_info(self, username: str) -> list[dict]:
        result = (
            self._db_handler.post_info.find(
                {"author": username, "featured": True, "archived": False}
            )
            .sort("created_at", -1)
            .limit(10)
            .as_list()
        )
        return result

    def find_posts_info_by_username(self, username: str) -> list[dict]:
        result = (
            self._db_handler.post_info.find({"author": username, "archived": False})
            .sort("created_at", -1)
            .as_list()
        )
        return result

    def find_all_archived_posts_info(self, username: str) -> list[dict]:
        result = (
            self._db_handler.post_info.find({"author": username, "archived": True})
            .sort("created_at", -1)
            .as_list()
        )
        return result

    def find_posts_with_pagination(
        self, username: str, page_number: int, posts_per_page: int
    ) -> list[dict]:
        if page_number == 1:
            result = (
                self._db_handler.post_info.find({"author": username, "archived": False})
                .sort("created_at", -1)
                .limit(posts_per_page)
                .as_list()
            )

        elif page_number > 1:
            result = (
                self._db_handler.post_info.find({"author": username, "archived": False})
                .sort("created_at", -1)
                .skip((page_number - 1) * posts_per_page)
                .limit(posts_per_page)
                .as_list()
            )

        return result

    def get_full_post(self, post_uid: str) -> dict:
        target_post = self._db_handler.post_info.find_one({"post_uid": post_uid})
        target_post_content = self._db_handler.post_content.find_one({"post_uid": post_uid}).get(
            "content"
        )
        target_post["content"] = target_post_content

        return target_post

    def read_increment(self, post_uid: str) -> None:
        self._db_handler.post_info.make_increments(
            filter={"post_uid": post_uid}, increments={"reads": 1}
        )

    def view_increment(self, post_uid: str) -> None:
        self._db_handler.post_info.make_increments(
            filter={"post_uid": post_uid}, increments={"views": 1}
        )


post_utils = PostUtils(db_handler=mongodb)
