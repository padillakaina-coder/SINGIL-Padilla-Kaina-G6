from django.contrib import messages
from django.db import transaction as db_tx
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from .forms import PersonForm, RepaymentForm, TransactionForm
from .models import Person, Repayment, Transaction, refresh_statuses


@role_required('USER')
def person_list(request):
    form = PersonForm(request.POST or None, user=request.user)
    if request.method == 'POST':
        if form.is_valid():
            person = form.save(commit=False)
            person.user = request.user
            person.save()
            messages.success(request, f'{person.person_name} was added.')
            return redirect('person_list')
        messages.error(request, 'Please fix the errors below.')
    people = Person.objects.filter(user=request.user)
    return render(request, 'debts/person_list.html', {'form': form, 'people': people})


@role_required('USER')
def person_delete(request, pk):
    person = get_object_or_404(Person, pk=pk, user=request.user)
    if request.method == 'POST':
        if person.transactions.exists():  # BR-11
            messages.error(request, 'This person has transactions and cannot be deleted.')
        else:
            person.delete()
            messages.success(request, 'Person deleted.')
    return redirect('person_list')


@role_required('USER')
def transaction_list(request):
    qs = Transaction.objects.filter(person__user=request.user).select_related('person', 'status')
    refresh_statuses(qs)
    return render(request, 'debts/transaction_list.html', {'transactions': qs})


@role_required('USER')
def transaction_create(request):
    form = TransactionForm(request.POST or None, user=request.user)
    if request.method == 'POST':
        if form.is_valid():
            t = form.save(commit=False)
            t.remaining_balance = t.principal_amount
            t.update_status()
            t.save()
            messages.success(request, 'Transaction recorded.')
            return redirect('transaction_detail', pk=t.pk)
        messages.error(request, 'Please fix the errors below.')
    return render(request, 'debts/transaction_form.html', {'form': form, 'title': 'Add Transaction'})


@role_required('USER')
def transaction_detail(request, pk):
    t = get_object_or_404(Transaction.objects.select_related('person', 'status'),
                          pk=pk, person__user=request.user)
    t.refresh_status()
    return render(request, 'debts/transaction_detail.html', {'transaction': t})


@role_required('USER')
def transaction_edit(request, pk):
    t = get_object_or_404(Transaction, pk=pk, person__user=request.user)
    paid = t.amount_paid  # computed before the form changes the instance
    form = TransactionForm(request.POST or None, instance=t, user=request.user)
    if request.method == 'POST':
        if form.is_valid():
            t = form.save(commit=False)
            t.remaining_balance = t.principal_amount - paid  # BR-14
            t.update_status()
            t.save()
            messages.success(request, 'Transaction updated.')
            return redirect('transaction_detail', pk=t.pk)
        messages.error(request, 'Please fix the errors below.')
    return render(request, 'debts/transaction_form.html', {'form': form, 'title': 'Edit Transaction'})


@role_required('USER')
def transaction_delete(request, pk):
    t = get_object_or_404(Transaction, pk=pk, person__user=request.user)
    if request.method == 'POST':
        t.delete()
        messages.success(request, 'Transaction deleted.')
        return redirect('transaction_list')
    return render(request, 'debts/confirm_delete.html', {'transaction': t})


@role_required('USER')
def repayment_create(request, pk):
    t = get_object_or_404(Transaction.objects.select_related('person'), pk=pk, person__user=request.user)
    if t.remaining_balance <= 0:  # BR-16
        messages.error(request, 'This transaction is already fully paid.')
        return redirect('transaction_detail', pk=t.pk)

    form = RepaymentForm(request.POST or None, transaction=t)
    if request.method == 'POST':
        if form.is_valid():
            with db_tx.atomic():
                locked = Transaction.objects.select_for_update().get(pk=t.pk)
                amount = form.cleaned_data['amount_paid']
                if amount > locked.remaining_balance:
                    form.add_error('amount_paid', 'The balance changed. Please check the amount.')
                else:
                    repayment = form.save(commit=False)
                    repayment.transaction = locked
                    # BR-15: FULL only if it equals the balance at the time of payment
                    repayment.payment_type = (Repayment.FULL if amount == locked.remaining_balance
                                              else Repayment.PARTIAL)
                    repayment.save()
                    locked.remaining_balance -= amount  # BR-14
                    locked.update_status()
                    locked.save()
                    messages.success(request, f'Repayment of ₱{amount} recorded.')
                    return redirect('transaction_detail', pk=t.pk)
        messages.error(request, 'Please fix the errors below.')
    return render(request, 'debts/repayment_form.html', {'form': form, 'transaction': t})
