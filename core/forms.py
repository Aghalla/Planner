from django import forms
from .models import Task, Habit, Goal, CalendarEvent, UserSettings


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'priority', 'due_date', 'due_time', 'goal', 'is_main_task']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'عنوان کار...'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'توضیحات...'}),
            'priority': forms.Select(attrs={'class': 'form-input'}),
            'due_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'due_time': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'goal': forms.Select(attrs={'class': 'form-input'}),
        }


class HabitForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ['name', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'نام عادت...'}),
            'icon': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '🎯'}),
        }


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['title', 'description', 'deadline', 'parent_goal']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'عنوان هدف...'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'توضیحات...'}),
            'deadline': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'parent_goal': forms.Select(attrs={'class': 'form-input'}),
        }


class CalendarEventForm(forms.ModelForm):
    class Meta:
        model = CalendarEvent
        fields = ['title', 'description', 'date', 'time', 'reminder', 'reminder_minutes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'عنوان رویداد...'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'توضیحات...'}),
            'date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'reminder_minutes': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = [
            'display_name', 'notifications_enabled', 'task_reminder',
            'habit_reminder', 'goal_reminder', 'event_reminder',
            'pomodoro_reminder', 'focus_duration', 'short_break_duration',
            'long_break_duration', 'pomodoros_until_long_break',
            'greeting_enabled', 'daily_content_enabled',
        ]
