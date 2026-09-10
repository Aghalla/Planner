from django.contrib import admin
from .models import (
    UserProfile, Task, Habit, HabitLog, Goal,
    CalendarEvent, PomodoroSession, DailyContent,
    UserSettings, DashboardWidget,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'priority', 'completed', 'due_date', 'is_main_task')
    list_filter = ('completed', 'priority', 'is_main_task')


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_active')


@admin.register(HabitLog)
class HabitLogAdmin(admin.ModelAdmin):
    list_display = ('habit', 'date', 'completed')


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'completed', 'status', 'deadline')


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'date', 'reminder')


@admin.register(PomodoroSession)
class PomodoroSessionAdmin(admin.ModelAdmin):
    list_display = ('task', 'session_type', 'duration', 'started_at')


@admin.register(DailyContent)
class DailyContentAdmin(admin.ModelAdmin):
    list_display = ('date',)


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name')


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'widget_type', 'is_visible', 'order')
