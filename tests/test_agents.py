"""Tests for the agent-based inquiry routing system.

Covers Agent CRUD via the admin routes, the single-visa-agent
exclusivity rule, the package-assignment delete guard, and the CC
routing logic in email_service.send_admin_new_inquiry (package agent
vs. site-wide visa agent vs. no agent at all).
"""
import pytest
from datetime import date, timedelta
from models.agent import Agent
from models.package import TourPackage
from models.inquiry import Inquiry


def _make_agent(db, **overrides):
    defaults = dict(
        name="Juan Dela Cruz",
        email="juan@travelworthyph.com",
        notes=None,
        is_active=True,
        is_visa_agent=False,
    )
    defaults.update(overrides)
    agent = Agent(**defaults)
    db.session.add(agent)
    db.session.commit()
    return agent


def _make_package(db, **overrides):
    defaults = dict(
        title="Test Package",
        description="A test tour package",
        destination="Test Destination",
        duration_days=5,
        price=10000.00,
        currency="PHP",
        is_active=True,
        package_type="domestic",
    )
    defaults.update(overrides)
    package = TourPackage(**defaults)
    db.session.add(package)
    db.session.commit()
    return package


def _make_inquiry(db, **overrides):
    today = date.today()
    defaults = dict(
        name="Maria Santos",
        email="maria@example.com",
        contact_number="09171234567",
        destination="Palawan",
        travel_date_from=today + timedelta(days=10),
        travel_date_to=today + timedelta(days=14),
        num_adults=2,
        status="new",
    )
    defaults.update(overrides)
    inquiry = Inquiry(**defaults)
    db.session.add(inquiry)
    db.session.commit()
    return inquiry


class TestAgentAccess:
    """Non-admins should never reach any agents route."""

    def test_list_requires_login(self, client):
        response = client.get("/admin/agents")
        assert response.status_code in (302, 401, 403)

    def test_list_rejects_non_admin_user(self, authenticated_client):
        response = authenticated_client.get("/admin/agents")
        assert response.status_code in (302, 403)

    def test_add_requires_login(self, client):
        response = client.post("/admin/agents/add", data={"name": "X", "email": "x@example.com"})
        assert response.status_code in (302, 401, 403)

    def test_toggle_active_rejects_non_admin(self, app, authenticated_client):
        from app import db

        agent = _make_agent(db)
        response = authenticated_client.post(f"/admin/agents/toggle-active/{agent.id}")
        assert response.status_code in (302, 403)

    def test_delete_rejects_non_admin(self, app, authenticated_client):
        from app import db

        agent = _make_agent(db)
        response = authenticated_client.post(f"/admin/agents/delete/{agent.id}")
        assert response.status_code in (302, 403)


class TestAgentViews:
    """Happy-path GET checks — none of these existed before, so a broken
    template (bad Jinja, missing context var) on any of these pages would
    have passed the whole suite silently."""

    def test_admin_can_view_agents_list(self, app, admin_client):
        from app import db

        _make_agent(db, name="Juan Dela Cruz")
        response = admin_client.get("/admin/agents")
        assert response.status_code == 200
        assert b"Juan Dela Cruz" in response.data

    def test_admin_can_view_add_agent_form(self, app, admin_client):
        response = admin_client.get("/admin/agents/add")
        assert response.status_code == 200

    def test_admin_can_view_edit_agent_form_with_existing_data(self, app, admin_client):
        from app import db

        agent = _make_agent(db, name="Juan Dela Cruz", email="juan@travelworthyph.com")
        response = admin_client.get(f"/admin/agents/edit/{agent.id}")
        assert response.status_code == 200
        assert b"Juan Dela Cruz" in response.data
        assert b"juan@travelworthyph.com" in response.data


class TestAgentNotFound:
    """Every mutating agent route uses db.get_or_404 — confirm a bogus id
    actually 404s instead of raising an unhandled exception."""

    def test_edit_nonexistent_agent_returns_404(self, app, admin_client):
        response = admin_client.get("/admin/agents/edit/999999")
        assert response.status_code == 404

    def test_toggle_active_nonexistent_agent_returns_404(self, app, admin_client):
        response = admin_client.post("/admin/agents/toggle-active/999999")
        assert response.status_code == 404

    def test_set_visa_agent_nonexistent_returns_404(self, app, admin_client):
        response = admin_client.post("/admin/agents/set-visa-agent/999999")
        assert response.status_code == 404

    def test_unset_visa_agent_nonexistent_returns_404(self, app, admin_client):
        response = admin_client.post("/admin/agents/unset-visa-agent/999999")
        assert response.status_code == 404

    def test_delete_nonexistent_agent_returns_404(self, app, admin_client):
        response = admin_client.post("/admin/agents/delete/999999")
        assert response.status_code == 404


