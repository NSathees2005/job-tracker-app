import streamlit as st

from datetime import datetime, date, time
from math import radians, sin, cos, sqrt, atan2

from streamlit_js_eval import get_geolocation
from streamlit_autorefresh import st_autorefresh

from database import (
    create_tables,
    create_user,
    login_user,

    add_task,
    get_tasks,
    complete_task,
    delete_task,
    get_task,

    add_note,
    get_all_notes,
    delete_note,

    get_activity_dates,
    get_streak,
    get_longest_streak,
    check_in,
    reset_streak,
    mark_task_location_verified
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Job Todo",
    page_icon="🔥",
    layout="wide"
)


# ==================================================
# DATABASE
# ==================================================

create_tables()


# ==================================================
# SESSION STATE
# ==================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "reset_streak_confirm" not in st.session_state:
    st.session_state.reset_streak_confirm = False

if "gps_check_task_id" not in st.session_state:
    st.session_state.gps_check_task_id = None
# ==================================================
# DISTANCE CALCULATION
# ==================================================

def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2
):

    R = 6371000

    lat1 = radians(lat1)
    lat2 = radians(lat2)

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        +
        cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return R * c


# ==================================================
# LOGIN / SIGNUP
# ==================================================

def authentication_page():

    st.title("🔥 Job Todo")

    st.write(
        "Manage your jobs, tasks, notes and daily streak."
    )

    login_tab, signup_tab = st.tabs(
        ["🔐 Login", "📝 Create Account"]
    )

    # ----------------------------------------------
    # LOGIN
    # ----------------------------------------------

    with login_tab:

        st.subheader("Login")

        email = st.text_input(
            "Email",
            key="login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "Login",
            use_container_width=True
        ):

            user = login_user(
                email,
                password
            )

            if user:

                st.session_state.logged_in = True
                st.session_state.user = user
                st.session_state.page = "Dashboard"

                st.success("Login successful!")

                st.rerun()

            else:

                st.error(
                    "Invalid email or password."
                )

    # ----------------------------------------------
    # SIGNUP
    # ----------------------------------------------

    with signup_tab:

        st.subheader("Create Account")

        username = st.text_input(
            "Username",
            key="signup_username"
        )

        email = st.text_input(
            "Email",
            key="signup_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="signup_password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="signup_confirm"
        )

        if st.button(
            "Create Account",
            use_container_width=True
        ):

            if not username or not email or not password:

                st.warning(
                    "Please fill all fields."
                )

            elif password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

            else:

                success = create_user(
                    username,
                    email,
                    password
                )

                if success:

                    st.success(
                        "Account created successfully!"
                    )

                else:

                    st.error(
                        "Username or email already exists."
                    )


# ==================================================
# SIDEBAR
# ==================================================

def sidebar():

    user = st.session_state.user

    st.sidebar.title("🔥 Job Todo")

    st.sidebar.write(
        f"Welcome, **{user['username']}**"
    )

    st.sidebar.divider()

    pages = [
        "Dashboard",
        "My Tasks",
        "Job Notes",
        "Streak"
    ]

    for page in pages:

        if st.sidebar.button(
            page,
            use_container_width=True
        ):

            st.session_state.page = page
            st.rerun()

    st.sidebar.divider()

    # ----------------------------------------------
    # RESET STREAK
    # ----------------------------------------------

    if st.sidebar.button(
        "🔄 Reset Streak",
        use_container_width=True
    ):

        st.session_state.reset_streak_confirm = True

    if st.session_state.get(
        "reset_streak_confirm",
        False
    ):

        st.sidebar.warning(
            "⚠️ This will clear your entire streak history."
        )

        col1, col2 = st.sidebar.columns(2)

        with col1:

            if st.button(
                "Yes, Reset",
                key="confirm_reset"
            ):

                reset_streak(
                    user["id"]
                )

                st.session_state.reset_streak_confirm = False

                st.success(
                    "🔥 Streak reset successfully!"
                )

                st.rerun()

        with col2:

            if st.button(
                "Cancel",
                key="cancel_reset"
            ):

                st.session_state.reset_streak_confirm = False

                st.rerun()

    # ----------------------------------------------
    # LOGOUT
    # ----------------------------------------------

    st.sidebar.divider()

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.user = None

        st.rerun()


