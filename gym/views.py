from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.contrib import messages
from .models import Member, CheckInOut
import qrcode
import io
import base64
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import EmailMessage
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image
# from .wallet import WalletPassGenerator

def home(request):
    """Home page with scan button"""
    return render(request, 'gym/home.html')

def scan(request):
    """QR code scanning page"""
    return render(request, 'gym/scan.html')

@require_http_methods(["GET", "POST"])
def scan_result(request):
    """Handle QR code scan results and check-in/check-out actions"""
    member_uuid = request.GET.get("uuid")
    action = request.GET.get("action")  # 'checkin' or 'checkout'
    context = {}
    if member_uuid:
        try:
            member = Member.objects.get(uuid=member_uuid)
            context['member'] = member
            if action == 'checkin':
                # Verifica abbonamento
                if not member.is_active:
                    CheckInOut.objects.create(
                        member=member,
                        subscription_status='scaduto'
                    )
                    context['status'] = 'error'
                    context['message'] = 'Abbonamento scaduto: non hai accesso.'
                # Verifica certificato medico
                elif not member.is_medical_certificate_active:
                    CheckInOut.objects.create(
                        member=member,
                        subscription_status='attivo'
                    )
                    context['status'] = 'error'
                    context['message'] = 'Certificato medico scaduto: non puoi entrare.'
                # Abbonamento e certificato validi
                else:
                    # Verifica se ha già fatto check-in
                    active_access = CheckInOut.objects.filter(
                        member=member, 
                        check_out__isnull=True
                    ).order_by('-check_in').first()
                    
                    if active_access and active_access.is_active:
                        context['status'] = 'success'
                        context['message'] = 'Hai già fatto il check-in!'
                    else:
                        CheckInOut.objects.create(
                            member=member,
                            subscription_status='attivo'
                        )
                        context['status'] = 'success'
                        context['message'] = 'Check-in effettuato con successo!'
            elif action == 'checkout':
                # Find last active access
                active_access = CheckInOut.objects.filter(member=member, check_out__isnull=True).order_by('-check_in').first()
                if active_access and active_access.is_active:
                    active_access.check_out = timezone.now()
                    active_access.save()
                    return render(request, "gym/see_you_later.html", {"member": member})
                else:
                    context['status'] = 'error'
                    context['message'] = 'Devi fare il check-in prima di poter fare il check-out.'
            else:
                context['member_uuid'] = member.uuid
        except Member.DoesNotExist:
            context['status'] = 'error'
            context['message'] = 'Membro non trovato.'
    else:
        context['status'] = 'error'
        context['message'] = 'QR code non valido.'
    return render(request, "gym/scan_result.html", context)

def generate_qr(request, member_id):
    """Generate QR code for a member"""
    member = get_object_or_404(Member, id=member_id)
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(member.qr_code)
    qr.make(fit=True)
    
    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for display
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_image = base64.b64encode(buffer.getvalue()).decode()
    
    return render(request, 'gym/qr_code.html', {
        'member': member,
        'qr_image': qr_image
    })

