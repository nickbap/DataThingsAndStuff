class CommentState:
    HIDDEN = "hidden"
    VISIBLE = "visible"


class PostStatus:
    ARCHIVED = "archived"
    DRAFT = "draft"
    PUBLISHED = "published"


COMMENT_STATUS_STYLE = {
    CommentState.HIDDEN: "badge bg-danger",
    CommentState.VISIBLE: "badge bg-success",
}

POST_STATUS_STYLE = {
    PostStatus.ARCHIVED: "badge bg-dark",
    PostStatus.DRAFT: "badge bg-warning text-dark",
    PostStatus.PUBLISHED: "badge bg-success",
}

ALLOWABLE_IMAGE_TYPES = [".jpg", ".jpeg", ".png", ".gif"]