# ==================================================
# DASHBOARD
# ==================================================

def dashboard():

    user_id = st.session_state.user["id"]

    tasks = get_tasks(user_id)

    current_streak = get_streak(user_id)

    longest_streak = get_longest_streak(user_id)

    st.title("📊 Dashboard")

    st.write(
        f"Welcome back, **{st.session_state.user['username']}**!"
    )

    st.divider()

    total_tasks = len(tasks)

    completed_tasks = sum(
        task["completed"]
        for task in tasks
    )

    pending_tasks = (
        total_tasks - completed_tasks
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "📋 Total Tasks",
            total_tasks
        )

    with col2:

        st.metric(
            "✅ Completed",
            completed_tasks
        )

    with col3:

        st.metric(
            "⏳ Pending",
            pending_tasks
        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "🔥 Current Streak",
            current_streak
        )

    with col2:

        st.metric(
            "🏆 Longest Streak",
            longest_streak
        )

    st.divider()

    # ----------------------------------------------
    # TODAY'S REMINDERS
    # ----------------------------------------------

    today = date.today().isoformat()

    today_tasks = [
        task
        for task in tasks
        if task["due_date"] == today
        and not task["completed"]
    ]

    if today_tasks:

        st.subheader("⏰ Today's Tasks")

        for task in today_tasks:

            scheduled = task.get(
                "scheduled_time"
            )

            if scheduled:

                st.info(
                    f"⏰ {scheduled} — "
                    f"**{task['title']}**"
                )

            else:

                st.info(
                    f"📋 **{task['title']}**"
                )


# ==================================================
# TASK PAGE
# ==================================================

