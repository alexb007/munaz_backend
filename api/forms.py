from django import forms

from api.models import ConstructionObject, ConstructionObjectDocumentType


class ConstructionObjectForm(forms.ModelForm):
    class Meta:
        model = ConstructionObject
        fields = '__all__'

        def clean_title(self):
            print("CLEAN TITLE")

        def clean(self):
            print("CLEANING")
            required_document_types = set(
                ConstructionObjectDocumentType.objects.filter(required=True).values_list('id', flat=True))
            uploaded_document_types = set(self.model.documents.values_list("document_type__id", flat=True))

            diff = required_document_types.difference(uploaded_document_types)
            print(diff)
            print("ASDSAD")
            if len(diff) > 0:
                raise forms.ValidationError("Iltimos barcha majburiy hujjatlarni biriktiring")
            return self.cleaned_data


class GenerateUsersForm(forms.Form):
    num_users = forms.IntegerField(
        label="Number of users to generate",
        min_value=1,
        max_value=10000,
        initial=100,
        help_text="Enter the number of random users to create and export."
    )