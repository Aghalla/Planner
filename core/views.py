import json
from datetime import date, timedelta, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import models
from .models import (
    UserProfile, Task, Habit, HabitLog, Goal, CalendarEvent,
    PomodoroSession, DailyContent, UserSettings, DashboardWidget,
)
from .forms import TaskForm, HabitForm, GoalForm, CalendarEventForm, UserSettingsForm


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        display_name = request.POST.get('display_name', '').strip()
        if not username or not password:
            return render(request, 'register.html', {'error': 'لطفاً تمام فیلدها را پر کنید'})
        if password != password2:
            return render(request, 'register.html', {'error': 'رمزهای عبور مطابقت ندارند'})
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'این نام کاربری قبلاً استفاده شده'})
        user = User.objects.create_user(username=username, password=password)
        UserProfile.objects.create(user=user, display_name=display_name or username)
        UserSettings.objects.create(user=user, display_name=display_name or username)
        widget_types = ['greeting', 'daily_content', 'tasks', 'habits', 'goals', 'pomodoro', 'calendar_mini', 'stats_mini']
        for i, wt in enumerate(widget_types):
            DashboardWidget.objects.create(user=user, widget_type=wt, order=i)
        login(request, user)
        return redirect('dashboard')
    return render(request, 'register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        return render(request, 'login.html', {'error': 'نام کاربری یا رمز عبور اشتباه است'})
    return render(request, 'login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    today = date.today()
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    now_hour = datetime.now().hour
    if now_hour < 12:
        greeting = 'صبح بخیر'
    elif now_hour < 17:
        greeting = 'روز بخیر'
    else:
        greeting = 'شب بخیر'
    profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'display_name': settings_obj.display_name})
    user_name = profile.display_name or request.user.username
    yesterday = today - timedelta(days=1)
    overdue_tasks = Task.objects.filter(
        user=request.user, completed=False, due_date__lt=today, due_date__isnull=False,
    )
    for task in overdue_tasks:
        task.carry_over = True
        task.carry_over_date = yesterday
        task.save()
    main_tasks = Task.objects.filter(
        user=request.user, is_main_task=True, completed=False,
    ).order_by('main_task_order')[:3]
    today_tasks = Task.objects.filter(user=request.user, due_date=today)
    habits = Habit.objects.filter(user=request.user, is_active=True)
    goals = Goal.objects.filter(user=request.user, completed=False, parent_goal__isnull=True)
    daily_content = DailyContent.objects.filter(date=today).first()
    widgets = DashboardWidget.objects.filter(user=request.user).order_by('order')
    today_sessions = PomodoroSession.objects.filter(
        user=request.user, session_type='focus', started_at__date=today,
    )
    total_focus_minutes = sum(s.duration for s in today_sessions)
    pomodoro_count = today_sessions.count()
    context = {
        'greeting': greeting,
        'user_name': user_name,
        'today': today,
        'main_tasks': main_tasks,
        'today_tasks': today_tasks,
        'habits': habits,
        'goals': goals,
        'daily_content': daily_content,
        'widgets': widgets,
        'total_focus_minutes': total_focus_minutes,
        'pomodoro_count': pomodoro_count,
        'settings': settings_obj,
        'page_data': json.dumps({
            'goals': [{'id': g.id, 'title': g.title} for g in Goal.objects.filter(user=request.user, completed=False)],
            'tasks': [],
        }),
    }
    return render(request, 'dashboard.html', context)


