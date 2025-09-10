from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Member, CheckInOut

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'email', 'phone', 'subscription_status', 'days_remaining', 'medical_certificate_status_colored', 'medical_certificate_days_remaining', 'registration_fee_status_colored', 'registration_fee_paid_until', 'photo_preview', 'take_photo_button', 'payment_type', 'receipt_number', 'qr_code_preview', 'download_qr_buttons', 'send_qr_email_button')
    list_filter = ('subscription_start', 'subscription_end', 'medical_certificate_start', 'medical_certificate_end', 'payment_type', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    readonly_fields = ('uuid', 'qr_code_preview', 'photo_preview', 'take_photo_button', 'download_qr_buttons', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Informazioni Personali', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'photo', 'photo_preview', 'take_photo_button')
        }),
        ('Abbonamento', {
            'fields': ('subscription_start', 'subscription_end', 'payment_type', 'receipt_number')
        }),
        ('Certificato Medico', {
            'fields': ('medical_certificate_start', 'medical_certificate_end')
        }),
        ('Iscrizione annuale (20€)', {
            'fields': ('registration_fee_paid_until',)
        }),
        ('Sistema', {
            'fields': ('uuid', 'qr_code_preview', 'download_qr_buttons'),
            'classes': ('collapse',)
        }),
        ('Metadati', {
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
            return format_html('<img src="{}" width="100" height="100" />', obj.qr_code_image.url)
        return "Nessun QR Code"
    qr_code_preview.short_description = 'QR Code'

    def medical_certificate_status_colored(self, obj):
        """Mostra lo stato del certificato medico con colori"""
        status = obj.medical_certificate_status
        if status == "Attivo":
            color = 'green'
        elif status == "Scaduto":
            color = 'red'
        else:
            color = 'orange'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, status)
    medical_certificate_status_colored.short_description = 'Stato Certificato'

    def registration_fee_status_colored(self, obj):
        status = obj.registration_fee_status
        if status == 'Attiva':
            color = 'green'
        elif status == 'Scaduta':
            color = 'red'
        else:
            color = 'orange'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, status)
    registration_fee_status_colored.short_description = 'Iscrizione (20€)'

    def photo_preview(self, obj):
        """Mostra la foto del membro"""
        if obj.photo:
            return format_html('<img src="{}" width="60" height="60" style="border-radius: 50%; object-fit: cover;" />', obj.photo.url)
        return "Nessuna foto"
    photo_preview.short_description = 'Foto'

    def take_photo_button(self, obj):
        """Pulsante per scattare foto live"""
        if not obj.pk:
            return "Salva il membro prima di scattare una foto"
        url = reverse('gym:take_photo', kwargs={'member_id': obj.pk})
        return format_html(
            '<a href="{}" class="button" target="_blank">📷 Scatta Foto</a>',
            url
        )
    take_photo_button.short_description = 'Foto Live'

    def download_qr_buttons(self, obj):
        """Pulsanti per scaricare il QR code"""
        if obj.uuid:
            return format_html(
                '<a href="{}?format=png" class="button" target="_blank">📱 PNG</a> '
                '<a href="{}?format=pdf" class="button" target="_blank">📄 PDF</a>',
                f'/download-qr/{obj.pk}/',
                f'/download-qr/{obj.pk}/'
            )
        return "QR non disponibile"
    download_qr_buttons.short_description = 'Download QR'

    def send_qr_email_button(self, obj):
        if obj.email:
            return format_html(
                '<a href="{}" class="button">✉️ Invia QR + Tessera</a>',
                f'/send-qr-email/{obj.pk}/'
            )
        return "Email non disponibile"
    send_qr_email_button.short_description = 'Invia Email'

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