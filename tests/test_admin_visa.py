"""Tests for admin visa management routes."""
from models.visa import VisaCountry


def _make_visa(db, **overrides):
    defaults = dict(country_name='Japan', is_active=True)
    defaults.update(overrides)
    visa = VisaCountry(**defaults)
    db.session.add(visa)
    db.session.commit()
    return visa


class TestVisaListAccess:
    def test_requires_login(self, client):
        response = client.get('/admin/visa')
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        response = authenticated_client.get('/admin/visa')
        assert response.status_code in (302, 403)

    def test_admin_can_access(self, app, admin_client):
        response = admin_client.get('/admin/visa')
        assert response.status_code == 200


class TestVisaAdd:
    def test_requires_login(self, client):
        response = client.post('/admin/visa/add', data={'country_name': 'Japan'})
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db
        authenticated_client.post('/admin/visa/add', data={'country_name': 'Japan'})
        assert VisaCountry.query.count() == 0

    def test_valid_post_creates_visa(self, app, admin_client):
        from app import db
        admin_client.post('/admin/visa/add', data={'country_name': 'Japan', 'is_active': 'on'})
        assert VisaCountry.query.filter_by(country_name='Japan').count() == 1

    def test_missing_country_name_does_not_save(self, app, admin_client):
        from app import db
        admin_client.post('/admin/visa/add', data={'country_name': ''})
        assert VisaCountry.query.count() == 0

    def test_get_renders_form(self, app, admin_client):
        response = admin_client.get('/admin/visa/add')
        assert response.status_code == 200

    def test_redirects_to_visa_list_after_add(self, app, admin_client):
        response = admin_client.post(
            '/admin/visa/add',
            data={'country_name': 'South Korea'},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert '/admin/visa' in response.headers['Location']


class TestVisaEdit:
    def test_requires_login(self, app, client):
        from app import db
        visa = _make_visa(db)
        response = client.post(f'/admin/visa/edit/{visa.id}', data={'country_name': 'New Name'})
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db
        visa = _make_visa(db)
        authenticated_client.post(f'/admin/visa/edit/{visa.id}', data={'country_name': 'New Name'})
        assert db.session.get(VisaCountry, visa.id).country_name == 'Japan'

    def test_admin_can_edit(self, app, admin_client):
        from app import db
        visa = _make_visa(db)
        admin_client.post(f'/admin/visa/edit/{visa.id}', data={'country_name': 'South Korea'})
        assert db.session.get(VisaCountry, visa.id).country_name == 'South Korea'

    def test_nonexistent_visa_returns_404(self, app, admin_client):
        response = admin_client.get('/admin/visa/edit/99999')
        assert response.status_code == 404


class TestVisaDelete:
    def test_requires_login(self, app, client):
        from app import db
        visa = _make_visa(db)
        response = client.post(f'/admin/visa/delete/{visa.id}')
        assert response.status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        from app import db
        visa = _make_visa(db)
        authenticated_client.post(f'/admin/visa/delete/{visa.id}')
        assert db.session.get(VisaCountry, visa.id) is not None

    def test_admin_can_delete(self, app, admin_client):
        from app import db
        visa = _make_visa(db)
        visa_id = visa.id
        response = admin_client.post(f'/admin/visa/delete/{visa_id}')
        assert response.status_code == 302
        assert db.session.get(VisaCountry, visa_id) is None

    def test_nonexistent_visa_returns_404(self, app, admin_client):
        response = admin_client.post('/admin/visa/delete/99999')
        assert response.status_code == 404


class TestVisaPublicPage:
    def test_visa_page_renders(self, client):
        response = client.get('/packages/visa')
        assert response.status_code == 200

    def test_visa_requirements_endpoint(self, app, client):
        from app import db
        visa = _make_visa(db)
        response = client.get(f'/packages/visa/country/{visa.id}/requirements')
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Japan'

    def test_visa_requirements_nonexistent_returns_404(self, client):
        response = client.get('/packages/visa/country/99999/requirements')
        assert response.status_code == 404
