# Feature: Add Email Report Delivery

The following plan should be complete, but validate documentation and codebase patterns before implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files.

## Feature Description

Add ability to email generated reports directly to clients or stakeholders. Support multiple recipients, custom subject lines, and optional summary in email body. Integrate with scheduled audits for automatic delivery.

## User Story

As an **SEO consultant**
I want to **automatically email reports to clients**
So that **clients receive reports without manual file sharing**

## Problem Statement

After generating reports, users must manually:
- Download/locate the report file
- Compose an email
- Attach the report
- Send to client

This is tedious for recurring reports and doesn't scale.

## Solution Statement

Implement email delivery using Python's `smtplib` with MIME attachments. Support SMTP configuration via environment variables. Add email options to CLI and integrate with scheduler for automatic delivery.

## Feature Metadata

**Feature Type**: New Capability
**Estimated Complexity**: Medium
**Primary Systems Affected**: Report delivery, scheduler integration
**Dependencies**: None (uses stdlib `smtplib`, `email`)

---

## CONTEXT REFERENCES

### Relevant Codebase Files - READ BEFORE IMPLEMENTING

- `seo-health-report/__init__.py` (lines 50-150) - Why: `generate_report()` to extend with email option
- `seo-health-report/scripts/generate_summary.py` (lines 1-50) - Why: `generate_executive_summary()` for email body content
- `seo-health-report/scripts/scheduler.py` - Why: Integration point for automatic email delivery

### New Files to Create

- `seo-health-report/scripts/email_delivery.py` - Email sending functionality

### Files to Update

- `seo-health-report/__init__.py` - Add email parameters and delivery call
- `seo-health-report/scripts/scheduler.py` - Add email to scheduled jobs

### Relevant Documentation

