"""Agent model for routing package inquiries to the right staff member."""
from datetime import datetime, timezone
from app import db


class Agent(db.Model):
    """A staff member who can be assigned to packages.

    Referenced by TourPackage.assigned_agent_id — updating an agent's
    email here automatically applies to every package they're assigned to.
    """

    __tablename__ = "agents"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    notes = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_visa_agent = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Agent {self.name}>"
