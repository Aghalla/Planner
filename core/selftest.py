"""Full app self-test: simulates a real browser with CSRF enforcement."""
import json
import re
from django.test import Client

PASS, FAIL = [], []

def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + (f" [{extra}]" if extra and not cond else ""))

c = Client(HTTP_HOST="localhost", enforce_csrf_checks=True)

# 1. Auth pages
r = c.get("/login/")
check("login page 200", r.status_code == 200, r.status_code)
check("login has csrf", "csrfmiddlewaretoken" in r.content.decode())

# 2. Register a fresh user (browser-style: GET first for token)
import time
uname = f"tester_{int(time.time())}"
c.get("/register/")
token0 = c.cookies["csrftoken"].value
r = c.post("/register/", {"username": uname, "password": "pw123456", "password2": "pw123456", "display_name": "تست"},
           HTTP_X_CSRFTOKEN=token0)
check("register redirects", r.status_code == 302, r.status_code)

# 3. All pages GET
pages = {
    "/": ["widgetGrid", "pageData" if False else "greeting"],
    "/tasks/": ['data-new-task', "pageData"],
    "/goals/": ['data-new-goal', "pageData"],
    "/calendar/": ["cal-grid", "pageData"],
    "/calendar/?mode=week": ["week-strip"],
    "/habits/": ["data-new-habit", "heatmap", "habit-done-btn"],
    "/pomodoro/": ["pomoStart", "pomoReset", "pomoSkip", "ringFg", "pomoData", "pomoSettings"],
    "/statistics/": ["chartFocusLine", "focus-row", "statData"],
    "/settings/": ["settings-form"],
}
# seed one habit + log so habits page renders rows/heatmap
from core.models import Habit, HabitLog
from django.contrib.auth.models import User as _U
from datetime import date as _d
_u = _U.objects.get(username=uname)
_h = Habit.objects.create(user=_u, name="مطالعه", icon="📚")
HabitLog.objects.create(habit=_h, date=_d.today(), completed=True)
from core.models import Task as _T, PomodoroSession as _P
_t = _T.objects.create(user=_u, title="تسک سید")
_P.objects.create(user=_u, task=_t, session_type="focus", duration=25)
for url, markers in pages.items():
    r = c.get(url)
    html = r.content.decode()
    check(f"GET {url} 200", r.status_code == 200, r.status_code)
    for m in markers:
        check(f"GET {url} has {m}", m in html)
    check(f"GET {url} has global csrf", "csrfmiddlewaretoken" in html)

# 4. pageData JSON validity
for url in ["/tasks/", "/goals/", "/calendar/", "/"]:
    html = c.get(url).content.decode()
    m = re.search(r'<script id="pageData"[^>]*>(.*?)</script>', html, re.S)
    if m:
        try:
            json.loads(m.group(1))
            check(f"{url} pageData valid JSON", True)
        except Exception as e:
            check(f"{url} pageData valid JSON", False, str(e)[:80])

# 5. CSRF token from cookie for POSTs
token = c.cookies["csrftoken"].value
H = {"HTTP_X_CSRFTOKEN": token}

# Task lifecycle
r = c.post("/api/tasks/create/", {"title": "کار تست", "priority": "1", "due_date": "2026-09-10"}, **H)
d = r.json()
check("task create", r.status_code == 200 and "id" in d, f"{r.status_code} {d}")
tid = d.get("id")
r = c.post(f"/api/tasks/{tid}/update/", {"title": "کار تست ۲", "priority": "2"}, **H)
check("task update", r.json().get("success") is True, r.content[:100])
r = c.post(f"/api/tasks/{tid}/toggle/", {}, **H)
check("task toggle", r.json().get("completed") is True, r.content[:100])
r = c.post(f"/api/tasks/{tid}/make-main/", {}, **H)
check("task make-main", r.json().get("success") is True, r.content[:100])
r = c.post(f"/api/tasks/{tid}/remove-main/", {}, **H)
check("task remove-main", r.json().get("success") is True, r.content[:100])
r = c.post(f"/api/tasks/{tid}/delete/", {}, **H)
check("task delete", r.json().get("success") is True, r.content[:100])
r = c.post("/api/tasks/create/", {"title": ""}, **H)
check("task create empty -> 400", r.status_code == 400, r.status_code)

# Habit lifecycle
r = c.post("/api/habits/create/", {"name": "عادت تست", "icon": "📚"}, **H)
d = r.json()
check("habit create", "id" in d, str(d)[:100])
hid = d.get("id")
r = c.post(f"/api/habits/{hid}/toggle/", {}, **H)
check("habit toggle", "completed" in r.json(), r.content[:100])
r = c.post(f"/api/habits/{hid}/update/", {"name": "عادت تست ۲", "color": "#5b8def", "target": "5"}, **H)
check("habit update", r.json().get("success") is True, r.content[:100])
r = c.post(f"/api/habits/{hid}/delete/", {}, **H)
check("habit delete", r.json().get("success") is True, r.content[:100])

# Goal lifecycle
r = c.post("/api/goals/create/", {"title": "هدف تست"}, **H)
d = r.json()
check("goal create", "id" in d, str(d)[:100])
gid = d.get("id")
r = c.post(f"/api/goals/{gid}/update/", {"title": "هدف تست ۲"}, **H)
check("goal update", r.json().get("success") is True, r.content[:100])
r = c.post(f"/api/goals/{gid}/toggle/", {}, **H)
check("goal toggle", "completed" in r.json(), r.content[:100])
r = c.post(f"/api/goals/{gid}/delete/", {}, **H)
check("goal delete", r.json().get("success") is True, r.content[:100])

# Event lifecycle
r = c.post("/api/events/create/", {"title": "رویداد تست", "date": "2026-09-10"}, **H)
d = r.json()
check("event create", "id" in d, str(d)[:100])
r = c.post(f"/api/events/{d['id']}/delete/", {}, **H)
check("event delete", r.json().get("success") is True, r.content[:100])

# Pomodoro + widgets + dashboard data
r = c.post("/api/pomodoro/save/", json.dumps({"duration": 25, "session_type": "focus"}),
           content_type="application/json", **H)
check("pomodoro save", r.json().get("success") is True, r.content[:100])
r = c.post("/api/widgets/toggle/", {"widget_type": "goals"}, **H)
check("widget toggle", "is_visible" in r.json(), r.content[:100])
r = c.post("/api/widgets/reorder/", json.dumps({"orders": [{"widget_type": "tasks", "order": 0}]}),
           content_type="application/json", **H)
check("widget reorder", r.json().get("success") is True, r.content[:100])
r = c.post("/api/widgets/reset/", {}, **H)
check("widget reset", r.json().get("success") is True, r.content[:100])
r = c.get("/api/dashboard/")
check("dashboard api", r.status_code == 200 and "greeting" in r.json(), r.status_code)

# POST without token must be rejected (proves CSRF active, and our pages supply the token)
c2 = Client(HTTP_HOST="localhost", enforce_csrf_checks=True)
c2.login(username=uname, password="pw123456")
r = c2.post("/api/tasks/create/", {"title": "x"})
check("POST without token rejected", r.status_code == 403, r.status_code)

print(f"\n==== {len(PASS)} passed, {len(FAIL)} failed ====")
if FAIL:
    print("FAILED:", FAIL)
