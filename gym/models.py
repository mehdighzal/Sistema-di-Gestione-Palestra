from django.db import models
from django.utils import timezone
from django.core.validators import EmailValidator, RegexValidator
from django.db.models.signals import pre_save
from django.dispatch import receiver
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image

class Member(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.CharField(max_length=36, unique=True, editable=False)
    first_name = models.CharField(max_length=100, verbose_name="Nome")
    last_name = models.CharField(max_length=100, verbose_name="Cognome")
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        verbose_name="Email"
    )
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')],
        verbose_name="Telefono"
    )
    subscription_start = models.DateField(verbose_name="Data inizio abbonamento")
    subscription_end = models.DateField(verbose_name="Data fine abbonamento")
    medical_certificate_start = models.DateField(verbose_name="Data inizio certificato medico", null=True, blank=True)
    medical_certificate_end = models.DateField(verbose_name="Data fine certificato medico", null=True, blank=True)
    qr_code_image = models.ImageField(
        upload_to='qr_codes/',
        null=True,
        blank=True,
        verbose_name="QR Code"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    PAYMENT_CHOICES = [
        ('carta', 'Carta'),
        ('contanti', 'Contanti'),
    ]
    payment_type = models.CharField(
        max_length=10,
        choices=PAYMENT_CHOICES,
        default='carta',
        verbose_name="Tipo di Pagamento"
    )
    receipt_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Numero Ricevuta"
    )

    class Meta:
        verbose_name = "Membro"
        verbose_name_plural = "Membri"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def generate_qr_code(self):
        """Generate QR code image for the member"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(str(self.uuid))
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        # Save to ImageField
        filename = f'qr_code_{self.uuid}.png'
        self.qr_code_image.save(filename, File(buffer), save=False)

    @property
    def is_active(self):
        """Check if the subscription is active"""
        today = timezone.now().date()
        return self.subscription_start <= today <= self.subscription_end

    @property
    def days_remaining(self):
        """Calculate days remaining in subscription"""
        if self.subscription_end:
            today = timezone.now().date()
            delta = self.subscription_end - today
            return max(0, delta.days)
        return 0

    @property
    def is_medical_certificate_active(self):
        """Verifica se il certificato medico è attivo"""
        if not self.medical_certificate_end:
            return False
        today = timezone.now().date()
        return today <= self.medical_certificate_end

    @property
    def medical_certificate_days_remaining(self):
        """Calcola i giorni rimanenti del certificato medico"""
        if self.medical_certificate_end:
            today = timezone.now().date()
            delta = self.medical_certificate_end - today
            return max(0, delta.days)
        return 0

    @property
    def medical_certificate_status(self):
        """Restituisce lo stato del certificato medico"""
        if not self.medical_certificate_end:
            return "Non specificato"
        return "Attivo" if self.is_medical_certificate_active else "Scaduto"

    @property
    def can_access_gym(self):
        """Verifica se il membro può accedere alla palestra (abbonamento E certificato validi)"""
        return self.is_active and self.is_medical_certificate_active

@receiver(pre_save, sender=Member)
def generate_member_qr_code(sender, instance, **kwargs):
    """Signal to generate QR code before saving"""
    if not instance.qr_code_image:
        instance.generate_qr_code()

class CheckInOut(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name="Membro")
    check_in = models.DateTimeField(auto_now_add=True, verbose_name="Check-in")
    check_out = models.DateTimeField(null=True, blank=True, verbose_name="Check-out")
    SUBSCRIPTION_STATUS_CHOICES = [
        ('attivo', 'Attivo'),
        ('scaduto', 'Scaduto'),
    ]
    subscription_status = models.CharField(
        max_length=10,
        choices=SUBSCRIPTION_STATUS_CHOICES,
        default='attivo',
        verbose_name="Stato Abbonamento al Check-in"
    )
    
    class Meta:
        verbose_name = "Accesso"
        verbose_name_plural = "Accessi"
        ordering = ['-check_in']

    def __str__(self):
        return f"{self.member} - {self.check_in.strftime('%d/%m/%Y %H:%M')}"

    @property
    def duration(self):
        """Calculate duration of gym visit"""
        if not self.check_out:
            return None
        return self.check_out - self.check_in 

    @property
    def is_active(self):
        """Return True if check-out is not set and not expired (within 2 hours)."""
        if self.check_out:
            return False
        now = timezone.now()
        return (now - self.check_in).total_seconds() <= 7200

    @property
    def status_color(self):
        if self.is_active:
            return 'green'
        return 'red' 