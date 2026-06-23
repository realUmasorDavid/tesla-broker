from django import forms
from .models import KYCVerification, Profile
from django.utils.translation import gettext_lazy as _

INPUT  = 'w-full px-4 py-3 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-black focus:border-black transition'
SELECT = INPUT + ' bg-white'
FILE   = ('block w-full text-sm text-gray-500 '
          'file:mr-4 file:py-2 file:px-4 '
          'file:rounded-lg file:border-0 '
          'file:text-sm file:font-medium '
          'file:bg-gray-900 file:text-white '
          'hover:file:bg-gray-700 transition')
 
 
class KYCForm(forms.ModelForm):
 
    class Meta:
        model  = KYCVerification
        fields = [
            'id_type', 'id_number',
            'id_front', 'id_back',
            'selfie',
            # 'address_type', 'proof_of_address',
        ]
        widgets = {
            'id_type': forms.Select(attrs={'class': SELECT}),
            'id_number': forms.TextInput(attrs={
                'class': INPUT,
                'placeholder': 'Enter your document number',
            }),
            'id_front': forms.ClearableFileInput(attrs={'class': FILE, 'accept': 'image/*'}),
            'id_back':  forms.ClearableFileInput(attrs={'class': FILE, 'accept': 'image/*'}),
            'selfie':   forms.ClearableFileInput(attrs={'class': FILE, 'accept': 'image/*'}),
            'address_type': forms.Select(attrs={'class': SELECT}),
            'proof_of_address': forms.ClearableFileInput(attrs={
                'class': FILE, 'accept': 'image/*,.pdf'
            }),
        }
        labels = {
            'id_type':    'Document Type',
            'id_number':  'Document Number',
            'id_front':   'Front of Document',
            'id_back':    'Back of Document (not required for passport)',
            'selfie':     'Selfie Holding Your Document',
            'address_type':      'Address Document Type',
            'proof_of_address':  'Proof of Address',
        }
 
    def clean(self):
        cleaned = super().clean()
        id_type = cleaned.get('id_type')
        id_number = cleaned.get('id_number')
        id_front  = cleaned.get('id_front')
        selfie    = cleaned.get('selfie')
 
        if not id_type:
            self.add_error('id_type', 'Please select a document type.')
        if not id_number:
            self.add_error('id_number', 'Please enter your document number.')
        if not id_front:
            self.add_error('id_front', 'Please upload the front of your document.')
        if not selfie:
            self.add_error('selfie', 'Please upload a selfie holding your document.')
 
        return cleaned
    
