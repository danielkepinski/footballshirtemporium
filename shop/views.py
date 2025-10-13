# shop/views.py
from django.shortcuts import get_object_or_404, render

from cart.forms import CartAddProductForm
from .models import Category, Product, Team


def home(request):
    return render(request, "shop/home.html", {"show_hero": True})


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
