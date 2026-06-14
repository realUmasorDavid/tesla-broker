from django import forms
from .models import KYCVerification, Profile

class KYCForm(forms.ModelForm):
    class Meta:
        model = KYCVerification
        fields = ['id_type', 'id_number', 'id_front', 'id_back', 'selfie']
        widgets = {
            'id_number': forms.TextInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full px-4 py-3 rounded-2xl border border-gray-300 focus:outline-none focus:border-black resize-none'})

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'date_of_birth', 'address', 'city', 'country']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full px-4 py-3 rounded-2xl border border-gray-300 focus:outline-none focus:border-black resize-none'})