def task_page():

    user_id = st.session_state.user["id"]

    # Refresh every 30 seconds.
    # This lets the app detect task reminder times
    # while the page is open.
    st_autorefresh(
        interval=30000,
        key="task_auto_refresh"
    )

    tasks = get_tasks(user_id)

    st.title("📋 My Tasks")

    # ==================================================
    # CURRENT STREAK / CHECK-IN
    # ==================================================

    current_streak = get_streak(user_id)

    activity_dates = get_activity_dates(user_id)

    today = date.today().isoformat()

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "🔥 Current Streak",
            current_streak
        )

    with col2:

        if today not in activity_dates:

            if st.button(
                "🔥 CHECK IN TODAY",
                use_container_width=True
            ):

                check_in(user_id)

                st.success(
                    "🔥 Today's check-in completed!"
                )

                st.rerun()

        else:

            st.success(
                "✅ You already checked in today."
            )

    st.divider()

    # ==================================================
    # TIME REMINDERS
    # ==================================================

    now = datetime.now()

    current_date = now.date()
    current_time = now.time()

    reminder_tasks = []

    for task in tasks:

        if task["completed"]:
            continue

        if not task["due_date"]:
            continue

        if not task["scheduled_time"]:
            continue

        try:

            task_date = datetime.strptime(
                task["due_date"],
                "%Y-%m-%d"
            ).date()

            task_time = datetime.strptime(
                task["scheduled_time"],
                "%H:%M"
            ).time()

        except:

            continue

        if task_date == current_date:

            # Reminder becomes active when
            # current time reaches scheduled time.

            if current_time >= task_time:

                reminder_tasks.append(task)

    if reminder_tasks:

        st.subheader("🔔 REMINDERS")

        for task in reminder_tasks:

            if task["location_required"]:

                st.warning(
                    f"🏋️ **Time to go to "
                    f"{task['title']}!**"
                )

            else:

                st.warning(
                    f"⏰ **Time for "
                    f"{task['title']}!**"
                )

    # ==================================================
    # ADD TASK
    # ==================================================

    with st.expander(
        "➕ Add New Task",
        expanded=False
    ):

        title = st.text_input(
            "Task Title",
            placeholder="Example: Go to Gym"
        )

        company = st.text_input(
            "Company",
            placeholder="Example: TCS"
        )

        role = st.text_input(
            "Role",
            placeholder="Example: Software Developer"
        )

        description = st.text_area(
            "Description"
        )

        task_date = st.date_input(
            "Task Date",
            value=date.today()
        )

        task_time = st.time_input(
            "Task Time",
            value=time(18, 0)
        )

        st.subheader(
            "📍 Location Verification"
        )

        location_required = st.checkbox(
            "Require location check-in"
        )

        location_name = ""
        latitude = None
        longitude = None
        radius = 200.0

        if location_required:

            location_name = st.text_input(
                "Location Name",
                placeholder="Example: My Gym"
            )

            st.write(
                "Enter the location's "
                "latitude and longitude."
            )

            col1, col2 = st.columns(2)

            with col1:

                latitude = st.number_input(
                    "Latitude",
                    format="%.7f",
                    value=0.0
                )

            with col2:

                longitude = st.number_input(
                    "Longitude",
                    format="%.7f",
                    value=0.0
                )

            radius = st.number_input(
                "Allowed Radius (meters)",
                min_value=10.0,
                max_value=5000.0,
                value=200.0,
                step=10.0
            )

            st.caption(
                "Example: 200 meters means you "
                "must be within 200 m of the location."
            )

        if st.button(
            "➕ Add Task",
            use_container_width=True
        ):

            if not title.strip():

                st.error(
                    "Please enter a task title."
                )

            elif location_required and (
                latitude == 0.0
                or longitude == 0.0
            ):

                st.error(
                    "Please enter valid latitude "
                    "and longitude."
                )

            else:

                add_task(
                    user_id=user_id,
                    title=title,
                    company=company,
                    role=role,
                    description=description,
                    due_date=task_date.isoformat(),
                    scheduled_time=task_time.strftime(
                        "%H:%M"
                    ),
                    location_name=location_name,
                    location_lat=latitude,
                    location_lon=longitude,
                    location_radius=radius,
                    location_required=1
                    if location_required
                    else 0
                )

                st.success(
                    "✅ Task added successfully!"
                )

                st.rerun()

    st.divider()

    # ==================================================
    # PENDING TASKS
    # ==================================================

    pending_tasks = [
        task
        for task in tasks
        if not task["completed"]
    ]

    st.subheader(
        f"⏳ Pending Tasks ({len(pending_tasks)})"
    )

    if not pending_tasks:

        st.success(
            "🎉 No pending tasks!"
        )

    else:

        for task in pending_tasks:

            with st.container(border=True):

                col1, col2 = st.columns(
                    [4, 1]
                )

                with col1:

                    st.markdown(
                        f"### 📋 {task['title']}"
                    )

                    if task["company"]:

                        st.write(
                            f"🏢 Company: "
                            f"{task['company']}"
                        )

                    if task["role"]:

                        st.write(
                            f"💼 Role: "
                            f"{task['role']}"
                        )

                    if task["description"]:

                        st.write(
                            task["description"]
                        )

                    st.write(
                        f"📅 Date: "
                        f"{task['due_date']}"
                    )

                    if task["scheduled_time"]:

                        st.write(
                            f"⏰ Time: "
                            f"{task['scheduled_time']}"
                        )

                    if task["location_required"]:

                        st.write(
                            f"📍 Location: "
                            f"{task['location_name']}"
                        )

                        st.write(
                            f"📏 Required radius: "
                            f"{task['location_radius']} m"
                        )

                with col2:

                    # ----------------------------------
                    # NORMAL TASK
                    # ----------------------------------

                    if not task["location_required"]:

                        if st.button(
                            "✅ Complete",
                            key=f"complete_{task['id']}",
                            use_container_width=True
                        ):

                            complete_task(
                                task["id"],
                                user_id
                            )

                            st.success(
                                "Task completed!"
                            )

                            st.rerun()

                    # ----------------------------------
                    # LOCATION TASK
                    # ----------------------------------

                    else:

                        if st.button(
                            "📍 CHECK IN",
                            key=f"location_{task['id']}",
                            use_container_width=True
                        ):
                            st.session_state.gps_check_task_id = task["id"]
                            st.rerun()

                            st.info(
                                "📡 Getting your location..."
                            )

                            location = get_geolocation()

                            # --------------------------
                            # LOCATION ERROR
                            # --------------------------

                            if (
                                location
                                and "error" in location
                            ):

                                error_code = location[
                                    "error"
                                ].get("code")

                                error_message = location[
                                    "error"
                                ].get("message")

                                if error_code == 1:

                                    st.error(
                                        "❌ Location permission "
                                        "was denied."
                                    )

                                else:

                                    st.error(
                                        f"❌ GPS Error: "
                                        f"{error_message}"
                                    )

                            # --------------------------
                            # LOCATION SUCCESS
                            # --------------------------

                            elif location:

                                user_lat = location[
                                    "coords"
                                ]["latitude"]

                                user_lon = location[
                                    "coords"
                                ]["longitude"]

                                task_lat = task[
                                    "location_lat"
                                ]

                                task_lon = task[
                                    "location_lon"
                                ]

                                radius = task[
                                    "location_radius"
                                ]

                                distance = calculate_distance(
                                    user_lat,
                                    user_lon,
                                    task_lat,
                                    task_lon
                                )

                                st.write(
                                    f"📍 Your latitude: "
                                    f"`{user_lat:.6f}`"
                                )

                                st.write(
                                    f"📍 Your longitude: "
                                    f"`{user_lon:.6f}`"
                                )

                                st.write(
                                    f"📏 Distance from "
                                    f"{task['location_name']}: "
                                    f"`{distance:.2f} m`"
                                )

                                if distance <= radius:

                                    mark_task_location_verified(
                                        task["id"],
                                        user_id
                                    )

                                    st.success(
                                        f"✅ You reached "
                                        f"{task['location_name']}!"
                                    )

                                    st.success(
                                        "🎉 Task completed."
                                    )

                                    st.rerun()

                                else:

                                    st.error(
                                        f"❌ You haven't "
                                        f"reached "
                                        f"{task['location_name']} yet."
                                    )

                                    st.warning(
                                        f"You are "
                                        f"{distance:.0f} m away."
                                    )

                                    st.info(
                                        f"You need to be "
                                        f"within {radius:.0f} m."
                                    )

                    # ----------------------------------
                    # DELETE
                    # ----------------------------------

                    if st.button(
                        "🗑️ Delete",
                        key=f"delete_{task['id']}",
                        use_container_width=True
                    ):

                        delete_task(
                            task["id"],
                            user_id
                        )

                        st.rerun()

    # ==================================================
    # COMPLETED TASKS
    # ==================================================

    st.divider()

    completed_tasks = [
        task
        for task in tasks
        if task["completed"]
    ]

    st.subheader(
        f"✅ Completed Tasks ({len(completed_tasks)})"
    )

    if not completed_tasks:

        st.info(
            "No completed tasks yet."
        )

    else:

        for task in completed_tasks:

            with st.container(border=True):

                st.markdown(
                    f"### ✅ {task['title']}"
                )

                if task["company"]:

                    st.write(
                        f"🏢 {task['company']}"
                    )

                if task["due_date"]:

                    st.write(
                        f"📅 {task['due_date']}"
                    )

                if task["scheduled_time"]:

                    st.write(
                        f"⏰ {task['scheduled_time']}"
                    )

                if task["location_verified"]:

                    st.success(
                        "📍 Location verified"
                    )

                    if task["checkin_time"]:

                        st.caption(
                            f"Checked in: "
                            f"{task['checkin_time']}"
                        )
