# shop/views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from .forms import ContactForm
from django.db.models import Q

from cart.forms import CartAddProductForm
from .models import Category, Product, Team


def home(request):
    return render(request, "shop/home.html", {"show_hero": True})

def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            message = form.cleaned_data["message"]

            subject = f"Contact form message from {name}"
            body = (
                f"From: {name} <{email}>\n\n"
                f"Message:\n{message}"
            )

            # who receives the email (set your address here)
            to_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None)
            if not to_email:
                # fallback: show message but don't error
                messages.warning(request, "Email settings not configured; message not sent. (Set DEFAULT_FROM_EMAIL or EMAIL_HOST_USER)")
            else:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=to_email,   # use a verified sender (e.g., your SMTP user)
                    recipient_list=[to_email],
                    fail_silently=False,
                )
                messages.success(request, "Thanks! Your message has been sent.")

            return redirect("contact")  # stay on page with flash message
    else:
        form = ContactForm()

    return render(request, "shop/contact.html", {"form": form})


def product_list(request, category_slug=None, team_slug=None):
    """
    List products, optionally filtered by category or team.
    Also provides a small set of popular teams for quick filtering.
    """
    category = None
    team = None

    # Base queryset
    products_qs = (
        Product.objects.filter(available=True)
        .select_related("category", "team")
    )

    # Optional filters
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products_qs = products_qs.filter(category=category)

    if team_slug:
        team = get_object_or_404(Team, slug=team_slug)
        products_qs = products_qs.filter(team=team)

    # Popular teams (simple approach: distinct teams that have available products)
    popular_teams = (
        Team.objects.filter(products__available=True)
        .order_by("name")
        .distinct()[:8]
    )

    context = {
        "category": category,
        "team": team,
        "categories": Category.objects.all(),
        "products": products_qs,
        "popular_teams": popular_teams,
    }
    return render(request, "shop/product/list.html", context)


def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    cart_product_form = CartAddProductForm()
    return render(
        request,
        "shop/product/detail.html",
        {
            "product": product,
            "cart_product_form": cart_product_form,
        },
    )

def search(request):
    q = (request.GET.get("q") or "").strip()
    products = Product.objects.filter(available=True)
    if q:
        products = products.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(category__name__icontains=q)
        )

    return render(request, "shop/search.html", {
        "q": q,
        "products": products,
        "results_count": products.count(),
    },
    )