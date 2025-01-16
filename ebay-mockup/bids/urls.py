from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create-listing", views.create_listing, name="create-listing"),
    path("watchlist", views.view_watchlist, name="watchlist"),
    path("categories", views.categories, name="categories"),
    path("categories/<str:category>", views.categories, name="categories"),
    path("add-to-watchlist/<int:listing_id>", views.add_to_watchlist, name="add-to-watchlist"),
    path("place-bid/<int:listing_id>", views.place_bid, name="place-bid"),
    path("close-auction/<int:listing_id>", views.close_auction, name="close-auction"),
    path("comment/<int:listing_id>", views.comment, name="comment"),
    path("listing/<int:listing_id>", views.view_listing, name="listing")

]
