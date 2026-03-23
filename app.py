import streamlit as st
import random
import json
import os
from datetime import datetime

# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------
st.set_page_config(page_title="Study Planner", page_icon="📚", layout="wide")

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%);
    }

    .main-title {
        font-size: 2.6rem;
        font-weight: 800;
        color: #1f2d3d;
        margin-bottom: 0.15rem;
    }

    .subtitle {
        color: #5b6b7a;
        font-size: 1rem;
        margin-bottom: 1.2rem;
    }

    .pretty-card {
        background: white;
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 0 8px 24px rgba(31, 45, 61, 0.08);
        border: 1px solid #e8eef7;
        margin-bottom: 16px;
    }

    .course-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1f2d3d;
        margin-bottom: 8px;
    }

    .small-text {
        color: #607080;
        font-size: 0.95rem;
        margin: 4px 0;
    }

    .metric-box {
        background: white;
        border-radius: 16px;
        padding: 14px 16px;
        box-shadow: 0 6px 20px rgba(31, 45, 61, 0.06);
        border: 1px solid #e8eef7;
        text-align: center;
        margin-bottom: 10px;
    }

    .metric-label {
        font-size: 0.9rem;
        color: #6b7c8d;
        margin-bottom: 6px;
    }

    .metric-value {
        font-size: 1.55rem;
        font-weight: 800;
        color: #1f2d3d;
    }

    .day-box {
        background: white;
        border-radius: 16px;
        padding: 14px;
        min-height: 160px;
        box-shadow: 0 6px 20px rgba(31, 45, 61, 0.05);
        border: 1px solid #e8eef7;
        margin-bottom: 16px;
    }

    .day-title {
        font-size: 1rem;
        font-weight: 700;
        color: #1f2d3d;
        margin-bottom: 10px;
    }

    .block-pill {
        border-radius: 10px;
        padding: 8px 10px;
        color: white;
        font-size: 0.88rem;
        font-weight: 600;
        margin-bottom: 8px;
    }

    .task-soon {
        border-left: 8px solid #ef4444 !important;
        background: #fff7f7 !important;
    }

    .task-medium {
        border-left: 8px solid #f59e0b !important;
        background: #fffaf2 !important;
    }

    .task-normal {
        border-left: 8px solid #6366f1 !important;
        background: #ffffff !important;
    }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #334155 100%);
    }

    div[data-testid="stSidebar"] * {
        color: white !important;
    }

    .stButton > button {
        border-radius: 12px;
        border: none;
        background: linear-gradient(90deg, #4f46e5, #7c3aed);
        color: white;
        font-weight: 600;
        padding: 0.6rem 1rem;
    }

    .stButton > button:hover {
        background: linear-gradient(90deg, #4338ca, #6d28d9);
        color: white;
    }

    .stDownloadButton > button {
        border-radius: 12px;
        border: none;
        background: linear-gradient(90deg, #0f766e, #0891b2);
        color: white;
        font-weight: 600;
        padding: 0.6rem 1rem;
    }

    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea {
        border-radius: 12px !important;
    }

    div[data-baseweb="select"] > div {
        border-radius: 12px !important;
    }

    .section-gap {
        margin-top: 0.6rem;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------
GOOGLE_COLORS = {
    "Tomato Red": "#D50000",
    "Orange": "#F4511E",
    "Yellow": "#F6BF26",
    "Green": "#0B8043",
    "Mint": "#33B679",
    "Blue": "#039BE5",
    "Lavender": "#7986CB",
    "Purple": "#8E24AA"
}

VALID_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
VALID_STATUSES = ["not started", "in progress", "done"]
VALID_PRIORITIES = ["low", "medium", "high"]

MIN_STUDY = 1
MAX_STUDY = 40
DATA_FILE = "study_planner_data.json"

# --------------------------------------------------
# DATA HELPERS
# --------------------------------------------------
def save_data():
    data = {
        "courses": st.session_state.courses,
        "used_colors": st.session_state.used_colors
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("courses", []), data.get("used_colors", [])
        except Exception:
            return [], []
    return [], []

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "initialized" not in st.session_state:
    loaded_courses, loaded_used_colors = load_data()
    st.session_state.courses = loaded_courses
    st.session_state.used_colors = loaded_used_colors
    st.session_state.initialized = True

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def safe_time_input(t):
    t = t.strip().lower()
    try:
        hour = int(t[:-2])
        if hour < 1 or hour > 12:
            raise ValueError

        if "pm" in t and hour != 12:
            hour += 12
        if "am" in t and hour == 12:
            hour = 0
        return hour
    except Exception:
        return None

def format_time(h):
    suffix = "am" if h < 12 else "pm"
    hh = h % 12
    if hh == 0:
        hh = 12
    return f"{hh}{suffix}"

def parse_time_blocks(block_text):
    blocks = []
    if not block_text.strip():
        return blocks

    for line in block_text.strip().splitlines():
        line = line.strip().lower()
        if not line:
            continue
        try:
            start_str, end_str = line.split("-")
            start = safe_time_input(start_str.strip())
            end = safe_time_input(end_str.strip())

            if start is None or end is None:
                continue
            if end <= start:
                continue

            blocks.append((start, end))
        except Exception:
            continue
    return blocks

def allocate_study_hours(days, time_blocks, study_hours):
    assigned = {}
    remaining = study_hours

    for d in days:
        assigned[d] = []
        for start, end in time_blocks.get(d, []):
            if remaining <= 0:
                break

            available = end - start
            used = min(available, remaining)
            remaining -= used
            assigned_end = start + used
            assigned[d].append(f"{format_time(start)} - {format_time(assigned_end)}")

        if remaining <= 0:
            break

    return assigned, remaining

def calculate_recommended_study(lecture_hours, difficulty):
    study_hours = lecture_hours * 2
    if difficulty == "easy":
        study_hours -= 1
    elif difficulty == "hard":
        study_hours += 2
    study_hours = max(MIN_STUDY, min(MAX_STUDY, study_hours))
    return study_hours

def get_unused_color():
    color_list = list(GOOGLE_COLORS.items())
    available = [(name, hex_code) for name, hex_code in color_list if hex_code not in st.session_state.used_colors]

    if available:
        color_name, hex_code = random.choice(available)
        st.session_state.used_colors.append(hex_code)
        return color_name, hex_code
    return random.choice(color_list)

def get_all_tasks():
    all_tasks = []
    for ci, course in enumerate(st.session_state.courses):
        for ti, task in enumerate(course["tasks"]):
            all_tasks.append((ci, ti, course, task))
    return all_tasks

def delete_course(index):
    hex_code = st.session_state.courses[index]["hex_code"]
    if hex_code in st.session_state.used_colors:
        st.session_state.used_colors.remove(hex_code)
    st.session_state.courses.pop(index)
    save_data()

def get_task_counts():
    tasks = get_all_tasks()
    total = len(tasks)
    done = sum(1 for _, _, _, t in tasks if t["status"] == "done")
    in_progress = sum(1 for _, _, _, t in tasks if t["status"] == "in progress")
    not_started = sum(1 for _, _, _, t in tasks if t["status"] == "not started")
    return total, done, in_progress, not_started

def get_priority_score(priority):
    order = {"high": 0, "medium": 1, "low": 2}
    return order.get(priority, 3)

def sort_tasks(tasks):
    return sorted(tasks, key=lambda x: (get_priority_score(x[3]["size"]), x[3]["status"], str(x[3]["due"]).lower()))

def course_completion(course):
    total = len(course["tasks"])
    if total == 0:
        return 0
    done = sum(1 for t in course["tasks"] if t["status"] == "done")
    return done / total

def render_course_card(course):
    progress = int(course_completion(course) * 100)
    st.markdown(
        f"""
        <div class="pretty-card" style="border-left: 10px solid {course['hex_code']};">
            <div class="course-title">{course['name']}</div>
            <div class="small-text"><strong>Difficulty:</strong> {course['difficulty'].title()}</div>
            <div class="small-text"><strong>Study Hours:</strong> {course['study']} hrs/week</div>
            <div class="small-text"><strong>Target Grade:</strong> {course['target_grade']}%</div>
            <div class="small-text"><strong>Course Color:</strong> {course['color_name']}</div>
            <div class="small-text"><strong>Task Completion:</strong> {progress}%</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.progress(progress / 100 if progress > 0 else 0)

def parse_due_date(date_str):
    if not date_str or not str(date_str).strip():
        return None

    patterns = [
        "%Y-%m-%d",
        "%B %d",
        "%b %d",
        "%B %d %Y",
        "%b %d %Y",
        "%m/%d/%Y",
        "%m/%d/%y"
    ]

    for pattern in patterns:
        try:
            dt = datetime.strptime(str(date_str).strip(), pattern)
            if "%Y" not in pattern:
                dt = dt.replace(year=datetime.today().year)
            return dt.date()
        except Exception:
            continue
    return None

def days_until_due(date_str):
    due_date = parse_due_date(date_str)
    if due_date is None:
        return None
    today = datetime.today().date()
    return (due_date - today).days

def get_task_urgency_class(task):
    d = days_until_due(task["due"])
    if d is None:
        return "task-normal"
    if d <= 3:
        return "task-soon"
    if d <= 7:
        return "task-medium"
    return "task-normal"

def urgency_label(task):
    d = days_until_due(task["due"])
    if d is None:
        return "Date not parsed"
    if d < 0:
        return f"Overdue by {abs(d)} day(s)"
    if d == 0:
        return "Due today"
    return f"Due in {d} day(s)"

def build_weekly_calendar():
    calendar = {day: [] for day in VALID_DAYS}
    for course in st.session_state.courses:
        for day, blocks in course["assigned"].items():
            for block in blocks:
                calendar[day].append({
                    "course": course["name"],
                    "time": block,
                    "color": course["hex_code"]
                })
    return calendar

def export_data_json():
    data = {
        "courses": st.session_state.courses,
        "used_colors": st.session_state.used_colors
    }
    return json.dumps(data, indent=2)

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown('<div class="main-title">📚 Study Planner</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Plan courses, track assignments, and build a personalized weekly study schedule.</div>',
    unsafe_allow_html=True
)

total_tasks, done_tasks, in_progress_tasks, not_started_tasks = get_task_counts()

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">Courses</div>
        <div class="metric-value">{len(st.session_state.courses)}</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">Total Tasks</div>
        <div class="metric-value">{total_tasks}</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">Completed</div>
        <div class="metric-value">{done_tasks}</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">In Progress</div>
        <div class="metric-value">{in_progress_tasks}</div>
    </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
section = st.sidebar.radio(
    "Navigate",
    [
        "Dashboard",
        "Add Course",
        "View Weekly Schedule",
        "View Day Schedule",
        "Edit Courses",
        "Assignments",
        "Data"
    ]
)

st.sidebar.markdown("---")

if st.sidebar.button("Save Data"):
    save_data()
    st.sidebar.success("Saved successfully.")

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
if section == "Dashboard":
    st.markdown("## Dashboard")

    if not st.session_state.courses:
        st.info("No courses added yet.")
    else:
        left, right = st.columns([1.1, 1])

        with left:
            st.markdown("### Course Overview")
            for course in st.session_state.courses:
                render_course_card(course)

        with right:
            st.markdown("### Weekly Calendar")
            weekly_calendar = build_weekly_calendar()

            day_cols_top = st.columns(4)
            for i, day in enumerate(VALID_DAYS[:4]):
                with day_cols_top[i]:
                    st.markdown(f'<div class="day-box"><div class="day-title">{day}</div>', unsafe_allow_html=True)
                    if weekly_calendar[day]:
                        for item in weekly_calendar[day]:
                            st.markdown(
                                f'<div class="block-pill" style="background:{item["color"]};">{item["course"]}<br>{item["time"]}</div>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown('<div class="small-text">No blocks</div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

            day_cols_bottom = st.columns(3)
            for i, day in enumerate(VALID_DAYS[4:]):
                with day_cols_bottom[i]:
                    st.markdown(f'<div class="day-box"><div class="day-title">{day}</div>', unsafe_allow_html=True)
                    if weekly_calendar[day]:
                        for item in weekly_calendar[day]:
                            st.markdown(
                                f'<div class="block-pill" style="background:{item["color"]};">{item["course"]}<br>{item["time"]}</div>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown('<div class="small-text">No blocks</div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### Priority / Upcoming Tasks")
        all_tasks = sort_tasks(get_all_tasks())

        if not all_tasks:
            st.info("No tasks added yet.")
        else:
            for _, _, course, task in all_tasks:
                urgency_class = get_task_urgency_class(task)
                st.markdown(
                    f"""
                    <div class="pretty-card {urgency_class}">
                        <div class="course-title">{task['title']}</div>
                        <div class="small-text"><strong>Course:</strong> {course['name']}</div>
                        <div class="small-text"><strong>Type:</strong> {task['type']}</div>
                        <div class="small-text"><strong>Due:</strong> {task['due']}</div>
                        <div class="small-text"><strong>Urgency:</strong> {urgency_label(task)}</div>
                        <div class="small-text"><strong>Weight:</strong> {task['weight']}%</div>
                        <div class="small-text"><strong>Priority:</strong> {task['size'].title()}</div>
                        <div class="small-text"><strong>Status:</strong> {task['status'].title()}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# --------------------------------------------------
# ADD COURSE
# --------------------------------------------------
elif section == "Add Course":
    st.markdown("## Add Course")

    with st.form("add_course_form"):
        name = st.text_input("Course name")
        lecture_hours = st.number_input("Lecture hours this week", min_value=0, max_value=40, step=1)
        difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
        target_grade = st.number_input("Target final grade", min_value=0.0, max_value=100.0, step=1.0)

        recommended_study = calculate_recommended_study(lecture_hours, difficulty)
        st.info(f"Recommended study hours per week: {recommended_study}")

        override = st.checkbox("Change recommended study hours?")
        if override:
            study_hours = st.number_input("Preferred study hours per week", min_value=MIN_STUDY, max_value=MAX_STUDY, value=recommended_study, step=1)
        else:
            study_hours = recommended_study

        days = st.multiselect("Choose study days", VALID_DAYS)

        st.markdown("### Time windows")
        st.caption("For each selected day, enter one block per line, like: 4pm-6pm")

        time_blocks_text = {}
        for d in days:
            time_blocks_text[d] = st.text_area(f"{d} time windows", placeholder="4pm-6pm\n7pm-9pm", key=f"block_{d}")

        st.markdown("### Add tasks now (optional)")
        num_tasks = st.number_input("How many tasks do you want to add now?", min_value=0, max_value=10, step=1, value=0)

        tasks = []
        for i in range(num_tasks):
            st.markdown(f"**Task {i+1}**")
            c1, c2 = st.columns(2)
            with c1:
                title = st.text_input(f"Task title {i+1}", key=f"title_{i}")
                task_type = st.text_input(f"Task type {i+1}", key=f"type_{i}", placeholder="quiz, midterm, essay, lab report")
                due = st.text_input(f"Due date {i+1}", key=f"due_{i}", placeholder="2026-04-02 or April 2")
            with c2:
                weight = st.number_input(f"Weight % {i+1}", min_value=0.0, max_value=100.0, step=1.0, key=f"weight_{i}")
                priority = st.selectbox(f"Priority {i+1}", VALID_PRIORITIES, key=f"priority_{i}")
                status = st.selectbox(f"Status {i+1}", ["not started", "in progress"], key=f"status_{i}")

            tasks.append({
                "title": title,
                "type": task_type,
                "due": due,
                "size": priority,
                "weight": weight,
                "status": status
            })

        submitted = st.form_submit_button("Add Course")

    if submitted:
        if not name.strip():
            st.error("Please enter a course name.")
        elif not days:
            st.error("Please select at least one study day.")
        else:
            time_blocks = {}
            for d in days:
                time_blocks[d] = parse_time_blocks(time_blocks_text[d])

            color_name, hex_code = get_unused_color()
            assigned, remaining = allocate_study_hours(days, time_blocks, study_hours)

            course = {
                "name": name,
                "lecture": lecture_hours,
                "study": study_hours,
                "difficulty": difficulty,
                "target_grade": target_grade,
                "days": days,
                "time_blocks": time_blocks,
                "assigned": assigned,
                "color_name": color_name,
                "hex_code": hex_code,
                "tasks": tasks
            }

            st.session_state.courses.append(course)
            save_data()
            st.success(f"{name} added successfully.")

            if remaining > 0:
                st.warning(
                    f"Only {study_hours - remaining} of {study_hours} study hours fit into your time windows."
                )

# --------------------------------------------------
# VIEW WEEKLY SCHEDULE
# --------------------------------------------------
elif section == "View Weekly Schedule":
    st.markdown("## Weekly Schedule")

    if not st.session_state.courses:
        st.info("No courses added yet.")
    else:
        weekly_calendar = build_weekly_calendar()
        top = st.columns(4)
        for i, day in enumerate(VALID_DAYS[:4]):
            with top[i]:
                st.markdown(f'<div class="day-box"><div class="day-title">{day}</div>', unsafe_allow_html=True)
                if weekly_calendar[day]:
                    for item in weekly_calendar[day]:
                        st.markdown(
                            f'<div class="block-pill" style="background:{item["color"]};">{item["course"]}<br>{item["time"]}</div>',
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown('<div class="small-text">No study blocks</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        bottom = st.columns(3)
        for i, day in enumerate(VALID_DAYS[4:]):
            with bottom[i]:
                st.markdown(f'<div class="day-box"><div class="day-title">{day}</div>', unsafe_allow_html=True)
                if weekly_calendar[day]:
                    for item in weekly_calendar[day]:
                        st.markdown(
                            f'<div class="block-pill" style="background:{item["color"]};">{item["course"]}<br>{item["time"]}</div>',
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown('<div class="small-text">No study blocks</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### Course Details")
        for course in st.session_state.courses:
            render_course_card(course)

# --------------------------------------------------
# VIEW DAY SCHEDULE
# --------------------------------------------------
elif section == "View Day Schedule":
    st.markdown("## Schedule by Day")
    selected_day = st.selectbox("Choose a day", VALID_DAYS)

    found = False
    for course in st.session_state.courses:
        blocks = course["assigned"].get(selected_day, [])
        if blocks:
            found = True
            st.markdown(
                f"""
                <div class="pretty-card" style="border-left: 8px solid {course['hex_code']};">
                    <div class="course-title">{course['name']}</div>
                    <div class="small-text"><strong>{selected_day}:</strong> {", ".join(blocks)}</div>
                    <div class="small-text"><strong>Difficulty:</strong> {course['difficulty'].title()}</div>
                    <div class="small-text"><strong>Target Grade:</strong> {course['target_grade']}%</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    if not found:
        st.info("No study blocks scheduled for this day.")

# --------------------------------------------------
# EDIT COURSES
# --------------------------------------------------
elif section == "Edit Courses":
    st.markdown("## Edit Courses")

    if not st.session_state.courses:
        st.info("No courses added yet.")
    else:
        course_names = [course["name"] for course in st.session_state.courses]
        selected_course_name = st.selectbox("Choose a course", course_names)
        course_index = course_names.index(selected_course_name)
        course = st.session_state.courses[course_index]

        render_course_card(course)

        with st.form("edit_course_form"):
            new_name = st.text_input("Course name", value=course["name"])
            new_lecture = st.number_input("Lecture hours", min_value=0, max_value=40, step=1, value=int(course["lecture"]))
            new_difficulty = st.selectbox(
                "Difficulty",
                ["easy", "medium", "hard"],
                index=["easy", "medium", "hard"].index(course["difficulty"])
            )
            new_target = st.number_input("Target grade", min_value=0.0, max_value=100.0, step=1.0, value=float(course["target_grade"]))
            new_study = st.number_input("Study hours per week", min_value=MIN_STUDY, max_value=MAX_STUDY, step=1, value=int(course["study"]))
            new_days = st.multiselect("Study days", VALID_DAYS, default=course["days"])

            st.markdown("### Edit time windows")
            new_time_blocks_text = {}
            for d in new_days:
                existing_text = ""
                if d in course["time_blocks"]:
                    existing_text = "\n".join([f"{format_time(start)}-{format_time(end)}" for start, end in course["time_blocks"][d]])
                new_time_blocks_text[d] = st.text_area(f"{d} time windows", value=existing_text, key=f"edit_{d}")

            save_changes = st.form_submit_button("Save Changes")

        if save_changes:
            new_time_blocks = {}
            for d in new_days:
                new_time_blocks[d] = parse_time_blocks(new_time_blocks_text[d])

            new_assigned, remaining = allocate_study_hours(new_days, new_time_blocks, new_study)

            st.session_state.courses[course_index]["name"] = new_name
            st.session_state.courses[course_index]["lecture"] = new_lecture
            st.session_state.courses[course_index]["difficulty"] = new_difficulty
            st.session_state.courses[course_index]["target_grade"] = new_target
            st.session_state.courses[course_index]["study"] = new_study
            st.session_state.courses[course_index]["days"] = new_days
            st.session_state.courses[course_index]["time_blocks"] = new_time_blocks
            st.session_state.courses[course_index]["assigned"] = new_assigned
            save_data()

            st.success("Course updated successfully.")
            if remaining > 0:
                st.warning(f"Only {new_study - remaining} of {new_study} study hours fit into your time windows.")

        if st.button("Delete This Course"):
            delete_course(course_index)
            st.success("Course deleted.")
            st.rerun()

# --------------------------------------------------
# ASSIGNMENTS
# --------------------------------------------------
elif section == "Assignments":
    st.markdown("## Assignments")

    if not st.session_state.courses:
        st.info("No courses added yet.")
    else:
        tab1, tab2 = st.tabs(["View / Update Tasks", "Add Task"])

        with tab1:
            all_tasks = sort_tasks(get_all_tasks())

            if not all_tasks:
                st.info("No assignments added yet.")
            else:
                for idx, (ci, ti, course, task) in enumerate(all_tasks):
                    urgency_class = get_task_urgency_class(task)

                    st.markdown(
                        f"""
                        <div class="pretty-card {urgency_class}">
                            <div class="course-title">{task['title']}</div>
                            <div class="small-text"><strong>Course:</strong> {course['name']}</div>
                            <div class="small-text"><strong>Type:</strong> {task['type']}</div>
                            <div class="small-text"><strong>Due:</strong> {task['due']}</div>
                            <div class="small-text"><strong>Urgency:</strong> {urgency_label(task)}</div>
                            <div class="small-text"><strong>Weight:</strong> {task['weight']}%</div>
                            <div class="small-text"><strong>Priority:</strong> {task['size'].title()}</div>
                            <div class="small-text"><strong>Status:</strong> {task['status'].title()}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    new_status = st.selectbox(
                        f"Change status for {task['title']}",
                        VALID_STATUSES,
                        index=VALID_STATUSES.index(task["status"]),
                        key=f"status_update_{idx}"
                    )

                    c1, c2 = st.columns(2)

                    with c1:
                        if st.button(f"Update {task['title']}", key=f"update_btn_{idx}"):
                            st.session_state.courses[ci]["tasks"][ti]["status"] = new_status
                            save_data()
                            st.success(f"Updated {task['title']} to {new_status}")
                            st.rerun()

                    with c2:
                        if st.button(f"Delete {task['title']}", key=f"delete_btn_{idx}"):
                            st.session_state.courses[ci]["tasks"].pop(ti)
                            save_data()
                            st.success(f"Deleted {task['title']}")
                            st.rerun()

        with tab2:
            course_names = [course["name"] for course in st.session_state.courses]
            selected_course_name = st.selectbox("Choose course", course_names, key="task_course")
            course_index = course_names.index(selected_course_name)

            with st.form("add_task_form"):
                title = st.text_input("Task title")
                task_type = st.text_input("Task type", placeholder="quiz, midterm, essay, lab report")
                due = st.text_input("Due date", placeholder="2026-04-02 or April 2")
                weight = st.number_input("Weight %", min_value=0.0, max_value=100.0, step=1.0)
                priority = st.selectbox("Priority", VALID_PRIORITIES)
                status = st.selectbox("Status", ["not started", "in progress"])

                add_task = st.form_submit_button("Add Task")

            if add_task:
                if not title.strip():
                    st.error("Please enter a task title.")
                else:
                    st.session_state.courses[course_index]["tasks"].append({
                        "title": title,
                        "type": task_type,
                        "due": due,
                        "size": priority,
                        "weight": weight,
                        "status": status
                    })
                    save_data()
                    st.success("Task added successfully.")

# --------------------------------------------------
# DATA
# --------------------------------------------------
elif section == "Data":
    st.markdown("## Data")

    st.write("Use these tools to export or reset your planner data.")

    export_str = export_data_json()
    st.download_button(
        label="Download planner data as JSON",
        data=export_str,
        file_name="study_planner_data.json",
        mime="application/json"
    )

    if st.button("Reset All Data"):
        st.session_state.courses = []
        st.session_state.used_colors = []
        save_data()
        st.success("All planner data was reset.")
        st.rerun()