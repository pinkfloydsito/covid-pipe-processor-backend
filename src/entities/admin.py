from django.utils.translation import gettext_lazy as _
from django.template.response import TemplateResponse
from django.shortcuts import render
from django.contrib import admin
from django.db.models import Q
from entities.models import CovidPipe, Location, Movement 
from entities.forms import CovidPipeForm


class DateListFilter(admin.SimpleListFilter):
    title = _('date')

    parameter_name = 'date'

    def lookups(self, request, model_admin):
        movements = Movement.objects.all().values_list('date__date').distinct()

        return [[ date[0], date[0] ] for date in movements]

    def queryset(self, request, queryset):
        if self.value():
            movements = queryset.filter(Q(date__date=self.value()))
            return movements


class PipeListFilter(admin.SimpleListFilter):
    title = _('pipe')

    parameter_name = 'pipe'

    def lookups(self, request, model_admin):
        pipes = CovidPipe.objects.all().distinct()

        return [[pipe.id, pipe.name] for pipe in pipes]

    def queryset(self, request, queryset):
        if self.value():
            movements = queryset.filter(Q(pipe=self.value()))
            return movements

class LocationFilter(admin.SimpleListFilter):
    title = _('Last Location')

    parameter_name = 'last_movement'

    def lookups(self, request, model_admin):
        locations = Location.objects.all().distinct()

        result = []
        result.append(['empty', 'Empty'])
        result.extend([[location.id, location.name] for location in locations])
        return result

    def queryset(self, request, queryset):
        if self.value() == 'empty':
            return queryset.filter(Q(last_movement__isnull=True))
        if self.value():
            pipes = queryset.filter(Q(last_movement__destination=self.value()))
            return pipes

class OriginListFilter(admin.SimpleListFilter):
    title = _('origin')

    parameter_name = 'origin'

    def lookups(self, request, model_admin):
        locations = Location.objects.all().distinct()

        return [[location.id, location.name] for location in locations]

    def queryset(self, request, queryset):
        if self.value():
            movements = queryset.filter(Q(origin=self.value()))
            return movements

class DestinationListFilter(admin.SimpleListFilter):
    title = _('destination')

    parameter_name = 'destination'

    def lookups(self, request, model_admin):
        locations = Location.objects.all().distinct()
        return [[location.id, location.name] for location in locations]

    def queryset(self, request, queryset):
        if self.value():
            movements = queryset.filter(Q(destination=self.value()))
            return movements


class PipeAdmin(admin.ModelAdmin):
    autocomplete_fields = ('last_movement', )
    list_per_page = 20000
    actions = ['move', ]
    search_fields = ['name']
    form = CovidPipeForm
    list_filter = ('con_muestra', LocationFilter, )
    
    def move(self, request, queryset):
        locations = Location.objects.all()
        if 'apply' in request.POST:
            location = request.POST.get('location')[0]
            description = request.POST.get('description')[0]
            has_muestra = request.POST.get('con_muestra', None)
            con_muestra = False
            if has_muestra is not None:
                con_muestra = True

            for pipe in queryset:
                pipe.con_muestra = con_muestra
                pipe.save()
                Movement.objects.create(description=description, origin=pipe.last_movement.destination if pipe.last_movement else None,
                                        destination=Location.objects.get(id=location), pipe=pipe)
        else:
            return render(request, 'admin/move.html', context={'pipes':queryset, 'locations': locations})

    fieldsets = (
        (None, {
            'fields': ('name', 'range_pipes', 'last_movement', 'con_muestra'),
        }),
    )

    move.short_description = "Mover pipes"


class MovementAdmin(admin.ModelAdmin):
    search_fields = ('destination__name', )
    autocomplete_fields = ('pipe', 'destination', 'origin', )
    list_filter = (DateListFilter,
        OriginListFilter, DestinationListFilter, PipeListFilter, )
    list_display = ('id', 'origin', 'destination', 'created')


class LocationAdmin(admin.ModelAdmin):
    search_fields = ['name', ]


admin.site.register(Movement, MovementAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(CovidPipe, PipeAdmin)
