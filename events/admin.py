from django.contrib import admin
from django.utils.html import format_html
from .models import Event, TicketType


class TicketTypeInline(admin.TabularInline):  # or admin.StackedInline for a bigger form
    model = TicketType
    extra = 1  # number of empty forms shown
    fields = ('name', 'price', 'available')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'price', 'organizer', 'created_at', 'image')
    list_filter = ['date']
    search_fields = ('title', 'description')
    ordering = ['-date']
    readonly_fields = ['created_at', 'image_preview']

    fieldsets = (
        ('Event Details', {
            'fields': ('title', 'description', 'date', 'time', 'location', 'price', 'image')
        }),
        ('Organizer Info', {
            'fields': ('organizer', 'created_at', 'image_preview')
        }),
    )

    inlines = [TicketTypeInline]  # ✅ allows adding VIP/Regular/Group tickets inside event admin

    def save_model(self, request, obj, form, change):
        if not obj.organizer:
            obj.organizer = request.user
        super().save_model(request, obj, form, change)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="150" style="border-radius: 4px;" />', obj.image.url)
        return "No Image"

    image_preview.short_description = 'Preview'


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('event', 'name', 'price', 'available')
    list_filter = ['event', 'name']
    search_fields = ('event__title', 'name')