@login_required
def tasks_view(request):
    from .jalali_utils import to_jalali
    J_MONTHS = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
                'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    today = date.today()
    tasks = Task.objects.filter(user=request.user)
    status_filter = request.GET.get('status', 'today')
    if status_filter == 'today':
        tasks = tasks.filter(due_date=today)
    elif status_filter == 'overdue':
        tasks = tasks.filter(completed=False, due_date__lt=today, due_date__isnull=False)
    elif status_filter == 'pending':
        tasks = tasks.filter(completed=False)
    elif status_filter == 'completed':
        tasks = tasks.filter(completed=True)
    tasks = list(tasks.select_related('goal').order_by('completed', 'due_date', '-priority'))

    def jalali_label(d):
        if d is None:
            return 'بدون تاریخ'
        if d == today:
            return 'امروز'
        try:
            jy, jm, jd = to_jalali(d.year, d.month, d.day)
            return f"{jd} {J_MONTHS[jm - 1]} {jy}"
        except Exception:
            return str(d)

    groups = {}
    for t in tasks:
        key = t.due_date.isoformat() if t.due_date else 'none'
        if key not in groups:
            groups[key] = {'key': key, 'label': jalali_label(t.due_date),
                           'is_overdue': bool(t.due_date and t.due_date < today),
                           'items': []}
        groups[key]['items'].append(t)
    ordered_keys = sorted(groups.keys())
    if 'none' in ordered_keys:
        ordered_keys.remove('none')
        ordered_keys.append('none')
    grouped = [groups[k] for k in ordered_keys]

    goals = Goal.objects.filter(user=request.user, completed=False)
    page_data = {
        'goals': [{'id': g.id, 'title': g.title} for g in goals],
        'tasks': [{
            'id': t.id, 'title': t.title,
            'due_date': t.due_date.isoformat() if t.due_date else '',
            'due_time': str(t.due_time)[:5] if t.due_time else '',
            'priority': t.priority,
            'goal_id': t.goal_id or '',
            'is_main_task': t.is_main_task,
        } for t in tasks],
    }
    context = {
        'grouped': grouped,
        'goals': goals,
        'today': today,
        'status_filter': status_filter,
        'page_data': json.dumps(page_data),
    }
    return render(request, 'tasks.html', context)


@login_required
@require_POST
def task_update_view(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    title = request.POST.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'عنوان الزامی است'}, status=400)
    task.title = title
    task.priority = int(request.POST.get('priority', task.priority))
    task.due_date = request.POST.get('due_date') or None
    task.due_time = request.POST.get('due_time') or None
    task.goal_id = request.POST.get('goal') or None
    task.is_main_task = request.POST.get('is_main_task') == 'on'
    task.save()
    return JsonResponse({'success': True})


@login_required
@require_POST
def task_create_view(request):
    title = request.POST.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'عنوان الزامی است'}, status=400)
    task = Task.objects.create(
        user=request.user,
        title=title,
        description=request.POST.get('description', ''),
        priority=int(request.POST.get('priority', 2)),
        due_date=request.POST.get('due_date') or None,
        due_time=request.POST.get('due_time') or None,
        goal_id=request.POST.get('goal') or None,
        is_main_task=request.POST.get('is_main_task') == 'on',
    )
    return JsonResponse({
        'id': task.id,
        'title': task.title,
        'priority': task.priority,
        'completed': task.completed,
        'due_date': str(task.due_date) if task.due_date else None,
    })


