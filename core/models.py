"""Model SQLAlchemy untuk ATW (public) dan FVI (internal).

Menggunakan PostGIS geometry via geoalchemy2.
"""
from sqlalchemy import Boolean
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, Date, DateTime,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship
from geoalchemy2 import Geometry

PublicBase = declarative_base()
InternalBase = declarative_base()


# =========================================================
# PUBLIC SCHEMA — ATW
# =========================================================

class Region(PublicBase):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True)
    level = Column(String(20), nullable=False)
    kode_bps = Column(String(20), index=True)
    kode_kemendagri = Column(String(20), index=True)
    nama = Column(String(150), nullable=False)
    parent_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    geom = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326))

    parent = relationship("Region", remote_side=[id], backref="children")

    __table_args__ = (
        Index("ix_region_level_nama", "level", "nama"),
    )


class Budget(PublicBase):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    year = Column(Integer, nullable=False)
    source_fund = Column(String(50))
    program = Column(String(200))
    activity = Column(String(200))
    category = Column(String(50))
    pagu = Column(Float, default=0.0)
    realisasi_q1 = Column(Float, default=0.0)
    realisasi_q2 = Column(Float, default=0.0)
    realisasi_q3 = Column(Float, default=0.0)
    realisasi_q4 = Column(Float, default=0.0)

    region = relationship("Region")

    __table_args__ = (Index("ix_budget_region_year", "region_id", "year"),)


class Transfer(PublicBase):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    year = Column(Integer, nullable=False)
    type = Column(String(50), nullable=False)
    pagu = Column(Float, default=0.0)
    realisasi_q1 = Column(Float, default=0.0)
    realisasi_q2 = Column(Float, default=0.0)
    realisasi_q3 = Column(Float, default=0.0)
    realisasi_q4 = Column(Float, default=0.0)

    region = relationship("Region")

    __table_args__ = (
        UniqueConstraint("region_id", "year", "type", name="uq_transfer"),
        Index("ix_transfer_year_type", "year", "type"),
    )


class OwnRevenue(PublicBase):
    __tablename__ = "own_revenue"

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    year = Column(Integer, nullable=False)
    type = Column(String(50))
    target = Column(Float, default=0.0)
    realisasi = Column(Float, default=0.0)

    region = relationship("Region")


class PNBP(PublicBase):
    __tablename__ = "pnbp"

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    year = Column(Integer, nullable=False)
    sector = Column(String(50))
    amount = Column(Float, default=0.0)

    region = relationship("Region")


class Project(PublicBase):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50))
    location_name = Column(String(255))
    geom = Column(Geometry(geometry_type="POINT", srid=4326))
    contractor = Column(String(255))
    contract_value = Column(Float, default=0.0)
    progress = Column(Float, default=0.0)
    status = Column(String(20))
    year = Column(Integer)

    region = relationship("Region")
    budget = relationship("Budget")

class Feedback(PublicBase):
    """Feedback dari publik untuk ATW."""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(150))
    category = Column(String(50), nullable=False)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    page_url = Column(String(500))
    user_agent = Column(String(500))
    status = Column(String(20), default="new")  # new | read | resolved | spam
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_feedback_status", "status"),
        Index("ix_feedback_created", "created_at"),
    )

class ProjectPhoto(PublicBase):
    """Foto dokumentasi proyek/kejadian di lapangan."""
    __tablename__ = "project_photos"

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    category = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(50))
    latitude = Column(Float)
    longitude = Column(Float)
    geom = Column(Geometry(geometry_type="POINT", srid=4326))
    uploaded_by = Column(String(100))
    status = Column(String(20), default="approved")
    created_at = Column(DateTime, default=datetime.utcnow)

    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_photo_region", "region_id"),
        Index("ix_photo_category", "category"),
        Index("ix_photo_created", "created_at"),
    )

class User(PublicBase):
    """User ATW dengan role-based access."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    full_name = Column(String(100))
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="kontributor")
    # role: publik | kontributor | verifikator | admin
    is_active = Column(Boolean, default=True, server_default="true", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)


class UserSession(PublicBase):
    """Session token untuk login."""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_agent = Column(String(500))
    ip_address = Column(String(50))

    user = relationship("User")

# =========================================================
# INTERNAL SCHEMA — FVI
# =========================================================

class MacroIndicator(InternalBase):
    __tablename__ = "macro_indicators"

    id = Column(Integer, primary_key=True)
    period = Column(Date, nullable=False)
    indicator = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)

    __table_args__ = (UniqueConstraint("period", "indicator", name="uq_macro"),)


class ExternalIndicator(InternalBase):
    __tablename__ = "external_indicators"

    id = Column(Integer, primary_key=True)
    period = Column(Date, nullable=False)
    indicator = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)

    __table_args__ = (UniqueConstraint("period", "indicator", name="uq_external"),)


class RegionalCluster(InternalBase):
    __tablename__ = "regional_clusters"

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, nullable=False)
    cluster_id = Column(Integer, nullable=False)
    silhouette = Column(Float)
    year = Column(Integer)

    __table_args__ = (UniqueConstraint("region_id", "year", name="uq_cluster"),)


class FVIScore(InternalBase):
    __tablename__ = "fvi_scores"

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer)
    internal_score = Column(Float)
    macro_score = Column(Float)
    external_score = Column(Float)
    fvi_score = Column(Float)
    fvi_lower = Column(Float)
    fvi_upper = Column(Float)
    risk_class = Column(String(20))
    dominant_factor = Column(String(100))

    __table_args__ = (
        UniqueConstraint("region_id", "year", "quarter", name="uq_fvi"),
        Index("ix_fvi_year", "year"),
    )


class PanelExpert(InternalBase):
    __tablename__ = "panel_experts"

    id = Column(Integer, primary_key=True)
    name = Column(String(150))
    affiliation = Column(String(200))
    expertise = Column(String(200))
    role = Column(String(50))
    weight_vote = Column(Float, default=1.0)


class AHPWeight(InternalBase):
    __tablename__ = "ahp_weights"

    id = Column(Integer, primary_key=True)
    layer = Column(String(30))
    variable = Column(String(100))
    weight = Column(Float)
    panel_id = Column(Integer, ForeignKey("panel_experts.id"))
    consistency_ratio = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class FiscalDistressLabel(InternalBase):
    __tablename__ = "fiscal_distress_labels"

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    label = Column(String(30))
    category = Column(String(50))
    confidence = Column(String(20))
    source = Column(Text)
    submitted_by = Column(String(150))
    verified_by = Column(String(150))
    created_at = Column(DateTime, default=datetime.utcnow)


class AnomalyFlag(InternalBase):
    __tablename__ = "anomaly_flags"

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, nullable=False)
    project_id = Column(Integer)
    year = Column(Integer)
    flag_type = Column(String(50))
    severity = Column(String(20))
    description = Column(Text)
    detected_at = Column(DateTime, default=datetime.utcnow)


class AuditNote(InternalBase):
    __tablename__ = "audit_notes"

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer)
    project_id = Column(Integer)
    note = Column(Text)
    author = Column(String(150))
    created_at = Column(DateTime, default=datetime.utcnow)