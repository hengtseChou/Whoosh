from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class PostInfo:
    """
    Data required to create new `PostInfo`:
    - `post_uid` -> should be generated by `post_uid_generator.generate_post_uid()`
    - `title`
    - `subtitle`
    - `author`
    - `tags`

    Optional data:
    - `cover_url`
    - `custom_slug`

    Fields that are automatically generated:
    - `created_at`
    - `last_updated`
    - `archived`
    - `featured`
    - `views`
    - `reads`
    """

    post_uid: str
    title: str
    subtitle: str
    author: str
    tags: list[str]
    cover_url: str
    custom_slug: str
    created_at: datetime = datetime.now(timezone.utc)
    last_updated: datetime = datetime.now(timezone.utc)
    archived: bool = False
    featured: bool = False
    views: int = 0
    reads: int = 0


@dataclass
class PostContent:
    """
    Data required to create new `PostContent`:
    - `post_uid` -> should be generated by `post_uid_generator.generate_post_uid()`
    - `author`
    - `content`
    """

    post_uid: str
    author: str
    content: str
