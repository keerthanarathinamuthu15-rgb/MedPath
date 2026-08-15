import streamlit as st

# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="MedPath",
    page_icon="🩺",
    layout="centered"
)


# ============================================================
# CUSTOM DESIGN
# ============================================================

st.markdown("""
<style>

.stApp {
    background-color: #BADAD5;
}

/* =========================================================
   MEDPATH TITLE
   ========================================================= */

.medpath-title {
    font-family: "Bradley Hand ITC", cursive;
    font-size: 100px;
    font-weight: bold;
    color: #21575B;
    text-align: center;
    margin-top: 150px;
    margin-bottom: 10px;
    line-height: 1;
}


/* =========================================================
   SUBTITLE
   ========================================================= */

.medpath-subtitle {
    font-family: "Segoe UI", sans-serif;
    font-size: 25px;
    font-weight: 400;
    color: #21575B;
    text-align: center;
    margin-top: 15px;
}


/* =========================================================
   BUTTONS
   ========================================================= */

div.stButton > button {
    background-color: #21575B;
    color: #FFFFFF;
    font-family: "Segoe UI", sans-serif;
    font-size: 18px;
    font-weight: 600;
    border: none;
    border-radius: 10px;
    padding: 12px 30px;
    height: 50px;
}

div.stButton > button:hover {
    background-color: #2D6B70;
    color: #FFFFFF;
}


/* =========================================================
   DASHBOARD CARDS
   ========================================================= */

.dashboard-card {
    background-color: #FFFFFF;
    padding: 25px;
    border-radius: 15px;
    margin-top: 15px;
    margin-bottom: 15px;
    box-shadow: 0px 3px 10px rgba(0,0,0,0.08);
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# PAGE NAVIGATION
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "home"


# ============================================================
# PAGE 1 — MEDPATH HOME
# ============================================================

if st.session_state.page == "home":

    st.markdown(
        '<div class="medpath-title">MedPath</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="medpath-subtitle">'
        'Guiding Every Step of Your Health Journey.'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ONLY ONE GET STARTED BUTTON
    if st.button(
        "Get Started →",
        use_container_width=True,
        key="page1_get_started"
    ):
        st.session_state.page = "patient"
        st.rerun()


# ============================================================
# PAGE 2 — PATIENT INFORMATION
# ============================================================

elif st.session_state.page == "patient":

    st.markdown(
        '<div class="medpath-title" '
        'style="font-size:55px; margin-top:40px;">'
        'Patient Information'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="medpath-subtitle" '
        'style="font-size:18px;">'
        'Enter the basic information to begin the patient journey.'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # PATIENT NAME
    # --------------------------------------------------------

    patient_name = st.text_input(
        "Patient Name",
        key="patient_name_input"
    )

    # --------------------------------------------------------
    # PATIENT ID
    # --------------------------------------------------------

    patient_id = st.text_input(
        "Patient ID",
        key="patient_id_input"
    )

    # --------------------------------------------------------
    # AGE
    # --------------------------------------------------------

    age = st.number_input(
        "Age",
        min_value=0,
        max_value=120,
        value=25,
        key="age_input"
    )

    # --------------------------------------------------------
    # GENDER
    # --------------------------------------------------------

    gender = st.selectbox(
        "Gender",
        ["Select", "Female", "Male", "Other"],
        key="gender_input"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # CONTINUE BUTTON
    # --------------------------------------------------------

    if st.button(
        "Continue →",
        use_container_width=True,
        key="patient_continue"
    ):

        # Check patient name and ID
        if patient_name.strip() == "" or patient_id.strip() == "":
            st.warning(
                "Please enter the Patient Name and Patient ID."
            )

        # Check gender
        elif gender == "Select":
            st.warning(
                "Please select the gender."
            )

        # Save information and move to dashboard
        else:

            st.session_state.patient_name = patient_name
            st.session_state.patient_id = patient_id
            st.session_state.age = age
            st.session_state.gender = gender

            st.session_state.page = "dashboard"

            st.rerun()


# ============================================================
# PAGE 3 — PATIENT DASHBOARD
# ============================================================

elif st.session_state.page == "dashboard":

    st.markdown(
        '<div class="medpath-title" '
        'style="font-size:55px; margin-top:40px;">'
        'MedPath Dashboard'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="medpath-subtitle" '
        'style="font-size:18px;">'
        'Your health journey starts here.'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ========================================================
    # PATIENT DETAILS
    # ========================================================

    st.markdown(
        '<div class="dashboard-card">',
        unsafe_allow_html=True
    )

    st.subheader("Patient Details")

    st.write(
        f"**Patient Name:** {st.session_state.patient_name}"
    )

    st.write(
        f"**Patient ID:** {st.session_state.patient_id}"
    )

    st.write(
        f"**Age:** {st.session_state.age}"
    )

    st.write(
        f"**Gender:** {st.session_state.gender}"
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    # ========================================================
    # HEALTH JOURNEY
    # ========================================================

    st.subheader("Health Journey")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "📄 Upload Medical Report",
            use_container_width=True,
            key="upload_medical_report"
        ):
            st.info(
                "Medical report upload will be added here."
            )

    with col2:

        if st.button(
            "🩺 Health Records",
            use_container_width=True,
            key="health_records"
        ):
            st.info(
                "Health records will be displayed here."
            )