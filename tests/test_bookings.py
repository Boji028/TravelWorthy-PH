"""Tests for booking routes."""
import pytest
from datetime import datetime, timedelta, timezone
from models.booking import Booking
from constants import BookingStatus


class TestBookingCreation:
    """Test booking creation functionality."""

    def test_create_booking_valid(self, authenticated_client, test_package):
        """Test successful booking creation."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).date()
        
        response = authenticated_client.post(f'/bookings/book/{test_package.id}', data={
            'num_travelers': 2,
            'travel_date': str(future_date),
            'contact_number': '+1234567890',
            'special_requests': 'Window seat preferred'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'successfully' in response.data or b'submitted' in response.data
        
        booking = Booking.query.filter_by(package_id=test_package.id).first()
        assert booking is not None
        assert booking.num_travelers == 2

    def test_booking_past_date(self, authenticated_client, test_package):
        """Test booking with past travel date."""
        past_date = (datetime.now(timezone.utc) - timedelta(days=10)).date()
        
        response = authenticated_client.post(f'/bookings/book/{test_package.id}', data={
            'num_travelers': 2,
            'travel_date': str(past_date),
            'contact_number': '+1234567890'
        }, follow_redirects=True)
        
        assert b'future' in response.data

    def test_booking_invalid_travelers(self, authenticated_client, test_package):
        """Test booking with invalid number of travelers."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).date()
        
        response = authenticated_client.post(f'/bookings/book/{test_package.id}', data={
            'num_travelers': 0,
            'travel_date': str(future_date),
            'contact_number': '+1234567890'
        })
        
        assert response.status_code == 200

    def test_booking_insufficient_slots(self, authenticated_client, test_package):
        """Test booking when insufficient slots available."""
        # Book more than available
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).date()
        
        response = authenticated_client.post(f'/bookings/book/{test_package.id}', data={
            'num_travelers': test_package.available_slots + 5,
            'travel_date': str(future_date),
            'contact_number': '+1234567890'
        }, follow_redirects=True)
        
        assert b'not enough slots' in response.data or b'available' in response.data

    def test_booking_unauthenticated(self, client, test_package):
        """Test booking without authentication."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).date()
        
        response = client.post(f'/bookings/book/{test_package.id}', data={
            'num_travelers': 2,
            'travel_date': str(future_date),
            'contact_number': '+1234567890'
        }, follow_redirects=True)
        
        # Should redirect to login
        assert response.status_code == 200


class TestBookingCancellation:
    """Test booking cancellation."""

    def test_cancel_booking_success(self, authenticated_client, test_booking):
        """Test successful booking cancellation."""
        response = authenticated_client.post(
            f'/bookings/cancel/{test_booking.id}',
            follow_redirects=True
        )
        
        assert b'cancelled' in response.data
        
        # Verify booking status updated
        booking = Booking.query.get(test_booking.id)
        assert booking.status == BookingStatus.CANCELLED.value

    def test_cancel_already_cancelled(self, authenticated_client, app, test_booking):
        """Test cancelling an already cancelled booking."""
        with app.app_context():
            test_booking.status = BookingStatus.CANCELLED.value
            from app import db
            db.session.commit()
        
        response = authenticated_client.post(
            f'/bookings/cancel/{test_booking.id}',
            follow_redirects=True
        )
        
        assert b'already cancelled' in response.data

    def test_cancel_other_user_booking(self, client, authenticated_client, test_booking, test_user, app):
        """Test cancelling another user's booking."""
        # Create another user and authenticate
        from models.user import User
        from werkzeug.security import generate_password_hash
        
        with app.app_context():
            other_user = User(
                name='Other User',
                email='other@example.com',
                password=generate_password_hash('OtherPass123!'),
                is_admin=False
            )
            from app import db
            db.session.add(other_user)
            db.session.commit()
        
        # Login as other user
        client.post('/auth/login', data={
            'email': 'other@example.com',
            'password': 'OtherPass123!'
        })
        
        # Try to cancel other user's booking
        response = client.post(
            f'/bookings/cancel/{test_booking.id}',
            follow_redirects=True
        )
        
        assert b'Unauthorized' in response.data


class TestMyBookings:
    """Test my bookings listing."""

    def test_view_my_bookings(self, authenticated_client, test_booking):
        """Test viewing user's bookings."""
        response = authenticated_client.get('/bookings/my-bookings')
        
        assert response.status_code == 200
        assert b'my' in response.data.lower() or b'booking' in response.data.lower()

    def test_my_bookings_pagination(self, authenticated_client, test_user, test_package, app):
        """Test pagination of user's bookings."""
        with app.app_context():
            from app import db
            from datetime import date
            
            # Create multiple bookings
            for i in range(15):
                booking = Booking(
                    user_id=test_user.id,
                    package_id=test_package.id,
                    num_travelers=2,
                    travel_date=date.today() + timedelta(days=i+30),
                    total_price=5000.00,
                    status='pending'
                )
                db.session.add(booking)
            db.session.commit()
        
        response = authenticated_client.get('/bookings/my-bookings')
        assert response.status_code == 200
        
        # Test page 2
        response = authenticated_client.get('/bookings/my-bookings?page=2')
        assert response.status_code == 200
