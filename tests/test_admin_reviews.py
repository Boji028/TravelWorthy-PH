"""Tests for admin-entered package reviews and testimonials.

Customers no longer have accounts, so admin adds reviews after getting a
client's permission. Reviews keep their own copy of the client's name
and must survive deletion of any linked user account.
"""
from datetime import datetime
from werkzeug.security import generate_password_hash

from models.package import TourPackage
from models.package_review import PackageReview
from models.testimonial import Testimonial
from models.user import User


def _make_package(db, title="Boracay Escape"):
    pkg = TourPackage(title=title, description="d", destination="Boracay",
                      duration_days=3, price=5000, currency="PHP", is_active=True)
    db.session.add(pkg)
    db.session.commit()
    return pkg


class TestAddPackageReview:
    def test_requires_admin(self, app, client, authenticated_client):
        from app import db
        pkg = _make_package(db)
        data = {"package_id": pkg.id, "reviewer_name": "Maria", "rating": "5", "message": "Great"}
        client.post("/admin/package-reviews/add", data=data)
        authenticated_client.post("/admin/package-reviews/add", data=data)
        assert PackageReview.query.count() == 0

    def test_admin_can_add_a_review_with_no_user_account(self, app, admin_client):
        from app import db
        pkg = _make_package(db)
        admin_client.post("/admin/package-reviews/add", data={
            "package_id": pkg.id, "reviewer_name": "Maria Santos", "rating": "4",
            "message": "Lovely trip", "review_date": "2026-03-15",
        })
        review = PackageReview.query.one()
        assert review.reviewer_name == "Maria Santos"
        assert review.user_id is None
        assert review.rating == 4
        assert review.created_at.date() == datetime(2026, 3, 15).date()

    def test_rating_is_clamped_to_one_to_five(self, app, admin_client):
        from app import db
        pkg = _make_package(db)
        admin_client.post("/admin/package-reviews/add", data={
            "package_id": pkg.id, "reviewer_name": "A", "rating": "99", "message": "x"})
        assert PackageReview.query.one().rating == 5

    def test_name_and_message_are_required(self, app, admin_client):
        from app import db
        pkg = _make_package(db)
        admin_client.post("/admin/package-reviews/add", data={
            "package_id": pkg.id, "reviewer_name": "", "rating": "5", "message": "x"})
        admin_client.post("/admin/package-reviews/add", data={
            "package_id": pkg.id, "reviewer_name": "A", "rating": "5", "message": ""})
        assert PackageReview.query.count() == 0

    def test_a_package_is_required(self, app, admin_client):
        admin_client.post("/admin/package-reviews/add", data={
            "reviewer_name": "A", "rating": "5", "message": "x"})
        assert PackageReview.query.count() == 0

    def test_same_package_can_have_many_admin_reviews(self, app, admin_client):
        """The old one-review-per-user rule must not block admin reviews."""
        from app import db
        pkg = _make_package(db)
        for name in ["Ana", "Ben", "Cora"]:
            admin_client.post("/admin/package-reviews/add", data={
                "package_id": pkg.id, "reviewer_name": name, "rating": "5", "message": "x"})
        assert PackageReview.query.filter_by(package_id=pkg.id).count() == 3

    def test_html_in_name_is_stripped(self, app, admin_client):
        from app import db
        pkg = _make_package(db)
        admin_client.post("/admin/package-reviews/add", data={
            "package_id": pkg.id, "reviewer_name": "<script>x</script>Maria", "rating": "5", "message": "ok"})
        assert "<script>" not in PackageReview.query.one().reviewer_name


