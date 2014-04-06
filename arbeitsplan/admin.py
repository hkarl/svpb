from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from arbeitsplan.models import Aufgabengruppe, Aufgabe, Meldung, Zuteilung, Leistung


## class MitgliedInline (admin.StackedInline):
##     model = Mitglied
##     can_delete = False
##     verbose_name_plural = "Mitglieder"

## class UserAdmin (UserAdmin):
##     inlines = (MitgliedInline, )

class ZuteilungAdmin (admin.ModelAdmin):
    exclude = ('automatisch', )
    list_display = 'ausfuehrer', 'aufgabe'
    list_filter = ('ausfuehrer', 'aufgabe')
    
class AufgabeAdmin (admin.ModelAdmin):
    date_hierarchy = "datum"
    list_display = 'aufgabe', 'anzahl', 'datum',  'verantwortlich'
    list_filter = ('aufgabe', 'verantwortlich')

class MeldungAdmin (admin.ModelAdmin):
    date_hierachy = 'erstellt'
    list_display = 'melder', 'aufgabe'
    list_filter = ('melder', 'aufgabe')

class LeistungAdmin (admin.ModelAdmin):
    date_hierarchy = 'erstellt'
    list_display = ('melder', 'aufgabe', 'wann',  'status')
    list_filter = ('aufgabe__verantwortlich', 'status', 'aufgabe', 'wann',  )
    radio_fields = {'status': admin.HORIZONTAL}
    search_fields = ('melder__username',)

## admin.site.unregister(User)
## admin.site.register (User, UserAdmin)

admin.site.register (Zuteilung, ZuteilungAdmin)
admin.site.register(Aufgabengruppe)
admin.site.register(Aufgabe, AufgabeAdmin)
admin.site.register(Meldung, MeldungAdmin)
admin.site.register(Leistung, LeistungAdmin) 

