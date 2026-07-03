"""Tests for admin blog add/edit routes."""
from unittest.mock import patch
from datetime import datetime, timezone
from io import BytesIO
from models.blog import BlogPost


FAKE_UPLOAD = {
    "path": "https://res.cloudinary.com/test/image/upload/v1/blog.jpg",
    "size_kb": 80.0,
    "uploaded_at": datetime.now(timezone.utc),
}


def _make_post(db, **overrides):
    defaults = dict(title="Existing Post", content="<p>Content here.</p>", is_published=True)
    defaults.update(overrides)
    post = BlogPost(**defaults)
    db.session.add(post)
    db.session.commit()
    return post


class TestAddBlog:
    def test_requires_login(self, client):
        response = client.post("/admin/blog/add", data={"title": "Test", "content": "Body"})
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db

        authenticated_client.post("/admin/blog/add", data={"title": "Test", "content": "Body"})
        assert BlogPost.query.count() == 0

    def test_get_renders_form(self, app, admin_client):
        response = admin_client.get("/admin/blog/add")
        assert response.status_code == 200

    def test_valid_post_creates_blog(self, app, admin_client):
        from app import db

        admin_client.post(
            "/admin/blog/add",
            data={
                "title": "My Post",
                "content": "Some blog content here.",
            },
        )
        assert BlogPost.query.filter_by(title="My Post").count() == 1

    def test_missing_title_does_not_create(self, app, admin_client):
        from app import db

        admin_client.post("/admin/blog/add", data={"title": "", "content": "Body"})
        assert BlogPost.query.count() == 0

    def test_missing_content_does_not_create(self, app, admin_client):
        from app import db

        admin_client.post("/admin/blog/add", data={"title": "Title", "content": ""})
        assert BlogPost.query.count() == 0

    def test_published_flag_saved(self, app, admin_client):
        from app import db

        admin_client.post(
            "/admin/blog/add",
            data={
                "title": "Published Post",
                "content": "Body text.",
                "is_published": "on",
            },
        )
        post = BlogPost.query.first()
        assert post is not None
        assert post.is_published is True

    def test_unpublished_by_default(self, app, admin_client):
        from app import db

        admin_client.post(
            "/admin/blog/add",
            data={
                "title": "Draft Post",
                "content": "Body text.",
            },
        )
        post = BlogPost.query.first()
        assert post is not None
        assert post.is_published is False

    def test_image_upload_sets_url(self, app, admin_client):
        from app import db

        with patch("image_service.ImageUploadService.upload_and_compress", return_value=FAKE_UPLOAD):
            admin_client.post(
                "/admin/blog/add",
                data={
                    "title": "Post With Image",
                    "content": "Body.",
                    "featured_image": (BytesIO(b"img"), "photo.jpg"),
                },
                content_type="multipart/form-data",
            )
        post = BlogPost.query.first()
        assert post is not None
        assert post.featured_image == FAKE_UPLOAD["path"]

    def test_redirects_to_blog_list_on_success(self, app, admin_client):
        response = admin_client.post(
            "/admin/blog/add",
            data={"title": "A Post", "content": "Content."},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/admin/blog" in response.headers["Location"]


class TestEditBlog:
    def test_requires_login(self, app, client):
        from app import db

        post = _make_post(db)
        response = client.post(f"/admin/blog/edit/{post.id}", data={"title": "X", "content": "Y"})
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db

        post = _make_post(db)
        authenticated_client.post(f"/admin/blog/edit/{post.id}", data={"title": "Hacked", "content": "X"})
        assert db.session.get(BlogPost, post.id).title == "Existing Post"

    def test_get_renders_form(self, app, admin_client):
        from app import db

        post = _make_post(db)
        response = admin_client.get(f"/admin/blog/edit/{post.id}")
        assert response.status_code == 200

    def test_valid_post_updates_blog(self, app, admin_client):
        from app import db

        post = _make_post(db)
        admin_client.post(
            f"/admin/blog/edit/{post.id}",
            data={
                "title": "Updated Title",
                "content": "Updated content.",
            },
        )
        assert db.session.get(BlogPost, post.id).title == "Updated Title"

    def test_missing_title_does_not_update(self, app, admin_client):
        from app import db

        post = _make_post(db)
        admin_client.post(f"/admin/blog/edit/{post.id}", data={"title": "", "content": "Body"})
        assert db.session.get(BlogPost, post.id).title == "Existing Post"

    def test_missing_content_does_not_update(self, app, admin_client):
        from app import db

        post = _make_post(db)
        admin_client.post(f"/admin/blog/edit/{post.id}", data={"title": "Title", "content": ""})
        assert db.session.get(BlogPost, post.id).content == "<p>Content here.</p>"

    def test_nonexistent_post_returns_404(self, app, admin_client):
        response = admin_client.get("/admin/blog/edit/99999")
        assert response.status_code == 404