- [Python smtplib](https://docs.python.org/3/library/smtplib.html)
  - Section: SMTP Objects
  - Why: Core email sending API
- [Python email.mime](https://docs.python.org/3/library/email.mime.html)
  - Section: MIMEMultipart, MIMEBase
  - Why: Building emails with attachments

### Patterns to Follow

**Environment variable pattern** (from `query_ai_systems.py`):
```python
api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
if not api_key:
    return {"error": "API_KEY not set"}
```

**Result dict pattern** (from `build_report.py`):
```python
result = {
    "success": False,
    "error": None,
    ...
}
```

---

## IMPLEMENTATION PLAN

### Prerequisites Gate

- [ ] SMTP credentials available (Gmail, SendGrid, etc.)
- [ ] Test email account for validation

### Phase 1: Foundation

Create email delivery module with SMTP support.

### Phase 2: Core Implementation

Implement email composition with attachments.

### Phase 3: Integration

Wire into report generation and scheduler.

### Phase 4: Testing

Validate email delivery with test accounts.

---

## STEP-BY-STEP TASKS

### Task 1: CREATE `seo-health-report/scripts/email_delivery.py`

- **IMPLEMENT**: Email sending functionality
- **IMPORTS**:
  ```python
  import os
  import smtplib
  import mimetypes
  from email.mime.multipart import MIMEMultipart
  from email.mime.text import MIMEText
  from email.mime.base import MIMEBase
  from email import encoders
  from typing import Dict, Any, List, Optional
  ```
- **COMPONENTS**:
  ```python
  # SMTP Configuration from environment
  SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
  SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
  SMTP_USER = os.environ.get("SMTP_USER", "")
  SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
  SMTP_FROM = os.environ.get("SMTP_FROM", "")  # Defaults to SMTP_USER
  
  def send_report_email(
      to_emails: List[str],
      subject: str,
      body_text: str,
      body_html: Optional[str] = None,
      attachment_path: Optional[str] = None,
      cc_emails: Optional[List[str]] = None,
      smtp_host: str = None,
      smtp_port: int = None,
      smtp_user: str = None,
      smtp_password: str = None,
      from_email: str = None
  ) -> Dict[str, Any]:
      """
      Send email with optional report attachment.
      
      Args:
          to_emails: List of recipient email addresses
          subject: Email subject line
          body_text: Plain text email body
          body_html: Optional HTML email body
          attachment_path: Path to report file to attach
          cc_emails: Optional CC recipients
          smtp_*: SMTP configuration (defaults to env vars)
          from_email: Sender email address
      
      Returns:
          Dict with success status and details
      """
      result = {
          "success": False,
          "recipients": to_emails,
          "error": None
      }
      
      # Get SMTP config
      host = smtp_host or SMTP_HOST
      port = smtp_port or SMTP_PORT
      user = smtp_user or SMTP_USER
      password = smtp_password or SMTP_PASSWORD
      sender = from_email or SMTP_FROM or user
      
      if not user or not password:
          result["error"] = "SMTP credentials not configured. Set SMTP_USER and SMTP_PASSWORD environment variables."
          return result
      
      try:
          # Create message
          msg = MIMEMultipart('alternative')
          msg['Subject'] = subject
          msg['From'] = sender
          msg['To'] = ', '.join(to_emails)
          if cc_emails:
              msg['Cc'] = ', '.join(cc_emails)
          
          # Add body
          msg.attach(MIMEText(body_text, 'plain'))
          if body_html:
              msg.attach(MIMEText(body_html, 'html'))
          
          # Add attachment
          if attachment_path and os.path.exists(attachment_path):
              attachment = create_attachment(attachment_path)
              if attachment:
                  msg.attach(attachment)
              else:
                  result["error"] = f"Could not attach file: {attachment_path}"
                  return result
          
          # Send email
          all_recipients = to_emails + (cc_emails or [])
          
          with smtplib.SMTP(host, port) as server:
              server.starttls()
              server.login(user, password)
              server.sendmail(sender, all_recipients, msg.as_string())
          
          result["success"] = True
          result["message"] = f"Email sent to {len(all_recipients)} recipients"
          
      except smtplib.SMTPAuthenticationError:
          result["error"] = "SMTP authentication failed. Check credentials."
      except smtplib.SMTPException as e:
          result["error"] = f"SMTP error: {str(e)}"
      except Exception as e:
          result["error"] = f"Email failed: {str(e)}"
      
      return result
  
  def create_attachment(file_path: str) -> Optional[MIMEBase]:
      """Create email attachment from file."""
      try:
          filename = os.path.basename(file_path)
          
          # Guess MIME type
          mime_type, _ = mimetypes.guess_type(file_path)
          if mime_type is None:
              mime_type = 'application/octet-stream'
          
          main_type, sub_type = mime_type.split('/', 1)
          
          with open(file_path, 'rb') as f:
              attachment = MIMEBase(main_type, sub_type)
              attachment.set_payload(f.read())
          
          encoders.encode_base64(attachment)
          attachment.add_header(
              'Content-Disposition',
              'attachment',
              filename=filename
          )
          
          return attachment
          
      except Exception as e:
          print(f"Error creating attachment: {e}")
          return None
  
  def generate_report_email_body(
      company_name: str,
      overall_score: int,
      grade: str,
      report_date: str,
      quick_wins: List[str] = None
  ) -> tuple:
      """
      Generate email body text and HTML for report delivery.
      
      Returns:
          Tuple of (plain_text, html)
      """
      quick_wins = quick_wins or []
      
      plain_text = f"""
  SEO Health Report for {company_name}
  
  Report Date: {report_date}
  Overall Score: {overall_score}/100 (Grade: {grade})
  
  Your SEO Health Report is attached to this email.
  
  """
      if quick_wins:
          plain_text += "Top Priority Actions:\n"
          for i, win in enumerate(quick_wins[:5], 1):
              plain_text += f"  {i}. {win}\n"
      
      plain_text += """
  
  For questions about this report, please contact your SEO consultant.
  
  ---
  Generated by SEO Health Report System
  """
      
      # HTML version
      html = f"""
  <html>
  <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <h1 style="color: #1a73e8;">SEO Health Report</h1>
      <h2>{company_name}</h2>
      
      <p><strong>Report Date:</strong> {report_date}</p>
      
      <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center;">
          <p style="font-size: 48px; margin: 0; color: {'#34a853' if overall_score >= 80 else '#fbbc04' if overall_score >= 60 else '#ea4335'};">
              {overall_score}
          </p>
          <p style="font-size: 24px; margin: 5px 0;">Grade: {grade}</p>
      </div>
      
      <p>Your complete SEO Health Report is attached to this email.</p>
  """
      
      if quick_wins:
          html += """
      <h3>Top Priority Actions</h3>
      <ol>
  """
          for win in quick_wins[:5]:
              html += f"        <li>{win}</li>\n"
          html += "    </ol>\n"
      
      html += """
      <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
      <p style="color: #666; font-size: 12px;">
          Generated by SEO Health Report System
      </p>
  </body>
  </html>
  """
      
      return plain_text, html
  
  def validate_email_config() -> Dict[str, Any]:
      """Validate SMTP configuration."""
      result = {
          "configured": False,
          "host": SMTP_HOST,
          "port": SMTP_PORT,
          "user_set": bool(SMTP_USER),
          "password_set": bool(SMTP_PASSWORD),
          "issues": []
      }
      
      if not SMTP_USER:
          result["issues"].append("SMTP_USER not set")
      if not SMTP_PASSWORD:
          result["issues"].append("SMTP_PASSWORD not set")
      
      result["configured"] = len(result["issues"]) == 0
      return result
  ```
- **GOTCHA**: Gmail requires "App Password" not regular password
- **VALIDATE**: `python -c "from seo_health_report.scripts.email_delivery import send_report_email, validate_email_config"`

### Task 2: UPDATE `seo-health-report/__init__.py`

- **IMPLEMENT**: Add email parameters to `generate_report()`
- **ADD** parameters:
  ```python
  def generate_report(
      ...
      email_to: Optional[List[str]] = None,
      email_cc: Optional[List[str]] = None,
      email_subject: Optional[str] = None,
      send_email: bool = False
  ) -> Dict[str, Any]:
  ```
- **ADD** after report generation:
  ```python
  # Email delivery
  if send_email and email_to:
      from .scripts.email_delivery import send_report_email, generate_report_email_body
      
      # Generate email content
      quick_win_texts = [w.get("action", "") for w in result.get("quick_wins", [])]
      body_text, body_html = generate_report_email_body(
          company_name=company_name,
          overall_score=result["overall_score"],
          grade=result["grade"],
          report_date=datetime.now().strftime("%B %d, %Y"),
          quick_wins=quick_win_texts
      )
      
      # Default subject
      subject = email_subject or f"SEO Health Report: {company_name} - Score {result['overall_score']}/100"
      
      # Send email
      email_result = send_report_email(
          to_emails=email_to,
          subject=subject,
          body_text=body_text,
          body_html=body_html,
          attachment_path=result["report"].get("output_path"),
          cc_emails=email_cc
      )
      
      result["email"] = email_result
      
      if email_result["success"]:
          print(f"Report emailed to: {', '.join(email_to)}")
      else:
          result["warnings"].append(f"Email failed: {email_result.get('error')}")
  ```
- **VALIDATE**: `python -c "from seo_health_report import generate_report; help(generate_report)"`

### Task 3: UPDATE CLI for email options

- **IMPLEMENT**: Add email arguments to CLI
- **ADD** to argparse:
  ```python
  parser.add_argument("--email-to", help="Email recipients (comma-separated)")
  parser.add_argument("--email-cc", help="CC recipients (comma-separated)")
  parser.add_argument("--email-subject", help="Custom email subject")
  parser.add_argument("--send-email", action="store_true", help="Send report via email")
  ```
- **ADD** to `main()`:
  ```python
  # Parse email recipients
  email_to = None
  if args.email_to:
      email_to = [e.strip() for e in args.email_to.split(",")]
  
  email_cc = None
  if args.email_cc:
      email_cc = [e.strip() for e in args.email_cc.split(",")]
  
  result = generate_report(
      ...
      email_to=email_to,
      email_cc=email_cc,
      email_subject=args.email_subject,
      send_email=args.send_email
  )
  ```
- **VALIDATE**: `python -m seo_health_report --help`

### Task 4: UPDATE scheduler for email delivery

- **IMPLEMENT**: Add email options to scheduled audits
- **UPDATE** `scheduled_audit()` in `scheduler.py`:
  ```python
  def scheduled_audit(
      url: str,
      company_name: str,
      keywords: list,
      output_dir: str,
      logo_file: str = "",
      email_to: list = None,
      send_email: bool = False
  ):
      result = generate_report(
          ...
          email_to=email_to,
          send_email=send_email
      )
  ```
- **UPDATE** `schedule_audit()`:
  ```python
  def schedule_audit(
      ...
      email_to: list = None,
      send_email: bool = False
  ) -> str:
      scheduler.add_job(
          scheduled_audit,
          ...
          kwargs={
              ...
              "email_to": email_to,
              "send_email": send_email
          },
          ...
      )
  ```
- **VALIDATE**: Schedule audit with email, verify email sent on execution

### Task 5: ADD email configuration CLI command

- **IMPLEMENT**: Command to check/test email config
- **ADD** subcommand:
  ```python
  email_parser = subparsers.add_parser("email-test", help="Test email configuration")
  email_parser.add_argument("--to", required=True, help="Test recipient email")
  ```
- **ADD** handler:
  ```python
  elif args.command == "email-test":
      from .scripts.email_delivery import send_report_email, validate_email_config
      
      # Validate config
      config = validate_email_config()
      if not config["configured"]:
          print("Email not configured:")
          for issue in config["issues"]:
              print(f"  - {issue}")
          return
      
      # Send test email
      result = send_report_email(
          to_emails=[args.to],
          subject="SEO Health Report - Test Email",
          body_text="This is a test email from SEO Health Report System.\n\nIf you received this, email delivery is working correctly."
      )
      
      if result["success"]:
          print(f"Test email sent to {args.to}")
      else:
          print(f"Test failed: {result['error']}")
  ```
- **VALIDATE**: `python -m seo_health_report email-test --to test@example.com`

---

## TESTING STRATEGY

### Manual Validation

1. Set SMTP environment variables
2. Run `email-test` command
3. Generate report with `--send-email --email-to user@example.com`
4. Verify email received with attachment
5. Schedule audit with email, verify delivery

### Edge Cases

1. Invalid email address → graceful error
2. Missing SMTP config → clear error message
3. Attachment file missing → error before send attempt
4. SMTP auth failure → specific error message

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style

```bash
python -m py_compile seo-health-report/scripts/email_delivery.py
```

### Level 2: Import Tests

```bash
python -c "from seo_health_report.scripts.email_delivery import send_report_email, validate_email_config"
```

### Level 3: Config Validation

```bash
python -c "
from seo_health_report.scripts.email_delivery import validate_email_config
config = validate_email_config()
print(f'Configured: {config[\"configured\"]}')
print(f'Issues: {config[\"issues\"]}')
"
```

### Level 4: Email Body Generation

```bash
python -c "
from seo_health_report.scripts.email_delivery import generate_report_email_body

text, html = generate_report_email_body(
    company_name='Test Corp',
    overall_score=75,
    grade='C',
    report_date='January 9, 2026',
    quick_wins=['Fix meta descriptions', 'Add schema markup']
)

print('Plain text preview:')
print(text[:200])
"
```

### Level 5: Integration Test (requires SMTP config)

```bash
# Set environment variables first:
# export SMTP_USER=your@email.com
# export SMTP_PASSWORD=your-app-password

python -m seo_health_report email-test --to your@email.com
```

---

## ACCEPTANCE CRITERIA

- [ ] Email module created with SMTP support
- [ ] Reports can be emailed via CLI flag
- [ ] Email includes score summary in body
- [ ] Report attached as file
- [ ] HTML and plain text versions sent
- [ ] CC recipients supported
- [ ] Custom subject line supported
- [ ] Scheduled audits can auto-email
- [ ] Clear error messages for config issues
- [ ] Test email command works

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each validation command passes
- [ ] Test email received successfully
- [ ] Report attachment opens correctly
- [ ] Scheduler integration works

---

## NOTES

**Design Decision**: Using stdlib `smtplib` for zero dependencies. For production, could use `sendgrid` or `mailgun` SDKs.

**Security**: SMTP password should be app-specific password, not main account password. For Gmail, enable 2FA and create app password.

**Environment Variables**:
```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your@gmail.com"
export SMTP_PASSWORD="your-app-password"
export SMTP_FROM="SEO Reports <your@gmail.com>"
```

**Future Enhancement**:
- Email templates with branding
- Delivery tracking/receipts
- Retry logic for failed sends
- SendGrid/Mailgun integration for scale