# ==================================================
# GPS LOCATION CHECK
# ==================================================
    gps_task_id = st.session_state.get(
        "gps_check_task_id"
)
    gps_task=None
    if gps_task_id:

        gps_task = get_task(
        gps_task_id,
        user_id
    )

    if gps_task:

        st.divider()

        st.subheader(
            f"📍 Checking location for: {gps_task['title']}"
        )

        st.info(
            "📡 Getting your current location..."
        )

        location = get_geolocation(
            component_key=f"getLocation_{gps_task_id}"
        )

        # ------------------------------------------
        # WAITING FOR LOCATION
        # ------------------------------------------

        if location is None:

            st.warning(
                "⏳ Waiting for GPS location..."
            )

            st.info(
                "Please allow location permission "
                "in your browser."
            )

        # ------------------------------------------
        # GPS ERROR
        # ------------------------------------------

        elif "error" in location:

            error = location["error"]

            error_code = error.get("code")
            error_message = error.get("message")

            if error_code == 1:

                st.error(
                    "❌ Location permission was denied."
                )

                st.info(
                    "Click the 🔒 icon near the website "
                    "address in Chrome and allow Location."
                )

            elif error_code == 2:

                st.error(
                    "❌ Your location could not be determined."
                )

            elif error_code == 3:

                st.error(
                    "❌ GPS request timed out."
                )

            else:

                st.error(
                    f"❌ GPS Error: {error_message}"
                )

            if st.button(
                "❌ Cancel GPS Check",
                key="cancel_gps"
            ):

                st.session_state.gps_check_task_id = None

                st.rerun()

        # ------------------------------------------
        # GPS SUCCESS
        # ------------------------------------------

        elif "coords" in location:

            user_lat = location["coords"]["latitude"]

            user_lon = location["coords"]["longitude"]

            task_lat = gps_task["location_lat"]

            task_lon = gps_task["location_lon"]

            radius = gps_task["location_radius"]

            # --------------------------------------
            # CALCULATE DISTANCE
            # --------------------------------------

            distance = calculate_distance(
                user_lat,
                user_lon,
                task_lat,
                task_lon
            )

            st.success(
                "📍 Location received successfully!"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Your Latitude",
                    f"{user_lat:.6f}"
                )

            with col2:

                st.metric(
                    "Your Longitude",
                    f"{user_lon:.6f}"
                )

            st.write(
                f"📍 **Destination:** "
                f"{gps_task['location_name']}"
            )

            st.write(
                f"📏 **Distance:** "
                f"{distance:.2f} meters"
            )

            st.write(
                f"🎯 **Allowed radius:** "
                f"{radius:.0f} meters"
            )

            # --------------------------------------
            # USER IS AT LOCATION
            # --------------------------------------

            if distance <= radius:

                mark_task_location_verified(
                    gps_task["id"],
                    user_id
                    
                )

                st.success(
                    f"✅ You reached "
                    f"**{gps_task['location_name']}**!"
                )

                st.success(
                    "🎉 Task completed successfully!"
                )

                st.session_state.gps_check_task_id = None

                st.rerun()

            # --------------------------------------
            # USER IS NOT AT LOCATION
            # --------------------------------------

            else:

                st.error(
                    f"❌ You haven't reached "
                    f"**{gps_task['location_name']}** yet."
                )

                st.warning(
                    f"You are approximately "
                    f"**{distance:.0f} meters** away."
                )

                st.info(
                    f"You need to be within "
                    f"**{radius:.0f} meters**."
                )

                if st.button(
                    "🔄 Check Location Again",
                    key="retry_gps"
                ):

                    st.rerun()

                if st.button(
                    "❌ Cancel",
                    key="cancel_gps_success"
                ):

                    st.session_state.gps_check_task_id = None

                    st.rerun()

