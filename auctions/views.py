from django import forms
from django.db.models import Max
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Listing, Bid, Comment


class NewListingForm(forms.Form):
    title = forms.CharField(widget=forms.TextInput(attrs={
        "class": "form-control", "autofocus": "", "placeholder": "Title"
    }), label="Title")
    description = forms.CharField(widget=forms.Textarea(attrs={
        "class": "form-control", "placeholder": "Description"
    }), label="Description")
    price = forms.FloatField(widget=forms.NumberInput(attrs={
        "class": "form-control", "placeholder": "Price", "step": "0.01"
    }), label="Price")
    image = forms.URLField(widget=forms.TextInput(attrs={
        "class": "form-control", "placeholder": "Image URL"
    }), label="Image")
    category = forms.CharField(widget=forms.TextInput(attrs={
        "class": "form-control", "placeholder": "Category"
    }), label="Category")


class NewBidForm(forms.Form):
    amount = forms.FloatField(widget=forms.NumberInput(attrs={
        "class": "form-control", "placeholder": "Bid", "step": "0.01"
    }), label="Bid")


class NewCommentForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea(attrs={
        "class": "form-control mb-3", "placeholder": "Enter your comment", "rows": "3"
    }), label="Comment")
    


def index(request):
    listings = Listing.objects.filter(active=True).all()
    return render(request, "auctions/index.html", {
        "listings": listings
    })


def categories(request):
    categories = []
    listings = Listing.objects.all()
    for listing in listings:
        if listing.category not in categories:
            categories.append(listing.category)

    return render(request, "auctions/categories.html", {
        "categories": categories
    })


def category(request, category):
    listings = Listing.objects.filter(active=True, category=category).all()
    return render(request, "auctions/category.html", {
        "listings": listings,
        "category": category
    })


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
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


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
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required(login_url="/login")
def create(request):
    if request.method == "POST":

        user = request.user
        form = NewListingForm(request.POST)

        if form.is_valid():
            title = form.cleaned_data["title"]
            description = form.cleaned_data["description"]
            price = form.cleaned_data["price"]
            image = form.cleaned_data["image"]
            category = form.cleaned_data["category"]

            listing = Listing(title=title, description=description, price=price, image=image, category=category, user=user)
            listing.save()

            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/create.html", {
                "form": form
            })

    return render(request, "auctions/create.html", {
        "form": NewListingForm()
    })


def listing(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    listing_bids = listing.bids.all()

    comments = listing.comments.all()

    user = request.user
    watchlisted = False
    winning = False
    if user in listing.watchers.all():
        watchlisted = True

    bid_count = len(listing_bids)
    if bid_count > 0:
        current_bid_amount = listing_bids.aggregate(Max("amount"))["amount__max"]
        current_bid = listing_bids.filter(amount=current_bid_amount).first()
        if current_bid.user == user:
            winning = True

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "form": NewBidForm(),
        "comment": NewCommentForm(),
        "comments": comments,
        "bid_count": bid_count,
        "watchlisted": watchlisted,
        "winning": winning
    })


@login_required(login_url="/login")
def watchlist(request):

    user = request.user
    watchlist = user.watchlist.all()

    if request.method == "POST":
        listing_id = int(request.POST["listing_id"])
        listing = Listing.objects.get(pk=listing_id)
        if listing in watchlist:
            user.watchlist.remove(listing)
        else:
            user.watchlist.add(listing)
        return HttpResponseRedirect(reverse("watchlist"))
    
    return render(request, "auctions/watchlist.html", {
        "watchlist": watchlist
    })


@login_required(login_url="/login")
def bid(request, listing_id):
    
    user = request.user
    listing = Listing.objects.get(pk=listing_id)

    form = NewBidForm(request.POST)

    if form.is_valid():
        amount = form.cleaned_data["amount"]

        if amount <= listing.price:
            return render(request, "auctions/error.html", {
                "code": "409: Conflict",
                "message": "Please enter a higher bid amount.",
                "listing_id": listing.id,
                "listing_price": listing.price
            }, status=409)

        bid = Bid(amount=amount, listing=listing, user=user)
        bid.save()

        listing.price = amount
        listing.save()

        return HttpResponseRedirect(reverse(viewname="listing", args=[listing_id]))

    return HttpResponseRedirect(reverse(viewname="listing", args=[listing_id]))


@login_required(login_url="/login")
def close(request, listing_id):
    user = request.user

    listing = Listing.objects.get(pk=listing_id)

    if user != listing.user:
        return HttpResponseRedirect(reverse("index"))

    listing.active = False

    listing_bids = listing.bids.all()
    bid_count = len(listing_bids)

    if bid_count > 0:
        winning_bid_amount = listing_bids.aggregate(Max("amount"))["amount__max"]
        winning_bid = listing_bids.get(amount=winning_bid_amount)
        winner = winning_bid.user
        listing.winner = winner
    
    listing.save()

    return HttpResponseRedirect(reverse("index"))


@login_required(login_url="/login")
def comment(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    user = request.user
    form = NewCommentForm(request.POST)

    if form.is_valid():
        content = form.cleaned_data["content"]
        new_comment = Comment(user=user, listing=listing, content=content)
        new_comment.save()

    return HttpResponseRedirect(reverse(viewname="listing", args=[listing_id]))


@login_required(login_url="/login")
def victories(request):
    victories = Listing.objects.filter(winner=request.user).all()

    return render(request, "auctions/victories.html", {
        "victories": victories
    })