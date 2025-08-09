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