class TestPackageReviewList:
    def test_list_shows_reviews_and_filters_by_package(self, app, admin_client):
        from app import db
        a, b = _make_package(db, "Alpha Tour"), _make_package(db, "Beta Tour")
        db.session.add_all([
            PackageReview(package_id=a.id, reviewer_name="Ana Reyes", rating=5, message="m"),
            PackageReview(package_id=b.id, reviewer_name="Ben Cruz", rating=4, message="m"),
        ])
        db.session.commit()
        everything = admin_client.get("/admin/package-reviews").get_data(as_text=True)
        assert "Ana Reyes" in everything and "Ben Cruz" in everything
        filtered = admin_client.get(f"/admin/package-reviews?package_id={a.id}").get_data(as_text=True)
        assert "Ana Reyes" in filtered and "Ben Cruz" not in filtered

    def test_admin_can_delete_a_review(self, app, admin_client):
        from app import db
        pkg = _make_package(db)
        r = PackageReview(package_id=pkg.id, reviewer_name="Ana", rating=5, message="m")
        db.session.add(r)
        db.session.commit()
        admin_client.post(f"/admin/package-reviews/delete/{r.id}")
        assert PackageReview.query.count() == 0


class TestAddTestimonial:
    def test_admin_can_add_a_testimonial_with_no_user_account(self, app, admin_client):
        admin_client.post("/admin/testimonials/add", data={
            "reviewer_name": "Juan Dela Cruz", "rating": "5", "message": "Best agency"})
        t = Testimonial.query.one()
        assert t.reviewer_name == "Juan Dela Cruz"
        assert t.user_id is None

    def test_testimonial_requires_admin(self, app, authenticated_client):
        authenticated_client.post("/admin/testimonials/add", data={
            "reviewer_name": "X", "rating": "5", "message": "y"})
        assert Testimonial.query.count() == 0

    def test_testimonial_shows_on_reviews_page_but_not_homepage(self, app, client):
        """The homepage testimonials section was removed; the Reviews page
        is now the only place they appear."""
        from app import db
        db.session.add(Testimonial(reviewer_name="Liza Mae", rating=5, message="Wonderful service"))
        db.session.commit()
        assert "Liza Mae" in client.get("/reviews").get_data(as_text=True)
        home = client.get("/").get_data(as_text=True)
        assert "Liza Mae" not in home
        assert 'id="testimonials"' not in home


class TestReviewsSurviveUserDeletion:
    """Deleting a user account used to cascade-delete every review they'd
    written. Reviews now keep their own name and outlive the account."""

    def test_package_review_survives_and_keeps_its_name(self, app, admin_client):
        from app import db
        pkg = _make_package(db)
        user = User(name="Old Customer", email="old@example.com",
                    password=generate_password_hash("TestPass123"), email_verified=True)
        db.session.add(user)
        db.session.commit()
        review = PackageReview(package_id=pkg.id, user_id=user.id, reviewer_name="Old Customer",
                               rating=5, message="Still here")
        db.session.add(review)
        db.session.commit()
        review_id = review.id

        admin_client.post(f"/admin/users/delete/{user.id}")

        survivor = db.session.get(PackageReview, review_id)
        assert survivor is not None
        assert survivor.user_id is None
        assert survivor.display_name == "Old Customer"

    def test_testimonial_survives_user_deletion(self, app, admin_client):
        from app import db
        user = User(name="Gone Customer", email="gone@example.com",
                    password=generate_password_hash("TestPass123"), email_verified=True)
        db.session.add(user)
        db.session.commit()
        t = Testimonial(user_id=user.id, reviewer_name="Gone Customer", rating=5, message="Great")
        db.session.add(t)
        db.session.commit()
        t_id = t.id

        admin_client.post(f"/admin/users/delete/{user.id}")

        survivor = db.session.get(Testimonial, t_id)
        assert survivor is not None
        assert survivor.display_name == "Gone Customer"


class TestDisplayName:
    def test_falls_back_to_linked_account_then_guest(self, app):
        from app import db
        user = User(name="Linked Person", email="l@example.com",
                    password=generate_password_hash("TestPass123"), email_verified=True)
        db.session.add(user)
        db.session.commit()
        pkg = _make_package(db)
        assert PackageReview(package_id=pkg.id, user_id=user.id, rating=5, message="m",
                             user=user).display_name == "Linked Person"
        assert PackageReview(package_id=pkg.id, rating=5, message="m").display_name == "Guest"
        assert PackageReview(package_id=pkg.id, reviewer_name="Typed", user=user,
                             rating=5, message="m").display_name == "Typed"
