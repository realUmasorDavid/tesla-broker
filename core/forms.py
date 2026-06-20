from django import forms
from .models import KYCVerification, Profile

class KYCForm(forms.ModelForm):
    class Meta:
        model = KYCVerification
        fields = []  # Dynamically populated

    def __init__(self, *args, tier=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tier = tier or 'tier1'

        # Base widget styling
        widget_attrs = {
            'class': 'w-full px-5 py-4 border border-gray-300 rounded-3xl focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition'
        }

        if self.tier == 'tier1':
            self.fields['id_type'] = forms.ChoiceField(
                choices=[
                    ('national_id', 'National ID'),
                    ('drivers_license', "Driver's License"),
                ],
                widget=forms.Select(attrs=widget_attrs)
            )
            self.fields['id_number'] = forms.CharField(
                max_length=100,
                widget=forms.TextInput(attrs=widget_attrs)
            )
            self.fields['id_front'] = forms.ImageField(
                widget=forms.ClearableFileInput(attrs={
                    'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-3 file:px-6 file:rounded-3xl file:border-0 file:text-sm file:font-medium file:bg-black file:text-white hover:file:bg-zinc-800'
                })
            )
            self.fields['selfie'] = forms.ImageField(
                widget=forms.ClearableFileInput(attrs={
                    'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-3 file:px-6 file:rounded-3xl file:border-0 file:text-sm file:font-medium file:bg-black file:text-white hover:file:bg-zinc-800'
                })
            )

        elif self.tier == 'tier2':
            self.fields['passport_number'] = forms.CharField(
                max_length=100,
                widget=forms.TextInput(attrs=widget_attrs)
            )
            self.fields['passport_image'] = forms.ImageField(
                widget=forms.ClearableFileInput(attrs={
                    'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-3 file:px-6 file:rounded-3xl file:border-0 file:text-sm file:font-medium file:bg-black file:text-white hover:file:bg-zinc-800'
                })
            )

        elif self.tier == 'tier3':
            self.fields['proof_of_address'] = forms.ImageField(
                widget=forms.ClearableFileInput(attrs={
                    'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-3 file:px-6 file:rounded-3xl file:border-0 file:text-sm file:font-medium file:bg-black file:text-white hover:file:bg-zinc-800'
                })
            )
            self.fields['address_type'] = forms.ChoiceField(
                choices=[
                    ('utility_bill', 'Utility Bill'),
                    ('bank_statement', 'Bank Statement'),
                    ('rental_agreement', 'Rental Agreement'),
                ],
                widget=forms.Select(attrs=widget_attrs)
            )

        # Add labels for all fields
        for field_name, field in self.fields.items():
            field.label = field.label or field_name.replace('_', ' ').title()

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'date_of_birth', 'address', 'city', 'country']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full px-4 py-3 rounded-2xl border border-gray-300 focus:outline-none focus:border-black resize-none'})