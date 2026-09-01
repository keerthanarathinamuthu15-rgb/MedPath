from pydantic import BaseModel
from typing import Optional


# ============================================================
# USER CREATE / REGISTRATION
# ============================================================

class UserCreate(BaseModel):

    # Common fields
    role: str
    full_name: str
    email: str
    mobile: str
    date_of_birth: str
    password: str

    # --------------------------------------------------------
    # Patient fields
    # --------------------------------------------------------

    gender: Optional[str] = None

    # --------------------------------------------------------
    # Doctor fields
    # --------------------------------------------------------

    specialization: Optional[str] = None
    license_number: Optional[str] = None
    hospital: Optional[str] = None

    # --------------------------------------------------------
    # CHW fields
    # --------------------------------------------------------

    employee_id: Optional[str] = None
    organization: Optional[str] = None
    region: Optional[str] = None


# ============================================================
# USER RESPONSE
# ============================================================

class UserResponse(BaseModel):

    # User ID
    user_id: str

    # Common user information
    role: str
    full_name: str
    email: str
    mobile: str
    date_of_birth: str

    # --------------------------------------------------------
    # Patient
    # --------------------------------------------------------

    gender: Optional[str] = None
    patient_id: Optional[str] = None

    # --------------------------------------------------------
    # Doctor
    # --------------------------------------------------------

    specialization: Optional[str] = None
    license_number: Optional[str] = None
    hospital: Optional[str] = None

    # --------------------------------------------------------
    # CHW
    # --------------------------------------------------------

    employee_id: Optional[str] = None
    organization: Optional[str] = None
    region: Optional[str] = None


# ============================================================
# USER LOGIN
# ============================================================

class UserLogin(BaseModel):

    email: str
    password: str
    role: str