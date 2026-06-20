import resend
from django.conf import settings

resend.api_key = settings.RESEND_API_KEY

def send_verification_email(to_email, code, purpose, first_name=''):
    action = 'sign in' if purpose == 'login' else 'verify your account'
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;background:#0a0a0a;color:#fff;border-radius:16px;overflow:hidden;border:1px solid #1f1f1f;">
      <div style="background:linear-gradient(135deg,#1a1a1a,#0a0a0a);padding:40px 32px 32px;">
        <h1 style="font-size:24px;font-weight:700;margin:0 0 8px;">Tesla Invest</h1>
        <p style="color:#9ca3af;margin:0;font-size:14px;">Investment Management Platform</p>
      </div>
      <div style="padding:32px;">
        <p style="color:#e5e7eb;font-size:15px;margin:0 0 8px;">Hi {first_name or 'there'},</p>
        <p style="color:#9ca3af;font-size:14px;margin:0 0 28px;line-height:1.6;">
          Use the code below to {action}. It expires in <strong style="color:#fff;">10 minutes</strong>.
        </p>
        <div style="background:#1a1a1a;border:1px solid #2e2e2e;border-radius:12px;padding:24px;text-align:center;margin-bottom:28px;">
          <p style="font-size:40px;font-weight:700;letter-spacing:12px;margin:0;color:#fff;">{code}</p>
        </div>
        <p style="color:#6b7280;font-size:12px;margin:0;line-height:1.6;">
          If you didn't request this, you can safely ignore this email. Do not share this code with anyone.
        </p>
      </div>
      <div style="background:#0a0a0a;border-top:1px solid #1f1f1f;padding:20px 32px;">
        <p style="color:#4b5563;font-size:12px;margin:0;">© 2026 Tesla Investment Management. All rights reserved.</p>
      </div>
    </div>
    """
    resend.Emails.send({
        "from": "Tesla Invest <onboarding@legitonlinetrading.com>",
        "to":      [to_email],
        "subject": f"{'Sign-in' if purpose == 'login' else 'Verify your account'} — your Tesla Invest code is {code}",
        "html":    html,
    })