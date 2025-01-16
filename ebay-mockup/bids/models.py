from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Listing(models.Model):
    CATEGORIES = (('Fashion', 'Fashion'), ('Toys', 'Toys'),
                  ('Electronics', 'Electronics'),
                  ('Home', 'Home'), ('Other', 'Other'))
    item_name = models.CharField(max_length=100)
    description = models.TextField(max_length=600)
    starting_bid = models.PositiveIntegerField(blank=False)
    image_path = models.CharField(blank=True, max_length=500)
    category = models.CharField(default="Other", blank=True,
                                max_length=13, choices=CATEGORIES)
    is_active = models.BooleanField(default=True)
    seller = models.ForeignKey("User", on_delete=models.CASCADE)
    date_posted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item_name} listed by {self.seller} starting at {self.starting_bid} in {self.category}"


class Bid(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount_bid = models.PositiveIntegerField()
    date_bid = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.amount_bid} bid by {self.user} on {self.listing.item_name} on {self.date_bid}"


class Comment(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    comment_text = models.TextField(max_length=600)

    def __str__(self):
        return f"{self.author} on {self.listing.item_name}: {self.comment_text}. {self.date_added}"


class Watchlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    listing = models.ManyToManyField(Listing, blank=True)
