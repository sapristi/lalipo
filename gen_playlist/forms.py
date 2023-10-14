from django import forms


class FirstForm(forms.Form):
    raw_text = forms.TextInput()
    input_type = forms.ChoiceField(choices=["stoned circus", "plages musicales"])
