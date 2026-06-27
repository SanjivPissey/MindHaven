from django import forms
from .models import Contact
from .models import MentalHealthSurvey  


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']

class MentalHealthSurveyForm(forms.ModelForm):
    class Meta:
        model = MentalHealthSurvey 

        fields = "__all__"