@login_required
@require_POST
def task_toggle_view(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.completed = not task.completed
    if task.completed:
        task.completed_at = timezone.now()
        task.status = 'completed'
    else:
        task.completed_at = None
        task.status = 'pending'
    task.save()
    return JsonResponse({'completed': task.completed})


@login_required
@require_POST
def task_delete_view(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def task_make_main_view(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    current_main = Task.objects.filter(user=request.user, is_main_task=True, completed=False).count()
    if current_main < 3:
        task.is_main_task = True
        task.main_task_order = current_main + 1
        task.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'حداکثر 3 کار اصلی'}, status=400)


@login_required
@require_POST
def task_remove_main_view(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.is_main_task = False
    task.main_task_order = 0
    task.save()
    return JsonResponse({'success': True})


@login_required
@require_POST
def task_carry_over_view(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    action = request.POST.get('action', 'tomorrow')
    if action == 'tomorrow':
        task.due_date = date.today() + timedelta(days=1)
        task.carry_over = True
        task.save()
    elif action == 'delete':
        task.delete()
    return JsonResponse({'success': True})


@login_required
def habits_view(request):
    today = date.today()
    habits = Habit.objects.filter(user=request.user, is_active=True)
    # shared 15-week heatmap columns (oldest left, like lifeboard)
    weeks = []
    for w in range(14, -1, -1):
        col = []
        for d in range(6, -1, -1):
            col.append((today - timedelta(days=w * 7 + d)).isoformat())
        weeks.append(col)
    week_start = today - timedelta(days=6)
    habit_data = []
    for h in habits:
        done_isos = set(
            HabitLog.objects.filter(habit=h, completed=True).values_list('date', flat=True)
        )
        done_str = {d.isoformat() for d in done_isos}
        week_count = HabitLog.objects.filter(
            habit=h, completed=True, date__gte=week_start).count()
        total_count = HabitLog.objects.filter(habit=h, completed=True).count()
        habit_data.append({
            'id': h.id,
            'name': h.name,
            'icon': h.icon,
            'color': h.color,
            'target': h.target,
            'streak': h.get_streak(),
            'completion_rate': h.get_completion_rate(),
            'completed_today': h.is_completed_today(),
            'week_count': week_count,
            'total_count': total_count,
            'done': done_str,
        })
    page_data = {
        'goals': [],
        'tasks': [],
        'habitsFull': [{
            'id': h['id'], 'name': h['name'], 'icon': h['icon'],
            'color': h['color'], 'target': h['target'],
        } for h in habit_data],
    }
    context = {'habits': habit_data, 'weeks': weeks, 'page_data': json.dumps(page_data)}
    return render(request, 'habits.html', context)


@login_required
@require_POST
def habit_create_view(request):
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'نام عادت الزامی است'}, status=400)
    habit = Habit.objects.create(
        user=request.user,
        name=name,
        icon=request.POST.get('icon', '🔥') or '🔥',
        color=request.POST.get('color', '#ff8a3d') or '#ff8a3d',
        target=int(request.POST.get('target', 7) or 7),
    )
    return JsonResponse({
        'id': habit.id,
        'name': habit.name,
        'icon': habit.icon,
        'streak': 0,
        'completion_rate': 0,
    })


@login_required
@require_POST
def habit_update_view(request, habit_id):
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'نام عادت الزامی است'}, status=400)
    habit.name = name
    habit.icon = request.POST.get('icon', habit.icon) or habit.icon
    habit.color = request.POST.get('color', habit.color) or habit.color
    habit.target = int(request.POST.get('target', habit.target) or habit.target)
    habit.save()
    return JsonResponse({'success': True})


@login_required
@require_POST
def habit_toggle_view(request, habit_id):
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    today = date.today()
    log, created = HabitLog.objects.get_or_create(habit=habit, date=today)
    log.completed = not log.completed
    log.save()
    return JsonResponse({
        'completed': log.completed,
        'streak': habit.get_streak(),
    })


@login_required
@require_POST
def habit_delete_view(request, habit_id):
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    habit.is_active = False
    habit.save()
    return JsonResponse({'success': True})


@login_required
def goals_view(request):
    from .jalali_utils import to_jalali
    J_MONTHS = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
                'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    today = date.today()
    goals = Goal.objects.filter(user=request.user, parent_goal__isnull=True).prefetch_related('tasks', 'sub_goals')
    goal_data = []
    for g in goals:
        sub_goals = g.sub_goals.all()
        tasks = list(g.tasks.all().order_by('completed', '-priority'))
        deadline_label = None
        is_late = False
        if g.deadline:
            try:
                jy, jm, jd = to_jalali(g.deadline.year, g.deadline.month, g.deadline.day)
                deadline_label = f"{jd} {J_MONTHS[jm - 1]} {jy}"
            except Exception:
                deadline_label = str(g.deadline)
            is_late = g.deadline < today and g.get_progress() < 100
        goal_data.append({
            'id': g.id,
            'title': g.title,
            'description': g.description,
            'deadline': g.deadline.isoformat() if g.deadline else '',
            'deadline_label': deadline_label,
            'is_late': is_late,
            'completed': g.completed,
            'status': g.status,
            'progress': g.get_progress(),
            'task_count': len(tasks),
            'completed_tasks': sum(1 for t in tasks if t.completed),
            'tasks': [{
                'id': t.id, 'title': t.title, 'completed': t.completed,
                'priority': t.priority,
                'due_time': str(t.due_time)[:5] if t.due_time else '',
            } for t in tasks],
            'sub_goals': [
                {'id': sg.id, 'title': sg.title, 'progress': sg.get_progress()}
                for sg in sub_goals
            ],
        })
    all_goals = Goal.objects.filter(user=request.user, completed=False)
    all_goal_tasks = []
    for g in goal_data:
        for t in g['tasks']:
            all_goal_tasks.append({
                'id': t['id'], 'title': t['title'], 'due_date': '',
                'due_time': t['due_time'], 'priority': t['priority'],
                'goal_id': g['id'], 'is_main_task': False,
            })
    page_data = {
        'goals': [{'id': g.id, 'title': g.title} for g in all_goals],
        'goalsFull': [{
            'id': g['id'], 'title': g['title'], 'description': g['description'],
            'deadline': g['deadline'],
        } for g in goal_data],
        'tasks': all_goal_tasks,
    }
    context = {'goals': goal_data, 'all_goals': all_goals, 'page_data': json.dumps(page_data)}
    return render(request, 'goals.html', context)


