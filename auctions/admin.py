from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Listing, User, Bid, Comment


class ListingAdmin(admin.ModelAdmin):
    filter_horizontal = ("watchers",)


# Register your models here.
admin.site.register(Listing, ListingAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Bid)
admin.site.register(Comment)
