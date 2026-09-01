from sqlalchemy import Column, Integer, String
from .database import Base


# ============================================================
# USER TABLE
# ============================================================

class User(Base):

    __tablename__ = "users"

    # --------------------------------------------------------
    # Primary Key
    # --------------------------------------------------------

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # --------------------------------------------------------
    # Common User Information
    # --------------------------------------------------------

    role = Column(
        String,
        nullable=False
    )

    full_name = Column(
        String,
        nullable=False
    )

    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    mobile = Column(
        String,
        nullable=False
    )

    date_of_birth = Column(
        String,
        nullable=False
    )

    gender = Column(
        String,
        nullable=True
    )

    password = Column(
        String,
        nullable=False
    )

    # --------------------------------------------------------
    # Doctor Information
    # --------------------------------------------------------

    specialization = Column(
        String,
        nullable=True
    )

    license_number = Column(
        String,
        nullable=True
    )

    hospital = Column(
        String,
        nullable=True
    )

    # --------------------------------------------------------
    # CHW Information
    # --------------------------------------------------------

    employee_id = Column(
        String,
        nullable=True
    )

    organization = Column(
        String,
        nullable=True
    )

    region = Column(
        String,
        nullable=True
    )


# ============================================================
# PATIENT TABLE
# ============================================================

class Patient(Base):

    __tablename__ = "patients"

    # --------------------------------------------------------
    # Internal Patient Database ID
    # --------------------------------------------------------

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # --------------------------------------------------------
    # MedPath Patient ID
    # Example: MP00001
    # --------------------------------------------------------

    patient_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    # --------------------------------------------------------
    # Link Patient to User
    # Patient.linked_user_id → User.id
    # --------------------------------------------------------

    linked_user_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    # --------------------------------------------------------
    # Patient Information
    # --------------------------------------------------------

    name = Column(
        String,
        nullable=False
    )

    date_of_birth = Column(
        String,
        nullable=False
    )

    gender = Column(
        String,
        nullable=True
    )

    phone = Column(
        String,
        nullable=True
    )