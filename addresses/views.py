from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .forms import AddressForm
from .models import Address


@login_required
def address_list(request):
    addresses = request.user.addresses.all()
    return render(request, "addresses/list.html", {"addresses": addresses})


@login_required
def address_create(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if address.is_default:
                request.user.addresses.update(is_default=False)
            address.save()
            return redirect("addresses:list")
    else:
        form = AddressForm()
    return render(request, "addresses/form.html", {"form": form, "title": "Add address"})


@login_required
def address_update(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            updated = form.save(commit=False)
            if updated.is_default:
                request.user.addresses.exclude(pk=address.pk).update(is_default=False)
            updated.save()
            return redirect("addresses:list")
    else:
        form = AddressForm(instance=address)
    return render(request, "addresses/form.html", {"form": form, "title": "Edit address"})


@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == "POST":
        address.delete()
        return redirect("addresses:list")
    return render(request, "addresses/confirm_delete.html", {"address": address})
