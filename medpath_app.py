"""
MedPath - Healthcare Coordination Platform

Streamlit frontend.

Run:
    streamlit run medpath_app.py

Authentication:
    Streamlit -> api_client.py -> FastAPI -> SQLite

The medical-record prototype data is currently stored locally in:
    data/patients.json

Authentication/user data is NOT read from users.json.
"""

from fastapi import requests
import streamlit as st
import json
import os
import uuid
from datetime import datetime, date
import requests as http_requests
from api_client import (
    register_user,
    login_user,
    get_current_user,
)


# ==============================================================
# CONFIG
# ==============================================================

APP_NAME = "MedPath"
APP_ICON = "🩺"
TAGLINE = "Connecting every step of the healthcare journey."

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

PATIENTS_FILE = os.path.join(DATA_DIR, "patients.json")
#medical document storage 

UPLOADS_DIR = os.path.join(DATA_DIR, "uploads") 
ROLES = ["Patient", "Doctor", "CHW"]

TIMELINE_EVENT_TYPES = [
    "Consultation",
    "Symptom",
    "Diagnosis",
    "Laboratory Test",
    "Prescription",
    "Hospital Visit",
    "Follow-up",
    "Medical Document",
]


st.set_page_config(
    page_title=f"{APP_NAME} - Healthcare Coordination",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==============================================================
# LOCAL PATIENT DATA HELPERS
# ==============================================================

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)

def load_db(path):
    ensure_data_dir()

    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, dict) else {}

    except (json.JSONDecodeError, FileNotFoundError, OSError):
        return {}


def save_db(path, data):
    ensure_data_dir()

    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
            default=str,
        )


def new_id(prefix):
    return f"{prefix}{uuid.uuid4().hex[:8].upper()}"


def create_empty_patient_record(
    patient_id,
    name,
    linked_user_id=None,
    date_of_birth=None,
    gender=None,
    phone=None,
):
    return {
        "patient_id": patient_id,
        "linked_user_id": linked_user_id,
        "name": name,
        "date_of_birth": date_of_birth,
        "age": None,
        "gender": gender,
        "bloodGroup": None,
        "phone": phone,
        "symptoms": [],
        "labs": [],
        "medications": [],
        "documents": [],
        "timeline": [],
        "appointments": [],
        "additional": {},
        "createdAt": datetime.now().isoformat(),
    }


def ensure_patient_record(user):
    """
    Make sure the local prototype patient record exists.

    Authentication comes from FastAPI/SQLite.
    The medical-record prototype currently uses patients.json.
    """

    if not user:
        return None

    patient_id = user.get("patient_id")

    if not patient_id:
        return None

    patients = load_db(PATIENTS_FILE)

    if patient_id not in patients:
        patients[patient_id] = create_empty_patient_record(
            patient_id=patient_id,
            name=user.get("full_name", "Patient"),
            linked_user_id=user.get("user_id"),
            date_of_birth=user.get("date_of_birth"),
            gender=user.get("gender"),
            phone=user.get("mobile"),
        )

        save_db(PATIENTS_FILE, patients)

    return patients[patient_id]


def get_patient_record(patient_id):
    if not patient_id:
        return None, {}

    patients = load_db(PATIENTS_FILE)

    patient = patients.get(patient_id)

    return patient, patients


def save_patient_record(patient_id, record, patients=None):
    if not patient_id:
        return

    if patients is None:
        patients = load_db(PATIENTS_FILE)

    patients[patient_id] = record

    save_db(PATIENTS_FILE, patients)


# ==============================================================
# CSS / DESIGN
# ==============================================================