@login_required
@require_POST
def goal_update_view(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    title = request.POST.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'عنوان هدف الزامی است'}, status=400)
    goal.title = title
    goal.description = request.POST.get('description', '')
    goal.deadline = request.POST.get('deadline') or None
    goal.save()
    return JsonResponse({'success': True})


@login_required
@require_POST
def goal_create_view(request):
    title = request.POST.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'عنوان هدف الزامی است'}, status=400)
    goal = Goal.objects.create(
        user=request.user,
        title=title,
        description=request.POST.get('description', ''),
        deadline=request.POST.get('deadline') or None,
        parent_goal_id=request.POST.get('parent_goal') or None,
    )
    return JsonResponse({
        'id': goal.id,
        'title': goal.title,
        'progress': goal.get_progress(),
    })


@login_required
@require_POST
def goal_toggle_view(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    goal.completed = not goal.completed
    if goal.completed:
        goal.completed_at = timezone.now()
        goal.status = 'completed'
    else:
        goal.completed_at = None
        goal.status = 'active'
    goal.save()
    return JsonResponse({'completed': goal.completed, 'progress': goal.get_progress()})


@login_required
@require_POST
def goal_delete_view(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    goal.delete()
    return JsonResponse({'success': True})


@login_required
def calendar_view(request):
    try:
        import jdatetime

        def _today_j():
            t = jdatetime.date.today()
            return t.year, t.month

        def _to_gregorian(y, m, d):
            g = jdatetime.date(y, m, d).togregorian()
            return g.year, g.month, g.day

        def _from_gregorian(gy, gm, gd):
            j = jdatetime.date.fromgregorian(day=gd, month=gm, year=gy)
            return j.year, j.month, j.day

        def _month_len(y, m):
            if m <= 6:
                return 31
            if m <= 11:
                return 30
            return 30 if y % 33 in (1, 5, 9, 13, 17, 22, 26, 30) else 29
    except ImportError:
        from .jalali_utils import (
            today_jalali as _tj, to_gregorian as _tg,
            to_jalali as _tj2, jalali_month_length as _ml,
        )

        def _today_j():
            return _tj()[0], _tj()[1]

        def _to_gregorian(y, m, d):
            return _tg(y, m, d)

        def _from_gregorian(gy, gm, gd):
            return _tj2(gy, gm, gd)

        def _month_len(y, m):
            return _ml(y, m)

    today = date.today()
    _ty, _tm = _today_j()
    jy = int(request.GET.get('jy', _ty))
    jm = int(request.GET.get('jm', _tm))
    mode = request.GET.get('mode', 'month')
    selected_iso = request.GET.get('selected')

    J_MONTHS = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
                'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    WEEKDAYS = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']

    def shift(y, m, n):
        m += n
        while m > 12:
            m -= 12
            y += 1
        while m < 1:
            m += 12
            y -= 1
        return y, m

    prev_jy, prev_jm = shift(jy, jm, -1)
    next_jy, next_jm = shift(jy, jm, 1)
    mlen = _month_len(jy, jm)
    _fgy, _fgm, _fgd = _to_gregorian(jy, jm, 1)
    first_g = date(_fgy, _fgm, _fgd)
    # jdatetime weekday: Monday=0..Sunday=6, Saturday=5 → Saturday-first offset
    offset = (first_g.weekday() - 5) % 7
    first_iso = first_g - timedelta(days=offset)

    # Build cells (always full weeks)
    total = offset + mlen
    while total % 7 != 0 or total < 35:
        total += 1
    cells = []
    for i in range(total):
        g = first_iso + timedelta(days=i)
        try:
            _jjy, _jjm, _jjd = _from_gregorian(g.year, g.month, g.day)
            jd_num = _jjd
            other = not (_jjy == jy and _jjm == jm)
        except Exception:
            jd_num = g.day
            other = True
        iso = g.isoformat()
        cells.append({
            'iso': iso, 'jd': jd_num, 'other': other,
            'is_today': g == today,
            'is_selected': iso == selected_iso,
        })

    # Range for queries
    start_iso = cells[0]['iso']
    end_iso = cells[-1]['iso']
    start_d = date.fromisoformat(start_iso)
    end_d = date.fromisoformat(end_iso)

    if mode in ('week', 'day'):
        base = date.fromisoformat(selected_iso) if selected_iso else today
        # Saturday of that week (weekday(): Mon=0..Sun=6, Sat=5)
        sat = base - timedelta(days=(base.weekday() - 5) % 7)
        week_isos = [(sat + timedelta(days=i)).isoformat() for i in range(7)]
        if mode == 'week':
            start_d = sat
            end_d = sat + timedelta(days=6)
        else:
            start_d = end_d = base

    events = CalendarEvent.objects.filter(user=request.user, date__gte=start_d, date__lte=end_d)
    tasks_qs = Task.objects.filter(user=request.user, due_date__gte=start_d, due_date__lte=end_d)
    logs = HabitLog.objects.filter(habit__user=request.user, date__gte=start_d, date__lte=end_d, completed=True)

    events_by_iso, tasks_by_iso, habits_by_iso = {}, {}, {}
    for e in events:
        events_by_iso.setdefault(e.date.isoformat(), []).append({
            'id': e.id, 'title': e.title, 'time': str(e.time) if e.time else None,
        })
    for t in tasks_qs:
        if t.due_date:
            tasks_by_iso.setdefault(t.due_date.isoformat(), []).append({
                'id': t.id, 'title': t.title, 'completed': t.completed,
            })
    for lg in logs:
        habits_by_iso[lg.date.isoformat()] = habits_by_iso.get(lg.date.isoformat(), 0) + 1

    for c in cells:
        iso = c['iso']
        c['events'] = events_by_iso.get(iso, [])
        c['tasks'] = tasks_by_iso.get(iso, [])
        c['habits'] = habits_by_iso.get(iso, 0)
        c['done'] = sum(1 for t in c['tasks'] if t['completed'])
        c['open'] = len(c['tasks']) - c['done']

    # Week strip data
    week_cells = []
    if mode in ('week', 'day'):
        for iso in (week_isos if mode == 'week' else [start_d.isoformat()]):
            pass
        base = date.fromisoformat(selected_iso) if selected_iso else today
        sat = base - timedelta(days=(base.weekday() - 5) % 7)
        for i in range(7):
            d = sat + timedelta(days=i)
            iso = d.isoformat()
            try:
                _, _, jd_num = _from_gregorian(d.year, d.month, d.day)
            except Exception:
                jd_num = d.day
            week_cells.append({
                'iso': iso, 'jd': jd_num, 'is_today': d == today,
                'is_selected': iso == (selected_iso or today.isoformat()),
                'wname': WEEKDAYS[i],
            })

    # Selected day detail
    sel_iso = selected_iso or today.isoformat()
    try:
        sel_date = date.fromisoformat(sel_iso)
    except ValueError:
        sel_date = today
        sel_iso = today.isoformat()
    try:
        _sj, _sm, _sd = _from_gregorian(sel_date.year, sel_date.month, sel_date.day)
        sel_label = f"{_sd} {J_MONTHS[_sm - 1]} {_sj}"
    except Exception:
        sel_label = sel_iso
    day_events = CalendarEvent.objects.filter(user=request.user, date=sel_date)
    day_tasks = Task.objects.filter(user=request.user, due_date=sel_date).order_by('completed', '-priority')
    day_habits = Habit.objects.filter(user=request.user, is_active=True)
    day_habits_done = HabitLog.objects.filter(habit__user=request.user, date=sel_date, completed=True).count()
    is_today_sel = sel_date == today

    cal_goals = Goal.objects.filter(user=request.user, completed=False)
    context = {
        'page_data': json.dumps({
            'goals': [{'id': g.id, 'title': g.title} for g in cal_goals],
            'tasks': [],
        }),
        'jy': jy, 'jm': jm,
        'month_title': f"{J_MONTHS[jm - 1]} {jy}",
        'weekdays': WEEKDAYS,
        'cells': cells,
        'mode': mode,
        'prev_jy': prev_jy, 'prev_jm': prev_jm,
        'next_jy': next_jy, 'next_jm': next_jm,
        'today_jy': _ty, 'today_jm': _tm,
        'today_iso': today.isoformat(),
        'selected_iso': sel_iso,
        'sel_label': sel_label,
        'is_today_sel': is_today_sel,
        'week_cells': week_cells,
        'day_events': day_events,
        'day_tasks': day_tasks,
        'day_habits': day_habits,
        'day_habits_done': day_habits_done,
    }
    return render(request, 'calendar.html', context)


@login_required
def calendar_day_view(request, year, month, day):
    target_date = date(year, month, day)
    events = CalendarEvent.objects.filter(user=request.user, date=target_date)
    tasks = Task.objects.filter(user=request.user, due_date=target_date)
    habits = Habit.objects.filter(user=request.user, is_active=True)
    completed_habits = 0
    for h in habits:
        if HabitLog.objects.filter(habit=h, date=target_date, completed=True).exists():
            completed_habits += 1
    pomodoro_sessions = PomodoroSession.objects.filter(
        user=request.user, session_type='focus', started_at__date=target_date,
    )
    total_focus = sum(s.duration for s in pomodoro_sessions)
    completed_tasks = tasks.filter(completed=True).count()
    context = {
        'target_date': target_date,
        'events': events,
        'tasks': tasks,
        'habits': habits,
        'completed_habits': completed_habits,
        'pomodoro_count': pomodoro_sessions.count(),
        'total_focus': total_focus,
        'completed_tasks': completed_tasks,
        'total_tasks': tasks.count(),
        'active_goals': Goal.objects.filter(user=request.user, completed=False).count(),
    }
    return render(request, 'calendar_day.html', context)


@login_required
@require_POST
def event_create_view(request):
    title = request.POST.get('title', '').strip()
    event_date = request.POST.get('date')
    if not title or not event_date:
        return JsonResponse({'error': 'عنوان و تاریخ الزامی است'}, status=400)
    event = CalendarEvent.objects.create(
        user=request.user,
        title=title,
        description=request.POST.get('description', ''),
        date=event_date,
        time=request.POST.get('time') or None,
        reminder=request.POST.get('reminder') == 'on',
        reminder_minutes=int(request.POST.get('reminder_minutes', 30)),
    )
    return JsonResponse({'id': event.id, 'title': event.title, 'date': str(event.date)})


@login_required
@require_POST
def event_delete_view(request, event_id):
    event = get_object_or_404(CalendarEvent, id=event_id, user=request.user)
    event.delete()
    return JsonResponse({'success': True})


@login_required
def pomodoro_view(request):
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    tasks = Task.objects.filter(user=request.user, completed=False)
    today_sessions = PomodoroSession.objects.filter(
        user=request.user, session_type='focus', started_at__date=date.today(),
    )
    total_focus = sum(s.duration for s in today_sessions)
    context = {
        'settings': settings_obj,
        'tasks': tasks,
        'total_focus': total_focus,
        'pomodoro_count': today_sessions.count(),
    }
    return render(request, 'pomodoro.html', context)


@login_required
@require_POST
def pomodoro_save_view(request):
    data = json.loads(request.body)
    task_id = data.get('task_id')
    duration = int(data.get('duration', 25))
    session_type = data.get('session_type', 'focus')
    task = None
    if task_id:
        # only link tasks that belong to this user
        task = Task.objects.filter(id=task_id, user=request.user).first()
    PomodoroSession.objects.create(
        user=request.user,
        task=task,
        session_type=session_type,
        duration=duration,
    )
    return JsonResponse({'success': True, 'task': task.title if task else None})


@login_required
@require_POST
def pomodoro_settings_view(request):
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    settings_obj.focus_duration = int(request.POST.get('focus_duration', 25))
    settings_obj.short_break_duration = int(request.POST.get('short_break_duration', 5))
    settings_obj.long_break_duration = int(request.POST.get('long_break_duration', 15))
    settings_obj.pomodoros_until_long_break = int(request.POST.get('pomodoros_until_long_break', 4))
    settings_obj.save()
    return JsonResponse({'success': True})


@login_required
def statistics_view(request):
    today = date.today()
    period = request.GET.get('period', 'weekly')
    if period == 'daily':
        start_date = today
    elif period == 'monthly':
        start_date = today - timedelta(days=30)
    else:
        start_date = today - timedelta(days=7)
    tasks = Task.objects.filter(user=request.user, created_at__date__gte=start_date)
    completed_tasks = tasks.filter(completed=True).count()
    total_tasks = tasks.count()
    habit_logs = HabitLog.objects.filter(habit__user=request.user, date__gte=start_date, completed=True)
    total_habits = Habit.objects.filter(user=request.user, is_active=True).count()
    pomodoro_sessions = PomodoroSession.objects.filter(
        user=request.user, session_type='focus', started_at__date__gte=start_date,
    )
    total_focus = sum(s.duration for s in pomodoro_sessions)
    pomodoro_count = pomodoro_sessions.count()
    goals = Goal.objects.filter(user=request.user)
    completed_goals = goals.filter(completed=True).count()
    best_day = None
    best_count = 0
    for i in range((today - start_date).days + 1):
        d = start_date + timedelta(days=i)
        count = Task.objects.filter(user=request.user, completed=True, completed_at__date=d).count()
        if count > best_count:
            best_count = count
            best_day = d
    from .jalali_utils import to_jalali as _tj
    days = []
    for i in range((today - start_date).days + 1):
        d = start_date + timedelta(days=i)
        day_tasks = Task.objects.filter(user=request.user, due_date=d)
        day_completed = day_tasks.filter(completed=True).count()
        day_habits = HabitLog.objects.filter(habit__user=request.user, date=d, completed=True).count()
        day_pomodoro = PomodoroSession.objects.filter(
            user=request.user, session_type='focus', started_at__date=d,
        ).aggregate(total=models.Sum('duration'))['total'] or 0
        try:
            _jy, _jm, _jd = _tj(d.year, d.month, d.day)
            _label = f"{_jd}"
        except Exception:
            _label = str(d.day)
        days.append({
            'date': str(d),
            'label': _label,
            'tasks_completed': day_completed,
            'tasks_total': day_tasks.count(),
            'habits_completed': day_habits,
            'focus_minutes': day_pomodoro,
        })
    task_focus = []
    for session in pomodoro_sessions.select_related('task'):
        name = session.task.title if session.task else 'بدون کار مشخص'
        existing = next((t for t in task_focus if t['name'] == name), None)
        if existing:
            existing['minutes'] += session.duration
        else:
            task_focus.append({'name': name, 'minutes': session.duration})
    task_focus_sorted = sorted(task_focus, key=lambda x: x['minutes'], reverse=True)[:10]
    context = {
        'period': period,
        'completed_tasks': completed_tasks,
        'total_tasks': total_tasks,
        'total_habits': total_habits,
        'habit_logs_count': habit_logs.count(),
        'total_focus': total_focus,
        'pomodoro_count': pomodoro_count,
        'completed_goals': completed_goals,
        'total_goals': goals.count(),
        'best_day': best_day,
        'best_count': best_count,
        'days': json.dumps(days),
        'task_focus': json.dumps(task_focus_sorted),
        'task_focus_list': task_focus_sorted,
        'productivity_score': round((completed_tasks / max(total_tasks, 1)) * 100),
    }
    return render(request, 'statistics.html', context)


@login_required
def settings_view(request):
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user, defaults={'display_name': settings_obj.display_name},
    )
    if request.method == 'POST':
        settings_obj.display_name = request.POST.get('display_name', settings_obj.display_name)
        settings_obj.notifications_enabled = request.POST.get('notifications_enabled') == 'on'
        settings_obj.task_reminder = request.POST.get('task_reminder') == 'on'
        settings_obj.habit_reminder = request.POST.get('habit_reminder') == 'on'
        settings_obj.goal_reminder = request.POST.get('goal_reminder') == 'on'
        settings_obj.event_reminder = request.POST.get('event_reminder') == 'on'
        settings_obj.pomodoro_reminder = request.POST.get('pomodoro_reminder') == 'on'
        settings_obj.focus_duration = int(request.POST.get('focus_duration', 25))
        settings_obj.short_break_duration = int(request.POST.get('short_break_duration', 5))
        settings_obj.long_break_duration = int(request.POST.get('long_break_duration', 15))
        settings_obj.pomodoros_until_long_break = int(request.POST.get('pomodoros_until_long_break', 4))
        settings_obj.greeting_enabled = request.POST.get('greeting_enabled') == 'on'
        settings_obj.daily_content_enabled = request.POST.get('daily_content_enabled') == 'on'
        settings_obj.save()
        profile.display_name = settings_obj.display_name
        profile.save()
        return redirect('settings')
    context = {'settings': settings_obj, 'profile': profile}
    return render(request, 'settings.html', context)


