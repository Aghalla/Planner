from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100, default='')

    def __str__(self):
        return self.display_name or self.user.username


class Task(models.Model):
    PRIORITY_CHOICES = [(1, 'High'), (2, 'Medium'), (3, 'Low')]
    STATUS_CHOICES = [('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    due_time = models.TimeField(null=True, blank=True)
    is_main_task = models.BooleanField(default=False)
    main_task_order = models.IntegerField(default=0)
    goal = models.ForeignKey('Goal', on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    carry_over = models.BooleanField(default=False)
    carry_over_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['completed', '-priority', 'due_date']

    def __str__(self):
        return self.title


class Habit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits')
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, default='🔥')
    color = models.CharField(max_length=10, default='#ff8a3d')
    target = models.IntegerField(default=7)
    is_active = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_streak(self):
        today = date.today()
        streak = 0
        current_date = today
        while True:
            log = HabitLog.objects.filter(habit=self, date=current_date, completed=True).exists()
            if log:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        return streak

    def get_completion_rate(self):
        today = date.today()
        start = self.created_at
        total_days = (today - start).days + 1
        if total_days <= 0:
            return 0
        completed = HabitLog.objects.filter(habit=self, completed=True).count()
        return round((completed / total_days) * 100, 1)

    def is_completed_today(self):
        return HabitLog.objects.filter(habit=self, date=date.today(), completed=True).exists()


class HabitLog(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField()
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('habit', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.habit.name} - {self.date}"


class Goal(models.Model):
    STATUS_CHOICES = [('active', 'Active'), ('completed', 'Completed'), ('paused', 'Paused')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    deadline = models.DateField(null=True, blank=True)
    parent_goal = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_goals')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['completed', 'deadline']

    def __str__(self):
        return self.title

    def get_progress(self):
        all_tasks = self.tasks.all()
        sub_goals = self.sub_goals.all()
        total = all_tasks.count() + sub_goals.count()
        if total == 0:
            return 0
        done = all_tasks.filter(completed=True).count() + sub_goals.filter(completed=True).count()
        return round((done / total) * 100, 1)


class CalendarEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    reminder = models.BooleanField(default=False)
    reminder_minutes = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'time']

    def __str__(self):
        return f"{self.title} - {self.date}"


class PomodoroSession(models.Model):
    SESSION_TYPES = [('focus', 'Focus'), ('short_break', 'Short Break'), ('long_break', 'Long Break')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pomodoro_sessions')
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name='pomodoro_sessions')
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='focus')
    duration = models.IntegerField(help_text='Duration in minutes')
    started_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.session_type} - {self.duration}min"


class DailyContent(models.Model):
    date = models.DateField(unique=True)
    tip = models.TextField()
    fact = models.TextField()
    quote = models.TextField()
    quote_author = models.CharField(max_length=200)
    challenge = models.TextField()

    def __str__(self):
        return f"Content for {self.date}"


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    display_name = models.CharField(max_length=100, default='کاربر')
    notifications_enabled = models.BooleanField(default=True)
    task_reminder = models.BooleanField(default=True)
    habit_reminder = models.BooleanField(default=True)
    goal_reminder = models.BooleanField(default=True)
    event_reminder = models.BooleanField(default=True)
    pomodoro_reminder = models.BooleanField(default=True)
    focus_duration = models.IntegerField(default=25)
    short_break_duration = models.IntegerField(default=5)
    long_break_duration = models.IntegerField(default=15)
    pomodoros_until_long_break = models.IntegerField(default=4)
    greeting_enabled = models.BooleanField(default=True)
    daily_content_enabled = models.BooleanField(default=True)
    theme = models.CharField(max_length=20, default='dark')

    def __str__(self):
        return f"Settings for {self.user.username}"


class DashboardWidget(models.Model):
    WIDGET_CHOICES = [
        ('greeting', 'Greeting'),
        ('daily_content', 'Daily Content'),
        ('tasks', 'Today Tasks'),
        ('habits', 'Habits'),
        ('goals', 'Goals'),
        ('pomodoro', 'Pomodoro'),
        ('calendar_mini', 'Mini Calendar'),
        ('stats_mini', 'Mini Stats'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_widgets')
    widget_type = models.CharField(max_length=50, choices=WIDGET_CHOICES)
    is_visible = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('user', 'widget_type')

    def __str__(self):
        return f"{self.widget_type} ({'visible' if self.is_visible else 'hidden'})"
