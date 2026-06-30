"""Tests for testimonial add/delete routes."""
from models.testimonial import Testimonial


class TestAddTestimonial:
    def test_requires_login(self, client):
        response = client.post('/testimonial', data={'message': 'Great!', 'rating': '5'})
        assert response.status_code in (302, 401, 403)

    def test_valid_post_creates_testimonial(self, app, authenticated_client):
        from app import db
        response = authenticated_client.post(
            '/testimonial',
            data={'message': 'Wonderful experience!', 'rating': '5'},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert Testimonial.query.count() == 1

    def test_empty_message_returns_400(self, app, authenticated_client):
        response = authenticated_client.post(
            '/testimonial',
            data={'message': '', 'rating': '5'},
        )
        assert response.status_code == 400
        assert Testimonial.query.count() == 0

    def test_message_over_500_chars_returns_400(self, app, authenticated_client):
        from app import db
        long_message = 'A' * 501
        response = authenticated_client.post(
            '/testimonial',
            data={'message': long_message, 'rating': '5'},
        )
        assert response.status_code == 400
        assert Testimonial.query.count() == 0

    def test_rating_clamped_to_valid_range(self, app, authenticated_client):
        from app import db
        authenticated_client.post(
            '/testimonial',
            data={'message': 'Good trip.', 'rating': '99'},
        )
        testimonial = Testimonial.query.first()
        assert testimonial is not None
        assert testimonial.rating == 5

    def test_invalid_rating_defaults_to_5(self, app, authenticated_client):
        from app import db
        authenticated_client.post(
            '/testimonial',
            data={'message': 'Good trip.', 'rating': 'bad'},
        )
        testimonial = Testimonial.query.first()
        assert testimonial is not None
        assert testimonial.rating == 5

    def test_response_contains_testimonial_data(self, app, authenticated_client, test_user):
        from app import db
        response = authenticated_client.post(
            '/testimonial',
            data={'message': 'Loved it!', 'rating': '4'},
        )
        data = response.get_json()
        assert data['rating'] == 4
        assert data['message'] == 'Loved it!'
        assert data['user_name'] == test_user.name


class TestDeleteTestimonial:
    def test_requires_login(self, app, client, test_user):
        from app import db
        testimonial = Testimonial(user_id=test_user.id, message='Great!', rating=5)
        db.session.add(testimonial)
        db.session.commit()
        response = client.post(f'/testimonial/delete/{testimonial.id}')
        assert response.status_code in (302, 401, 403)

    def test_non_admin_cannot_delete(self, app, authenticated_client, test_user):
        from app import db
        testimonial = Testimonial(user_id=test_user.id, message='Great!', rating=5)
        db.session.add(testimonial)
        db.session.commit()
        testimonial_id = testimonial.id
        authenticated_client.post(f'/testimonial/delete/{testimonial_id}')
        assert db.session.get(Testimonial, testimonial_id) is not None

    def test_admin_can_delete(self, app, admin_client, test_user):
        from app import db
        testimonial = Testimonial(user_id=test_user.id, message='Great!', rating=5)
        db.session.add(testimonial)
        db.session.commit()
        testimonial_id = testimonial.id
        response = admin_client.post(
            f'/testimonial/delete/{testimonial_id}',
            headers={'X-Requested-With': 'XMLHttpRequest'},
        )
        assert response.status_code == 200
        assert response.get_json()['success'] is True
        assert db.session.get(Testimonial, testimonial_id) is None

    def test_nonexistent_testimonial_returns_404(self, app, admin_client):
        response = admin_client.post('/testimonial/delete/99999')
        assert response.status_code == 404