@staff_member_required
def download_qr_code(request, member_id):
    """Download QR code in PNG or PDF format"""
    member = get_object_or_404(Member, id=member_id)
    format_type = request.GET.get('format', 'png').lower()
    
    if not member.qr_code_image:
        # Generate QR code if not exists
        member.generate_qr_code()
        member.save()
    
    if format_type == 'pdf':
        # Create PDF with QR code
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="tessera_{member.last_name}_{member.first_name}.pdf"'
        
        # Create PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Colori
        primary_color = (0, 0.3, 0.6)  # Blu scuro
        secondary_color = (0.9, 0.9, 0.9)  # Grigio chiaro
        text_color = (0.2, 0.2, 0.2)  # Grigio scuro
        
        # Header con sfondo colorato
        p.setFillColorRGB(*primary_color)
        p.rect(0, height - 100, width, 100, fill=True, stroke=False)
        
        # Titolo principale
        p.setFillColorRGB(1, 1, 1)  # Bianco
        p.setFont("Helvetica-Bold", 24)
        p.drawCentredString(width/2, height - 40, "TESSERA PALESTRA LEVEL")
        
        p.setFont("Helvetica", 14)
        p.drawCentredString(width/2, height - 65, "Codice QR Personale")
        
        # Sezione informazioni membro
        y_start = height - 140
        
        # Box informazioni con sfondo (più alto per includere certificato medico)
        p.setFillColorRGB(*secondary_color)
        p.rect(40, y_start - 160, width - 80, 160, fill=True, stroke=True)
        
        # Foto del membro (se presente)
        photo_x = 60
        photo_y = y_start - 100
        if member.photo:
            try:
                photo = ImageReader(member.photo.path)
                p.drawImage(photo, photo_x, photo_y, width=80, height=80, mask='auto')
                # Cornice foto
                p.setStrokeColorRGB(*primary_color)
                p.setLineWidth(2)
                p.rect(photo_x, photo_y, 80, 80, fill=False, stroke=True)
            except:
                # Se errore nella foto, mostra placeholder
                p.setFillColorRGB(*primary_color)
                p.rect(photo_x, photo_y, 80, 80, fill=True, stroke=False)
                p.setFillColorRGB(1, 1, 1)
                p.setFont("Helvetica-Bold", 12)
                p.drawCentredString(photo_x + 40, photo_y + 40, "FOTO")
        else:
            # Placeholder per foto
            p.setFillColorRGB(*primary_color)
            p.rect(photo_x, photo_y, 80, 80, fill=True, stroke=False)
            p.setFillColorRGB(1, 1, 1)
            p.setFont("Helvetica-Bold", 12)
            p.drawCentredString(photo_x + 40, photo_y + 40, "FOTO")
        
        # Informazioni membro a destra della foto
        info_x = 160
        p.setFillColorRGB(*text_color)
        
        # Nome e cognome grande
        p.setFont("Helvetica-Bold", 18)
        p.drawString(info_x, y_start - 25, f"{member.first_name} {member.last_name}")
        
        # Altre informazioni
        p.setFont("Helvetica", 12)
        p.drawString(info_x, y_start - 50, f"📧 Email: {member.email}")
        p.drawString(info_x, y_start - 70, f"📱 Telefono: {member.phone}")
        
        # Abbonamento
        p.drawString(info_x, y_start - 90, f"📅 Abbonamento: {member.subscription_start} → {member.subscription_end}")
        
        # Stato abbonamento con colore
        status_text = "🟢 ATTIVO" if member.is_active else "🔴 SCADUTO"
        status_color = (0, 0.6, 0) if member.is_active else (0.8, 0, 0)
        p.setFillColorRGB(*status_color)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(info_x, y_start - 110, f"Stato Abbonamento: {status_text}")
        
        # Certificato Medico
        p.setFillColorRGB(*text_color)
        p.setFont("Helvetica", 12)
        if member.medical_certificate_start and member.medical_certificate_end:
            p.drawString(info_x, y_start - 130, f"🏥 Certificato: {member.medical_certificate_start} → {member.medical_certificate_end}")
            
            # Stato certificato medico con colore
            cert_status_text = "🟢 VALIDO" if member.is_medical_certificate_active else "🔴 SCADUTO"
            cert_status_color = (0, 0.6, 0) if member.is_medical_certificate_active else (0.8, 0, 0)
            p.setFillColorRGB(*cert_status_color)
            p.setFont("Helvetica-Bold", 12)
            p.drawString(info_x, y_start - 150, f"Stato Certificato: {cert_status_text}")
        else:
            p.setFillColorRGB(0.8, 0.4, 0)  # Arancione per non specificato
            p.setFont("Helvetica-Bold", 12)
            p.drawString(info_x, y_start - 130, "🟠 Certificato Medico: NON SPECIFICATO")
        
        # Separatore (spostato più in basso)
        p.setStrokeColorRGB(*primary_color)
        p.setLineWidth(2)
        p.line(40, y_start - 190, width - 40, y_start - 190)
        
        # Sezione QR Code - Grande e centrato (spostata più in basso)
        qr_section_y = y_start - 220
        
        # Titolo sezione QR
        p.setFillColorRGB(*text_color)
        p.setFont("Helvetica-Bold", 16)
        p.drawCentredString(width/2, qr_section_y, "CODICE QR PER CHECK-IN")
        
        # QR Code grande centrato
        if member.qr_code_image:
            qr_size = 250  # QR code più grande
            qr_x = (width - qr_size) / 2  # Centrato
            qr_y = qr_section_y - qr_size - 30
            
            try:
                qr_image = ImageReader(member.qr_code_image.path)
                p.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)
                
                # Cornice QR
                p.setStrokeColorRGB(*primary_color)
                p.setLineWidth(3)
                p.rect(qr_x - 5, qr_y - 5, qr_size + 10, qr_size + 10, fill=False, stroke=True)
            except:
                # Placeholder QR
                p.setFillColorRGB(*secondary_color)
                p.rect(qr_x, qr_y, qr_size, qr_size, fill=True, stroke=True)
                p.setFillColorRGB(*text_color)
                p.setFont("Helvetica-Bold", 16)
                p.drawCentredString(qr_x + qr_size/2, qr_y + qr_size/2, "QR CODE")
        
        # UUID sotto il QR
        p.setFillColorRGB(*text_color)
        p.setFont("Helvetica", 10)
        p.drawCentredString(width/2, qr_y - 20, f"ID: {member.uuid}")
        
        # Footer
        footer_y = 50
        p.setFillColorRGB(*primary_color)
        p.setFont("Helvetica-Bold", 12)
        p.drawCentredString(width/2, footer_y + 20, "LEVEL - Sistema di Gestione Palestra")
        
        p.setFont("Helvetica", 10)
        p.drawCentredString(width/2, footer_y, "Presenta questo QR code per l'accesso alla palestra")
        
        # Data di generazione
        from datetime import datetime
        p.setFont("Helvetica", 8)
        p.drawString(40, 20, f"Generato il: {datetime.now().strftime('%d/%m/%Y alle %H:%M')}")
        
        p.showPage()
        p.save()
        
        pdf_data = buffer.getvalue()
        buffer.close()
        response.write(pdf_data)
        return response
        
    else:  # PNG format
        response = HttpResponse(content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="qr_code_{member.last_name}_{member.first_name}.png"'
        
        if member.qr_code_image:
            with open(member.qr_code_image.path, 'rb') as f:
                response.write(f.read())
        
        return response

@require_http_methods(["GET"])
def generate_wallet_pass(request, member_uuid):
    try:
        member = Member.objects.get(uuid=member_uuid)
        # generator = WalletPassGenerator(member)
        pass_type = request.GET.get("type", "apple")

        if pass_type == "apple":
            pass_json = generator.generate_apple_pass()
            response = HttpResponse(pass_json, content_type="application/vnd.apple.pkpass")
            response["Content-Disposition"] = f"attachment; filename=pass.pkpass"
            return response
        elif pass_type == "google":
            pass_json = generator.generate_google_pass()
            return JsonResponse(pass_json)
        else:
            return HttpResponse("Invalid pass type", status=400)
    except Member.DoesNotExist:
        return HttpResponse("Member not found", status=404)
    except Exception as e:
        return HttpResponse(f"Error generating pass: {e}", status=500)

@require_http_methods(["GET"])
def wallet(request):
    member = Member.objects.first()
    if not member:
        return HttpResponse("Nessun membro trovato.", status=404)
    return render(request, "gym/wallet.html", { "member_uuid": member.uuid }) 

@staff_member_required
def take_photo(request, member_id):
    """Interfaccia per scattare foto live con webcam"""
    member = get_object_or_404(Member, id=member_id)
    return render(request, 'gym/take_photo.html', {'member': member})

@staff_member_required
def save_photo(request, member_id):
    """Salva la foto scattata"""
    if request.method == 'POST':
        member = get_object_or_404(Member, id=member_id)
        
        # Ricevi l'immagine base64 dal frontend
        image_data = request.POST.get('image_data')
        if image_data:
            # Rimuovi il prefix "data:image/png;base64,"
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]
            
            # Decodifica l'immagine
            img_data = base64.b64decode(imgstr)
            
            # Crea il file
            img_name = f"member_{member.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
            
            # Salva nel campo photo
            from django.core.files.base import ContentFile
            member.photo.save(img_name, ContentFile(img_data), save=True)
            
            return JsonResponse({'success': True, 'message': 'Foto salvata con successo!'})
        
        return JsonResponse({'success': False, 'message': 'Errore nel salvare la foto'})
    
    return JsonResponse({'success': False, 'message': 'Metodo non consentito'}) 


