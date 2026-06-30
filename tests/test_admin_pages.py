"""Tests for the redesigned admin list pages: Blog, Visa, and Testimonials.

Covers search/filter query params, status counts, the AJAX toggle routes
(toggle_blog_published, toggle_visa_active), and the admin-triggered
testimonial delete flow.
"""
import pytest
from models.blog import BlogPost
from models.visa import VisaCountry
from models.testimonial import Testimonial
from models.testimonial_image import TestimonialImage


def _make_blog_post(db, **overrides):
    defaults = dict(
        title='Test Post',
        author='Admin',
        category='Tips',
        short_description='A short description',
        content='<p>Some content</p>',
        is_published=True,
    )
    defaults.update(overrides)
    post = BlogPost(**defaults)
    db.session.add(post)
    db.session.commit()
    return post


def _make_visa(db, **overrides):
    defaults = dict(
        country_name='Japan',
        flag_emoji='🇯🇵',
        is_active=True,
        region='Asia Pacific',
        visa_type='Tourist eVisa',
    )
    defaults.update(overrides)
    visa = VisaCountry(**defaults)
    db.session.add(visa)
    db.session.commit()
    return visa


def _make_testimonial(db, user_id, **overrides):
    defaults = dict(
        user_id=user_id,
        message='Great trip!',
        rating=5,
    )
    defaults.update(overrides)
    testimonial = Testimonial(**defaults)
    db.session.add(testimonial)
    db.session.commit()
    return testimonial


class TestBlogAdminAccess:
    """Non-admins should never reach these routes."""

    def test_blog_list_requires_login(self, client):
        response = client.get('/admin/blog')
        assert response.status_code in (302, 401, 403)

    def test_blog_list_rejects_non_admin_user(self, authenticated_client):
        response = authenticated_client.get('/admin/blog')
        assert response.status_code in (302, 403)

    def test_toggle_blog_published_requires_login(self, app, client):
        from app import db
        post = _make_blog_post(db)
        response = client.post(f'/admin/blog/toggle-published/{post.id}')
        assert response.status_code in (302, 401, 403)


class TestBlogAdminFiltering:
    def test_search_filters_by_title(self, app, admin_client):
        from app import db
        _make_blog_post(db, title='Bali beaches guide')
        _make_blog_post(db, title='Korea winter packing')

        response = admin_client.get('/admin/blog?search=Bali')
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert 'Bali beaches guide' in page
        assert 'Korea winter packing' not in page

    def test_search_filters_by_author(self, app, admin_client):
        from app import db
        _make_blog_post(db, title='Post One', author='Maria')
        _make_blog_post(db, title='Post Two', author='Juan')

        response = admin_client.get('/admin/blog?search=Maria')
        page = response.get_data(as_text=True)
        assert 'Post One' in page
        assert 'Post Two' not in page

    def test_category_filter(self, app, admin_client):
        from app import db
        _make_blog_post(db, title='Beach Post', category='Beach')
        _make_blog_post(db, title='Tips Post', category='Tips')

        response = admin_client.get('/admin/blog?category=Beach')
        page = response.get_data(as_text=True)
        assert 'Beach Post' in page
        assert 'Tips Post' not in page

    def test_status_filter_and_counts(self, app, admin_client):
        from app import db
        _make_blog_post(db, title='Published Post', is_published=True)
        _make_blog_post(db, title='Draft Post', is_published=False)

        response = admin_client.get('/admin/blog?status=draft')
        page = response.get_data(as_text=True)
        assert 'Draft Post' in page
        assert 'Published Post' not in page

        response_all = admin_client.get('/admin/blog')
        page_all = response_all.get_data(as_text=True)
        assert 'Published Post' in page_all
        assert 'Draft Post' in page_all


