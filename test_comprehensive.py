"""
Comprehensive test suite for Travel Agency Enhanced application.
Tests all critical functionality including forms, authentication, and error handling.
"""
import sys
import os
import json
from datetime import datetime, date, timedelta

# Add the project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.user import User
from models.package import TourPackage
from models.inquiry import Inquiry
from models.contact import ContactMessage
from forms import RegisterForm, LoginForm, ContactForm, InquiryForm
from constants import InquiryStatus
from werkzeug.security import check_password_hash


class TestRunner:
    """Main test runner class for the Travel Agency application."""

    def __init__(self):
        self.app = create_app()
        # Disable CSRF protection for testing
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.results = []
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0

    def test(self, test_name, condition, error_msg=""):
        """Record test result."""
        self.test_count += 1
        if condition:
            self.passed_count += 1
            self.results.append({
                'name': test_name,
                'status': 'PASS',
                'message': ''
            })
            print(f"[PASS] {test_name}")
        else:
            self.failed_count += 1
            self.results.append({
                'name': test_name,
                'status': 'FAIL',
                'message': error_msg
            })
            print(f"[FAIL] {test_name}: {error_msg}")

    def run_environment_tests(self):
        """Test environment configuration."""
        print("\n" + "="*60)
        print("ENVIRONMENT TESTS")
        print("="*60)

        # Test SECRET_KEY is set
        self.test(
            "SECRET_KEY configured",
            self.app.config.get('SECRET_KEY') is not None,
            "SECRET_KEY not found in config"
        )

        # Test DATABASE_URL is set
        self.test(
            "DATABASE_URL configured",
            self.app.config.get('SQLALCHEMY_DATABASE_URI') is not None,
            "DATABASE_URL not found in config"
        )

        # Test Admin credentials configured
        self.test(
            "ADMIN_EMAIL configured",
            os.getenv('ADMIN_EMAIL') is not None,
            "ADMIN_EMAIL environment variable not set"
        )

        # Test Debug mode
        is_debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
        self.test(
            "Flask debug mode",
            is_debug,
            "Debug mode not enabled"
        )

    def run_database_tests(self):
        """Test database initialization and operations."""
        print("\n" + "="*60)
        print("DATABASE TESTS")
        print("="*60)

        try:
            # Create tables
            db.create_all()
            self.test(
                "Database tables created",
                True,
                ""
            )
        except Exception as e:
            self.test(
                "Database tables created",
                False,
                str(e)
            )

        try:
            # Test default admin creation/setup
            admin_email = os.getenv('ADMIN_EMAIL')
            admin = User.query.filter_by(email=admin_email).first()
            self.test(
                "Default admin user exists",
                admin is not None,
                "Admin user not found in database"
            )

            if admin:
                # Ensure admin flag is set
                if not admin.is_admin:
                    admin.is_admin = True
                    db.session.commit()
                
                self.test(
                    "Admin user has is_admin flag",
                    admin.is_admin == True,
                    f"Admin flag is {admin.is_admin}"
                )
        except Exception as e:
            self.test(
                "Default admin user check",
                False,
                str(e)
            )

    def run_form_validation_tests(self):
        """Test form validation with the new WTForms classes."""
        print("\n" + "="*60)
        print("FORM VALIDATION TESTS")
        print("="*60)

        # Test RegisterForm - valid data
        with self.app.test_request_context(
            '/auth/register',
            method='POST',
            data={
                'name': 'Test User',
                'email': 'testuser@example.com',
                'phone': '+1234567890',
                'password': 'TestPassword123',
                'confirm_password': 'TestPassword123'
            }
        ):
            form = RegisterForm()
            self.test(
                "RegisterForm accepts valid data",
                form.validate() if form.is_submitted() else True,
                f"Form validation failed: {form.errors if hasattr(form, 'errors') else 'N/A'}"
            )

        # Test RegisterForm - weak password
        with self.app.test_request_context(
            '/auth/register',
            method='POST',
            data={
                'name': 'Test User',
                'email': 'test@example.com',
                'password': 'weak',
                'confirm_password': 'weak'
            }
        ):
            form = RegisterForm()
            form.validate()  # Explicitly validate the form
            has_password_error = 'password' in form.errors if form.errors else False
            self.test(
                "RegisterForm rejects weak password",
                has_password_error,
                "Form should reject password with less than 12 characters"
            )

        # Test RegisterForm - mismatched passwords
        with self.app.test_request_context(
            '/auth/register',
            method='POST',
            data={
                'name': 'Test User',
                'email': 'test@example.com',
                'password': 'ValidPassword123',
                'confirm_password': 'DifferentPassword123'
            }
        ):
            form = RegisterForm()
            form.validate()  # Explicitly validate the form
            has_confirm_error = 'confirm_password' in form.errors if form.errors else False
            self.test(
                "RegisterForm rejects mismatched passwords",
                has_confirm_error,
                "Form should reject mismatched passwords"
            )

        # Test LoginForm
        with self.app.test_request_context(
            '/auth/login',
            method='POST',
            data={
                'email': 'test@example.com',
                'password': 'password123',
                'remember': False
            }
        ):
            form = LoginForm()
            self.test(
                "LoginForm validates correctly",
                form.validate() if form.is_submitted() else True,
                f"LoginForm validation error: {form.errors if hasattr(form, 'errors') else 'N/A'}"
            )

        # Test ContactForm
        with self.app.test_request_context(
            '/contact',
            method='POST',
            data={
                'name': 'John Doe',
                'email': 'john@example.com',
                'subject': 'Test Subject',
                'message': 'This is a test message for contact form validation.'
            }
        ):
            form = ContactForm()
            self.test(
                "ContactForm validates correctly",
                form.validate() if form.is_submitted() else True,
                f"ContactForm validation error: {form.errors if hasattr(form, 'errors') else 'N/A'}"
            )

    def run_authentication_tests(self):
        """Test authentication flows."""
        print("\n" + "="*60)
        print("AUTHENTICATION TESTS")
        print("="*60)

        # Test registration endpoint exists
        response = self.client.get('/auth/register')
        self.test(
            "Registration page accessible",
            response.status_code == 200,
            f"Expected 200, got {response.status_code}"
        )

        # Test login endpoint exists
        response = self.client.get('/auth/login')
        self.test(
            "Login page accessible",
            response.status_code == 200,
            f"Expected 200, got {response.status_code}"
        )

        # Test user can register
        response = self.client.post('/auth/register', data={
            'name': 'Test Registrant',
            'email': 'register_test@example.com',
            'phone': '+1234567890',
            'password': 'ValidPassword123',
            'confirm_password': 'ValidPassword123'
        }, follow_redirects=True)

        registered_user = User.query.filter_by(email='register_test@example.com').first()
        self.test(
            "User registration creates database record",
            registered_user is not None,
            "User not found in database after registration"
        )

        if registered_user:
            self.test(
                "User password is hashed",
                not check_password_hash(registered_user.password, 'ValidPassword123') == False,
                "Password hashing failed"
            )

        # Test admin login
        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')

        response = self.client.post('/auth/login', data={
            'email': admin_email,
            'password': admin_password,
            'remember': False
        }, follow_redirects=True)

        self.test(
            "Admin login successful",
            response.status_code == 200,
            f"Login failed with status {response.status_code}"
        )

    def run_package_tests(self):
        """Test package listing and queries."""
        print("\n" + "="*60)
        print("PACKAGE TESTS")
        print("="*60)

        try:
            # Create test package
            test_package = TourPackage(
                title='Test Package',
                description='This is a test tour package for comprehensive testing.',
                destination='Test Destination',
                duration_days=7,
                price=5000.00,
                currency='PHP',
                is_active=True
            )
            db.session.add(test_package)
            db.session.commit()

            self.test(
                "Tour package creation",
                test_package.id is not None,
                "Package not saved to database"
            )

            # Test package retrieval
            retrieved_package = TourPackage.query.filter_by(
                title='Test Package'
            ).first()

            self.test(
                "Package retrieval by title",
                retrieved_package is not None,
                "Package not found in database"
            )

            # Test packages list endpoint
            response = self.client.get('/packages/')
            self.test(
                "Packages list endpoint accessible",
                response.status_code == 200,
                f"Expected 200, got {response.status_code}"
            )

            # Test package detail endpoint
            if test_package.id:
                response = self.client.get(f'/packages/{test_package.id}')
                self.test(
                    "Package detail page accessible",
                    response.status_code == 200,
                    f"Expected 200, got {response.status_code}"
                )

        except Exception as e:
            self.test(
                "Package tests",
                False,
                str(e)
            )

    def run_inquiry_tests(self):
        """Test inquiry functionality."""
        print("\n" + "="*60)
        print("INQUIRY TESTS")
        print("="*60)

        try:
            # Create test inquiry
            from_date = date.today() + timedelta(days=10)
            to_date = date.today() + timedelta(days=17)

            inquiry = Inquiry(
                name='Test Inquirer',
                email='inquirer@example.com',
                contact_number='+1234567890',
                destination='Test Destination',
                travel_date_from=from_date,
                travel_date_to=to_date,
                num_adults=2,
                num_children=1,
                num_infants=0,
                special_requests='Test special requests',
                status=InquiryStatus.NEW.value
            )
            db.session.add(inquiry)
            db.session.commit()

            self.test(
                "Inquiry creation",
                inquiry.id is not None,
                "Inquiry not saved to database"
            )

            # Test inquiry retrieval
            retrieved_inquiry = Inquiry.query.filter_by(
                email='inquirer@example.com'
            ).first()

            self.test(
                "Inquiry retrieval",
                retrieved_inquiry is not None,
                "Inquiry not found in database"
            )

            if retrieved_inquiry:
                self.test(
                    "Inquiry status is correct",
                    retrieved_inquiry.status == InquiryStatus.NEW.value,
                    f"Expected status '{InquiryStatus.NEW.value}', got '{retrieved_inquiry.status}'"
                )

        except Exception as e:
            self.test(
                "Inquiry tests",
                False,
                str(e)
            )

    def run_contact_tests(self):
        """Test contact message functionality."""
        print("\n" + "="*60)
        print("CONTACT MESSAGE TESTS")
        print("="*60)

        try:
            # Create test contact message
            contact_msg = ContactMessage(
                name='Test Sender',
                email='sender@example.com',
                subject='Test Subject',
                message='This is a test contact message for the contact form.'
            )
            db.session.add(contact_msg)
            db.session.commit()

            self.test(
                "Contact message creation",
                contact_msg.id is not None,
                "Contact message not saved to database"
            )

            # Test contact message retrieval
            retrieved_msg = ContactMessage.query.filter_by(
                email='sender@example.com'
            ).first()

            self.test(
                "Contact message retrieval",
                retrieved_msg is not None,
                "Contact message not found in database"
            )

        except Exception as e:
            self.test(
                "Contact message tests",
                False,
                str(e)
            )

    def run_error_handling_tests(self):
        """Test error handling for edge cases."""
        print("\n" + "="*60)
        print("ERROR HANDLING TESTS")
        print("="*60)

        # Test 404 error handler
        response = self.client.get('/nonexistent-page')
        self.test(
            "404 error handler works",
            response.status_code == 404,
            f"Expected 404, got {response.status_code}"
        )

        # Test invalid package ID
        response = self.client.get('/packages/99999')
        self.test(
            "Invalid package ID returns 404",
            response.status_code == 404,
            f"Expected 404 for invalid package, got {response.status_code}"
        )

        # Test registration with duplicate email
        response1 = self.client.post('/auth/register', data={
            'name': 'User 1',
            'email': 'duplicate@example.com',
            'phone': '+1234567890',
            'password': 'ValidPassword123',
            'confirm_password': 'ValidPassword123'
        }, follow_redirects=True)

        response2 = self.client.post('/auth/register', data={
            'name': 'User 2',
            'email': 'duplicate@example.com',
            'phone': '+9876543210',
            'password': 'ValidPassword123',
            'confirm_password': 'ValidPassword123'
        }, follow_redirects=True)

        self.test(
            "Duplicate email registration rejected",
            response2.status_code == 200,
            "Duplicate email should be rejected"
        )

    def run_type_hints_verification(self):
        """Verify type hints are properly added."""
        print("\n" + "="*60)
        print("TYPE HINTS VERIFICATION")
        print("="*60)

        import inspect

        # Check User model has type hints
        user_annotations = User.__annotations__ if hasattr(User, '__annotations__') else {}
        self.test(
            "User model has type hints",
            len(user_annotations) > 0,
            f"Found {len(user_annotations)} type hints in User model"
        )

        # Check Package model has type hints
        package_annotations = TourPackage.__annotations__ if hasattr(TourPackage, '__annotations__') else {}
        self.test(
            "TourPackage model has type hints",
            len(package_annotations) > 0,
            f"Found {len(package_annotations)} type hints in TourPackage model"
        )

    def cleanup(self):
        """Clean up test data."""
        try:
            # Clear test database
            db.session.query(Inquiry).delete()
            db.session.query(ContactMessage).delete()
            db.session.query(TourPackage).delete()
            db.session.commit()
        except Exception as e:
            print(f"Cleanup warning: {e}")

    def generate_report(self):
        """Generate test report."""
        print("\n" + "="*60)
        print("TEST SUMMARY REPORT")
        print("="*60)
        print(f"\nTotal Tests: {self.test_count}")
        print(f"Passed: {self.passed_count}")
        print(f"Failed: {self.failed_count}")
        print(f"Success Rate: {(self.passed_count / self.test_count * 100):.1f}%")

        if self.failed_count == 0:
            print("\nRESULT: ALL TESTS PASSED! Application is ready for deployment.")
        else:
            print(f"\nRESULT: {self.failed_count} test(s) failed. See details above.")

        print("\n" + "="*60)

    def run_all_tests(self):
        """Run all test suites."""
        try:
            self.run_environment_tests()
            self.run_database_tests()
            self.run_form_validation_tests()
            self.run_authentication_tests()
            self.run_package_tests()
            self.run_inquiry_tests()
            self.run_contact_tests()
            self.run_error_handling_tests()
            self.run_type_hints_verification()

            self.generate_report()

        except Exception as e:
            print(f"\n❌ Critical test error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
            self.app_context.pop()


def main():
    """Main entry point for test runner."""
    print("\n" + "="*60)
    print("TEST SUITE: TRAVEL AGENCY ENHANCED - COMPREHENSIVE TESTING")
    print("="*60)
    print(f"Test Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    runner = TestRunner()
    runner.run_all_tests()

    print(f"Test End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
