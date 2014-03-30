from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from arbeitsplan.models import Mitgliedsstatus, Mitglied, Aufgabengruppe, Aufgabe, Meldung, Zuteilung


class MitgliedInline (admin.StackedInline):
    model = Mitglied
    can_delete = False
    verbose_name_plural = "Mitglieder"

class UserAdmin (UserAdmin):
    inlines = (MitgliedInline, )

    
admin.site.unregister(User)
admin.site.register (User, UserAdmin)



admin.site.register(Mitgliedsstatus)
# admin.site.register(Mitglied)
admin.site.register(Aufgabengruppe)
admin.site.register(Aufgabe)
admin.site.register(Meldung)
admin.site.register(Zuteilung)