COUNTRY_CHOICES = [
    ('', 'Select Country'),
    ('Algeria', 'Algeria'),
    ('Angola', 'Angola'),
    ('Argentina', 'Argentina'),
    ('Armenia', 'Armenia'),
    ('Australia', 'Australia'),
    ('Austria', 'Austria'),
    ('Azerbaijan', 'Azerbaijan'),
    ('Bahrain', 'Bahrain'),
    ('Bangladesh', 'Bangladesh'),
    ('Belarus', 'Belarus'),
    ('Belgium', 'Belgium'),
    ('Bolivia', 'Bolivia'),
    ('Bosnia & Herzegovina', 'Bosnia & Herzegovina'),
    ('Botswana', 'Botswana'),
    ('Brazil', 'Brazil'),
    ('Bulgaria', 'Bulgaria'),
    ('Cameroon', 'Cameroon'),
    ('Canada', 'Canada'),
    ('Chile', 'Chile'),
    ('China', 'China'),
    ('Colombia', 'Colombia'),
    ('Croatia', 'Croatia'),
    ('Czech Republic', 'Czech Republic'),
    ('Denmark', 'Denmark'),
    ('Ecuador', 'Ecuador'),
    ('Egypt', 'Egypt'),
    ('Ethiopia', 'Ethiopia'),
    ('Finland', 'Finland'),
    ('France', 'France'),
    ('Georgia', 'Georgia'),
    ('Germany', 'Germany'),
    ('Ghana', 'Ghana'),
    ('Greece', 'Greece'),
    ('Guatemala', 'Guatemala'),
    ('Hungary', 'Hungary'),
    ('India', 'India'),
    ('Indonesia', 'Indonesia'),
    ('Iran', 'Iran'),
    ('Iraq', 'Iraq'),
    ('Ireland', 'Ireland'),
    ('Israel', 'Israel'),
    ('Italy', 'Italy'),
    ('Japan', 'Japan'),
    ('Jordan', 'Jordan'),
    ('Kazakhstan', 'Kazakhstan'),
    ('Kenya', 'Kenya'),
    ('Kuwait', 'Kuwait'),
    ('Lebanon', 'Lebanon'),
    ('Libya', 'Libya'),
    ('Malaysia', 'Malaysia'),
    ('Mexico', 'Mexico'),
    ('Morocco', 'Morocco'),
    ('Mozambique', 'Mozambique'),
    ('Myanmar', 'Myanmar'),
    ('Nepal', 'Nepal'),
    ('Netherlands', 'Netherlands'),
    ('New Zealand', 'New Zealand'),
    ('Nigeria', 'Nigeria'),
    ('Norway', 'Norway'),
    ('Oman', 'Oman'),
    ('Pakistan', 'Pakistan'),
    ('Panama', 'Panama'),
    ('Paraguay', 'Paraguay'),
    ('Peru', 'Peru'),
    ('Philippines', 'Philippines'),
    ('Poland', 'Poland'),
    ('Portugal', 'Portugal'),
    ('Qatar', 'Qatar'),
    ('Romania', 'Romania'),
    ('Russia', 'Russia'),
    ('Rwanda', 'Rwanda'),
    ('Saudi Arabia', 'Saudi Arabia'),
    ('Senegal', 'Senegal'),
    ('Serbia', 'Serbia'),
    ('Singapore', 'Singapore'),
    ('Slovakia', 'Slovakia'),
    ('Slovenia', 'Slovenia'),
    ('Somalia', 'Somalia'),
    ('South Africa', 'South Africa'),
    ('South Korea', 'South Korea'),
    ('Spain', 'Spain'),
    ('Sri Lanka', 'Sri Lanka'),
    ('Sudan', 'Sudan'),
    ('Sweden', 'Sweden'),
    ('Switzerland', 'Switzerland'),
    ('Syria', 'Syria'),
    ('Taiwan', 'Taiwan'),
    ('Tanzania', 'Tanzania'),
    ('Thailand', 'Thailand'),
    ('Tunisia', 'Tunisia'),
    ('Turkey', 'Turkey'),
    ('UAE', 'UAE'),
    ('Uganda', 'Uganda'),
    ('Ukraine', 'Ukraine'),
    ('United Kingdom', 'United Kingdom'),
    ('United States', 'United States'),
    ('Uruguay', 'Uruguay'),
    ('Uzbekistan', 'Uzbekistan'),
    ('Venezuela', 'Venezuela'),
    ('Vietnam', 'Vietnam'),
    ('Yemen', 'Yemen'),
    ('Zambia', 'Zambia'),
    ('Zimbabwe', 'Zimbabwe'),
]

class ProfileUpdateForm(forms.ModelForm):
    # Fields from User model
    first_name = forms.CharField(
        max_length=150, required=True, label='First Name',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition',
            'placeholder': 'First name',
        })
    )
    last_name = forms.CharField(
        max_length=150, required=True, label='Last Name',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition',
            'placeholder': 'Last name',
        })
    )
    email = forms.EmailField(
        required=True, label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition',
            'placeholder': 'email@example.com',
        })
    )
 
    class Meta:
        model = Profile
        fields = ['phone_number', 'date_of_birth', 'address', 'city', 'country']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition',
                'placeholder': '+1 800 000 0000',
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition',
                'type': 'date',
            }),
            'address': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition',
                'placeholder': '123 Main St, Apt 4B',
                'id': 'address-input',
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition',
                'placeholder': 'City',
            }),
            'country': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition bg-white',
            }),
        }
        labels = {
            'phone_number':  'Phone Number',
            'date_of_birth': 'Date of Birth',
            'address':       'Residential Address',
            'city':          'City',
            'country':       'Country',
        }
 
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['country'].choices = COUNTRY_CHOICES
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial  = user.last_name
            self.fields['email'].initial      = user.email
 
    def save_user(self, user):
        """Call this after form.save() to persist User model fields."""
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        user.email      = self.cleaned_data['email']
        user.username   = self.cleaned_data['email']  # keep username = email
        user.save(update_fields=['first_name', 'last_name', 'email', 'username'])