@login_required
@require_POST
def widget_toggle_view(request):
    widget_type = request.POST.get('widget_type')
    widget, _ = DashboardWidget.objects.get_or_create(user=request.user, widget_type=widget_type)
    widget.is_visible = not widget.is_visible
    widget.save()
    return JsonResponse({'is_visible': widget.is_visible})


@login_required
@require_POST
def widget_reorder_view(request):
    data = json.loads(request.body)
    orders = data.get('orders', [])
    for item in orders:
        DashboardWidget.objects.filter(
            user=request.user, widget_type=item['widget_type'],
        ).update(order=item['order'])
    return JsonResponse({'success': True})


@login_required
@require_POST
def widget_reset_view(request):
    widgets = DashboardWidget.objects.filter(user=request.user)
    for i, w in enumerate(widgets):
        w.order = i
        w.is_visible = True
        w.save()
    return JsonResponse({'success': True})


@login_required
def dashboard_data_view(request):
    today = date.today()
    now_hour = datetime.now().hour
    if now_hour < 12:
        greeting = 'صبح بخیر'
    elif now_hour < 17:
        greeting = 'روز بخیر'
    else:
        greeting = 'شب بخیر'
    profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'display_name': 'کاربر'})
    main_tasks = Task.objects.filter(
        user=request.user, is_main_task=True, completed=False,
    ).order_by('main_task_order')[:3]
    habits = Habit.objects.filter(user=request.user, is_active=True)
    habit_data = [{
        'id': h.id, 'name': h.name, 'icon': h.icon,
        'streak': h.get_streak(), 'completed_today': h.is_completed_today(),
    } for h in habits]
    today_sessions = PomodoroSession.objects.filter(
        user=request.user, session_type='focus', started_at__date=today,
    )
    return JsonResponse({
        'greeting': greeting,
        'user_name': profile.display_name,
        'main_tasks': [{'id': t.id, 'title': t.title, 'completed': t.completed} for t in main_tasks],
        'habits': habit_data,
        'focus_minutes': sum(s.duration for s in today_sessions),
        'pomodoro_count': today_sessions.count(),
    })
