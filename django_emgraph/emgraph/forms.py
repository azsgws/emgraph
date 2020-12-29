from django import forms

CATEGORIES = (
    ('constructors', 'constructors'),
    ('theorems', 'theorems'),
    ('registrations', 'registrations'),
    ('schemes', 'schemes'),
    ('definitions', 'definitions'),
    ('requirements', 'requirements'),
    ('expansions', 'expansions'),
    ('equalities', 'equalities'),
    )

class CategoriesForm(forms.Form):
    categories = forms.ChoiceField(
        label="category",
        required=True,
        widget=forms.CheckboxSelectMultiple,
        choices=CATEGORIES
    )
