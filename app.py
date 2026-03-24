import streamlit as st
import random
import json
import os
from datetime import datetime

st.set_page_config(page_title="Study Planner", layout="wide")

st.markdown("""
<style>
:root {
    --bg: #f7f7f5;
    --panel: #ffffff;
    --text: #1f1f1f;
    --muted: #666666;
    --line: #dddddd;
    --soft: #f1f1ee;
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg: #111111;
        --panel: #181818;
        --text: #f2f2f2;
        --muted: #b5b5b5;
        --line: #2b2b2b;
        --soft: #202020;
    }
}

.stApp {
    background: var(--bg);
}

.main-wrap {
    max-width: 1100px;
    margin: 0 auto;
}

.app-title {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.15rem;
}

.app-subtitle {
    color: var(--muted);
    font-size: 0.98rem;
    margin-bottom: 1.3rem;
}

.section-title {
    color: var(--text);
    font-size: 1.15rem;
    font-weight: 650;
    margin-top: 0.7rem;
    margin-bottom: 0.7rem;
}

.simple-box {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 14px 15px;
    margin-bottom: 12px;
}

.course-name {
    color: var(--text);
    font-weight: 700;
    font-size: 1rem;
    margin-bottom: 0.35rem;
}

.meta {
    color: var(--muted);
    font-size: 0.92rem;
    line-height: 1.55;
}

.day-box {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 12px;
    min-height: 130px;
    margin-bottom: 12px;
}

.day-title {
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.5rem;
    font-size: 0.98rem;
}

.schedule-row {
    padding: 7px 9px;
    border-left: 3px solid #888;
    background: var(--soft);
    margin-bottom: 7px;
    border-radius: 4px;
    color: var(--text);
    font-size: 0.9rem;
}

.task-box {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 14px 15px;
    margin-bottom: 12px;
}

.confirm-box {
    background: var(--soft);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 12px;
    margin-top: 8px;
    margin-bottom: 10px;
    color: var(--text);
}

.note {
    color: var(--muted);
    font-size: 0.9rem;
}

.small-stat {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 12px;
    margin-bottom: 10px;
}

.small-stat-label {
    color: var(--muted);
    font-size: 0.85rem;
}

.small-stat-value {
    color: var(--text);
    font-size: 1.3rem;
    font-weight: 700;
    margin-top: 0.15rem;
}

div[data-testid="stSidebar"] {
    background: var(--panel);
    border-right: 1px solid var(--line);
}

div[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

.stButton > button,
.stDownloadButton > button {
    border-radius: 8px;
    border: 1px solid var(--line);
    background: var(--panel);
    color: var(--text);
    font-weight: 600;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: #999;
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
div[data-baseweb="select"] > div {
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

GOOGLE_COLORS = {
    "Brick": "#b04a4a",
    "Cedar": "#8f5a3c",
    "Olive": "#7b8a46",
    "Forest": "#4f7a58",
    "Teal": "#3b7f7f",
    "Denim": "#4e6f99",
    "Indigo": "#5a5f9f",
    "Plum": "#7c5a7f",
}

VALID_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
VALID_STATUSES = ["not started", "in progress", "done"]
VALID_PRIORITIES = ["low", "medium", "high"]
MIN_STUDY = 1
MAX_STUDY = 40
DATA_FILE = "study_planner_data.json"


def save_data():
    data = {
        "courses": st.session_state.courses,
        "used_colors": st.session_state.used_colors,
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


if "initialized" not in st.session_state:
    loaded_courses, loaded_used_colors = load_data()
    st.session_state.courses = loaded_courses
    st.session_state.used_colors = loaded_used_colors
    st.session_state.initialized = True

if "confirm_reset" not in st.session_state:
    st.session_state.confirm_reset = False
if "confirm_delete_course" not in st.session_state:
    st.session_state.confirm_delete_course = None
if "confirm_delete_task" not in st.session_state:
    st.session_state.confirm_delete_task = None


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
            if start is None or end is None or end <= start:
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
            assigned[d].append(f"{format_time(start)} - {format_time(start + used)}")
        if remaining <= 0:
            break
    return assigned, remaining


def calculate_recommended_study(lecture_hours, difficulty):
    study_hours = lecture_hours * 2
    if difficulty == "easy":
        study_hours -= 1
    elif difficulty == "hard":
        study_hours += 2
    return max(MIN_STUDY, min(MAX_STUDY, study_hours))


def get_unused_color():
    color_list = list(GOOGLE_COLORS.items())
    available = [(n, h) for n, h in color_list if h not in st.session_state.used_colors]
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


def parse_due_date(date_str):
    if not date_str or not str(date_str).strip():
        return None
    patterns = ["%Y-%m-%d", "%B %d", "%b %d", "%B %d %Y", "%b %d %Y", "%m/%d/%Y", "%m/%d/%y"]
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


def urgency_label(task):
    d = days_until_due(task["due"])
    if d is None:
        return "date not parsed"
    if d < 0:
        return f"overdue by {abs(d)} day(s)"
    if d == 0:
        return "due today"
    return f"due in {d} day(s)"


def build_weekly_calendar():
    calendar = {day: [] for day in VALID_DAYS}
    for course in st.session_state.courses:
        for day, blocks in course["assigned"].items():
            for block in blocks:
                calendar[day].append({"course": course["name"], "time": block, "color": course["hex_code"]})
    return calendar


def export_data_json():
    data = {"courses": st.session_state.courses, "used_colors": st.session_state.used_colors}
    return json.dumps(data, indent=2)


def render_course_card(course):
    progress = int(course_completion(course) * 100)
    st.markdown(
        f"""
        <div class="simple-box">
            <div class="course-name">{course['name']}</div>
            <div class="meta">
                difficulty: {course['difficulty']}<br>
                study time: {course['study']} hrs/week<br>
                target grade: {course['target_grade']}%<br>
                course color: {course['color_name']}<br>
                completion: {progress}%
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_task_card(course, task):
    st.markdown(
        f"""
        <div class="task-box">
            <div class="course-name">{task['title']}</div>
            <div class="meta">
                course: {course['name']}<br>
                type: {task['type']}<br>
                due: {task['due']}<br>
                urgency: {urgency_label(task)}<br>
                weight: {task['weight']}%<br>
                priority: {task['size']}<br>
                status: {task['status']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
st.markdown('<div class="app-title">Study Planner</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Keep courses, assignments, and study blocks in one place.</div>', unsafe_allow_html=True)

total_tasks, done_tasks, in_progress_tasks, _ = get_task_counts()
s1, s2, s3 = st.columns(3)
with s1:
    st.markdown(f'<div class="small-stat"><div class="small-stat-label">Courses</div><div class="small-stat-value">{len(st.session_state.courses)}</div></div>', unsafe_allow_html=True)
with s2:
    st.markdown(f'<div class="small-stat"><div class="small-stat-label">Tasks</div><div class="small-stat-value">{total_tasks}</div></div>', unsafe_allow_html=True)
with s3:
    st.markdown(f'<div class="small-stat"><div class="small-stat-label">Done / In progress</div><div class="small-stat-value">{done_tasks} / {in_progress_tasks}</div></div>', unsafe_allow_html=True)

section = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Add Course", "Weekly Schedule", "Day View", "Edit Courses", "Assignments", "Data"],
)

st.sidebar.markdown("---")
if st.sidebar.button("Save"):
    save_data()
    st.sidebar.success("Saved.")

if section == "Dashboard":
    if not st.session_state.courses:
        st.info("No courses added yet.")
    else:
        left, right = st.columns([1.1, 1])
        with left:
            st.markdown('<div class="section-title">Courses</div>', unsafe_allow_html=True)
            for course in st.session_state.courses:
                render_course_card(course)
        with right:
            st.markdown('<div class="section-title">This week</div>', unsafe_allow_html=True)
            weekly_calendar = build_weekly_calendar()
            top = st.columns(4)
            for i, day in enumerate(VALID_DAYS[:4]):
                with top[i]:
                    st.markdown(f'<div class="day-box"><div class="day-title">{day}</div>', unsafe_allow_html=True)
                    if weekly_calendar[day]:
                        for item in weekly_calendar[day]:
                            st.markdown(
                                f'<div class="schedule-row" style="border-left-color:{item["color"]};">{item["course"]}<br>{item["time"]}</div>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.markdown('<div class="note">No study blocks</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            bottom = st.columns(3)
            for i, day in enumerate(VALID_DAYS[4:]):
                with bottom[i]:
                    st.markdown(f'<div class="day-box"><div class="day-title">{day}</div>', unsafe_allow_html=True)
                    if weekly_calendar[day]:
                        for item in weekly_calendar[day]:
                            st.markdown(
                                f'<div class="schedule-row" style="border-left-color:{item["color"]};">{item["course"]}<br>{item["time"]}</div>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.markdown('<div class="note">No study blocks</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">Upcoming tasks</div>', unsafe_allow_html=True)
        all_tasks = sort_tasks(get_all_tasks())
        if not all_tasks:
            st.info("No tasks added yet.")
        else:
            for _, _, course, task in all_tasks:
                render_task_card(course, task)

elif section == "Add Course":
    st.markdown('<div class="section-title">Add course</div>', unsafe_allow_html=True)
    with st.form("add_course_form"):
        name = st.text_input("Course name")
        lecture_hours = st.number_input("Lecture hours this week", min_value=0, max_value=40, step=1)
        difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
        target_grade = st.number_input("Target final grade", min_value=0.0, max_value=100.0, step=1.0)

        recommended_study = calculate_recommended_study(lecture_hours, difficulty)
        st.caption(f"Suggested study time: {recommended_study} hrs/week")

        override = st.checkbox("Set study hours manually")
        if override:
            study_hours = st.number_input("Study hours per week", min_value=MIN_STUDY, max_value=MAX_STUDY, value=recommended_study, step=1)
        else:
            study_hours = recommended_study

        days = st.multiselect("Study days", VALID_DAYS)
        st.caption("For each selected day, enter one time block per line, like 4pm-6pm")
        time_blocks_text = {}
        for d in days:
            time_blocks_text[d] = st.text_area(f"{d}", placeholder="4pm-6pm\n7pm-9pm", key=f"block_{d}")

        st.markdown("Assignments to add now (optional)")
        num_tasks = st.number_input("Number of tasks", min_value=0, max_value=10, step=1, value=0)
        tasks = []
        for i in range(num_tasks):
            st.markdown(f"Task {i+1}")
            c1, c2 = st.columns(2)
            with c1:
                title = st.text_input(f"Task title {i+1}", key=f"title_{i}")
                task_type = st.text_input(f"Task type {i+1}", key=f"type_{i}")
                due = st.text_input(f"Due date {i+1}", key=f"due_{i}", placeholder="2026-04-02 or April 2")
            with c2:
                weight = st.number_input(f"Weight % {i+1}", min_value=0.0, max_value=100.0, step=1.0, key=f"weight_{i}")
                priority = st.selectbox(f"Priority {i+1}", VALID_PRIORITIES, key=f"priority_{i}")
                status = st.selectbox(f"Status {i+1}", ["not started", "in progress"], key=f"status_{i}")
            tasks.append({"title": title, "type": task_type, "due": due, "size": priority, "weight": weight, "status": status})

        submitted = st.form_submit_button("Add course")

    if submitted:
        if not name.strip():
            st.error("Enter a course name.")
        elif not days:
            st.error("Select at least one study day.")
        else:
            time_blocks = {d: parse_time_blocks(time_blocks_text[d]) for d in days}
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
                "tasks": tasks,
            }
            st.session_state.courses.append(course)
            save_data()
            st.success(f"{name} added.")
            if remaining > 0:
                st.warning(f"Only {study_hours - remaining} of {study_hours} study hours fit in your time windows.")

elif section == "Weekly Schedule":
    st.markdown('<div class="section-title">Weekly schedule</div>', unsafe_allow_html=True)
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
                            f'<div class="schedule-row" style="border-left-color:{item["color"]};">{item["course"]}<br>{item["time"]}</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown('<div class="note">No study blocks</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        bottom = st.columns(3)
        for i, day in enumerate(VALID_DAYS[4:]):
            with bottom[i]:
                st.markdown(f'<div class="day-box"><div class="day-title">{day}</div>', unsafe_allow_html=True)
                if weekly_calendar[day]:
                    for item in weekly_calendar[day]:
                        st.markdown(
                            f'<div class="schedule-row" style="border-left-color:{item["color"]};">{item["course"]}<br>{item["time"]}</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown('<div class="note">No study blocks</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

elif section == "Day View":
    st.markdown('<div class="section-title">Day view</div>', unsafe_allow_html=True)
    selected_day = st.selectbox("Choose a day", VALID_DAYS)
    found = False
    for course in st.session_state.courses:
        blocks = course["assigned"].get(selected_day, [])
        if blocks:
            found = True
            st.markdown(
                f"""
                <div class="simple-box">
                    <div class="course-name">{course['name']}</div>
                    <div class="meta">{selected_day}: {', '.join(blocks)}<br>difficulty: {course['difficulty']}<br>target grade: {course['target_grade']}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    if not found:
        st.info("No study blocks scheduled for this day.")

elif section == "Edit Courses":
    st.markdown('<div class="section-title">Edit courses</div>', unsafe_allow_html=True)
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
            new_difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=["easy", "medium", "hard"].index(course["difficulty"]))
            new_target = st.number_input("Target grade", min_value=0.0, max_value=100.0, step=1.0, value=float(course["target_grade"]))
            new_study = st.number_input("Study hours per week", min_value=MIN_STUDY, max_value=MAX_STUDY, step=1, value=int(course["study"]))
            new_days = st.multiselect("Study days", VALID_DAYS, default=course["days"])
            st.caption("Use one block per line, like 4pm-6pm")
            new_time_blocks_text = {}
            for d in new_days:
                existing_text = ""
                if d in course["time_blocks"]:
                    existing_text = "\n".join([f"{format_time(start)}-{format_time(end)}" for start, end in course["time_blocks"][d]])
                new_time_blocks_text[d] = st.text_area(f"{d}", value=existing_text, key=f"edit_{d}")
            save_changes = st.form_submit_button("Save changes")

        if save_changes:
            new_time_blocks = {d: parse_time_blocks(new_time_blocks_text[d]) for d in new_days}
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
            st.success("Course updated.")
            if remaining > 0:
                st.warning(f"Only {new_study - remaining} of {new_study} study hours fit in your time windows.")

        if st.button("Delete this course"):
            st.session_state.confirm_delete_course = course_index
        if st.session_state.confirm_delete_course == course_index:
            st.markdown('<div class="confirm-box">Delete this course and all its tasks?</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Confirm delete course", key=f"confirm_delete_course_{course_index}"):
                    delete_course(course_index)
                    st.session_state.confirm_delete_course = None
                    st.rerun()
            with c2:
                if st.button("Cancel", key=f"cancel_delete_course_{course_index}"):
                    st.session_state.confirm_delete_course = None
                    st.rerun()

elif section == "Assignments":
    st.markdown('<div class="section-title">Assignments</div>', unsafe_allow_html=True)
    if not st.session_state.courses:
        st.info("No courses added yet.")
    else:
        tab1, tab2 = st.tabs(["View and update", "Add task"])
        with tab1:
            all_tasks = sort_tasks(get_all_tasks())
            if not all_tasks:
                st.info("No assignments added yet.")
            else:
                for idx, (ci, ti, course, task) in enumerate(all_tasks):
                    render_task_card(course, task)
                    new_status = st.selectbox(
                        f"Change status for {task['title']}",
                        VALID_STATUSES,
                        index=VALID_STATUSES.index(task["status"]),
                        key=f"status_update_{idx}",
                    )
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"Save status for {task['title']}", key=f"update_btn_{idx}"):
                            st.session_state.courses[ci]["tasks"][ti]["status"] = new_status
                            save_data()
                            st.rerun()
                    with c2:
                        task_key = f"{ci}_{ti}"
                        if st.button(f"Delete {task['title']}", key=f"delete_btn_{idx}"):
                            st.session_state.confirm_delete_task = task_key
                    task_key = f"{ci}_{ti}"
                    if st.session_state.confirm_delete_task == task_key:
                        st.markdown('<div class="confirm-box">Delete this task?</div>', unsafe_allow_html=True)
                        d1, d2 = st.columns(2)
                        with d1:
                            if st.button("Confirm delete task", key=f"confirm_delete_task_{idx}"):
                                st.session_state.courses[ci]["tasks"].pop(ti)
                                save_data()
                                st.session_state.confirm_delete_task = None
                                st.rerun()
                        with d2:
                            if st.button("Cancel", key=f"cancel_delete_task_{idx}"):
                                st.session_state.confirm_delete_task = None
                                st.rerun()
        with tab2:
            course_names = [course["name"] for course in st.session_state.courses]
            selected_course_name = st.selectbox("Choose course", course_names, key="task_course")
            course_index = course_names.index(selected_course_name)
            with st.form("add_task_form"):
                title = st.text_input("Task title")
                task_type = st.text_input("Task type")
                due = st.text_input("Due date", placeholder="2026-04-02 or April 2")
                weight = st.number_input("Weight %", min_value=0.0, max_value=100.0, step=1.0)
                priority = st.selectbox("Priority", VALID_PRIORITIES)
                status = st.selectbox("Status", ["not started", "in progress"])
                add_task = st.form_submit_button("Add task")
            if add_task:
                if not title.strip():
                    st.error("Enter a task title.")
                else:
                    st.session_state.courses[course_index]["tasks"].append(
                        {"title": title, "type": task_type, "due": due, "size": priority, "weight": weight, "status": status}
                    )
                    save_data()
                    st.success("Task added.")

elif section == "Data":
    st.markdown('<div class="section-title">Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="note">Export your planner or clear everything.</div>', unsafe_allow_html=True)
    export_str = export_data_json()
    st.download_button(
        label="Download data as JSON",
        data=export_str,
        file_name="study_planner_data.json",
        mime="application/json",
    )
    if st.button("Reset all data"):
        st.session_state.confirm_reset = True
    if st.session_state.confirm_reset:
        st.markdown('<div class="confirm-box">Reset everything? This will remove every course and task.</div>', unsafe_allow_html=True)
        r1, r2 = st.columns(2)
        with r1:
            if st.button("Confirm reset"):
                st.session_state.courses = []
                st.session_state.used_colors = []
                save_data()
                st.session_state.confirm_reset = False
                st.rerun()
        with r2:
            if st.button("Cancel reset"):
                st.session_state.confirm_reset = False
                st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
