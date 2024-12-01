from django.contrib import admin
from .models import Email, User, ScheduledEmail

# Register your models here.

admin.site.register(Email)
admin.site.register(User)
admin.site.register(ScheduledEmail)