def inject_css():
    st.markdown(
        """
        <style>

        :root {
            --mp-blue: #1565C0;
            --mp-blue-light: #E3F2FD;
            --mp-blue-dark: #0D47A1;
            --mp-grey: #607D8B;
        }

        .mp-logo {
            font-size: 1.9rem;
            font-weight: 800;
            color: var(--mp-blue-dark);
        }

        .mp-tagline {
            color: var(--mp-grey);
            font-size: 0.95rem;
            margin-top: -8px;
        }

        .mp-card {
            background: #ffffff;
            border: 1px solid #E0E6ED;
            border-radius: 14px;
            padding: 1.1rem 1.3rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(20,40,80,0.06);
        }

        .mp-card h4 {
            margin-top: 0;
            color: var(--mp-blue-dark);
        }

        .mp-empty {
            color: var(--mp-grey);
            font-style: italic;
            padding: 0.6rem 0;
        }

        .mp-badge-high {
            background: #FFEBEE;
            color: #C62828;
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
        }

        .mp-badge-medium {
            background: #FFF8E1;
            color: #F9A825;
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
        }

        .mp-badge-low {
            background: #E8F5E9;
            color: #2E7D32;
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
        }

        .mp-alert {
            background: #FFF3E0;
            border-left: 4px solid #FB8C00;
            padding: 0.7rem 1rem;
            border-radius: 8px;
            margin-bottom: 0.6rem;
        }

        .mp-metric {
            background: var(--mp-blue-light);
            border-radius: 12px;
            padding: 0.9rem 1rem;
            text-align: center;
        }

        .mp-disclaimer {
            font-size: 0.78rem;
            color: var(--mp-grey);
            margin-top: 0.4rem;
        }

        .stButton > button {
            border-radius: 10px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_logo(subtitle=None):
    st.markdown(
        f'<div class="mp-logo">{APP_ICON} {APP_NAME}</div>',
        unsafe_allow_html=True,
    )

    if subtitle:
        st.markdown(
            f'<div class="mp-tagline">{subtitle}</div>',
            unsafe_allow_html=True,
        )


def empty_state(text):
    st.markdown(
        f'<div class="mp-empty">{text}</div>',
        unsafe_allow_html=True,
    )


# ==============================================================
# SESSION STATE
# ==============================================================

def init_session_state():

    defaults = {
        "auth": False,
        "user_id": None,
        "user": None,
        "role": None,
        "page": "login",
        "selected_patient_id": None,
        "analyzed": {},
        "chatbot_history": {},
        "symptom_name":"",
        "medication_name":"",
        "medication_dosage":"",
        "medication_frequency":"",
        "appointment_reason":"",
        "timeline_description":""
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# ==============================================================
# CURRENT USER
# ==============================================================

def current_user():

    user_id = st.session_state.get("user_id")

    if not user_id:
        return None

    try:

        response = get_current_user(user_id)

        if response.status_code == 200:

            user = response.json()
        

            if not isinstance(user, dict):
                return None

            # Keep session user synchronized.
            st.session_state.user = user

            # Safely update role.
            role = user.get("role")

            if role:
                st.session_state.role = str(role).capitalize()

            return user

        return None

    except Exception as error:

        st.error(
            f"Unable to connect to the MedPath backend: {error}"
        )

        return None


# ==============================================================
# LOGOUT
# ==============================================================

def logout():

    st.session_state.auth = False
    st.session_state.user_id = None
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.page = "login"
    st.session_state.selected_patient_id = None


# ==============================================================
# AUTHENTICATION
# ==============================================================

def login_page():

    col1, col2, col3 = st.columns([1, 1.3, 1])

    with col2:

        st.write("")
        st.write("")

        render_logo(TAGLINE)

        st.write("")

        tabs = st.tabs(
            [
                "Sign In",
                "Register",
            ]
        )

        # ==========================================================
        # SIGN IN
        # ==========================================================

        with tabs[0]:

            st.markdown("##### I am a")

            role = st.radio(
                "Role",
                ROLES,
                horizontal=True,
                label_visibility="collapsed",
                key="login_role",
            )

            email = st.text_input(
                "Email",
                key="login_email",
                placeholder="Enter your registered email",
            )

            password = st.text_input(
                "Password",
                type="password",
                key="login_password",
                placeholder="Enter your password",
            )

            if st.button(
                "Sign In",
                use_container_width=True,
                type="primary",
            ):

                email = email.strip()

                if not email or not password:

                    st.warning(
                        "Please enter both email and password."
                    )

                    return

                login_data = {
                    "email": email,
                    "password": password,
                    "role": role.lower(),
                }

                try:

                    response = login_user(login_data)

                except Exception as error:

                    st.error(
                        f"Unable to connect to the MedPath backend: {error}"
                    )

                    return

                if response.status_code == 200:

                    try:
                        user = response.json()
                    except Exception:
                        st.error(
                            "The server returned an invalid login response."
                        )
                        return

                    if not isinstance(user, dict):

                        st.error(
                            "The server returned invalid user information."
                        )

                        return

                    user_id = user.get("user_id")
                    returned_role = user.get("role")

                    if not user_id:

                        st.error(
                            "Login succeeded, but the server did not return user_id."
                        )

                        st.json(user)

                        return

                    if not returned_role:

                        st.error(
                            "Login succeeded, but the server did not return role."
                        )

                        st.json(user)

                        return

                    # Store authentication state.
                    st.session_state.auth = True
                    st.session_state.user_id = user_id
                    st.session_state.user = user
                    st.session_state.role = user["role"].strip().upper()

                    if st.session_state.role == "patient":
                        st.session_state.role = "Patient"
                    elif st.session_state.role == "doctor":
                        st.session_state.role = "Doctor"
                    elif st.session_state.role == "chw":
                        st.session_state.role = "CHW"

                    st.session_state.page = "dashboard"

                    # If patient, make sure local prototype record exists.
                    if str(returned_role).lower() == "patient":

                        ensure_patient_record(user)

                    st.success("Login successful!")

                    st.rerun()

                else:

                    try:

                        data = response.json()

                        detail = data.get(
                            "detail",
                            "Login failed.",
                        )

                    except Exception:

                        detail = (
                            f"Login failed "
                            f"(HTTP {response.status_code})."
                        )

                    st.error(detail)

            st.write("")

            c1, c2 = st.columns(2)

            with c1:
                st.caption("Forgot Password?")

            with c2:
                st.caption(
                    "Don't have an account? Use the Register tab →"
                )

        # ==========================================================
        # REGISTER
        # ==========================================================

        with tabs[1]:

            register_form()


# ==============================================================
# REGISTRATION
# ==============================================================

def register_form():

    st.markdown("##### Create an account as")

    role = st.radio(
        "Register role",
        ROLES,
        horizontal=True,
        label_visibility="collapsed",
        key="reg_role",
    )

    with st.form(
        "register_form",
        clear_on_submit=False,
    ):

        full_name = st.text_input(
            "Full Name",
            placeholder="Enter your full name",
        )

        email = st.text_input(
            "Email",
            placeholder="Enter your email",
        )

        mobile = st.text_input(
            "Mobile Number",
            placeholder="Enter your mobile number",
        )

        dob = st.date_input(
            "Date of Birth",
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )

        extra = {}

        # ----------------------------------------------------------
        # PATIENT
        # ----------------------------------------------------------

        if role == "Patient":

            extra["gender"] = st.selectbox(
                "Gender",
                [
                    "Female",
                    "Male",
                    "Other",
                    "Prefer not to say",
                ],
            )

            extra["profilePhoto"] = st.file_uploader(
                "Profile Photo (optional)",
                type=[
                    "png",
                    "jpg",
                    "jpeg",
                ],
            )

        # ----------------------------------------------------------
        # DOCTOR
        # ----------------------------------------------------------

        elif role == "Doctor":

            extra["specialization"] = st.text_input(
                "Medical Specialization"
            )

            extra["licenseNumber"] = st.text_input(
                "Medical Registration / License Number"
            )

            extra["hospital"] = st.text_input(
                "Hospital / Clinic"
            )

        # ----------------------------------------------------------
        # CHW
        # ----------------------------------------------------------

        elif role == "CHW":

            extra["employeeId"] = st.text_input(
                "CHW / Employee ID"
            )

            extra["organization"] = st.text_input(
                "Organization / Health Center"
            )

            extra["region"] = st.text_input(
                "Area / Region"
            )

        password = st.text_input(
            "Password",
            type="password",
        )

        confirm = st.text_input(
            "Confirm Password",
            type="password",
        )

        submitted = st.form_submit_button(
            f"Create {role} Account",
            use_container_width=True,
            type="primary",
        )

    if not submitted:
        return

    # ==========================================================
    # VALIDATION
    # ==========================================================

    full_name = full_name.strip()
    email = email.strip()
    mobile = mobile.strip()

    if not full_name:

        st.warning("Please enter your full name.")
        return

    if not email:

        st.warning("Please enter your email.")
        return

    if not mobile:

        st.warning("Please enter your mobile number.")
        return

    if not password:

        st.warning("Please enter a password.")
        return

    if password != confirm:

        st.error("Passwords do not match.")
        return

    # ==========================================================
    # API DATA
    # ==========================================================

    user_data = {
        "role": role.lower(),
        "full_name": full_name,
        "email": email,
        "mobile": mobile,
        "date_of_birth": str(dob),
        "password": password,
        "gender": extra.get("gender"),
        "specialization": extra.get("specialization"),
        "license_number": extra.get("licenseNumber"),
        "hospital": extra.get("hospital"),
        "employee_id": extra.get("employeeId"),
        "organization": extra.get("organization"),
        "region": extra.get("region"),
    }

    # ==========================================================
    # REGISTER THROUGH FASTAPI
    # ==========================================================

    try:

        response = register_user(user_data)

    except Exception as error:

        st.error(
            f"Unable to connect to the MedPath backend: {error}"
        )

        return

    # FastAPI may return 200 or 201.
    if response.status_code in (200, 201):

        try:

            user = response.json()

        except Exception:

            st.error(
                "Registration succeeded, but the server returned invalid user data."
            )

            return

        if not isinstance(user, dict):

            st.error(
                "Registration succeeded, but the server returned invalid user information."
            )

            return

        user_id = user.get("user_id")
        returned_role = user.get("role")

        if not user_id:

            st.error(
                "Registration succeeded, but the server did not return user_id."
            )

            st.json(user)

            return

        if not returned_role:

            st.error(
                "Registration succeeded, but the server did not return role."
            )

            st.json(user)

            return

        # ======================================================
        # STORE SESSION
        # ======================================================

        st.session_state.auth = True
        st.session_state.user_id = user_id
        st.session_state.user = user
        st.session_state.role = user["role"].strip().lower()

        if st.session_state.role == "patient":
            st.session_state.role = "Patient"
        elif st.session_state.role == "doctor":
            st.session_state.role = "Doctor"
        elif st.session_state.role == "chw":
            st.session_state.role = "CHW"

        st.session_state.page = "dashboard"

        # ======================================================
        # PATIENT RECORD
        # ======================================================

        if str(returned_role).lower() == "patient":

            patient_id = user.get("patient_id")

            if patient_id:

                ensure_patient_record(user)

            else:

                st.warning(
                    "Account created successfully, but the backend "
                    "did not return a patient_id. Please check backend/main.py."
                )

        st.success(
            f"{role} account created successfully!"
        )

        st.rerun()

    else:

        try:

            data = response.json()

            detail = data.get(
                "detail",
                "Registration failed.",
            )

        except Exception:

            detail = (
                f"Registration failed "
                f"(HTTP {response.status_code})."
            )

        st.error(detail)


# ==============================================================
# PATIENT HEADER
# ==============================================================

def patient_header(user):

    st.markdown(
        f'<div class="mp-logo">{APP_ICON} {APP_NAME}</div>',
        unsafe_allow_html=True,
    )

    full_name = user.get(
        "full_name",
        "Patient",
    )

    st.markdown(
        f"### Welcome, {full_name}"
    )


# ==============================================================
# PATIENT DASHBOARD
# ==============================================================

def patient_dashboard_page(user):

    patient_header(user)

    patient_id = user.get("patient_id")

    if not patient_id:

        st.warning(
            "Your account is registered, but a Patient ID has not been assigned."
        )

        st.info(
            "The backend should create a Patient ID such as MP00001 "
            "when a Patient account is registered."
        )

        st.write("Current account information:")
        st.json(user)

        return

    patient, patients = get_patient_record(patient_id)

    if patient is None:

        patient = create_empty_patient_record(
            patient_id=patient_id,
            name=user.get("full_name", "Patient"),
            linked_user_id=user.get("user_id"),
            date_of_birth=user.get("date_of_birth"),
            gender=user.get("gender"),
            phone=user.get("mobile"),
        )

        patients[patient_id] = patient

        save_db(
            PATIENTS_FILE,
            patients,
        )

    # Safety defaults.
    patient.setdefault("symptoms", [])
    patient.setdefault("labs", [])
    patient.setdefault("documents", [])
    patient.setdefault("timeline", [])
    patient.setdefault("medications", [])
    patient.setdefault("appointments", [])

    has_any_data = bool(
        patient["symptoms"]
        or patient["labs"]
        or patient["documents"]
        or patient["timeline"]
        or patient["medications"]
    )

    if not has_any_data:

        st.markdown(
            '<div class="mp-card">',
            unsafe_allow_html=True,
        )

        st.markdown(
            "#### Your healthcare journey starts here"
        )

        st.write(
            "Add your medical information or upload your "
            "first medical document to begin building your health record."
        )

        c1, c2 = st.columns(2)

        with c1:

            if st.button(
                "Add Medical Information",
                type="primary",
            ):

                st.session_state.page = "My Profile"
                st.rerun()

        with c2:

            if st.button("Upload Document"):

                st.session_state.page = "Documents"
                st.rerun()

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    # ----------------------------------------------------------
    # METRICS
    # ----------------------------------------------------------

    cols = st.columns(4)

    metric_data = [
        (
            "My Health Journey",
            len(patient["timeline"]),
        ),
        (
            "Timeline",
            len(patient["timeline"]),
        ),
        (
            "Medical Documents",
            len(patient["documents"]),
        ),
        (
            "Symptoms",
            len(patient["symptoms"]),
        ),
    ]

    for column, (label, count) in zip(
        cols,
        metric_data,
    ):

        with column:

            st.markdown(
                f"""
                <div class="mp-metric">
                    <h3>{count}</h3>
                    {label}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    # ----------------------------------------------------------
    # RECENT TIMELINE
    # ----------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            '<div class="mp-card"><h4>Recent Timeline</h4>',
            unsafe_allow_html=True,
        )

        if patient["timeline"]:

            events = sorted(
                patient["timeline"],
                key=lambda x: x.get("date", ""),
                reverse=True,
            )

            for event in events[:5]:

                st.write(
                    f"**{event.get('date', '')}** — "
                    f"{event.get('type', '')}: "
                    f"{event.get('description', '')}"
                )

        else:

            empty_state(
                "No medical events yet"
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    # ----------------------------------------------------------
    # MEDICATIONS
    # ----------------------------------------------------------

    with col2:

        st.markdown(
            '<div class="mp-card"><h4>Medications</h4>',
            unsafe_allow_html=True,
        )

        if patient["medications"]:

            for medication in patient["medications"]:

                st.write(
                    f"- {medication.get('name', '')} "
                    f"({medication.get('dosage', '')}, "
                    f"{medication.get('frequency', '')})"
                )

        else:

            empty_state(
                "No medications on record."
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


# ==============================================================
# PATIENT PROFILE
# ==============================================================

def patient_profile_page(user):

    patient_header(user)

    patient_id = user.get("patient_id")

    if not patient_id:

        st.error(
            "Patient ID is missing from your account."
        )

        return

    patient, patients = get_patient_record(patient_id)

    if patient is None:

        patient = create_empty_patient_record(
            patient_id,
            user.get("full_name", "Patient"),
            user.get("user_id"),
            user.get("date_of_birth"),
            user.get("gender"),
            user.get("mobile"),
        )

        patients[patient_id] = patient

        save_db(
            PATIENTS_FILE,
            patients,
        )

    st.markdown(
        '<div class="mp-card"><h4>Account Information</h4>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)

    c1.write(
        f"**Full Name**\n\n"
        f"{user.get('full_name', '-')}"
    )

    c1.write(
        f"**Email**\n\n"
        f"{user.get('email', '-')}"
    )

    c2.write(
        f"**Mobile**\n\n"
        f"{user.get('mobile', '-')}"
    )

    c2.write(
        f"**Date of Birth**\n\n"
        f"{user.get('date_of_birth', '-')}"
    )

    c3.write(
        f"**Gender**\n\n"
        f"{user.get('gender', '-')}"
    )

    c3.write(
        f"**Patient ID**\n\n"
        f"{patient_id}"
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # ----------------------------------------------------------
    # ADDITIONAL HEALTH INFORMATION
    # ----------------------------------------------------------

    st.markdown(
        '<div class="mp-card"><h4>Additional Health Information</h4>',
        unsafe_allow_html=True,
    )

    additional = patient.get(
        "additional",
        {},
    )

    with st.form(
        "additional_info_form"
    ):

        c1, c2 = st.columns(2)

        blood_group = c1.text_input(
            "Blood Group",
            value=patient.get(
                "bloodGroup"
            ) or "",
        )

        height = c1.text_input(
            "Height",
            value=additional.get(
                "height",
                "",
            ),
        )

        weight = c1.text_input(
            "Weight",
            value=additional.get(
                "weight",
                "",
            ),
        )

        allergies = c2.text_input(
            "Allergies",
            value=additional.get(
                "allergies",
                "",
            ),
        )

        conditions = c2.text_input(
            "Existing Medical Conditions",
            value=additional.get(
                "conditions",
                "",
            ),
        )

        emergency_contact = st.text_input(
            "Emergency Contact",
            value=additional.get(
                "emergency_contact",
                "",
            ),
        )

        emergency_number = st.text_input(
            "Emergency Contact Number",
            value=additional.get(
                "emergency_number",
                "",
            ),
        )

        address = st.text_area(
            "Address",
            value=additional.get(
                "address",
                "",
            ),
        )

        preferred_hospital = st.text_input(
            "Preferred Hospital / Clinic",
            value=additional.get(
                "preferred_hospital",
                "",
            ),
        )

        save_clicked = st.form_submit_button(
            "Save Additional Information",
            type="primary",
        )

    if save_clicked:

        patient["bloodGroup"] = (
            blood_group or None
        )

        patient["additional"] = {
            "height": height,
            "weight": weight,
            "allergies": allergies,
            "conditions": conditions,
            "emergency_contact": emergency_contact,
            "emergency_number": emergency_number,
            "address": address,
            "preferred_hospital": preferred_hospital,
        }

        save_patient_record(
            patient_id,
            patient,
            patients,
        )

        st.success(
            "Additional information saved."
        )

        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )
def timeline_page(
    patient_id,
    editable=True,
):
    """
    Healthcare Timeline

    Supports:
    1. Manual events added by Patient / Doctor / CHW
    2. Future AI-generated events from the n8n workflow
    """

    if not patient_id:
        st.error("No patient selected.")
        return

    patient, patients = get_patient_record(patient_id)

    if patient is None:
        empty_state("Patient record not found.")
        return

    # ----------------------------------------------------------
    # Make sure timeline exists
    # ----------------------------------------------------------

    patient.setdefault("timeline", [])

    # ----------------------------------------------------------
    # PAGE HEADER
    # ----------------------------------------------------------

    st.markdown(
        '<div class="mp-card"><h4>Healthcare Timeline</h4>',
        unsafe_allow_html=True,
    )

    st.caption(
        "A chronological view of the patient's medical history, "
        "including manually recorded and AI-generated events."
    )

    # ==========================================================
    # ADD MANUAL EVENT
    # ==========================================================

    if editable:

        with st.expander("➕ Add Event"):

            with st.form(
                f"add_event_form_{patient_id}",
                clear_on_submit=True
            ):

                event_type = st.selectbox(
                    "Event Type",
                    TIMELINE_EVENT_TYPES,
                )

                event_date = st.date_input(
                    "Date",
                    value=date.today(),
                )

                description = st.text_area(
                    "Description",
                    placeholder="Enter event details",
                )

                submitted = st.form_submit_button(
                    "Add to Timeline",
                    type="primary",
                )

                if submitted:

                    if not description.strip():

                        st.warning(
                            "Please enter a description."
                        )

                    else:

                        # --------------------------------------------------
                        # Create manual timeline event
                        # --------------------------------------------------

                        new_event = {
                            "id": new_id("EVT"),

                            "type": event_type,

                            "date": str(event_date),

                            "description": description.strip(),

                            # Source helps distinguish manual vs AI events
                            "source": "manual",

                            "ai_generated": False,
                        }

                        patient["timeline"].append(
                            new_event
                        )

                        # --------------------------------------------------
                        # Save
                        # --------------------------------------------------

                        save_patient_record(
                            patient_id,
                            patient,
                            patients,
                        )

                        st.success(
                            "Event added to timeline."
                        )

                        st.rerun()

    # ==========================================================
    # TIMELINE DISPLAY
    # ==========================================================

    if patient["timeline"]:

        events = sorted(
            patient["timeline"],
            key=lambda x: x.get("date", ""),
            reverse=True,
        )

        st.markdown(
            "### Medical History"
        )

        for event in events:

            event_type = event.get(
                "type",
                "Medical Event",
            )

            event_date = event.get(
                "date",
                "",
            )

            description = event.get(
                "description",
                "",
            )

            source = event.get(
                "source",
                "manual",
            )

            # --------------------------------------------------
            # Identify AI-generated events
            # --------------------------------------------------

            if (
                source == "ai"
                or event.get("ai_generated") is True
            ):

                icon = "🤖"
                source_label = "AI-generated"

            elif event_type == "Medical Document":

                icon = "📄"
                source_label = "Document"

            elif event_type == "Symptom":

                icon = "🩺"
                source_label = "Symptom"

            elif event_type == "Medication":

                icon = "💊"
                source_label = "Medication"

            elif event_type == "Laboratory Test":

                icon = "🧪"
                source_label = "Laboratory"

            elif event_type == "Appointment":

                icon = "📅"
                source_label = "Appointment"

            else:

                icon = "📌"
                source_label = "Manual"

            # --------------------------------------------------
            # Event display
            # --------------------------------------------------

            st.markdown(
                f"**{event_date}**  \n"
                f"{icon} **{event_type}**"
            )

            st.caption(
                description
            )

            st.caption(
                f"Source: {source_label}"
            )

            st.markdown("---")

    else:

        empty_state(
            "No medical events yet."
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )
    
def documents_page(patient_id, editable=True):

    # Defensively ensure a patient identifier exists before using it.
    # This avoids NameError when the page is reached without an explicit
    # patient_id argument but the selected patient is available in session state.
    if "patient_id" not in locals():
        patient_id = st.session_state.get("selected_patient_id")

    if not patient_id:
        patient_id = st.session_state.get("selected_patient_id")

    patient, patients = get_patient_record(patient_id)

    if patient is None:
        st.error("Patient record not found.")
        return

    # ----------------------------------------------------------
    # Make sure required lists exist
    # ----------------------------------------------------------

    patient.setdefault("documents", [])
    patient.setdefault("timeline", [])

    # ==========================================================
    # PAGE HEADER
    # ==========================================================

    st.markdown(
        f'<div class="mp-logo">{APP_ICON} {APP_NAME}</div>',
        unsafe_allow_html=True
    )

    st.markdown("### Medical Documents")

    st.caption(
        "Upload and organize your healthcare documents. "
        "Documents will later be processed through the MedPath AI workflow."
    )

    # ==========================================================
    # UPLOAD DOCUMENT
    # ==========================================================

    st.markdown(
        '<div class="mp-card"><h4>📤 Upload Medical Document</h4>',
        unsafe_allow_html=True
    )

    if editable:

        uploaded = st.file_uploader(
            "Choose a medical document",
            type=[
                "pdf",
                "jpg",
                "jpeg",
                "png",
                "doc",
                "docx"
            ],
            help=(
                "Supported formats: PDF, JPG, JPEG, PNG, DOC and DOCX."
            ),
            key=f"medical_document_upload_{patient_id}"
        )

        if uploaded is not None:

            st.write(
                f"**Selected file:** {uploaded.name}"
            )

            file_size_kb = round(
                len(uploaded.getvalue()) / 1024,
                1
            )

            st.caption(
                f"{uploaded.type or 'Unknown file type'} "
                f"• {file_size_kb} KB"
            )

            if st.button(
                "📤 Upload Document",
                type="primary",
                use_container_width=True,
                key=f"confirm_document_upload_{patient_id}"
            ):

                # --------------------------------------------------
                # Check duplicate
                # --------------------------------------------------

                duplicate = any(
                    d.get("name") == uploaded.name
                    for d in patient["documents"]
                )

                if duplicate:

                    st.warning(
                        "A document with this name is already "
                        "present in this patient's record."
                    )

                else:

                    # --------------------------------------------------
                    # Create document record
                    # --------------------------------------------------

                    document_id = new_id("DOC")

                    # --------------------------------------------------
                    # Save uploaded file locally
                    # --------------------------------------------------

                    patient_upload_dir = os.path.join(
                        UPLOADS_DIR,
                        str(patient_id)
                    )

                    os.makedirs(
                        patient_upload_dir,
                        exist_ok=True
                    )

                    # Prevent unsafe filenames
                    safe_filename = os.path.basename(
                        uploaded.name
                    )

                    file_path = os.path.join(
                        patient_upload_dir,
                        safe_filename
                    )

                    with open(file_path, "wb") as f:
                        f.write(uploaded.getbuffer())

                    # Store relative path for future reference
                    relative_file_path = os.path.relpath(
                        file_path,
                        BASE_DIR
                    )
                    file_size_kb = round(
                        os.path.getsize(file_path) / 1024,
                        1
                    )

                    # --------------------------------------------------
                    # Send PDF to MedPath n8n workflow
                    # --------------------------------------------------

                    N8N_WEBHOOK_URL = (
                        "https://kavyaas.app.n8n.cloud/webhook-test/medpath/patient-review"
                    )

                    # --------------------------------------------------
                    # Send PDF to n8n and receive analysis
                    # --------------------------------------------------

                    n8n_result = None

                    try:

                        with open(file_path, "rb") as pdf_file:

                            response = http_requests.post(
                                N8N_WEBHOOK_URL,
                                files={
                                    "patient_record": (
                                        safe_filename,
                                        pdf_file,
                                        uploaded.type or "application/pdf"
                                    )
                                },
                                timeout=120
                            )

                        st.write(
                            "n8n HTTP Status:",
                            response.status_code
                        )

                        if response.ok:

                            st.success(
                                "✅ PDF successfully processed by n8n."
                            )

                            try:
                                n8n_result = response.json()

                            except ValueError:

                                st.error(
                                    "❌ n8n returned a response that is not valid JSON."
                                )

                                st.write(
                                    "n8n Response:",
                                    response.text
                                )

                        else:

                            st.error(
                                f"❌ n8n returned HTTP {response.status_code}"
                            )

                            st.write(
                                "n8n Response:",
                                response.text
                            )

                    except Exception as e:

                        st.error(
                            f"❌ Could not connect to n8n: "
                            f"{type(e).__name__}: {e}"
                        )

                    # --------------------------------------------------
                    # Create document record
                    # --------------------------------------------------

                    document = {
                        "id": document_id,
                        "name": uploaded.name,
                        "type": uploaded.type or "unknown",
                        "size_kb": file_size_kb,
                        "uploadedAt": datetime.now().isoformat(),

                        # Local file
                        "file_path": relative_file_path,

                        # Upload status
                        "status": "Uploaded",

                        # n8n workflow status
                        "processing_status": (
                            "Completed"
                            if n8n_result
                            else "Waiting for workflow"
                        ),

                        "analysis_status": (
                            "Completed"
                            if n8n_result
                            else "Not analyzed"
                        ),

                        "n8n_status": (
                            "Connected"
                            if n8n_result
                            else "Not connected"
                        ),

                        # --------------------------------------------------
                        # AI results returned by n8n
                        # --------------------------------------------------

                        "analysis": (
                            n8n_result.get("text")
                            if isinstance(n8n_result, dict)
                            else None
                        ),

                        "analysis_html": (
                            n8n_result.get("html")
                            if isinstance(n8n_result, dict)
                            else None
                        ),

                        "insights": [],

                        "timeline_events": [],

                        "missing_information": [],

                        # n8n workflow information
                        "workflow_id": None,

                        "processedAt": (
                            datetime.now().isoformat()
                            if n8n_result
                            else None
                        )
                    }

                    # --------------------------------------------------
                    # Save document
                    # --------------------------------------------------

                    patient["documents"].append(
                        document
                    )

                    # --------------------------------------------------
                    # Add document to timeline
                    # --------------------------------------------------

                    patient["timeline"].append({
                        "id": new_id("EVT"),
                        "type": "Medical Document",
                        "date": str(date.today()),
                        "description": (
                            f"Uploaded medical document: "
                            f"{uploaded.name}"
                        )
                    })

                    # --------------------------------------------------
                    # Save patient record
                    # --------------------------------------------------

                    save_patient_record(
                        patient_id,
                        patient,
                        patients
                    )

                    st.success(
                        "Medical document uploaded successfully."
                    )

                    st.info(
                        "The document is now waiting for the "
                        "MedPath AI workflow."
                    )

                    st.rerun()

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    # ==========================================================
    # UPLOADED DOCUMENTS
    # ==========================================================

    st.markdown(
        '<div class="mp-card"><h4>📚 Uploaded Documents</h4>',
        unsafe_allow_html=True
    )

    documents = patient.get(
        "documents",
        []
    )

    if not documents:

        empty_state(
            "No medical documents uploaded yet."
        )

    else:

        st.caption(
            f"{len(documents)} document(s) in this patient's record."
        )

        # ------------------------------------------------------
        # Display newest document first
        # ------------------------------------------------------

        for index, document in enumerate(
            reversed(documents)
        ):

            name = document.get(
                "name",
                "Unnamed document"
            )

            status = document.get(
                "status",
                "Uploaded"
            )

            processing_status = document.get(
                "processing_status",
                "Waiting for workflow"
            )

            analysis_status = document.get(
                "analysis_status",
                "Not analyzed"
            )

            uploaded_at = document.get(
                "uploadedAt",
                "-"
            )

            file_type = document.get(
                "type",
                "Unknown"
            )

            size_kb = document.get(
                "size_kb",
                "-"
            )

            # --------------------------------------------------
            # Document title
            # --------------------------------------------------

            st.markdown(
                f"### 📄 {name}"
            )

            st.caption(
                f"{file_type} • {size_kb} KB"
            )

            # --------------------------------------------------
            # Status columns
            # --------------------------------------------------

            c1, c2, c3 = st.columns(3)

            with c1:

                st.write("**Upload Status**")

                if status == "Uploaded":

                    st.success(
                        "✅ Uploaded"
                    )

                else:

                    st.info(status)

            with c2:

                st.write("**Workflow Status**")

                if processing_status == "Waiting for workflow":

                    st.info(
                        "⏳ Waiting for AI workflow"
                    )

                elif processing_status == "Processing":

                    st.warning(
                        "⚙️ Processing"
                    )

                elif processing_status == "Completed":

                    st.success(
                        "✅ Completed"
                    )

                else:

                    st.info(
                        processing_status
                    )

            with c3:

                st.write("**Analysis**")

                if analysis_status == "Completed":

                    st.success(
                        "✅ Available"
                    )

                elif analysis_status == "Processing":

                    st.warning(
                        "⚙️ Processing"
                    )

                else:

                    st.info(
                        "⏳ Not analyzed"
                    )

            # --------------------------------------------------
            # Document details
            # --------------------------------------------------

            with st.expander(
                f"View details — {name}",
                expanded=False
            ):

                st.write(
                    f"**Document ID:** "
                    f"{document.get('id', '-')}"
                )

                st.write(
                    f"**File type:** "
                    f"{file_type}"
                )

                st.write(
                    f"**File size:** "
                    f"{size_kb} KB"
                )

                st.write(
                    f"**Uploaded:** "
                    f"{uploaded_at}"
                )

                st.write(
                    f"**Processing:** "
                    f"{processing_status}"
                )

                st.write(
                    f"**Analysis:** "
                    f"{analysis_status}"
                )

                st.markdown("---")

                st.write(
                    "**MedPath AI Workflow**"
                )

                st.write(
                    "1. ✅ Document uploaded"
                )

                st.write(
                    "2. ⏳ Document processing"
                )

                st.write(
                    "3. ⏳ Medical information structuring"
                )

                st.write(
                    "4. ⏳ Timeline generation"
                )

                st.write(
                    "5. ⏳ Analysis and insights"
                )

                st.write(
                    "6. ⏳ AI chatbot availability"
                )

                st.caption(
                    "These stages will be connected to "
                    "your n8n automation workflow."
                )

            # --------------------------------------------------
            # Separator
            # --------------------------------------------------

            if index < len(documents) - 1:

                st.markdown("---")

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    # ==========================================================
    # AI PROCESSING INFORMATION
    # ==========================================================

    st.markdown(
        '<div class="mp-card"><h4>🤖 AI Processing</h4>',
        unsafe_allow_html=True
    )

    st.write(
        "Once the MedPath workflow is connected, uploaded "
        "documents will be sent to the automation workflow."
    )

    st.write(
        "The workflow will organize the information, generate "
        "the patient's relevant timeline events, produce "
        "analysis and insights, and make the information "
        "available to the MedPath AI Assistant."
    )

    st.caption(
        "AI-generated information should be verified by "
        "a healthcare professional."
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )
def symptoms_medications_appointments_page(patient_id, editable=True):
    patient, patients = get_patient_record(patient_id)

    # Make sure required lists always exist
    patient.setdefault("symptoms", [])
    patient.setdefault("medications", [])
    patient.setdefault("appointments", [])
    patient.setdefault("timeline", [])

    # ==========================================================
    # SYMPTOMS
    # ==========================================================

    st.markdown(
        '<div class="mp-card"><h4>Symptoms</h4>',
        unsafe_allow_html=True
    )

    if editable:

        with st.form("add_symptom_form", clear_on_submit=True):

            c1, c2, c3 = st.columns(3)

            name = c1.text_input(
                "Symptom",
                placeholder="Enter symptom"
            )

            severity = c2.selectbox(
                "Severity",
                ["Mild", "Moderate", "Severe"]
            )

            onset = c3.date_input(
                "Onset / Reported Date",
                value=date.today()
            )

            submitted = st.form_submit_button(
                "Add Symptom",
                type="primary"
            )

            if submitted:

                if not name.strip():
                    st.warning("Please enter a symptom.")
                else:

                    patient["symptoms"].append({
                        "id": new_id("SYM"),
                        "name": name.strip(),
                        "severity": severity,
                        "onset": str(onset)
                    })

                    patient["timeline"].append({
                        "id": new_id("EVT"),
                        "type": "Symptom",
                        "date": str(onset),
                        "description": f"{name.strip()} ({severity})"
                    })

                    save_patient_record(
                        patient_id,
                        patient,
                        patients
                    )

                    st.success("Symptom added successfully.")

                    st.rerun()

    if patient["symptoms"]:

        for s in patient["symptoms"]:

            st.write(
                f"- {s.get('name', '-')}"
                f" — {s.get('severity', '-')}"
                f" (since {s.get('onset', '-')})"
            )

    else:

        empty_state(
            "No symptoms recorded yet."
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # ==========================================================
    # MEDICATIONS
    # ==========================================================

    st.markdown(
        '<div class="mp-card"><h4>Medications</h4>',
        unsafe_allow_html=True
    )

    if editable:

        with st.form(
            "add_medication_form",
            clear_on_submit=True
        ):

            c1, c2, c3 = st.columns(3)

            mname = c1.text_input(
                "Medicine Name",
                placeholder="Enter medicine name"
            )

            dosage = c2.text_input(
                "Dosage",
                placeholder="Example: 500 mg"
            )

            frequency = c3.text_input(
                "Frequency",
                placeholder="Example: Twice daily"
            )

            submitted = st.form_submit_button(
                "Add Medication",
                type="primary"
            )

            if submitted:

                if not mname.strip():

                    st.warning(
                        "Please enter a medicine name."
                    )

                else:

                    patient["medications"].append({
                        "id": new_id("MED"),
                        "name": mname.strip(),
                        "dosage": dosage.strip(),
                        "frequency": frequency.strip(),
                        "status": "Active"
                    })

                    save_patient_record(
                        patient_id,
                        patient,
                        patients
                    )

                    st.success(
                        "Medication added successfully."
                    )

                    st.rerun()

    if patient["medications"]:

        for m in patient["medications"]:

            st.write(
                f"- {m.get('name', '-')}"
                f" — {m.get('dosage', '-')}, "
                f"{m.get('frequency', '-')}"
                f" ({m.get('status', 'Active')})"
            )

    else:

        empty_state(
            "No medications on record."
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # ==========================================================
    # APPOINTMENTS
    # ==========================================================

    st.markdown(
        '<div class="mp-card"><h4>Appointments</h4>',
        unsafe_allow_html=True
    )

    if editable:

        with st.form(
            "add_appt_form",
            clear_on_submit=True
        ):

            c1, c2 = st.columns(2)

            adate = c1.date_input(
                "Appointment Date",
                value=date.today()
            )

            reason = c2.text_input(
                "Reason",
                placeholder="Example: Follow-up consultation"
            )

            submitted = st.form_submit_button(
                "Add Appointment",
                type="primary"
            )

            if submitted:

                if not reason.strip():

                    st.warning(
                        "Please enter the appointment reason."
                    )

                else:

                    patient["appointments"].append({
                        "id": new_id("APT"),
                        "date": str(adate),
                        "reason": reason.strip(),
                        "status": "Pending"
                    })

                    save_patient_record(
                        patient_id,
                        patient,
                        patients
                    )

                    st.success(
                        "Appointment added successfully."
                    )

                    st.rerun()

    if patient["appointments"]:

        for a in patient["appointments"]:

            st.write(
                f"- {a.get('date', '-')}"
                f" — {a.get('reason', '-')}"
                f" ({a.get('status', 'Pending')})"
            )

    else:

        empty_state(
            "No appointments on record."
        )

    st.markdown('</div>', unsafe_allow_html=True)
#==============================================================
def generate_hypotheses(patient):
    """
    MedPath rule-based analysis engine.

    Uses ONLY information already stored in the patient's record:
    - Symptoms
    - Laboratory results
    - Medications
    - Timeline
    - Appointments
    - Documents

    It does not read/OCR documents and does not invent medical facts.
    """

    if not patient:
        return {
            "hypotheses": [],
            "missing_test": None,
            "summary": "No patient record is available."
        }

    symptoms = patient.get("symptoms") or []
    labs = patient.get("labs") or []
    medications = patient.get("medications") or []
    timeline = patient.get("timeline") or []
    appointments = patient.get("appointments") or []
    documents = patient.get("documents") or []

    # ----------------------------------------------------------
    # NORMALIZE DATA
    # ----------------------------------------------------------

    symptom_names = [
        str(s.get("name", "")).strip().lower()
        for s in symptoms
        if s.get("name")
    ]

    lab_map = {}

    for lab in labs:
        test_name = str(
            lab.get("test", "")
        ).strip().lower()

        if test_name:
            lab_map[test_name] = lab

    hypotheses = []
    missing_test = None

    # ----------------------------------------------------------
    # SYMPTOM FLAGS
    # ----------------------------------------------------------

    fatigue = any(
        "fatigue" in s or
        "tired" in s or
        "weakness" in s or
        "weak" in s
        for s in symptom_names
    )

    breathlessness = any(
        "breath" in s or
        "shortness of breath" in s or
        "breathlessness" in s
        for s in symptom_names
    )

    dizziness = any(
        "dizziness" in s or
        "dizzy" in s
        for s in symptom_names
    )

    headache = any(
        "headache" in s or
        "head pain" in s
        for s in symptom_names
    )

    thirst = any(
        "thirst" in s
        for s in symptom_names
    )

    frequent_urination = any(
        "urination" in s or
        "urinating" in s or
        "frequent urine" in s
        for s in symptom_names
    )

    blurred_vision = any(
        "blurred vision" in s or
        "blurry vision" in s or
        "vision" in s
        for s in symptom_names
    )

    # ----------------------------------------------------------
    # ANEMIA-RELATED PATTERN
    # ----------------------------------------------------------

    anemia_evidence = []

    if fatigue:
        anemia_evidence.append("Fatigue recorded")

    if breathlessness:
        anemia_evidence.append(
            "Breathlessness recorded"
        )

    if dizziness:
        anemia_evidence.append(
            "Dizziness recorded"
        )

    hemoglobin = None

    for name, lab in lab_map.items():

        if (
            "hemoglobin" in name
            or name == "hb"
            or name == "haemoglobin"
        ):
            try:
                hemoglobin = float(
                    lab.get("value")
                )
            except (TypeError, ValueError):
                hemoglobin = None

            break

    if hemoglobin is not None:

        anemia_evidence.append(
            f"Hemoglobin {hemoglobin} "
            f"{lab_map.get(name, {}).get('unit', '')}".strip()
        )

        if hemoglobin < 12:

            hypotheses.append({
                "condition": "Possible anemia pattern",
                "likelihood": "Medium",
                "evidence": anemia_evidence
            })

        elif fatigue or breathlessness or dizziness:

            hypotheses.append({
                "condition": "Symptoms requiring further evaluation",
                "likelihood": "Low",
                "evidence": anemia_evidence
            })

    elif fatigue and (
        breathlessness or dizziness
    ):

        hypotheses.append({
            "condition": "Possible anemia pattern",
            "likelihood": "Low",
            "evidence": anemia_evidence
        })

        missing_test = (
            "Complete Blood Count (CBC) / Hemoglobin"
        )

    # ----------------------------------------------------------
    # BLOOD-SUGAR-RELATED PATTERN
    # ----------------------------------------------------------

    glucose_evidence = []

    if thirst:
        glucose_evidence.append(
            "Increased thirst recorded"
        )

    if frequent_urination:
        glucose_evidence.append(
            "Frequent urination recorded"
        )

    if blurred_vision:
        glucose_evidence.append(
            "Blurred vision recorded"
        )

    glucose_value = None

    for name, lab in lab_map.items():

        if (
            "glucose" in name
            or "blood sugar" in name
            or "fasting sugar" in name
        ):

            try:
                glucose_value = float(
                    lab.get("value")
                )
            except (TypeError, ValueError):
                glucose_value = None

            if glucose_value is not None:

                glucose_evidence.append(
                    f"{lab.get('test', 'Glucose')} "
                    f"{glucose_value} "
                    f"{lab.get('unit', '')}".strip()
                )

            break

    if (
        len(glucose_evidence) >= 2
        and glucose_value is not None
        and glucose_value >= 100
    ):

        hypotheses.append({
            "condition": "Possible blood glucose abnormality pattern",
            "likelihood": "Medium",
            "evidence": glucose_evidence
        })

    elif len(glucose_evidence) >= 2:

        hypotheses.append({
            "condition": "Symptoms requiring blood glucose evaluation",
            "likelihood": "Low",
            "evidence": glucose_evidence
        })

        if missing_test is None:
            missing_test = "Blood glucose / HbA1c"

    # ----------------------------------------------------------
    # HEADACHE / DIZZINESS PATTERN
    # ----------------------------------------------------------

    if headache and dizziness:

        hypotheses.append({
            "condition": "Headache and dizziness pattern",
            "likelihood": "Low",
            "evidence": [
                "Headache recorded",
                "Dizziness recorded"
            ]
        })

    # ----------------------------------------------------------
    # GENERAL SYMPTOM ANALYSIS
    # ----------------------------------------------------------

    if not hypotheses and symptoms:

        evidence = [
            f"{s.get('name')} ({s.get('severity', 'severity not recorded')})"
            for s in symptoms
            if s.get("name")
        ]

        hypotheses.append({
            "condition": "Symptoms recorded — further evaluation required",
            "likelihood": "Low",
            "evidence": evidence
        })

    # ----------------------------------------------------------
    # NO MEDICAL DATA
    # ----------------------------------------------------------

    if not symptoms and not labs:

        hypotheses.append({
            "condition": "No clinical pattern identified yet",
            "likelihood": "Low",
            "evidence": [
                "No symptoms or laboratory results recorded"
            ]
        })

    # ----------------------------------------------------------
    # SUMMARY
    # ----------------------------------------------------------

    summary_parts = []

    if symptoms:
        summary_parts.append(
            f"{len(symptoms)} symptom(s)"
        )

    if labs:
        summary_parts.append(
            f"{len(labs)} laboratory result(s)"
        )

    if medications:
        summary_parts.append(
            f"{len(medications)} medication(s)"
        )

    if documents:
        summary_parts.append(
            f"{len(documents)} document(s)"
        )

    if timeline:
        summary_parts.append(
            f"{len(timeline)} timeline event(s)"
        )

    if appointments:
        pending = [
            a for a in appointments
            if str(a.get("status", "")).lower()
            == "pending"
        ]

        if pending:
            summary_parts.append(
                f"{len(pending)} pending appointment(s)"
            )

    if summary_parts:

        summary = (
            "Current patient record contains: "
            + ", ".join(summary_parts)
            + "."
        )

    else:

        summary = (
            "No medical information has been "
            "recorded for this patient yet."
        )

    # ----------------------------------------------------------
    # FINAL RESULT
    # ----------------------------------------------------------

    return {
        "hypotheses": hypotheses,
        "missing_test": missing_test,
        "summary": summary
    }
def insights_page(patient_id):

    patient, _ = get_patient_record(
        patient_id
    )

    if patient is None:

        empty_state(
            "Patient record not found."
        )

        return

    # ==========================================================
    # GENERATE CURRENT ANALYSIS
    # ==========================================================

    analysis_result = generate_hypotheses(
        patient
    )

    # Safety fallback
    if not isinstance(
        analysis_result,
        dict
    ):
        analysis_result = {
            "hypotheses": [],
            "missing_test": None,
            "summary": "No clinical analysis available."
        }

    # ==========================================================
    # CLINICAL INSIGHTS CARD
    # ==========================================================

    st.markdown(
        '<div class="mp-card"><h4>Clinical Insights</h4>',
        unsafe_allow_html=True,
    )

    # ==========================================================
    # CLINICAL SUMMARY
    # ==========================================================

    st.markdown(
        "### 🧾 Clinical Summary"
    )

    st.info(
        analysis_result.get(
            "summary",
            "No clinical summary available."
        )
    )

    # ==========================================================
    # PATTERNS & OBSERVATIONS
    # ==========================================================

    st.markdown(
        "### 🔎 Patterns & Observations"
    )

    hypotheses = analysis_result.get(
        "hypotheses",
        []
    )

    if hypotheses:

        for hypothesis in hypotheses:

            condition = hypothesis.get(
                "condition",
                "Clinical observation"
            )

            likelihood = hypothesis.get(
                "likelihood",
                "Not specified"
            )

            evidence = hypothesis.get(
                "evidence",
                []
            )

            st.write(
                f"**{condition}** — "
                f"{likelihood}"
            )

            if evidence:

                st.caption(
                    "Evidence: "
                    + ", ".join(
                        str(item)
                        for item in evidence
                    )
                )

    else:

        st.info(
            "No specific clinical pattern identified "
            "from the current patient data."
        )

    # ==========================================================
    # MISSING INFORMATION
    # ==========================================================

    st.markdown(
        "### ⚠️ Missing Information"
    )

    missing_test = analysis_result.get(
        "missing_test"
    )

    if missing_test:

        st.warning(
            f"Additional information that may be useful: "
            f"{missing_test}"
        )

    else:

        st.success(
            "No specific missing information was identified "
            "by the current analysis."
        )

    # ==========================================================
    # FUTURE N8N ANALYSIS
    # ==========================================================

    st.markdown(
        "### 🤖 AI Workflow Analysis"
    )

    st.info(
        "Document-based AI analysis will appear here "
        "when the MedPath n8n workflow is connected."
    )

    st.caption(
        "The n8n workflow will organize uploaded document "
        "information, generate timeline events, produce "
        "analysis and insights, and make the structured "
        "information available to the MedPath AI Assistant."
    )

    # ==========================================================
    # DISCLAIMER
    # ==========================================================

    st.markdown(
        '<div class="mp-disclaimer">'
        'AI-generated information should be verified by '
        'a healthcare professional.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ==========================================================
    # CLOSE CARD
    # ==========================================================

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )
def alerts_page(patient_id):

    patient, _ = get_patient_record(
        patient_id
    )

    if patient is None:

        empty_state(
            "Patient record not found."
        )

        return

    st.markdown(
        '<div class="mp-card"><h4>Alerts</h4>',
        unsafe_allow_html=True,
    )

    shown = False

    if st.session_state.analyzed.get(
        patient_id,False
    ):

        hypotheses = generate_hypotheses(
            patient
        )

        if hypotheses["missing_test"]:

            st.markdown(
                f'<div class="mp-alert">'
                f'Your doctor recommends: '
                f'{hypotheses["missing_test"]}'
                f'</div>',
                unsafe_allow_html=True,
            )

            shown = True

    if not shown:

        empty_state(
            "No alerts"
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ==============================================================
# DOCTOR DASHBOARD
# ==============================================================

def doctor_dashboard_page(user):

    st.markdown(
        f'<div class="mp-logo">{APP_ICON} {APP_NAME}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "### Doctor Dashboard"
    )

    st.caption(
        f"Welcome back, "
        f"{user.get('full_name', 'Doctor')}"
    )

    patients = load_db(
        PATIENTS_FILE
    )

    # ----------------------------------------------------------
    # PATIENT IDENTIFICATION
    # ----------------------------------------------------------

    st.markdown(
        '<div class="mp-card"><h4>Patient Identification</h4>',
        unsafe_allow_html=True,
    )

    options = {}

    for patient_id, patient in patients.items():

        name = patient.get(
            "name",
            "Unknown Patient",
        )

        options[
            f"{name} ({patient_id})"
        ] = patient_id

    if options:

        choice = st.selectbox(
            "Select Patient",
            list(options.keys()),
        )

        if st.button(
            "🔍 Load Patient"
        ):

            st.session_state.selected_patient_id = (
                options[choice]
            )

            st.rerun()

    else:

        empty_state(
            "No patients available yet."
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # ----------------------------------------------------------
    # METRICS
    # ----------------------------------------------------------

    high_priority = 0

    for patient_id, patient in patients.items():

        if st.session_state.analyzed.get(
            patient_id
        ):

            hypotheses = generate_hypotheses(
                patient
            )

            if hypotheses["missing_test"]:

                high_priority += 1

    m1, m2, m3, m4 = st.columns(4)

    with m1:

        st.markdown(
            f'<div class="mp-metric">'
            f'<h3>{len(patients)}</h3>'
            f'Total Patients'
            f'</div>',
            unsafe_allow_html=True,
        )

    with m2:

        st.markdown(
            '<div class="mp-metric">'
            '<h3>--</h3>'
            "Today's Appointments"
            '</div>',
            unsafe_allow_html=True,
        )

    with m3:

        st.markdown(
            '<div class="mp-metric">'
            '<h3>--</h3>'
            "Pending Reports"
            '</div>',
            unsafe_allow_html=True,
        )

    with m4:

        st.markdown(
            f'<div class="mp-metric">'
            f'<h3>{high_priority}</h3>'
            f'High Priority'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.write("")

    patient_id = (
        st.session_state.selected_patient_id
    )

    patient = patients.get(
        patient_id
    )

    # ----------------------------------------------------------
    # PATIENT OVERVIEW
    # ----------------------------------------------------------

    st.markdown(
        '<div class="mp-card"><h4>Patient Overview</h4>',
        unsafe_allow_html=True,
    )

    if not patient:

        empty_state(
            "Select a patient to view their overview."
        )

    else:

        st.write(
            f"**Patient ID:** "
            f"{patient.get('patient_id', patient_id)}"
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.write(
            f"**Name**\n\n"
            f"{patient.get('name', '-')}"
        )

        c2.write(
            f"**Age**\n\n"
            f"{patient.get('age', '-')}"
        )

        c3.write(
            f"**Gender**\n\n"
            f"{patient.get('gender', '-')}"
        )

        c4.write(
            f"**Blood Group**\n\n"
            f"{patient.get('bloodGroup') or 'Not recorded'}"
        )

        condition = "Not yet analyzed"

        if st.session_state.analyzed.get(
            patient_id
        ):

            hypotheses = generate_hypotheses(
                patient
            )

            if hypotheses["hypotheses"]:

                condition = hypotheses[
                    "hypotheses"
                ][0]["condition"]

        c1, c2, c3, c4 = st.columns(4)

        c1.write(
            f"**Current Condition**\n\n"
            f"{condition}"
        )

        c2.write(
            "**Department**\n\n"
            "Not recorded"
        )

        c3.write(
            f"**Attending Doctor**\n\n"
            f"{user.get('full_name', '-')}"
        )

        c4.write(
            "**Next Appointment**\n\n"
            "Not recorded"
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # ----------------------------------------------------------
    # AI SUMMARY
    # ----------------------------------------------------------

    st.markdown(
        '<div class="mp-card"><h4>AI Clinical Summary</h4>',
        unsafe_allow_html=True,
    )

    if (
        patient
        and st.session_state.analyzed.get(
            patient_id
        )
    ):

        st.write(
            generate_hypotheses(
                patient
            )["summary"]
        )

    else:

        st.write(
            "AI-generated summary will appear here."
        )

    st.markdown(
        '<div class="mp-disclaimer">'
        'AI-generated information should be verified before clinical use.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # ----------------------------------------------------------
    # AI HYPOTHESES
    # ----------------------------------------------------------

    st.markdown(
        '<div class="mp-card"><h4>AI Clinical Hypotheses</h4>',
        unsafe_allow_html=True,
    )

    analyze_disabled = patient is None

    if st.button(
        "✨ Analyze",
        disabled=analyze_disabled,
    ):

        st.session_state.analyzed[
            patient_id
        ] = True

        st.rerun()

    if patient and st.session_state.analyzed.get(
        patient_id
    ):

        hypotheses = generate_hypotheses(
            patient
        )

        if hypotheses["missing_test"]:

            st.markdown(
                f'<div class="mp-alert">'
                f'⚠️ Missing test — '
                f'no {hypotheses["missing_test"]} on record'
                f'</div>',
                unsafe_allow_html=True,
            )

        for index, hypothesis in enumerate(
            hypotheses["hypotheses"]
        ):

            badge_class = {
                "High": "mp-badge-high",
                "Medium": "mp-badge-medium",
                "Low": "mp-badge-low",
            }.get(
                hypothesis["likelihood"],
                "mp-badge-low",
            )

            opacity = (
                "1"
                if index == 0
                else "0.55"
            )

            evidence = ", ".join(
                hypothesis["evidence"]
            )

            st.markdown(
                f"""
                <div style="opacity:{opacity}">
                    <b>{hypothesis["condition"]}</b>
                    <span class="{badge_class}">
                        {hypothesis["likelihood"]}
                    </span>
                    <br>
                    <span class="mp-disclaimer">
                        Evidence: {evidence}
                    </span>
                </div>
                <br>
                """,
                unsafe_allow_html=True,
            )

        if hypotheses["missing_test"]:

            st.write(
                f"**Recommended:** order "
                f"{hypotheses['missing_test']} to confirm"
            )

    elif not patient:

        empty_state(
            "Select and load a patient to run AI analysis."
        )

    else:

        empty_state(
            "Click Analyze to generate AI-supported hypotheses."
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # ----------------------------------------------------------
    # CLINICAL TRENDS
    # ----------------------------------------------------------

    st.markdown(
        '<div class="mp-card"><h4>Clinical Trends</h4>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Vital Signs graph — placeholder"
    )

    st.caption(
        "Laboratory Trends graph — placeholder"
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # ----------------------------------------------------------
    # DOCUMENTS
    # ----------------------------------------------------------

    st.markdown(
        '<div class="mp-card"><h4>Documents & Reports</h4>',
        unsafe_allow_html=True,
    )

    if patient and patient.get(
        "documents"
    ):

        for document in patient[
            "documents"
        ]:

            st.write(
                f"- {document.get('name', 'Document')} "
                f"({document.get('type', 'unknown')})"
            )

    else:

        empty_state(
            "Uploaded reports, prescriptions, scans will appear here."
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # ----------------------------------------------------------
    # AI INSIGHTS
    # ----------------------------------------------------------

    st.markdown(
        '<div class="mp-card"><h4>AI Insights Summary</h4>',
        unsafe_allow_html=True,
    )

    if patient:

        analyzed = st.session_state.analyzed.get(
            patient_id
        )

        hypotheses = (
            generate_hypotheses(patient)
            if analyzed
            else None
        )

        rows = [
            (
                "Symptoms Identified",
                ", ".join(
                    s.get("name", "")
                    for s in patient.get(
                        "symptoms",
                        [],
                    )
                )
                or "None recorded",
            ),
            (
                "Possible Diagnosis",
                (
                    hypotheses["hypotheses"][0]["condition"]
                    if hypotheses
                    else "Not yet analyzed"
                ),
            ),
            (
                "Medications",
                ", ".join(
                    m.get("name", "")
                    for m in patient.get(
                        "medications",
                        [],
                    )
                )
                or "None recorded",
            ),
            (
                "Allergies",
                patient.get(
                    "additional",
                    {},
                ).get(
                    "allergies",
                    "Not recorded",
                )
                or "Not recorded",
            ),
            (
                "Risk Flags",
                "Not recorded",
            ),
            (
                "Missing Information",
                (
                    hypotheses["missing_test"]
                    if hypotheses
                    and hypotheses["missing_test"]
                    else (
                        "Not yet analyzed"
                        if not analyzed
                        else "None flagged"
                    )
                ),
            ),
        ]

        for label, value in rows:

            c1, c2 = st.columns(
                [2, 3]
            )

            c1.write(
                f"**{label}**"
            )

            c2.write(
                value
            )

    else:

        empty_state(
            "Select a patient to view AI insights."
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ==============================================================
# DOCTOR / CHW ADD PATIENT
# ==============================================================

def doctor_add_patient_form():

    st.markdown(
        '<div class="mp-card"><h4>Add / Register Patient</h4>',
        unsafe_allow_html=True,
    )

    with st.form(
        "doctor_add_patient"
    ):

        name = st.text_input(
            "Full Name"
        )

        c1, c2, c3 = st.columns(3)

        age = c1.number_input(
            "Age",
            min_value=0,
            max_value=120,
            step=1,
        )

        gender = c2.selectbox(
            "Gender",
            [
                "Female",
                "Male",
                "Other",
            ],
        )

        phone = c3.text_input(
            "Phone"
        )

        submitted = st.form_submit_button(
            "Create Patient Record",
            type="primary",
        )

    if submitted:

        if not name.strip():

            st.warning(
                "Please enter the patient's name."
            )

            return

        patients = load_db(
            PATIENTS_FILE
        )

        patient_id = new_id(
            "MP"
        )

        patients[patient_id] = {
            "patient_id": patient_id,
            "linked_user_id": None,
            "name": name.strip(),
            "age": int(age),
            "gender": gender,
            "bloodGroup": None,
            "phone": phone.strip(),
            "symptoms": [],
            "labs": [],
            "medications": [],
            "documents": [],
            "timeline": [],
            "appointments": [],
            "additional": {},
            "createdAt": datetime.now().isoformat(),
        }

        save_db(
            PATIENTS_FILE,
            patients,
        )

        st.success(
            f"Patient created with ID {patient_id}."
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ==============================================================
# CHW DASHBOARD
# ==============================================================

def chw_dashboard_page(user):

    st.markdown(
        f'<div class="mp-logo">{APP_ICON} {APP_NAME}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "### CHW Dashboard"
    )

    st.caption(
        f"Welcome, "
        f"{user.get('full_name', 'CHW')}"
    )

    patients = load_db(
        PATIENTS_FILE
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            '<div class="mp-card"><h4>Patient Coordination</h4>',
            unsafe_allow_html=True,
        )

        if patients:

            for patient_id, patient in patients.items():

                st.write(
                    f"- {patient.get('name', 'Unknown')} "
                    f"({patient_id})"
                )

        else:

            empty_state(
                "No patients assigned yet."
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    with col2:

        st.markdown(
            '<div class="mp-card"><h4>Follow-Up</h4>',
            unsafe_allow_html=True,
        )

        pending_appointments = []

        missing_documents = []

        for patient_id, patient in patients.items():

            for appointment in patient.get(
                "appointments",
                [],
            ):

                if appointment.get(
                    "status"
                ) == "Pending":

                    pending_appointments.append(
                        (
                            patient_id,
                            appointment,
                        )
                    )

            if not patient.get(
                "documents"
            ):

                missing_documents.append(
                    (
                        patient_id,
                        patient,
                    )
                )

        if pending_appointments:

            st.write(
                "**Upcoming Follow-ups**"
            )

            for patient_id, appointment in pending_appointments:

                patient = patients.get(
                    patient_id,
                    {},
                )

                st.write(
                    f"- {patient.get('name', 'Unknown')}: "
                    f"{appointment.get('reason', '')} "
                    f"on {appointment.get('date', '')}"
                )

        else:

            empty_state(
                "No follow-ups available."
            )

        if missing_documents:

            st.write(
                "**Documents Awaiting Upload**"
            )

            for patient_id, patient in missing_documents:

                st.write(
                    f"- {patient.get('name', 'Unknown')}"
                )

        else:

            empty_state(
                "No pending documents."
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    doctor_add_patient_form()


# ==============================================================
# CHATBOT
# ==============================================================

CHATBOT_SUGGESTIONS = {

    "Patient": [
        "Summarize my medical history",
        "What information is missing from my health record?",
        "Explain my timeline",
    ],

    "Doctor": [
        "Summarize this patient's medical history",
        "What follow-ups are pending?",
        "What information is missing?",
    ],

    "CHW": [
        "Which documents are still missing?",
        "When is the patient's next follow-up?",
        "Show pending coordination tasks",
    ],
}


def chatbot_reply(
    role,
    patient,
    question,
):

    if patient is None:

        return (
            "I don't have a patient selected yet, "
            "so I don't have any medical records to analyze."
        )

    has_data = bool(
        patient.get("symptoms")
        or patient.get("labs")
        or patient.get("documents")
        or patient.get("timeline")
        or patient.get("medications")
    )

    if not has_data:

        return (
            "I don't have any medical records to analyze yet."
        )

    question = question.lower()

    if "symptom" in question:

        symptoms = patient.get(
            "symptoms",
            [],
        )

        if symptoms:

            names = ", ".join(
                s.get("name", "")
                for s in symptoms
            )

            return (
                f"Recorded symptoms: {names}."
            )

        return (
            "No symptoms are recorded yet."
        )

    if "medication" in question:

        medications = patient.get(
            "medications",
            [],
        )

        if medications:

            names = ", ".join(
                m.get("name", "")
                for m in medications
            )

            return (
                f"Current/past medications on record: {names}."
            )

        return (
            "No medications are recorded yet."
        )

    if "missing" in question:

        missing = []

        if not patient.get(
            "labs"
        ):
            missing.append(
                "laboratory results"
            )

        if not patient.get(
            "documents"
        ):
            missing.append(
                "uploaded documents"
            )

        if not patient.get(
            "appointments"
        ):
            missing.append(
                "appointment history"
            )

        if missing:

            return (
                "Based on the current record, missing "
                "information includes: "
                + ", ".join(missing)
                + "."
            )

        return (
            "The record looks reasonably complete "
            "based on what's been entered."
        )

    if (
        "timeline" in question
        or "history" in question
        or "summar" in question
    ):

        timeline = patient.get(
            "timeline",
            [],
        )

        if timeline:

            events = "; ".join(
                f"{event.get('date', '')}: "
                f"{event.get('type', '')} - "
                f"{event.get('description', '')}"
                for event in timeline[-5:]
            )

            return (
                f"Here are the most recent recorded events: "
                f"{events}."
            )

        return (
            "There are no timeline events recorded yet."
        )

    if (
        "follow" in question
        or "pending" in question
    ):

        pending = [
            appointment
            for appointment in patient.get(
                "appointments",
                [],
            )
            if appointment.get(
                "status"
            ) == "Pending"
        ]

        if pending:

            return (
                f"There are {len(pending)} "
                "pending follow-up item(s) on record."
            )

        return (
            "No pending follow-ups are recorded."
        )

    if "document" in question:

        documents = patient.get(
            "documents",
            [],
        )

        if documents:

            names = ", ".join(
                d.get("name", "")
                for d in documents
            )

            return (
                f"Documents on record: {names}."
            )

        return (
            "No documents have been uploaded yet."
        )

    return (
        "I can only answer using what's actually "
        "recorded for this patient. Try asking about "
        "symptoms, medications, the timeline, "
        "or missing information."
    )


def render_chatbot():

    user = current_user()

    if not user:
        return

    role = st.session_state.get(
        "role"
    )

    patient = None

    if role == "Patient":

        patient_id = user.get(
            "patient_id"
        )

        if patient_id:

            patient, _ = get_patient_record(
                patient_id
            )

    else:

        selected_patient_id = (
            st.session_state.get(
                "selected_patient_id"
            )
        )

        if selected_patient_id:

            patient, _ = get_patient_record(
                selected_patient_id
            )

    with st.sidebar:

        st.markdown("---")

        with st.expander(
            "💬 Ask MedPath — AI Assistant",
            expanded=False,
        ):

            st.caption(
                f"{APP_ICON} MedPath AI Assistant"
            )

            st.caption(
                "Ask questions about your MedPath health information."
            )

            history_key = str(
                st.session_state.get(
                    "user_id"
                )
            )

            history = (
                st.session_state
                .chatbot_history
                .setdefault(
                    history_key,
                    [],
                )
            )

            for who, text in history[-8:]:

                if who == "user":

                    st.markdown(
                        f"**You:** {text}"
                    )

                else:

                    st.markdown(
                        f"**MedPath AI:** {text}"
                    )

            st.caption(
                "Suggested:"
            )

            for index, chip in enumerate(
                CHATBOT_SUGGESTIONS.get(
                    role,
                    [],
                )
            ):

                if st.button(
                    chip,
                    key=f"chat_chip_{index}",
                ):

                    history.append(
                        (
                            "user",
                            chip,
                        )
                    )

                    history.append(
                        (
                            "assistant",
                            chatbot_reply(
                                role,
                                patient,
                                chip,
                            ),
                        )
                    )

                    st.rerun()

            question = st.text_input(
                "Type a question…",
                key="chat_input",
            )

            col_a, col_b = st.columns(2)

            with col_a:

                if st.button(
                    "Send",
                    key="chat_send",
                ) and question:

                    history.append(
                        (
                            "user",
                            question,
                        )
                    )

                    history.append(
                        (
                            "assistant",
                            chatbot_reply(
                                role,
                                patient,
                                question,
                            ),
                        )
                    )

                    st.rerun()

            with col_b:

                if st.button(
                    "Clear conversation",
                    key="chat_clear",
                ):

                    st.session_state.chatbot_history[
                        history_key
                    ] = []

                    st.rerun()


# ==============================================================
# SIDEBAR
# ==============================================================

NAV = {

    "Patient": [
        "Dashboard",
        "My Profile",
        "My Timeline",
        "Documents",
        "Insights",
        "Alerts",
        "Settings",
    ],

    "Doctor": [
        "Dashboard",
        "Patients",
        "Search Patient",
        "Timeline",
        "Documents",
        "Notes",
        "Insights",
        "Alerts",
        "Profile",
    ],

    "CHW": [
        "Dashboard",
        "Patients",
        "Add Patient",
        "Search Patient",
        "Documents",
        "Follow-ups",
        "Notes",
        "Timeline",
        "Alerts",
        "Profile",
    ],
}


def sidebar_nav():

    user = current_user()

    role = str(
        st.session_state.get("role", "")
    ).strip().lower()

    role_display = {
        "patient": "Patient",
        "doctor": "Doctor",
        "chw": "CHW"
    }.get(role, role)

    with st.sidebar:

        render_logo()

        st.caption(
            f"{role_display} workspace"
        )

        st.markdown("---")

        for item in NAV.get(
            role_display,
            []
        ):

            if st.button(
                item,
                key=f"nav_{item}",
                use_container_width=True
            ):

                st.session_state.page = item

                st.rerun()

        st.markdown("---")

        if st.button(
            "Logout",
            use_container_width=True
        ):

            logout()

            st.rerun()

    render_chatbot()

# ==============================================================
# PATIENT ROUTER
# ==============================================================

def route_patient(
    page,
    user,
):

    patient_id = user.get(
        "patient_id"
    )

    if page in (
        "dashboard",
        "Dashboard",
    ):

        patient_dashboard_page(
            user
        )

    elif page == "My Profile":

        patient_profile_page(
            user
        )

    elif page == "My Timeline":

        if patient_id:
            timeline_page(
                patient_id
            )
        else:
            st.error(
                "Patient ID is missing."
            )

    elif page == "Documents":

        if patient_id:
            documents_page(
                patient_id
            )
        else:
            st.error(
                "Patient ID is missing."
            )

    elif page == "Insights":

        if patient_id:
            insights_page(
                patient_id
            )
        else:
            st.error(
                "Patient ID is missing."
            )

    elif page == "Alerts":

        if patient_id:
            alerts_page(
                patient_id
            )
        else:
            st.error(
                "Patient ID is missing."
            )

    elif page == "Settings":

        if patient_id:
            symptoms_medications_appointments_page(
                patient_id
            )
        else:
            st.error(
                "Patient ID is missing."
            )

    else:

        patient_dashboard_page(
            user
        )


# ==============================================================
# DOCTOR ROUTER
# ==============================================================

def route_doctor(
    page,
    user,
):

    if page in (
        "dashboard",
        "Dashboard",
        "Patients",
        "Search Patient",
    ):

        doctor_dashboard_page(
            user
        )

    elif page == "Timeline":

        patient_id = (
            st.session_state.get(
                "selected_patient_id"
            )
        )

        if patient_id:

            timeline_page(
                patient_id,
                editable=False,
            )

        else:

            empty_state(
                "Select a patient from the Dashboard first."
            )

    elif page == "Documents":

        patient_id = (
            st.session_state.get(
                "selected_patient_id"
            )
        )

        if patient_id:

            documents_page(
                patient_id,
                editable=False,
            )

        else:

            empty_state(
                "Select a patient from the Dashboard first."
            )

    elif page == "Notes":

        st.markdown(
            '<div class="mp-card"><h4>Notes</h4>',
            unsafe_allow_html=True,
        )

        empty_state(
            "No notes recorded yet."
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    elif page == "Insights":

        patient_id = (
            st.session_state.get(
                "selected_patient_id"
            )
        )

        if patient_id:

            insights_page(
                patient_id
            )

        else:

            empty_state(
                "Select a patient from the Dashboard first."
            )

    elif page == "Alerts":

        patient_id = (
            st.session_state.get(
                "selected_patient_id"
            )
        )

        if patient_id:

            alerts_page(
                patient_id
            )

        else:

            empty_state(
                "Select a patient from the Dashboard first."
            )

    elif page == "Profile":

        st.markdown(
            '<div class="mp-card"><h4>Doctor Profile</h4>',
            unsafe_allow_html=True,
        )

        st.write(
            f"**Name:** "
            f"{user.get('full_name', '-')}"
        )

        st.write(
            f"**Email:** "
            f"{user.get('email', '-')}"
        )

        st.write(
            f"**Specialization:** "
            f"{user.get('specialization', '-')}"
        )

        st.write(
            f"**License Number:** "
            f"{user.get('license_number', '-')}"
        )

        st.write(
            f"**Hospital / Clinic:** "
            f"{user.get('hospital', '-')}"
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    else:

        doctor_dashboard_page(
            user
        )


# ==============================================================
# CHW ROUTER
# ==============================================================

def route_chw(
    page,
    user,
):

    if page in (
        "dashboard",
        "Dashboard",
        "Patients",
        "Search Patient",
    ):

        chw_dashboard_page(
            user
        )

    elif page == "Add Patient":

        doctor_add_patient_form()

    elif page == "Documents":

        patients = load_db(
            PATIENTS_FILE
        )

        options = {}

        for patient_id, patient in patients.items():

            options[
                f"{patient.get('name', 'Unknown')} "
                f"({patient_id})"
            ] = patient_id

        if options:

            choice = st.selectbox(
                "Select Patient",
                list(options.keys()),
            )

            documents_page(
                options[choice]
            )

        else:

            empty_state(
                "No patients assigned yet."
            )

    elif page == "Follow-ups":

        chw_dashboard_page(
            user
        )

    elif page == "Notes":

        st.markdown(
            '<div class="mp-card"><h4>Notes</h4>',
            unsafe_allow_html=True,
        )

        empty_state(
            "No notes recorded yet."
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    elif page == "Timeline":

        patients = load_db(
            PATIENTS_FILE
        )

        options = {}

        for patient_id, patient in patients.items():

            options[
                f"{patient.get('name', 'Unknown')} "
                f"({patient_id})"
            ] = patient_id

        if options:

            choice = st.selectbox(
                "Select Patient",
                list(options.keys()),
            )

            timeline_page(
                options[choice]
            )

        else:

            empty_state(
                "No patients assigned yet."
            )

    elif page == "Alerts":

        st.markdown(
            '<div class="mp-card"><h4>Alerts</h4>',
            unsafe_allow_html=True,
        )

        empty_state(
            "No alerts"
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    elif page == "Profile":

        st.markdown(
            '<div class="mp-card"><h4>CHW Profile</h4>',
            unsafe_allow_html=True,
        )

        st.write(
            f"**Name:** "
            f"{user.get('full_name', '-')}"
        )

        st.write(
            f"**Email:** "
            f"{user.get('email', '-')}"
        )

        st.write(
            f"**Employee ID:** "
            f"{user.get('employee_id', '-')}"
        )

        st.write(
            f"**Organization:** "
            f"{user.get('organization', '-')}"
        )

        st.write(
            f"**Region:** "
            f"{user.get('region', '-')}"
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    else:

        chw_dashboard_page(
            user
        )


# ==============================================================
# MAIN
# ==============================================================

def main():

    init_session_state()

    inject_css()

    # ----------------------------------------------------------
    # NOT LOGGED IN
    # ----------------------------------------------------------

    if not st.session_state.auth:

        login_page()

        return

    # ----------------------------------------------------------
    # LOAD USER FROM FASTAPI
    # ----------------------------------------------------------

    user = current_user()

    if user is None:

        st.session_state.auth = False
        st.session_state.user_id = None
        st.session_state.user = None
        st.session_state.role = None
        st.session_state.page = "login"

        st.warning(
            "Your session has expired. Please sign in again."
        )

        st.rerun()

        return

    # ----------------------------------------------------------
    # KEEP PATIENT RECORD AVAILABLE
    # ----------------------------------------------------------

    if str(user.get("role", "")).strip().lower() == "patient":

        ensure_patient_record(user)

    # ----------------------------------------------------------
    # GET ROLE SAFELY
    # ----------------------------------------------------------

    role = str(user.get("role", "")).strip().lower()

    # Keep session state consistent
    st.session_state.role = role

    # ----------------------------------------------------------
    # SIDEBAR
    # ----------------------------------------------------------

    sidebar_nav()

    page = st.session_state.get(
        "page",
        "dashboard",
    )

    # ----------------------------------------------------------
    # ROUTING
    # ----------------------------------------------------------

    if role == "patient":

        route_patient(
            page,
            user,
        )

    elif role == "doctor":

        route_doctor(
            page,
            user,
        )

    elif role == "chw":

        route_chw(
            page,
            user,
        )

    else:

        st.error(
            f"Unknown user role: {user.get('role')}"
        )


# ==============================================================
# START APPLICATION
# ==============================================================

if __name__ == "__main__":
    main()