@staff_member_required
def send_qr_email(request, member_id):
    """Invia una mail al membro con il suo QR code PNG e la tessera PDF in allegato."""
    member = get_object_or_404(Member, id=member_id)

    try:
        # Assicurati che esista un'immagine del QR
        if not member.qr_code_image:
            member.generate_qr_code()
            member.save()

        if not member.email:
            messages.error(request, "Il membro non ha un'email valida.")
            return redirect(reverse('admin:gym_member_change', args=[member.id]))

        subject = "La tua tessera e QR code - Palestra LEVEL"
        body = (
            f"Ciao {member.first_name},\n\n"
            "in allegato trovi:\n"
            "- Il tuo QR code personale (PNG) per l'accesso rapido\n"
            "- La tua tessera completa (PDF) con tutte le informazioni\n\n"
            "Conserva entrambi i file e porta la tessera PDF stampata o il QR code sul telefono.\n\n"
            "A presto,\nLEVEL"
        )

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or settings.EMAIL_HOST_USER,
            to=[member.email],
        )

        # Allega il QR PNG
        with open(member.qr_code_image.path, 'rb') as f:
            email.attach(
                filename=f"qr_code_{member.last_name}_{member.first_name}.png",
                content=f.read(),
                mimetype='image/png'
            )

        # Genera e allega la tessera PDF
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.utils import ImageReader
        import io
        
        # Crea PDF della tessera
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Colori
        primary_color = (0, 0.3, 0.6)  # Blu scuro
        secondary_color = (0.9, 0.9, 0.9)  # Grigio chiaro
        text_color = (0.2, 0.2, 0.2)  # Grigio scuro
        
        # Header con sfondo colorato
        p.setFillColorRGB(*primary_color)
        p.rect(0, height - 100, width, 100, fill=True, stroke=False)
        
        # Titolo principale
        p.setFillColorRGB(1, 1, 1)  # Bianco
        p.setFont("Helvetica-Bold", 24)
        p.drawCentredString(width/2, height - 40, "TESSERA PALESTRA LEVEL")
        
        p.setFont("Helvetica", 14)
        p.drawCentredString(width/2, height - 65, "Codice QR Personale")
        
        # Sezione informazioni membro
        y_start = height - 140
        
        # Box informazioni con sfondo (più alto per includere certificato medico)
        p.setFillColorRGB(*secondary_color)
        p.rect(40, y_start - 160, width - 80, 160, fill=True, stroke=True)
        
        # Foto del membro (se presente)
        photo_x = 60
        photo_y = y_start - 100
        if member.photo:
            try:
                photo_image = ImageReader(member.photo.path)
                p.drawImage(photo_image, photo_x, photo_y, width=80, height=100)
            except:
                # Placeholder foto
                p.setFillColorRGB(*secondary_color)
                p.rect(photo_x, photo_y, 80, 100, fill=True, stroke=True)
                p.setFillColorRGB(*text_color)
                p.setFont("Helvetica", 10)
                p.drawCentredString(photo_x + 40, photo_y + 50, "FOTO")
        
        # Informazioni membro
        info_x = 160
        p.setFillColorRGB(*text_color)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(info_x, y_start - 20, f"{member.first_name} {member.last_name}")
        
        p.setFont("Helvetica", 12)
        p.drawString(info_x, y_start - 40, f"ID: {member.uuid}")
        p.drawString(info_x, y_start - 60, f"Email: {member.email}")
        p.drawString(info_x, y_start - 80, f"Telefono: {member.phone}")
        
        # Data di nascita
        if member.date_of_birth:
            p.drawString(info_x, y_start - 100, f"Nato il: {member.date_of_birth.strftime('%d/%m/%Y')}")
        
        # Certificato medico
        cert_status = "✓ Presente" if member.medical_certificate else "✗ Non presente"
        cert_color = (0, 0.6, 0) if member.medical_certificate else (0.8, 0, 0)
        p.setFillColorRGB(*cert_color)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(info_x, y_start - 120, f"Certificato Medico: {cert_status}")
        
        # Data scadenza abbonamento
        if member.subscription_end_date:
            p.setFillColorRGB(*text_color)
            p.setFont("Helvetica", 12)
            p.drawString(info_x, y_start - 140, f"Abbonamento valido fino al: {member.subscription_end_date.strftime('%d/%m/%Y')}")
        
        # Sezione QR Code
        qr_section_y = y_start - 200
        
        # Titolo sezione QR
        p.setFillColorRGB(*primary_color)
        p.setFont("Helvetica-Bold", 16)
        p.drawCentredString(width/2, qr_section_y, "CODICE QR PER CHECK-IN")
        
        # QR Code grande centrato
        if member.qr_code_image:
            qr_size = 250  # QR code più grande
            qr_x = (width - qr_size) / 2  # Centrato
            qr_y = qr_section_y - qr_size - 30
            
            try:
                qr_image = ImageReader(member.qr_code_image.path)
                p.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)
                
                # Cornice QR
                p.setStrokeColorRGB(*primary_color)
                p.setLineWidth(3)
                p.rect(qr_x - 5, qr_y - 5, qr_size + 10, qr_size + 10, fill=False, stroke=True)
            except:
                # Placeholder QR
                p.setFillColorRGB(*secondary_color)
                p.rect(qr_x, qr_y, qr_size, qr_size, fill=True, stroke=True)
                p.setFillColorRGB(*text_color)
                p.setFont("Helvetica-Bold", 16)
                p.drawCentredString(qr_x + qr_size/2, qr_y + qr_size/2, "QR CODE")
        
        # UUID sotto il QR
        p.setFillColorRGB(*text_color)
        p.setFont("Helvetica", 10)
        p.drawCentredString(width/2, qr_y - 20, f"ID: {member.uuid}")
        
        # Footer
        footer_y = 50
        p.setFillColorRGB(*primary_color)
        p.setFont("Helvetica-Bold", 12)
        p.drawCentredString(width/2, footer_y + 20, "LEVEL - Sistema di Gestione Palestra")
        
        p.setFont("Helvetica", 10)
        p.drawCentredString(width/2, footer_y, "Presenta questo QR code per l'accesso alla palestra")
        
        # Data di generazione
        from datetime import datetime
        p.setFont("Helvetica", 8)
        p.drawString(40, 20, f"Generato il: {datetime.now().strftime('%d/%m/%Y alle %H:%M')}")
        
        p.showPage()
        p.save()
        
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Allega la tessera PDF
        email.attach(
            filename=f"tessera_{member.last_name}_{member.first_name}.pdf",
            content=pdf_data,
            mimetype='application/pdf'
        )

        email.send(fail_silently=False)
        messages.success(request, f"Email inviata a {member.email} con QR code e tessera PDF.")
    except Exception as exc:
        messages.error(request, f"Errore nell'invio dell'email: {exc}")

    return redirect(reverse('admin:gym_member_change', args=[member.id]))