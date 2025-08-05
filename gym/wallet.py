import os
import json
import uuid
import qrcode
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from datetime import datetime, timedelta
# from passbook.models import Pass, Barcode, BarcodeFormat
# from passbook.signer import PassSigner

class WalletPassGenerator:
    def __init__(self, member):
        self.member = member
        self.pass_type_identifier = "pass.com.yourgym.memberpass"  # Replace with your Pass Type ID
        self.team_identifier = "YOUR_TEAM_ID"  # Replace with your Apple Developer Team ID
        self.organization_name = "Your Gym"
        self.pass_description = "Gym Membership Card"
        
        # Paths for certificates
        self.cert_path = os.path.join(settings.BASE_DIR, 'certificates', 'pass.pem')
        self.key_path = os.path.join(settings.BASE_DIR, 'certificates', 'pass.key')
        self.wwdr_path = os.path.join(settings.BASE_DIR, 'certificates', 'wwdr.pem')
        
    def generate_qr_code(self):
        """Generate QR code for the member's UUID"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.member.uuid)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    def generate_pass_json(self):
        """Generate the pass.json file content"""
        pass_data = {
            "formatVersion": 1,
            "passTypeIdentifier": self.pass_type_identifier,
            "teamIdentifier": self.team_identifier,
            "organizationName": self.organization_name,
            "description": self.pass_description,
            "serialNumber": str(uuid.uuid4()),
            "generic": {
                "primaryFields": [
                    {
                        "key": "member",
                        "label": "MEMBER",
                        "value": f"{self.member.first_name} {self.member.last_name}"
                    }
                ],
                "secondaryFields": [
                    {
                        "key": "subscription",
                        "label": "SUBSCRIPTION",
                        "value": "Active" if self.member.is_subscription_active() else "Expired"
                    }
                ],
                "auxiliaryFields": [
                    {
                        "key": "valid_until",
                        "label": "VALID UNTIL",
                        "value": self.member.subscription_end.strftime("%Y-%m-%d") if self.member.subscription_end else "N/A"
                    }
                ]
            },
            "barcode": {
                "format": "PKBarcodeFormatQR",
                "message": self.member.uuid,
                "messageEncoding": "iso-8859-1",
                "altText": self.member.uuid
            }
        }
        return json.dumps(pass_data)

    def generate_apple_pass(self):
        """Placeholder for Apple Wallet pass generation. Use applepassgenerator instead."""
        return {
            'error': 'Apple Wallet pass generation is not implemented. Use applepassgenerator instead.'
        }

    def generate_google_pass(self):
        """Placeholder for Google Wallet pass generation. No open-source Python package available."""
        return {
            'error': 'Google Wallet pass generation is not implemented. Use Google Pay API directly.'
        } 