class TestAgentCRUD:
    def test_admin_can_add_agent(self, app, admin_client):
        response = admin_client.post(
            "/admin/agents/add",
            data={
                "name": "Juan Dela Cruz",
                "email": "juan@travelworthyph.com",
                "notes": "Handles Palawan packages",
                "is_active": "on",
            },
        )
        assert response.status_code == 302
        agent = Agent.query.filter_by(email="juan@travelworthyph.com").first()
        assert agent is not None
        assert agent.name == "Juan Dela Cruz"
        assert agent.is_active is True

    def test_add_agent_requires_name_and_email(self, app, admin_client):
        response = admin_client.post("/admin/agents/add", data={"name": "", "email": ""})
        assert response.status_code == 302
        assert Agent.query.count() == 0

    def test_admin_can_edit_agent(self, app, admin_client):
        from app import db

        agent = _make_agent(db, name="Old Name")
        response = admin_client.post(
            f"/admin/agents/edit/{agent.id}",
            data={
                "name": "New Name",
                "email": "new@example.com",
                "notes": "",
                "is_active": "on",
            },
        )
        assert response.status_code == 302
        db.session.refresh(agent)
        assert agent.name == "New Name"
        assert agent.email == "new@example.com"

    def test_toggle_active_flips_state_and_returns_json(self, app, admin_client):
        from app import db

        agent = _make_agent(db, is_active=True)
        response = admin_client.post(f"/admin/agents/toggle-active/{agent.id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["is_active"] is False
        db.session.refresh(agent)
        assert agent.is_active is False


class TestVisaAgentExclusivity:
    def test_set_visa_agent_marks_agent(self, app, admin_client):
        from app import db

        agent = _make_agent(db)
        response = admin_client.post(f"/admin/agents/set-visa-agent/{agent.id}")
        assert response.status_code == 200
        db.session.refresh(agent)
        assert agent.is_visa_agent is True

    def test_setting_new_visa_agent_unsets_previous_one(self, app, admin_client):
        from app import db

        agent_a = _make_agent(db, name="Agent A", email="a@example.com", is_visa_agent=True)
        agent_b = _make_agent(db, name="Agent B", email="b@example.com")

        response = admin_client.post(f"/admin/agents/set-visa-agent/{agent_b.id}")
        assert response.status_code == 200

        db.session.refresh(agent_a)
        db.session.refresh(agent_b)
        assert agent_a.is_visa_agent is False
        assert agent_b.is_visa_agent is True

    def test_only_one_agent_is_ever_visa_agent(self, app, admin_client):
        from app import db

        agents = [_make_agent(db, name=f"Agent {i}", email=f"agent{i}@example.com") for i in range(4)]
        for agent in agents:
            admin_client.post(f"/admin/agents/set-visa-agent/{agent.id}")

        visa_agents = Agent.query.filter_by(is_visa_agent=True).all()
        assert len(visa_agents) == 1
        assert visa_agents[0].id == agents[-1].id

    def test_unset_visa_agent_clears_flag(self, app, admin_client):
        from app import db

        agent = _make_agent(db, is_visa_agent=True)
        response = admin_client.post(f"/admin/agents/unset-visa-agent/{agent.id}")
        assert response.status_code == 200
        db.session.refresh(agent)
        assert agent.is_visa_agent is False


class TestAgentDelete:
    def test_admin_can_delete_unassigned_agent(self, app, admin_client):
        from app import db

        agent = _make_agent(db)
        agent_id = agent.id
        response = admin_client.post(f"/admin/agents/delete/{agent_id}")
        assert response.status_code == 302
        assert db.session.get(Agent, agent_id) is None

    def test_cannot_delete_agent_assigned_to_a_package(self, app, admin_client):
        from app import db

        agent = _make_agent(db)
        _make_package(db, assigned_agent_id=agent.id)
        agent_id = agent.id

        response = admin_client.post(f"/admin/agents/delete/{agent_id}")
        assert response.status_code == 302
        assert db.session.get(Agent, agent_id) is not None

    def test_deleting_visa_agent_is_allowed_but_flashes_a_warning(self, app, admin_client):
        """Deleting the current visa agent (when they hold no packages) is
        still allowed — same as before — but now flashes an explicit
        warning that visa-inquiry routing just broke, instead of deleting
        silently with no feedback at all."""
        from app import db

        agent = _make_agent(db, is_visa_agent=True)
        agent_id = agent.id

        response = admin_client.post(f"/admin/agents/delete/{agent_id}", follow_redirects=True)
        assert response.status_code == 200
        assert db.session.get(Agent, agent_id) is None
        # No agent is configured to receive visa inquiries anymore — visa
        # emails will now stop being CC'd to anyone until a new one is set.
        assert Agent.query.filter_by(is_visa_agent=True).first() is None
        page = response.get_data(as_text=True)
        assert "visa agent" in page.lower()
        assert "no longer be cc" in page.lower()


class TestInquiryAgentRouting:
    """Tests email_service.send_admin_new_inquiry's CC logic directly,
    bypassing the route layer so the test can capture the outgoing
    flask_mail.Message before it's discarded.
    """

    @pytest.fixture
    def captured_messages(self, app, monkeypatch):
        """Force mail 'on' for this test and capture every Message
        instead of actually sending it."""
        app.config["MAIL_USERNAME"] = "noreply@travelworthyph.com"
        sent = []
        import email_service

        monkeypatch.setattr(email_service.mail, "send", lambda msg: sent.append(msg))
        return sent

    def test_package_inquiry_ccs_active_assigned_agent(self, app, captured_messages):
        from app import db
        from email_service import send_admin_new_inquiry

        agent = _make_agent(db, email="agent@example.com", is_active=True)
        package = _make_package(db, assigned_agent_id=agent.id)
        inquiry = _make_inquiry(db, package_id=package.id)

        send_admin_new_inquiry("admin@example.com", inquiry)

        assert len(captured_messages) == 1
        assert captured_messages[0].cc == ["agent@example.com"]

    def test_package_inquiry_skips_cc_when_agent_inactive(self, app, captured_messages):
        from app import db
        from email_service import send_admin_new_inquiry

        agent = _make_agent(db, email="agent@example.com", is_active=False)
        package = _make_package(db, assigned_agent_id=agent.id)
        inquiry = _make_inquiry(db, package_id=package.id)

        send_admin_new_inquiry("admin@example.com", inquiry)

        assert len(captured_messages) == 1
        assert captured_messages[0].cc == []

    def test_package_inquiry_with_no_assigned_agent_has_no_cc(self, app, captured_messages):
        from app import db
        from email_service import send_admin_new_inquiry

        package = _make_package(db)
        inquiry = _make_inquiry(db, package_id=package.id)

        send_admin_new_inquiry("admin@example.com", inquiry)

        assert len(captured_messages) == 1
        assert captured_messages[0].cc == []

    def test_visa_inquiry_ccs_the_visa_agent(self, app, captured_messages):
        from app import db
        from email_service import send_admin_new_inquiry

        _make_agent(db, email="visa@example.com", is_visa_agent=True, is_active=True)
        inquiry = _make_inquiry(db, special_requests="[FOR VISA] Need help with Japan visa")

        send_admin_new_inquiry("admin@example.com", inquiry)

        assert len(captured_messages) == 1
        assert captured_messages[0].cc == ["visa@example.com"]

    def test_visa_inquiry_with_no_visa_agent_has_no_cc(self, app, captured_messages):
        from app import db
        from email_service import send_admin_new_inquiry

        inquiry = _make_inquiry(db, special_requests="[FOR VISA] Need help with Japan visa")

        send_admin_new_inquiry("admin@example.com", inquiry)

        assert len(captured_messages) == 1
        assert captured_messages[0].cc == []

    def test_visa_inquiry_skips_inactive_visa_agent(self, app, captured_messages):
        from app import db
        from email_service import send_admin_new_inquiry

        _make_agent(db, email="visa@example.com", is_visa_agent=True, is_active=False)
        inquiry = _make_inquiry(db, special_requests="[FOR VISA] Need help with Japan visa")

        send_admin_new_inquiry("admin@example.com", inquiry)

        assert len(captured_messages) == 1
        assert captured_messages[0].cc == []

    def test_general_inquiry_no_package_no_visa_tag_has_no_cc(self, app, captured_messages):
        from app import db
        from email_service import send_admin_new_inquiry

        _make_agent(db, email="visa@example.com", is_visa_agent=True, is_active=True)
        inquiry = _make_inquiry(db, special_requests="Just a general question, no tags")

        send_admin_new_inquiry("admin@example.com", inquiry)

        assert len(captured_messages) == 1
        assert captured_messages[0].cc == []

    def test_package_agent_takes_priority_over_visa_tag(self, app, captured_messages):
        """A package-linked inquiry always routes to the package's agent,
        never the visa agent — package_id is checked before special_requests
        in the if/elif, so this documents existing (correct) precedence
        rather than a gap."""
        from app import db
        from email_service import send_admin_new_inquiry

        package_agent = _make_agent(db, name="Package Agent", email="package-agent@example.com")
        _make_agent(db, name="Visa Agent", email="visa-agent@example.com", is_visa_agent=True)
        package = _make_package(db, assigned_agent_id=package_agent.id)
        inquiry = _make_inquiry(db, package_id=package.id, special_requests="[FOR VISA] mistakenly tagged")

        send_admin_new_inquiry("admin@example.com", inquiry)

        assert len(captured_messages) == 1
        assert captured_messages[0].cc == ["package-agent@example.com"]
