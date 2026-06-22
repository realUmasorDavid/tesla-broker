import resend
from django.conf import settings

resend.api_key = settings.RESEND_API_KEY

LOGO_URL = 'https://res.cloudinary.com/dqqgr0j4l/image/upload/v1782115061/logo2_dsyojj.svg'

def _base_wrapper(content_html):
    """Shared outer shell for all emails."""
    logo_block = f'''
        <div style="text-align:center;margin-bottom:32px;">
            <img src="{LOGO_URL}" alt="Tesla Capital"
                 style="height:36px;width:auto;display:inline-block;" />
        </div>
    ''' if LOGO_URL else '''
        <div style="margin-bottom:32px;">
            <h2 style="font-size:20px;font-weight:700;margin:0;color:#fff;letter-spacing:-0.5px;">
                Tesla Capital
            </h2>
            <p style="color:#6b7280;font-size:12px;margin:4px 0 0;">Investment Management Platform</p>
        </div>
    '''
 
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background:#000;font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#000;padding:40px 16px;">
    <tr>
      <td align="center">
        <table width="100%" cellpadding="0" cellspacing="0"
               style="max-width:480px;background:#0d0d0d;border-radius:20px;overflow:hidden;border:1px solid #1f1f1f;">
 
          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#1a1a1a 0%,#0d0d0d 100%);
                        padding:36px 36px 28px;border-bottom:1px solid #1f1f1f;">
              {logo_block}
            </td>
          </tr>
 
          <!-- Body -->
          <tr>
            <td style="padding:36px;">
              {content_html}
            </td>
          </tr>
 
          <!-- Footer -->
          <tr>
            <td style="background:#080808;border-top:1px solid #1f1f1f;padding:20px 36px;">
              <p style="color:#374151;font-size:11px;margin:0;line-height:1.6;">
                © 2026 Tesla Capital. All rights reserved.<br/>
                You're receiving this email because you created an account on Tesla Capital.
              </p>
            </td>
          </tr>
 
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
 
 
def send_verification_email(to_email, code, purpose, first_name=''):
    action = 'sign in to your account' if purpose == 'login' else 'verify your Tesla Capital account'
 
    content = f"""
        <p style="color:#e5e7eb;font-size:16px;font-weight:600;margin:0 0 8px;">
            Hi {first_name or 'there'},
        </p>
        <p style="color:#9ca3af;font-size:14px;margin:0 0 28px;line-height:1.7;">
            Use the verification code below to {action}.
            It expires in <strong style="color:#fff;">10 minutes</strong>.
        </p>
 
        <!-- OTP Box -->
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
          <tr>
            <td align="center"
                style="background:#141414;border:1px solid #2e2e2e;border-radius:14px;padding:28px;">
              <p style="font-size:44px;font-weight:700;letter-spacing:14px;
                         margin:0;color:#fff;font-variant-numeric:tabular-nums;">
                {code}
              </p>
            </td>
          </tr>
        </table>
 
        <!-- Expiry note -->
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
          <tr>
            <td style="background:#1a1a0a;border:1px solid #2e2e00;border-radius:10px;padding:12px 16px;">
              <p style="color:#ca8a04;font-size:12px;margin:0;">
                ⏱ This code expires in 10 minutes. Do not share it with anyone.
              </p>
            </td>
          </tr>
        </table>
 
        <p style="color:#4b5563;font-size:12px;margin:0;line-height:1.7;">
            If you didn't request this code, you can safely ignore this email.
            Someone may have entered your email address by mistake.
        </p>
    """
 
    subject = (
        f"Your Tesla Capital sign-in code: {code}"
        if purpose == 'login'
        else f"Verify your Tesla Capital account — code: {code}"
    )
 
    resend.Emails.send({
        "from":    "Tesla Capital <onboarding@legitonlinetrading.com>",
        "to":      [to_email],
        "subject": subject,
        "html":    _base_wrapper(content),
    })
 
 
def send_welcome_email(to_email, first_name):
    content = f"""
        <p style="color:#e5e7eb;font-size:18px;font-weight:700;margin:0 0 8px;">
            Welcome to Tesla Capital, {first_name}! 🎉
        </p>
        <p style="color:#9ca3af;font-size:14px;margin:0 0 28px;line-height:1.7;">
            Your account has been successfully created.
            Fund your account and complete your KYC verification to unlock all
            platform features and start investing.
        </p>
 
        <!-- Steps -->
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;border-collapse:separate;border-spacing:0 10px;">
          <tr>
            <td style="background:#141414;border:1px solid #1f1f1f;border-radius:12px;padding:14px 16px;">
              <table cellpadding="0" cellspacing="0">
                <tr>
                  <td style="font-size:22px;padding-right:14px;vertical-align:middle;">💳</td>
                  <td style="vertical-align:middle;">
                    <p style="margin:0;font-size:13px;font-weight:600;color:#fff;">Step 1 — Fund Your Account</p>
                    <p style="margin:2px 0 0;font-size:12px;color:#6b7280;">Deposit via BTC, ETH, or LTC to get started</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="background:#141414;border:1px solid #1f1f1f;border-radius:12px;padding:14px 16px;">
              <table cellpadding="0" cellspacing="0">
                <tr>
                  <td style="font-size:22px;padding-right:14px;vertical-align:middle;">🔐</td>
                  <td style="vertical-align:middle;">
                    <p style="margin:0;font-size:13px;font-weight:600;color:#fff;">Step 2 — Complete KYC</p>
                    <p style="margin:2px 0 0;font-size:12px;color:#6b7280;">Verify your identity to unlock all features</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="background:#141414;border:1px solid #1f1f1f;border-radius:12px;padding:14px 16px;">
              <table cellpadding="0" cellspacing="0">
                <tr>
                  <td style="font-size:22px;padding-right:14px;vertical-align:middle;">📈</td>
                  <td style="vertical-align:middle;">
                    <p style="margin:0;font-size:13px;font-weight:600;color:#fff;">Step 3 — Start Investing</p>
                    <p style="margin:2px 0 0;font-size:12px;color:#6b7280;">Trade stocks, join plans, or order a Tesla</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
 
        <!-- CTA -->
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td align="center">
              <a href="https://yourdomain.com/dashboard/"
                 style="display:inline-block;background:#fff;color:#000;
                        padding:14px 36px;border-radius:10px;
                        font-size:14px;font-weight:600;text-decoration:none;
                        letter-spacing:-0.2px;">
                Go to Dashboard →
              </a>
            </td>
          </tr>
        </table>
    """
 
    resend.Emails.send({
        "from":    "Tesla Capital <onboarding@legitonlinetrading.com>",
        "to":      [to_email],
        "subject": f"Welcome to Tesla Capital, {first_name}! Your account is ready 🚀",
        "html":    _base_wrapper(content),
    })