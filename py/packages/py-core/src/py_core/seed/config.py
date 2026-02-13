"""Seed configuration loading from YAML files."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from py_core.database.models.user import UserRole
from py_core.database.models.widget import WidgetStatus


@dataclass
class UserSeedConfig:
    """Configuration for a user to seed."""

    email: str
    role: UserRole | None = None  # None = regular user
    approved: bool = True  # Seeded users are approved by default


@dataclass
class WidgetSeedConfig:
    """Configuration for a widget to seed."""

    name: str
    description: str | None = None
    status: WidgetStatus = WidgetStatus.DRAFT
    priority: int = 0
    is_public: bool = False


@dataclass
class SeedConfig:
    """Complete seed configuration."""

    users: list[UserSeedConfig] = field(default_factory=list)
    widgets: list[WidgetSeedConfig] = field(default_factory=list)

    @classmethod
    def load(cls, seed_dir: Path | None = None) -> "SeedConfig":
        """
        Load seed configuration from YAML files.

        Args:
            seed_dir: Directory containing seed data files.
                      Defaults to py-core/seed/ directory.

        Returns:
            SeedConfig with users and widgets from YAML files.
        """
        if seed_dir is None:
            # Default to py-core/seed/ directory (sibling to src/)
            seed_dir = Path(__file__).parent.parent.parent.parent / "seed"

        users: list[UserSeedConfig] = []
        widgets: list[WidgetSeedConfig] = []

        # Load users
        users_yaml = seed_dir / "users.yaml"
        if users_yaml.exists():
            users = cls._load_users_from_yaml(users_yaml)

        # Load widgets
        widgets_yaml = seed_dir / "widgets.yaml"
        if widgets_yaml.exists():
            widgets = cls._load_widgets_from_yaml(widgets_yaml)

        return cls(users=users, widgets=widgets)

    @classmethod
    def _load_users_from_yaml(cls, path: Path) -> list[UserSeedConfig]:
        """Load users from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f) or {}

        return [
            UserSeedConfig(
                email=str(u["email"]),
                role=UserRole(u["role"]) if u.get("role") else None,
                approved=u.get("approved", True),
            )
            for u in data.get("users", [])
        ]

    @classmethod
    def _load_widgets_from_yaml(cls, path: Path) -> list[WidgetSeedConfig]:
        """Load widgets from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f) or {}

        return [
            WidgetSeedConfig(
                name=str(w["name"]),
                description=w.get("description"),
                status=(
                    WidgetStatus(w["status"]) if w.get("status") else WidgetStatus.DRAFT
                ),
                priority=w.get("priority", 0),
                is_public=w.get("is_public", False),
            )
            for w in data.get("widgets", [])
        ]
