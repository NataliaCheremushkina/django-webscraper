import re
from django import forms


class PostForm(forms.Form):
    url = forms.URLField(widget=forms.TextInput(attrs={'placeholder': 'https://www.instagram.com/p/CFdH_JXAGyx/'}))
    caption = forms.BooleanField(required=False, label_suffix='')

    def clean_url(self):
        url = self.cleaned_data['url']
        if not re.fullmatch(r'https:\/\/www\.instagram\.com\/(?:p|tv)\/.+', url):
            raise forms.ValidationError('Error: url is wrong.')
        return url
