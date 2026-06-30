"""Tests for admin blog management routes."""
from models.blog import BlogPost


def _make_post(db, **overrides):
    defaults = dict(
        title='Test Post',
        content='<p>Some content here.</p>',
        is_published=True,
    )
    defaults.update(overrides)
    post = BlogPost(**defaults)
    db.session.add(post)
    db.session.commit()
    return post


class TestBlogListAccess:
    def test_requires_login(self, client):
        response = client.get('/admin/blog')
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        response = authenticated_client.get('/admin/blog')
        assert response.status_code in (302, 403)

    def test_admin_can_access(self, app, admin_client):
        response = admin_client.get('/admin/blog')
        assert response.status_code == 200


class TestDeleteBlog:
    def test_requires_login(self, client):
        response = client.post('/admin/blog/delete/1')
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db
        post = _make_post(db)
        authenticated_client.post(f'/admin/blog/delete/{post.id}')
        assert db.session.get(BlogPost, post.id) is not None

    def test_admin_can_delete(self, app, admin_client):
        from app import db
        post = _make_post(db)
        post_id = post.id
        response = admin_client.post(f'/admin/blog/delete/{post_id}')
        assert response.status_code == 302
        assert db.session.get(BlogPost, post_id) is None

    def test_nonexistent_post_returns_404(self, app, admin_client):
        response = admin_client.post('/admin/blog/delete/99999')
        assert response.status_code == 404

    def test_redirects_to_blog_list(self, app, admin_client):
        from app import db
        post = _make_post(db)
        response = admin_client.post(
            f'/admin/blog/delete/{post.id}', follow_redirects=False
        )
        assert '/admin/blog' in response.headers['Location']


class TestBlogPublicRoutes:
    def test_blog_list_renders(self, app, client):
        from app import db
        _make_post(db)
        response = client.get('/blog/')
        assert response.status_code == 200

    def test_blog_list_shows_only_published(self, app, client):
        from app import db
        _make_post(db, title='Published', is_published=True)
        _make_post(db, title='Draft', is_published=False)
        response = client.get('/blog/')
        assert b'Published' in response.data
        assert b'Draft' not in response.data

    def test_blog_detail_renders(self, app, client):
        from app import db
        post = _make_post(db)
        response = client.get(f'/blog/{post.id}')
        assert response.status_code == 200

    def test_blog_detail_unpublished_returns_404(self, app, client):
        from app import db
        post = _make_post(db, is_published=False)
        response = client.get(f'/blog/{post.id}')
        assert response.status_code == 404

    def test_blog_list_category_filter(self, app, client):
        from app import db
        _make_post(db, title='Travel Tips', category='tips')
        _make_post(db, title='Destinations', category='destinations')
        response = client.get('/blog/?category=tips')
        assert b'Travel Tips' in response.data
        assert b'Destinations' not in response.data
