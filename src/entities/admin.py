from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.utils.translation import gettext_lazy as _
from rangefilter.filter import DateRangeFilter
from django.template.response import TemplateResponse
from django.shortcuts import render
from django.contrib import admin
from django.db.models import Q
from entities.models import CovidPipe, Location, Movement 
from entities.forms import CovidPipeForm

import re


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


class MovementInlineAdmin(admin.TabularInline):
    # autocomplete_fields = ['supervisor']
    model = Movement
    verbose_name_plural = "Movimientos"
    extra = 1


class PipeAdmin(admin.ModelAdmin):
    class Meta:
        ordering = ('name', '-myinteger',)

    inlines = (MovementInlineAdmin, )
    autocomplete_fields = ('last_movement', 'alias')
    list_per_page = 1000
    actions = ['move', 'update_dates',]
    search_fields = ['name']
    form = CovidPipeForm
    list_filter = (( 'last_movement__date_created', DateRangeFilter), ('last_movement__date_sent', DateRangeFilter), 'con_muestra', LocationFilter, )
    list_display = ('name', 'con_muestra', 'get_date_prepared', 'get_date_sent', 'get_from_location', 'get_location')

    # def get_ordering(self, request):
    #     return ['mystring', 'myinteger']

    def get_queryset(self, request):
        qs = super(PipeAdmin, self).get_queryset(request)
        qs = qs.extra(
            select={'myinteger': "NULLIF(regexp_replace(name, '\D','','g'), '')::numeric",
                    'mystring': "translate(name,'0123456789','')"
            }
        ).order_by('myinteger')
        return qs

    def ordernamiento(self, obj):
        return obj.myinteger

    ordernamiento.admin_order_field = 'myinteger'
    ordernamiento.short_name_description = 'Name Sort'

    def get_location(self, obj):
        return obj.last_movement.destination if obj.last_movement else 'No tiene ubicación'

    get_location.short_description = 'Destino'

    def get_from_location(self, obj):
        return obj.last_movement.origin if obj.last_movement else 'No tiene ubicación'

    get_from_location.short_description = 'Origen'

    def get_date_created(self, obj):
        return (obj.last_movement and obj.last_movement.date_created) or ''

    get_date_created.short_description = 'Fecha de creación'
    get_date_created.admin_order_field = 'last_movement__date_created'

    def get_date_sent(self, obj):
        return (obj.last_movement and obj.last_movement.date_sent) or ''

    get_date_sent.short_description = 'Fecha de envío'
    get_date_sent.admin_order_field = 'last_movement__date_sent'

    def get_date_prepared(self, obj):
        return (obj.last_movement and obj.last_movement.date_created) or ''

    get_date_prepared.short_description = 'Fecha de preparación'
    get_date_prepared.admin_order_field = 'last_movement__date_created'
    
    def move(self, request, queryset):
        locations = Location.objects.all()
        if 'apply' in request.POST:
            location = request.POST.get('location')
            description = request.POST.get('description')
            has_muestra = request.POST.get('con_muestra', None)
            con_muestra = False
            if has_muestra is not None:
                con_muestra = True

            inicio = request.POST.get('inicio', None)
            fin = request.POST.get('fin', None)

            if inicio and fin:
                try:
                    match_0 = re.match(r"([a-z]+)([0-9]+)", inicio, re.I)
                    match_1 = re.match(r"([a-z]+)([0-9]+)", fin, re.I)
                    items_0 = None
                    if match_0:
                        items_0 = match_0.groups()

                    items_1 = None
                    if match_1:
                        items_1 = match_1.groups()
                    
                    if match_0 and match_1:
                        for i in range(int(items_0[1]), int(items_1[1])+1):
                            try:
                                pipe = CovidPipe.objects.get(name="{}{}".format(items_0[0], str(i)))
                                pipe.con_muestra = con_muestra
                                pipe.save()
                                Movement.objects.create(
                                    description=description,
                                    origin=pipe.last_movement.destination if pipe.last_movement else None,
                                    destination=Location.objects.get(id=location), pipe=pipe)
                            except Exception:
                                pass
                    else:
                        for i in range(int(inicio), int(fin)+1):
                            try:
                                pipe = CovidPipe.objects.get(name=str(i))
                                pipe.con_muestra = con_muestra
                                pipe.save()
                                Movement.objects.create(
                                    description=description,
                                    origin=pipe.last_movement.destination if pipe.last_movement else None,
                                    destination=Location.objects.get(id=location), pipe=pipe)
                                
                            except Exception:
                                pass
                                    
                except Exception as e:
                    print(e)

                return
               
            for pipe in queryset:
                pipe.con_muestra = con_muestra
                pipe.save()
                Movement.objects.create(description=description, origin=pipe.last_movement.destination if pipe.last_movement else None, destination=Location.objects.get(id=location), pipe=pipe)

        else:
            return render(request, 'admin/move.html', context={'pipes':queryset, 'locations': locations})

    def update_dates(self, request, queryset):
        locations = Location.objects.all()
        if 'apply' in request.POST:
            location = request.POST.get('location')
            description = request.POST.get('description')
            has_muestra = request.POST.get('con_muestra', None)

            inicio = request.POST.get('inicio', None)
            fin = request.POST.get('fin', None)

            created = request.POST.get('created', None)
            moved = request.POST.get('moved', None)

            estado = request.POST.get('estado', None)

            if inicio and fin:
                try:
                    match_0 = re.match(r"([a-z]+)([0-9]+)", inicio, re.I)
                    match_1 = re.match(r"([a-z]+)([0-9]+)", fin, re.I)
                    items_0 = None
                    if match_0:
                        items_0 = match_0.groups()

                    items_1 = None
                    if match_1:
                        items_1 = match_1.groups()
                    
                    if match_0 and match_1:
                        for i in range(int(items_0[1]), int(items_1[1])+1):
                            try:
                                pipe = CovidPipe.objects.get(name="{}{}".format(items_0[0], str(i)))
                                if estado == 'creado':
                                    pipe.last_movement.state = Movement.CREATED
                                elif estado == 'enviado':
                                    pipe.last_movement.state = Movement.SENT

                                if created:
                                    pipe.last_movement.date_created = created

                                if moved:
                                    pipe.last_movement.date_sent = moved

                                pipe.last_movement.save()
                            except Exception as e:
                                print(e)
                    else:
                        for i in range(int(inicio), int(fin)+1):
                            try:
                                pipe = CovidPipe.objects.get(name=str(i))
                                if estado == 'creado':
                                    pipe.last_movement.state = Movement.CREATED
                                elif estado == 'enviado':
                                    pipe.last_movement.state = Movement.SENT

                                if created:
                                    pipe.last_movement.date_created = created

                                if moved:
                                    pipe.last_movement.date_sent = moved

                                pipe.last_movement.save()
                                
                            except Exception:
                                pass
                                    
                except Exception as e:
                    print(e)

                return
            for pipe in queryset:
                if estado == 'creado':
                    pipe.last_movement.state = Movement.CREATED
                elif estado == 'enviado':
                    pipe.last_movement.state = Movement.SENT

                if created:
                    pipe.last_movement.date_created = created

                if moved:
                    pipe.last_movement.date_sent = moved

                pipe.last_movement.save()

        else:
            return render(request, 'admin/update_dates.html', context={'pipes':queryset, 'locations': locations})

    fieldsets = (
        (None, {
            'fields': ('name', 'range_pipes', 'last_movement', 'con_muestra', 'alias'),
        }),
    )

    move.acts_on_all = True
    move.short_description = "Mover pipes"

    update_dates.acts_on_all = True
    update_dates.short_description = "Actualizar fechas / estado"


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
