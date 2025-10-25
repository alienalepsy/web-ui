"""
Application settings and configuration

This module provides a flexible configuration system that can be easily
extended and modified for future requirements.
"""

from pathlib import Path
from typing import Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.parent


class DatabaseConfig(BaseModel):
    """Database configuration"""
    type: str = Field(default="sqlite", description="Database type (sqlite, postgresql, mysql)")
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="tesl_tracker.db", description="Database name")
    user: str = Field(default="", description="Database user")
    password: str = Field(default="", description="Database password")

    @property
    def connection_string(self) -> str:
        """Generate database connection string"""
        if self.type == "sqlite":
            db_path = BASE_DIR / self.name
            return f"sqlite:///{db_path}"
        elif self.type == "postgresql":
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        elif self.type == "mysql":
            return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        else:
            raise ValueError(f"Unsupported database type: {self.type}")


class EntitlementConfig(BaseModel):
    """TESL entitlement configuration - easily modifiable for policy changes"""

    # Current entitlement amounts (can be updated annually)
    level_1_annual_entitlement: float = Field(
        default=38000.00,
        description="Annual TESL entitlement for Level 1 Staff Specialists"
    )

    # Maximum accrual period (years)
    max_accrual_years: int = Field(
        default=2,
        description="Maximum years of TESL entitlement that can be accrued"
    )

    # Financial year settings
    financial_year_start_month: int = Field(
        default=7,
        description="Financial year start month (1-12, 7=July for Australian FY)"
    )
    financial_year_start_day: int = Field(
        default=1,
        description="Financial year start day"
    )

    # Pro-rata calculation settings
    enable_fte_prorata: bool = Field(
        default=True,
        description="Enable pro-rata calculation based on FTE"
    )
    enable_partial_year_prorata: bool = Field(
        default=True,
        description="Enable pro-rata calculation for partial year employment"
    )

    # Level 2-5 default multipliers (can be overridden per facility)
    level_2_multiplier: float = Field(default=0.8, description="Level 2 entitlement multiplier")
    level_3_multiplier: float = Field(default=0.6, description="Level 3 entitlement multiplier")
    level_4_multiplier: float = Field(default=0.4, description="Level 4 entitlement multiplier")
    level_5_multiplier: float = Field(default=0.2, description="Level 5 entitlement multiplier")

    def get_level_multiplier(self, level: int) -> float:
        """Get entitlement multiplier for a given level"""
        multipliers = {
            1: 1.0,
            2: self.level_2_multiplier,
            3: self.level_3_multiplier,
            4: self.level_4_multiplier,
            5: self.level_5_multiplier,
        }
        return multipliers.get(level, 0.0)


class ApprovalConfig(BaseModel):
    """Approval workflow configuration"""

    # Approval levels required for different claim amounts
    approval_thresholds: Dict[str, float] = Field(
        default={
            "supervisor": 0,      # All claims need supervisor approval
            "committee": 5000,    # Claims > $5000 need committee approval
            "finance": 10000,     # Claims > $10000 need finance approval
        },
        description="Approval thresholds by role"
    )

    # Auto-approval settings (future feature)
    enable_auto_approval: bool = Field(
        default=False,
        description="Enable automatic approval for qualifying claims"
    )
    auto_approval_max_amount: float = Field(
        default=1000,
        description="Maximum amount for auto-approval"
    )


class NotificationConfig(BaseModel):
    """Notification and alert configuration"""

    # Balance warning thresholds (percentage of max)
    balance_warning_threshold: float = Field(
        default=0.9,
        description="Send warning when balance reaches this percentage of maximum"
    )

    # Expiry warning periods (months before year end)
    expiry_warning_months: list[int] = Field(
        default=[9, 6, 3],
        description="Months before year end to send expiry warnings"
    )

    # Email settings (for future integration)
    enable_email_notifications: bool = Field(default=False)
    smtp_host: str = Field(default="")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")
    from_email: str = Field(default="noreply@health.nsw.gov.au")


class SecurityConfig(BaseModel):
    """Security and audit configuration"""

    # Session settings
    session_timeout_minutes: int = Field(default=60, description="Session timeout in minutes")

    # Audit settings
    enable_audit_log: bool = Field(default=True, description="Enable audit logging")
    audit_retention_days: int = Field(default=2555, description="Audit log retention (7 years)")

    # Data retention
    data_retention_years: int = Field(default=7, description="Data retention period (Australian requirement)")


class UIConfig(BaseModel):
    """User interface configuration"""

    # Gradio settings
    server_name: str = Field(default="127.0.0.1", description="Server bind address")
    server_port: int = Field(default=7789, description="Server port")
    theme: str = Field(default="default", description="UI theme")

    # Pagination
    default_page_size: int = Field(default=25, description="Default number of items per page")
    max_page_size: int = Field(default=100, description="Maximum items per page")


class AppConfig(BaseModel):
    """Main application configuration"""

    # Sub-configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    entitlements: EntitlementConfig = Field(default_factory=EntitlementConfig)
    approvals: ApprovalConfig = Field(default_factory=ApprovalConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    ui: UIConfig = Field(default_factory=UIConfig)

    # Application metadata
    app_name: str = Field(default="TESL Balance Tracker")
    app_version: str = Field(default="1.0.0")
    environment: str = Field(default="development", description="Environment (development/staging/production)")

    # Feature flags (for future features)
    features: Dict[str, bool] = Field(
        default={
            "advanced_reporting": True,
            "data_export": True,
            "bulk_import": False,
            "api_access": False,
            "mobile_app": False,
        },
        description="Feature flags for conditional functionality"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton configuration instance
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Get application configuration singleton"""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reload_config() -> AppConfig:
    """Reload configuration from environment"""
    global _config
    _config = AppConfig()
    return _config


# Export configuration
config = get_config()
