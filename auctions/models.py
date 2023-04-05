from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

    def __str__(self):
        return f"{self.id}: {self.username}"


class Listing(models.Model):
    title = models.CharField(max_length=128)
    description = models.CharField(max_length=1024)
    price = models.FloatField()
    image = models.URLField(blank=True)
    category = models.CharField(max_length=64)
    watchers = models.ManyToManyField(User, blank=True, related_name="watchlist")
    active = models.BooleanField(default=True)
    winner = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name="victories")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id}: {self.title}, {self.category}, {self.price}"


class Bid(models.Model):
    amount = models.FloatField(default=0.00)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id}: {self.user.username} bids on Listing:{self.listing.id} for {self.amount}"


class Comment(models.Model):
    content = models.CharField(max_length=512, default="")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on Listing:{self.listing.id}"