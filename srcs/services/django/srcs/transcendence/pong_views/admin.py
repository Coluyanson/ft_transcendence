from django.contrib import admin

# Register your models here.

from .models import BaseUser, Match, Group, Message, Tournament, TournamentPartecipant

admin.site.register(BaseUser)
admin.site.register(Match)
admin.site.register(Group)
admin.site.register(Message)
admin.site.register(Tournament)
admin.site.register(TournamentPartecipant)