
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from .forms import PersonForm, TransactionForm
from .models import Person, Transaction, refresh_statuses


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

