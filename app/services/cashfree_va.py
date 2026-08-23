import requests
from django.conf import settings


def create_virtual_account(order_id, name, email, phone=None, pan=None, aadhaar=None):
    env = getattr(settings, 'CASHFREE_ENV', 'sandbox')
    base_url = 'https://api.cashfree.com' if env == 'production' else 'https://sandbox.cashfree.com'

    headers = {
        'x-client-id': settings.CASHFREE_APP_ID,
        'x-client-secret': settings.CASHFREE_SECRET_KEY,
        'x-api-version': getattr(settings, 'CASHFREE_API_VERSION', '2023-08-01'),
        'Content-Type': 'application/json',
    }

    body = {
        'virtual_account_details': {
            'virtual_account_id': str(order_id)[:20],
            'virtual_account_name': (name or 'AnkuOn2 Investor')[:50],
            'virtual_account_email': email,
        }
    }
    if phone:
        try:
            body['virtual_account_details']['virtual_account_phone'] = int(str(phone)[-10:])
        except Exception:
            pass

    kyc = {}
    if pan:
        kyc['pan'] = pan
    if aadhaar:
        try:
            kyc['aadhaar'] = int(str(aadhaar))
        except Exception:
            pass
    if kyc:
        body['kyc_details'] = kyc

    try:
        res = requests.post(f'{base_url}/pg/vba', json=body, headers=headers, timeout=30)
        data = res.json()
        va_list = data.get('virtual_bank_accounts') or []
        if not va_list:
            print('Cashfree VA error:', data)
            return None
        va = va_list[0]
        bank_code = va.get('vba_bank_code', '')
        bank_name = {'UTIB': 'Axis Bank', 'ICIC': 'ICICI Bank', 'YESB': 'Yes Bank'}.get(bank_code, bank_code)
        return {
            'accountNumber': str(va.get('vba_account_number', '')),
            'ifsc': va.get('vba_ifsc', ''),
            'accountName': va.get('virtual_account_details', {}).get('virtual_account_name') or name,
            'bankName': bank_name,
            'bankCode': bank_code,
            'status': va.get('vba_status', 'ACTIVE'),
        }
    except Exception as e:
        print('VA creation exception:', e)
        return None
