from django import forms
from .models import KYCVerification, Profile
from django.utils.translation import gettext_lazy as _

class KYCForm(forms.ModelForm):
    class Meta:
        model = KYCVerification
        fields = '__all__'   # Important: Include all fields

    def __init__(self, *args, tier=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tier = tier or 'tier1'

        widget_attrs = {
            'class': 'w-full px-5 py-4 border border-gray-300 rounded-3xl focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition'
        }

        file_attrs = {
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-3 file:px-6 file:rounded-3xl file:border-0 file:text-sm file:font-medium file:bg-black file:text-white hover:file:bg-zinc-800'
        }

        # Hide fields that are not for current tier
        for field_name in list(self.fields.keys()):
            if self.tier == 'tier1':
                if field_name not in ['national_id_number', 'national_id_front', 'national_id_back', 'drivers_license_number', 'drivers_license_front', 'drivers_license_back', 'selfie']:
                    self.fields.pop(field_name)
            elif self.tier == 'tier2':
                if field_name not in ['passport_number', 'passport_image']:
                    self.fields.pop(field_name)
            elif self.tier == 'tier3':
                if field_name not in ['proof_of_address', 'address_type']:
                    self.fields.pop(field_name)

        # Tier 1 - Both National ID and Driver's License
        if self.tier == 'tier1':
            self.fields['national_id_number'] = forms.CharField(max_length=100, widget=forms.TextInput(attrs=widget_attrs))
            self.fields['national_id_front'] = forms.ImageField(widget=forms.ClearableFileInput(attrs=file_attrs))
            self.fields['national_id_back'] = forms.ImageField(widget=forms.ClearableFileInput(attrs=file_attrs))

            self.fields['drivers_license_number'] = forms.CharField(max_length=100, widget=forms.TextInput(attrs=widget_attrs))
            self.fields['drivers_license_front'] = forms.ImageField(widget=forms.ClearableFileInput(attrs=file_attrs))
            self.fields['drivers_license_back'] = forms.ImageField(widget=forms.ClearableFileInput(attrs=file_attrs))

            self.fields['selfie'] = forms.ImageField(widget=forms.ClearableFileInput(attrs=file_attrs))

        # Tier 2 and 3 remain similar
        elif self.tier == 'tier2':
            self.fields['passport_number'] = forms.CharField(max_length=100, widget=forms.TextInput(attrs=widget_attrs))
            self.fields['passport_image'] = forms.ImageField(widget=forms.ClearableFileInput(attrs=file_attrs))

        elif self.tier == 'tier3':
            self.fields['proof_of_address'] = forms.ImageField(widget=forms.ClearableFileInput(attrs=file_attrs))
            self.fields['address_type'] = forms.ChoiceField(
                choices=[
                    ('utility_bill', 'Utility Bill'),
                    ('bank_statement', 'Bank Statement'),
                    ('rental_agreement', 'Rental Agreement'),
                ],
                widget=forms.Select(attrs=widget_attrs)
            )

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['date_of_birth', 'address', 'city', 'country']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        widget_attrs = {
            'class': 'w-full px-5 py-4 border border-gray-300 rounded-3xl focus:outline-none '
                     'focus:border-black focus:ring-1 focus:ring-black transition'
        }

        # Date of Birth
        self.fields['date_of_birth'].widget = forms.DateInput(
            attrs={**widget_attrs, 'type': 'date'}
        )
        self.fields['date_of_birth'].label = "Date of Birth"

        # Address
        self.fields['address'].widget = forms.Textarea(attrs={**widget_attrs, 'rows': 2})
        self.fields['address'].label = "Street Address"

        # City
        self.fields['city'].widget = forms.TextInput(attrs=widget_attrs)
        self.fields['city'].label = "City"

        # Country - Proper dropdown with many options
        self.fields['country'].widget = forms.Select(attrs=widget_attrs)
        self.fields['country'].label = "Country"
        
        # Important: Define choices here
        self.fields['country'].choices = [
            ('', 'Select Country'),
            ('United States', '🇺🇸 United States'),
            ('United Kingdom', '🇬🇧 United Kingdom'),
            ('Canada', '🇨🇦 Canada'),
            ('Nigeria', '🇳🇬 Nigeria'),
            ('Germany', '🇩🇪 Germany'),
            ('France', '🇫🇷 France'),
            ('India', '🇮🇳 India'),
            ('Brazil', '🇧🇷 Brazil'),
            ('Australia', '🇦🇺 Australia'),
            ('South Africa', '🇿🇦 South Africa'),
            ('Kenya', '🇰🇪 Kenya'),
            ('Ghana', '🇬🇭 Ghana'),
            ('United Arab Emirates', '🇦🇪 United Arab Emirates'),
            ('China', '🇨🇳 China'),
            ('Japan', '🇯🇵 Japan'),
        ]