st.divider()

st.subheader("🧪 GPS Test")

if st.button("📍 Test My Location"):

    st.session_state.test_gps = True
    st.rerun()


if st.session_state.get("test_gps", False):

    location = get_geolocation()

    if location is None:

        st.info(
            "⏳ Waiting for location..."
        )

    elif "error" in location:

        st.error(
            location["error"]["message"]
        )

    elif "coords" in location:

        lat = location["coords"]["latitude"]
        lon = location["coords"]["longitude"]

        st.success(
            "✅ GPS working!"
        )

        st.write(
            f"Latitude: `{lat}`"
        )

        st.write(
            f"Longitude: `{lon}`"
        )
# ==================================================
# NOTES PAGE
# ==================================================

def notes_page():

    user_id = st.session_state.user["id"]

    st.title("📝 Job Notes")

    notes = get_all_notes(user_id)

    # ----------------------------------------------
    # ADD NOTE
    # ----------------------------------------------

    tasks = get_tasks(user_id)

    with st.expander(
        "➕ Add Note"
    ):

        if not tasks:

            st.info(
                "Create a task first."
            )

        else:

            task_options = {
                f"{task['title']} "
                f"({task['company'] or 'No company'})":
                task["id"]

                for task in tasks
            }

            selected_task = st.selectbox(
                "Select Task",
                list(task_options.keys())
            )

            note_content = st.text_area(
                "Write your note"
            )

            if st.button(
                "Save Note",
                use_container_width=True
            ):

                if note_content.strip():

                    add_note(
                        task_options[selected_task],
                        note_content
                    )

                    st.success(
                        "📝 Note saved!"
                    )

                    st.rerun()

                else:

                    st.warning(
                        "Please enter a note."
                    )

    st.divider()

    # ----------------------------------------------
    # GROUP NOTES BY DATE
    # ----------------------------------------------

    if not notes:

        st.info(
            "No notes yet."
        )

        return

    grouped_notes = {}

    for note in notes:

        created_at = note["created_at"]

        try:

            note_date = datetime.strptime(
                created_at[:10],
                "%Y-%m-%d"
            ).date()

        except:

            note_date = date.today()

        grouped_notes.setdefault(
            note_date,
            []
        ).append(note)

    for note_date in sorted(
        grouped_notes.keys(),
        reverse=True
    ):

        st.subheader(
            f"📅 {note_date.strftime('%d %B %Y')}"
        )

        for note in grouped_notes[note_date]:

            with st.container(border=True):

                st.markdown(
                    f"### 📌 {note['title']}"
                )

                if note["company"]:

                    st.write(
                        f"🏢 {note['company']}"
                    )

                if note["role"]:

                    st.write(
                        f"💼 {note['role']}"
                    )

                st.write(
                    note["content"]
                )

                st.caption(
                    f"🕒 {note['created_at']}"
                )

                if st.button(
                    "🗑️ Delete Note",
                    key=f"delete_note_{note['id']}"
                ):

                    delete_note(
                        note["id"]
                    )

                    st.rerun()


