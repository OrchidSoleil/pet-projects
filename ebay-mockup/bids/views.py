from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.forms import ModelForm
from .models import User, Listing, Bid, Comment, Watchlist


def index(request):
    listings = Listing.objects.filter(is_active=True)
    # get the bids for active listings to update the current price
    for listing in listings:
        biggest_bid = (Bid.objects.filter(listing=listing.id).aggregate(Max('amount_bid')))["amount_bid__max"]
        if biggest_bid:
            listing.starting_bid = biggest_bid
    return render(request, "bids/index.html", {"listings": listings})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "bids/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "bids/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "bids/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "bids/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "bids/register.html")


@login_required
def create_listing(request):
    if request.method == "POST":
        form = CreateListingForm(request.POST)
        if form.is_valid():
            # save listing before committing to database, described in python crash course
            listing_instance = form.save(commit=False)
            # add additional data, excluded from form, then commit
            listing_instance.seller = request.user
            listing_instance.save()
            return index(request)
        else:
            # if form is invalid, it will be populated with data user inputted
            return render(request, "bids/create-listing.html", {"message": "Invalid data.", "form": form})
    form = CreateListingForm()
    return render(request, "bids/create-listing.html", {"form": form})


class CreateListingForm(ModelForm):
    class Meta:
        model = Listing
        fields = ['item_name', 'description', 'starting_bid', 'image_path', 'category']


def view_listing(request, listing_id, message=None):
    try:
        listing = Listing.objects.get(pk=listing_id)
    except Listing.DoesNotExist:
        return render(request, "bids/listing.html",
                      {"message": 'Listing Not Found.'})
    # check if listing on a watchlist
    # eric matthes in python crash course describes _set.
    comments = listing.comment_set.order_by("-date_added")
    comment_form = CommentForm()
    color = 'pink'
    biggest_bid = (Bid.objects.filter(listing=listing_id).aggregate(Max('amount_bid')))["amount_bid__max"]
    if request.user.is_authenticated:
        if Watchlist.objects.filter(user=request.user, listing=listing_id).exists():
            color = '#d9d2ca'
    if not listing.is_active:
        # https://stackoverflow.com/questions/7981837/aggregate-vs-annotate-in-django
        # ordering results by descending will get us the highest bidder at the top
        winner = Bid.objects.filter(listing=listing_id).annotate(Max('amount_bid')).order_by('-amount_bid')[0].user
        return render(request, "bids/listing.html", {
            "message": message,
            "listing": listing,
            "winner": winner,
            "comments": comments,
            "comment_form": comment_form,
            "biggest_bid": biggest_bid
        })
    form = BidForm()
    return render(request, "bids/listing.html", {"listing": listing, "form": form,
                                                 "comment_form": comment_form,
                                                 "comments": comments,
                                                 "message": message, "color": color,
                                                 "biggest_bid": biggest_bid})


@login_required
def add_to_watchlist(request, listing_id):
    # get a watchlist for current user if exists or create it
    watchlist, created = Watchlist.objects.get_or_create(user=request.user)
    # add specific listing to watchlist or remove if it's there
    if not Watchlist.objects.filter(user=request.user, listing=listing_id).exists():
        watchlist.listing.add(Listing.objects.get(pk=listing_id))
        message = 'Listing added to your Watchlist'
    else:
        watchlist.listing.remove(Listing.objects.get(pk=listing_id))
        message = 'Listing removed from your Watchlist'
    return view_listing(request, listing_id, message=message)


@login_required
def view_watchlist(request):
    watchlist_object = Watchlist.objects.filter(user=request.user)
    watchlist = []
    for owner in watchlist_object:
        listings = owner.listing.all()
        for listing in listings:
            # check if the item was bid upon and if so, update the price for view
            biggest_bid = (Bid.objects.filter(listing=listing.id).aggregate(Max('amount_bid')))["amount_bid__max"]
            if biggest_bid:
                listing.starting_bid = biggest_bid
            watchlist.append(listing)
    return render(request, "bids/watchlist.html", {"watchlist": watchlist})


@login_required
def place_bid(request, listing_id):
    form = BidForm(request.POST)
    # find the biggest bid and if there's None, compare to starting bid
    biggest_bid = (Bid.objects.filter(listing=listing_id).aggregate(Max('amount_bid')))["amount_bid__max"]
    if not biggest_bid:
        biggest_bid = (Listing.objects.get(pk=listing_id)).starting_bid
    if form.is_valid():
        amount_bid = form.cleaned_data["amount_bid"]
        if amount_bid <= biggest_bid:
            message = f"Your bid must be bigger than {biggest_bid}."
            return view_listing(request, listing_id, message=message)
        bid_instance = form.save(commit=False)
        # add additional data, excluded from form, then commit
        bid_instance.user = request.user
        bid_instance.listing = Listing.objects.get(id=listing_id)
        bid_instance.save()
        message = 'Your bid is placed.'
    return view_listing(request, listing_id, message=message)


class BidForm(ModelForm):
    class Meta:
        model = Bid
        fields = ['amount_bid']
        # remove labels from html
        labels = {
            "amount_bid": ""
        }


def close_auction(request, listing_id):
    # deactivate listing by changing the value in db
    listing = Listing.objects.get(id=listing_id)
    listing.is_active = False
    listing.save()
    message = "Auction is closed."
    return view_listing(request, listing_id, message=message)


@login_required
def comment(request, listing_id):
    form = CommentForm(request.POST)
    if form.is_valid():
        comment_instance = form.save(commit=False)
        # add additional data, excluded from form, then save
        comment_instance.author = request.user
        comment_instance.listing = Listing.objects.get(id=listing_id)
        comment_instance.save()
    return view_listing(request, listing_id)


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ["comment_text"]
        # remove label https://dev.to/greenteabiscuit/deleting-the-form-field-label-in-django-1i20
        labels = {
            "comment_text": ""
        }


def categories(request, category=None):
    listings = Listing.objects.filter(category=category, is_active=True)
    return render(request, 'bids/categories.html', {"listings": listings, "category": category})
