from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import User, Patient
from .schemas import UserCreate, UserResponse, UserLogin


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="MedPath API"
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "MedPath backend is running"
    }


# ============================================================
# CONVERT USER DATABASE OBJECT TO RESPONSE
# ============================================================

def user_to_response(user, patient_id=None):

    return {
        "user_id": str(user.id),

        "role": user.role,

        "full_name": user.full_name,

        "email": user.email,

        "mobile": user.mobile,

        "date_of_birth": user.date_of_birth,

        "gender": user.gender,

        "patient_id": patient_id,

        "specialization": user.specialization,

        "license_number": user.license_number,

        "hospital": user.hospital,

        "employee_id": user.employee_id,

        "organization": user.organization,

        "region": user.region
    }


# ============================================================
# REGISTER USER
# ============================================================

@app.post(
    "/register",
    response_model=UserResponse
)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Clean input
    # --------------------------------------------------------

    email = user.email.strip().lower()
    role = user.role.strip().lower()

    # --------------------------------------------------------
    # Validate role
    # --------------------------------------------------------

    if role not in ["patient", "doctor", "chw"]:

        raise HTTPException(
            status_code=400,
            detail="Invalid role. Choose Patient, Doctor, or CHW."
        )

    # --------------------------------------------------------
    # Check whether email already exists
    # --------------------------------------------------------

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # --------------------------------------------------------
    # Create User
    # --------------------------------------------------------

    new_user = User(

        role=role,

        full_name=user.full_name.strip(),

        email=email,

        mobile=user.mobile.strip(),

        date_of_birth=user.date_of_birth,

        gender=user.gender,

        password=user.password,

        # Doctor fields
        specialization=user.specialization,

        license_number=user.license_number,

        hospital=user.hospital,

        # CHW fields
        employee_id=user.employee_id,

        organization=user.organization,

        region=user.region
    )

    # --------------------------------------------------------
    # Save User
    # --------------------------------------------------------

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # --------------------------------------------------------
    # Patient ID
    # --------------------------------------------------------

    patient_id = None

    if role == "patient":

        patient_id = f"MP{new_user.id:05d}"

        new_patient = Patient(

            patient_id=patient_id,

            linked_user_id=new_user.id,

            name=user.full_name.strip(),

            date_of_birth=user.date_of_birth,

            gender=user.gender,

            phone=user.mobile.strip()
        )

        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)

    # --------------------------------------------------------
    # Return registered user
    # --------------------------------------------------------

    return user_to_response(
        new_user,
        patient_id
    )


# ============================================================
# LOGIN USER
# ============================================================

@app.post(
    "/login",
    response_model=UserResponse
)
def login_user(
    user: UserLogin,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Clean input
    # --------------------------------------------------------

    email = user.email.strip().lower()
    role = user.role.strip().lower()

    # --------------------------------------------------------
    # Find user by email
    # --------------------------------------------------------

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    # --------------------------------------------------------
    # User not found
    # --------------------------------------------------------

    if not existing_user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # --------------------------------------------------------
    # Check password
    # --------------------------------------------------------

    if existing_user.password != user.password:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # --------------------------------------------------------
    # Check role
    # --------------------------------------------------------

    if existing_user.role.strip().lower() != role:

        raise HTTPException(
            status_code=401,
            detail="Incorrect role selected"
        )

    # --------------------------------------------------------
    # Get Patient ID
    # --------------------------------------------------------

    patient_id = None

    if existing_user.role.strip().lower() == "patient":

        patient = (
            db.query(Patient)
            .filter(
                Patient.linked_user_id == existing_user.id
            )
            .first()
        )

        if patient:

            patient_id = patient.patient_id

    # --------------------------------------------------------
    # Return logged-in user
    # --------------------------------------------------------

    return user_to_response(
        existing_user,
        patient_id
    )


# ============================================================
# CURRENT USER
# ============================================================

@app.get(
    "/me",
    response_model=UserResponse
)
def get_current_user(
    user_id: int,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Find user
    # --------------------------------------------------------

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # --------------------------------------------------------
    # Get Patient ID
    # --------------------------------------------------------

    patient_id = None

    if user.role.strip().lower() == "patient":

        patient = (
            db.query(Patient)
            .filter(
                Patient.linked_user_id == user.id
            )
            .first()
        )

        if patient:

            patient_id = patient.patient_id

    # --------------------------------------------------------
    # Return current user
    # --------------------------------------------------------

    return user_to_response(
        user,
        patient_id
    )