# ==================================================
# STREAK PAGE
# ==================================================

def streak_page():

    user_id = st.session_state.user["id"]

    current_streak = get_streak(user_id)

    longest_streak = get_longest_streak(user_id)

    st.title("🔥 Streak")

    st.write(
        "Complete your daily activity and "
        "build your 100-day streak."
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "🔥 Current Streak",
            current_streak
        )

    with col2:

        st.metric(
            "🏆 Longest Streak",
            longest_streak
        )

    with col3:

        st.metric(
            "🎯 Goal",
            "100 Days"
        )

    st.divider()

    progress = min(
        current_streak / 100,
        1.0
    )

    st.progress(progress)

    st.write(
        f"**{current_streak} / 100 days completed**"
    )

    st.divider()

    # ----------------------------------------------
    # 100 BOXES
    # ----------------------------------------------

    st.subheader(
        "📅 100 Day Streak"
    )

    for row_start in range(1, 101, 10):

        columns = st.columns(10)

        for index, day in enumerate(
            range(
                row_start,
                min(row_start + 10, 101)
            )
        ):

            with columns[index]:

                if day <= current_streak:

                    background = "#22c55e"
                    text_color = "white"

                elif day == current_streak + 1:

                    background = "#3b82f6"
                    text_color = "white"

                else:

                    background = "#1f2937"
                    text_color = "#9ca3af"

                st.markdown(
                    f"""
                    <div style="
                        background:{background};
                        color:{text_color};
                        height:60px;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        border-radius:10px;
                        margin-bottom:10px;
                        font-size:20px;
                        font-weight:bold;
                    ">
                        {day}
                    </div>
                    """,
                    unsafe_allow_html=True
                )


# ==================================================
# MAIN APP
# ==================================================

if not st.session_state.logged_in:

    authentication_page()

else:

    sidebar()

    if st.session_state.page == "Dashboard":

        dashboard()

    elif st.session_state.page == "My Tasks":

        task_page()

    elif st.session_state.page == "Job Notes":

        notes_page()

    elif st.session_state.page == "Streak":

        streak_page()