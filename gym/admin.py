from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Member, CheckInOut

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'email', 'phone', 
                   'subscription_status', 'days_remaining', 'payment_type', 'receipt_number', 'qr_code_preview')
    list_filter = ('subscription_start', 'subscription_end')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    readonly_fields = ('uuid', 'qr_code_preview', 'created_at', 'updated_at')
    fieldsets = (
        ('Informazioni Personali', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Abbonamento', {
            'fields': ('subscription_start', 'subscription_end', 'payment_type', 'receipt_number')
        }),
        ('QR Code', {
            'fields': ('uuid', 'qr_code_image', 'qr_code_preview'),
            'classes': ('collapse',)
        }),
        ('Informazioni Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def subscription_status(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: green;">✓ Attivo</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Scaduto</span>'
        )
    subscription_status.short_description = "Stato Abbonamento"

    def qr_code_preview(self, obj):
        if obj.qr_code_image:
            return format_html(
                '<img src="{}" style="max-height: 50px;"/>',
                obj.qr_code_image.url
            )
        return "QR Code non generato"
    qr_code_preview.short_description = "QR Code"

@admin.register(CheckInOut)
class CheckInOutAdmin(admin.ModelAdmin):
    list_display = ('member', 'check_in', 'check_out', 'duration_display', 'colored_status', 'colored_subscription_status')
    list_filter = ('check_in', 'check_out')
    search_fields = ('member__first_name', 'member__last_name', 'member__email')
    readonly_fields = ('check_in', 'check_out')

    def duration_display(self, obj):
        if obj.duration:
            hours = obj.duration.total_seconds() / 3600
            return f"{hours:.1f} ore"
        return "In corso"
    duration_display.short_description = "Durata"

    def colored_status(self, obj):
        color = obj.status_color
        label = 'Attivo' if color == 'green' else 'Scaduto'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, label)
    colored_status.short_description = 'Stato'

    def colored_subscription_status(self, obj):
        color = 'green' if obj.subscription_status == 'attivo' else 'red'
        label = obj.get_subscription_status_display()
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, label)
    colored_subscription_status.short_description = 'Abbonamento al Check-in' 