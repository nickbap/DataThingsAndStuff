class PostStatus:
    ARCHIVED = "archived"
    DRAFT = "draft"
    PUBLISHED = "published"


POST_STATUS_STYLE = {
    PostStatus.ARCHIVED: "badge bg-dark",
    PostStatus.DRAFT: "badge bg-warning text-dark",
    PostStatus.PUBLISHED: "badge bg-success",
}

ALLOWABLE_IMAGE_TYPES = [".jpg", ".jpeg", ".png", ".gif"]
