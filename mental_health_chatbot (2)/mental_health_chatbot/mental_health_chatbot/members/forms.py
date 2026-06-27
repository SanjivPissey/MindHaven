from django import forms
from django.contrib.auth.models import User
from .models import Contact
from .models import MentalHealthSurvey  
from .models import UserProfile


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']

class MentalHealthSurveyForm(forms.ModelForm):
    class Meta:
        model = MentalHealthSurvey
        exclude = ['user']

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['full_name', 'email', 'phone_number']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'required': True}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].disabled = True  # Prevent email change

    def clean(self):
        cleaned_data = super().clean()
        phone_number = cleaned_data.get('phone_number')
        if phone_number and not phone_number.isdigit():
            self.add_error('phone_number', 'Phone number must contain only digits')
        return cleaned_data

from django import forms
from .models import UserFeedback

CHOICES = [
    ('', 'Select...'),  # Adding a default option
    ('Very Helpful', 'Very Helpful'),
    ('Somewhat Helpful', 'Somewhat Helpful'),
    ('Not Helpful', 'Not Helpful')
]

EASE_CHOICES = [
    ('', 'Select...'),  # Adding a default option
    ('Very Easy', 'Very Easy'),
    ('Moderate', 'Moderate'),
    ('Difficult', 'Difficult')
]

USEFUL_CHOICES = [
    ('', 'Select...'),  # Adding a default option
    ('Very Useful', 'Very Useful'),
    ('Somewhat Useful', 'Somewhat Useful'),
    ('Not Useful', 'Not Useful')
]

SATISFACTION_CHOICES = [
    ('', 'Select...'),  # Adding a default option
    ('Very Satisfied', 'Very Satisfied'),
    ('Satisfied', 'Satisfied'),
    ('Unsatisfied', 'Unsatisfied')
]

RECOMMEND_CHOICES = [
    ('', 'Select...'),  # Adding a default option
    ('Yes', 'Yes'),
    ('Maybe', 'Maybe'),
    ('No', 'No')
]

class FeedbackForm(forms.ModelForm):
    # By not setting an initial value, no option will be pre-selected.
    helpful = forms.ChoiceField(choices=CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    ease_of_use = forms.ChoiceField(choices=EASE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    dashboard_feedback = forms.ChoiceField(choices=USEFUL_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    satisfaction = forms.ChoiceField(choices=SATISFACTION_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    recommend = forms.ChoiceField(choices=RECOMMEND_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = UserFeedback
        fields = ['helpful', 'ease_of_use', 'dashboard_feedback', 'satisfaction', 'recommend', 'suggestions']
        widgets = {
            'suggestions': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
