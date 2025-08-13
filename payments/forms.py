from django import forms

class PhoneForm(forms.Form):
    phone = forms.CharField(label="Phone Number (e.g. 2547...)", max_length=20)