class TestBlogPublishToggle:
    def test_toggle_flips_published_state(self, app, admin_client):
        from app import db
        post = _make_blog_post(db, is_published=True)

        response = admin_client.post(f'/admin/blog/toggle-published/{post.id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['is_published'] is False

        db.session.refresh(post)
        assert post.is_published is False

    def test_toggle_twice_returns_to_original_state(self, app, admin_client):
        from app import db
        post = _make_blog_post(db, is_published=True)

        admin_client.post(f'/admin/blog/toggle-published/{post.id}')
        admin_client.post(f'/admin/blog/toggle-published/{post.id}')

        db.session.refresh(post)
        assert post.is_published is True


class TestVisaAdminFiltering:
    def test_search_filters_by_country_name(self, app, admin_client):
        from app import db
        _make_visa(db, country_name='Japan')
        _make_visa(db, country_name='South Korea')

        response = admin_client.get('/admin/visa?search=Japan')
        page = response.get_data(as_text=True)
        assert 'Japan' in page
        assert 'South Korea' not in page

    def test_region_filter(self, app, admin_client):
        from app import db
        _make_visa(db, country_name='Japan', region='Asia Pacific')
        _make_visa(db, country_name='France', region='Europe')

        response = admin_client.get('/admin/visa?region=Europe')
        page = response.get_data(as_text=True)
        assert '<strong>France</strong>' in page
        assert '<strong>Japan</strong>' not in page

    def test_status_filter_and_counts(self, app, admin_client):
        from app import db
        _make_visa(db, country_name='Active Country', is_active=True)
        _make_visa(db, country_name='Inactive Country', is_active=False)

        response = admin_client.get('/admin/visa?status=inactive')
        page = response.get_data(as_text=True)
        assert 'Inactive Country' in page
        assert 'Active Country' not in page


class TestVisaActiveToggle:
    def test_toggle_flips_active_state(self, app, admin_client):
        from app import db
        visa = _make_visa(db, is_active=True)

        response = admin_client.post(f'/admin/visa/toggle-active/{visa.id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['is_active'] is False

        db.session.refresh(visa)
        assert visa.is_active is False

    def test_toggle_requires_login(self, app, client):
        from app import db
        visa = _make_visa(db)
        response = client.post(f'/admin/visa/toggle-active/{visa.id}')
        assert response.status_code in (302, 401, 403)


class TestTestimonialsAdminFiltering:
    def test_search_filters_by_user_name(self, app, admin_client, test_user, admin_user):
        from app import db
        _make_testimonial(db, test_user.id, message='From test user')
        _make_testimonial(db, admin_user.id, message='From admin user')

        response = admin_client.get(f'/admin/testimonials?search={test_user.name.split()[0]}')
        page = response.get_data(as_text=True)
        assert 'From test user' in page
        assert 'From admin user' not in page

    def test_search_filters_by_email(self, app, admin_client, test_user, admin_user):
        from app import db
        _make_testimonial(db, test_user.id, message='From test user')
        _make_testimonial(db, admin_user.id, message='From admin user')

        response = admin_client.get(f'/admin/testimonials?search={test_user.email}')
        page = response.get_data(as_text=True)
        assert 'From test user' in page
        assert 'From admin user' not in page

    def test_rating_filter_and_counts(self, app, admin_client, test_user):
        from app import db
        _make_testimonial(db, test_user.id, message='Five star review', rating=5)
        _make_testimonial(db, test_user.id, message='One star review', rating=1)

        response = admin_client.get('/admin/testimonials?rating=5')
        page = response.get_data(as_text=True)
        assert 'Five star review' in page
        assert 'One star review' not in page


class TestTestimonialImagesDisplay:
    """Regression test for the template bug we found: the admin page used
    to read the dead `testimonial.image` string field instead of the real
    `testimonial.images` relationship, so uploaded photos never appeared."""

    def test_uploaded_images_appear_in_admin_list(self, app, admin_client, test_user):
        from app import db
        testimonial = _make_testimonial(db, test_user.id, message='Review with photos')
        img = TestimonialImage(testimonial_id=testimonial.id, path='https://res.cloudinary.com/test/image1.jpg', order=0)
        db.session.add(img)
        db.session.commit()

        response = admin_client.get('/admin/testimonials')
        page = response.get_data(as_text=True)
        assert 'https://res.cloudinary.com/test/image1.jpg' in page


class TestTestimonialAdminDelete:
    def test_admin_can_delete_via_ajax(self, app, admin_client, test_user):
        from app import db
        testimonial = _make_testimonial(db, test_user.id, message='Delete me')
        testimonial_id = testimonial.id

        response = admin_client.post(
            f'/testimonial/delete/{testimonial_id}',
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        assert response.status_code == 200
        assert response.get_json()['success'] is True
        assert Testimonial.query.get(testimonial_id) is None

    def test_non_admin_cannot_delete(self, app, authenticated_client, admin_user):
        from app import db
        testimonial = _make_testimonial(db, admin_user.id, message='Protected')
        testimonial_id = testimonial.id

        response = authenticated_client.post(
            f'/testimonial/delete/{testimonial_id}',
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )

        assert response.status_code == 403
        assert response.get_json()['success'] is False
        assert Testimonial.query.get(testimonial_id) is not None