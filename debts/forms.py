from django import forms
from django.utils import timezone

from .models import Person, Transaction, Repayment

class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ('person_name', 'relationship', 'contact_info')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_person_name(self):  # BR-06
        name = self.cleaned_data['person_name'].strip()
        if Person.objects.filter(user=self.user, person_name__iexact=name).exists():
            raise forms.ValidationError('You already have a person with this name.')
        return name


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ('person', 'direction', 'principal_amount', 'transaction_date',
                  'due_date', 'purpose', 'notes')
        widgets = {
            'transaction_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'due_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # BR-03/BR-06: a user can only pick their own people
        self.fields['person'].queryset = Person.objects.filter(user=user)
        self.fields['person'].empty_label = 'Select a person'

    def clean(self):
        data = super().clean()
        tdate = data.get('transaction_date')
        due = data.get('due_date')
        amount = data.get('principal_amount')
        direction = data.get('direction')

        if tdate and tdate > timezone.localdate():  # BR-10
            self.add_error('transaction_date', 'The transaction date cannot be later than today.')
        if tdate and due and due < tdate:  # BR-09
            self.add_error('due_date', 'The due date must be on or after the transaction date.')

        if self.instance.pk:  # editing an existing transaction
            paid = self.instance.amount_paid
            if amount is not None and amount < paid:  # BR-17
                self.add_error('principal_amount',
                               f'The amount cannot be lower than the ₱{paid} already repaid.')
            if paid > 0 and direction and direction != self.instance.direction:  # BR-07
                self.add_error('direction',
                               'The direction cannot be changed after a repayment has been recorded.')
        return data
    
    class RepaymentForm(forms.ModelForm):
    class Meta:
        model = Repayment
        fields = ('amount_paid', 'payment_date', 'notes')
        widgets = {
            'payment_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    def __init__(self, *args, transaction=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.transaction = transaction

    def clean(self):
        data = super().clean()
        amount = data.get('amount_paid')
        pdate = data.get('payment_date')
        t = self.transaction

        if t.remaining_balance <= 0:  # BR-16
            raise forms.ValidationError('This transaction is already fully paid.')
        if amount is not None and amount > t.remaining_balance:  # BR-12
            self.add_error('amount_paid',
                           f'The payment cannot be more than the remaining balance of ₱{t.remaining_balance}.')
        if pdate:
            if pdate < t.transaction_date:  # BR-13
                self.add_error('payment_date', 'The payment date cannot be earlier than the transaction date.')
            if pdate > timezone.localdate():
                self.add_error('payment_date', 'The payment date cannot be later than today.')
        return data