from fpdf import FPDF
from fpdf.enums import XPos, YPos

BLUE = (10, 102, 194)
BLACK = (30, 30, 30)
GRAY = (100, 100, 100)
LIGHT = (245, 246, 248)


class Guide(FPDF):
    def header(self):
        self.set_fill_color(*BLUE)
        self.rect(0, 0, 210, 18, "F")
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(255, 255, 255)
        self.set_y(5)
        self.cell(0, 8, "AutoLinkedIn - User Guide", align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(6)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")

    def section(self, title):
        self.ln(4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*BLUE)
        self.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*BLUE)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        self.set_text_color(*BLACK)

    def body(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*BLACK)
        self.multi_cell(self.epw, 6, text)
        self.ln(1)

    def step(self, number, text):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*BLUE)
        self.cell(8, 6, f"{number}.")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*BLACK)
        self.multi_cell(self.epw - 8, 6, text)

    def box(self, label, value):
        self.set_fill_color(*LIGHT)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*GRAY)
        self.cell(58, 7, f"  {label}", fill=True)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*BLACK)
        self.cell(self.epw - 58, 7, f"  {value}", fill=True,
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def code(self, text):
        self.set_fill_color(30, 30, 30)
        self.set_font("Courier", "", 8)
        self.set_text_color(200, 230, 200)
        self.multi_cell(self.epw, 5, text, fill=True)
        self.set_text_color(*BLACK)
        self.ln(2)

    def warn(self, text):
        self.set_fill_color(255, 249, 230)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(180, 120, 0)
        self.multi_cell(self.epw, 6, f"  NOTE: {text}", fill=True)
        self.ln(2)
        self.set_text_color(*BLACK)


pdf = Guide(orientation="P", unit="mm", format="A4")
pdf.set_margins(10, 22, 10)
pdf.set_auto_page_break(auto=True, margin=18)
pdf.add_page()

# Title block
pdf.set_font("Helvetica", "B", 22)
pdf.set_text_color(*BLUE)
pdf.ln(2)
pdf.cell(0, 12, "AutoLinkedIn", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
pdf.set_font("Helvetica", "", 12)
pdf.set_text_color(*GRAY)
pdf.cell(0, 7, "Automated Weekly LinkedIn Post Pipeline",
         new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
pdf.ln(6)

# Overview
pdf.section("1. What It Does")
pdf.body(
    "AutoLinkedIn runs automatically every Monday at 9:00 AM UTC. It searches the web for "
    "the latest tech news, generates a formatted LinkedIn post using Gemini AI, and emails "
    "you a draft for review. You approve it with two clicks and it publishes directly to "
    "your LinkedIn personal profile."
)

# Weekly flow
pdf.section("2. Weekly Workflow")
pdf.step(1, "Monday 9:00 AM UTC - GitHub Actions triggers automatically.")
pdf.step(2, "Gemini 2.5 Flash searches the web and writes a 3-item tech roundup post.")
pdf.step(3, "Draft is emailed to riyazthandora@gmail.com for review.")
pdf.step(4, "Open the email and review the post content.")
pdf.step(5, 'Click "Publish to LinkedIn" button in the email.')
pdf.step(6, 'GitHub Actions page opens - click "Run workflow" to publish.')
pdf.body("\nThe post goes live on your LinkedIn profile within seconds of step 6.")

# Manual trigger
pdf.section("3. Triggering Manually")
pdf.body("To generate or publish outside the Monday schedule:")
pdf.step(1, "Go to github.com/riyazthandora-maker/AutoLinkedIn")
pdf.step(2, 'Click the "Actions" tab.')
pdf.step(3, 'Select "Generate LinkedIn Post" or "Publish LinkedIn Post".')
pdf.step(4, 'Click "Run workflow" on the right side.')
pdf.ln(2)
pdf.warn('Use the "Dry run" checkbox in the Publish workflow to preview without posting.')

# Token renewal
pdf.section("4. Renewing the LinkedIn Access Token")
pdf.body(
    "The LinkedIn access token expires every 60 days. When the Publish workflow fails "
    "with a 401 error, it is time to renew. Next renewal due: approximately 22 August 2026."
)
pdf.body("Option A - LinkedIn Developer Portal (easiest, no code):")
pdf.step(1, "Go to developer.linkedin.com and open your app.")
pdf.step(2, 'Click the "Auth" tab.')
pdf.step(3, 'Scroll to "OAuth 2.0 tools" and click "Request access token".')
pdf.step(4, "Select scopes: openid, profile, w_member_social.")
pdf.step(5, "Click Request access token and approve on the consent screen.")
pdf.step(6, "Copy the token into GitHub Secrets > LINKEDIN_ACCESS_TOKEN > Update.")
pdf.ln(3)
pdf.body("Option B - Run the setup script locally (PowerShell):")
pdf.code(
    "  $env:LINKEDIN_CLIENT_ID='<YOUR_CLIENT_ID>'\n"
    "  $env:LINKEDIN_CLIENT_SECRET='<YOUR_CLIENT_SECRET>'\n"
    "  python D:\\Users\\Riyaz\\Projects\\LinkedInPost\\setup_linkedin_auth.py"
)
pdf.body("Browser opens, approve on LinkedIn, copy the printed token into GitHub Secrets.")

# Secrets reference
pdf.section("5. GitHub Secrets & Variables Reference")
pdf.body(
    "Location: github.com/riyazthandora-maker/AutoLinkedIn\n"
    "         > Settings > Secrets and variables > Actions"
)
pdf.ln(2)
pdf.set_fill_color(*BLUE)
pdf.set_font("Helvetica", "B", 9)
pdf.set_text_color(255, 255, 255)
pdf.cell(58, 7, "  NAME", fill=True)
pdf.cell(22, 7, "  TYPE", fill=True)
pdf.cell(0, 7, "  DESCRIPTION", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.ln(1)
pdf.box("GEMINI_API_KEY", "Secret   | Google AI Studio API key")
pdf.box("RESEND_API_KEY", "Secret   | Resend email API key")
pdf.box("LINKEDIN_ACCESS_TOKEN", "Secret   | LinkedIn OAuth token (renew every 60 days)")
pdf.box("RESEND_FROM_EMAIL", "Variable | bot@gnosiscore.org (verified Resend sender)")
pdf.box("GEMINI_MODEL", "Variable | Optional - defaults to gemini-2.5-flash")

# Troubleshooting
pdf.section("6. Common Errors & Fixes")
pdf.box("401 Unauthorized", "LinkedIn token expired - renew using Section 4 above")
pdf.box("403 Forbidden", "Token missing openid/profile scope - re-run OAuth with all 3 scopes")
pdf.box("API key is invalid", "RESEND_API_KEY is empty or wrong - update in GitHub Secrets")
pdf.box("model is required", "GEMINI_MODEL variable is empty - delete it or set gemini-2.5-flash")
pdf.box("No API key provided", "GEMINI_API_KEY is missing - add it in GitHub Secrets")

# Post format
pdf.section("7. Post Format")
pdf.body("Each generated post follows this exact structure:")
pdf.code(
    "  [FOMO hook - one punchy line for CTO/exec audience]\n\n"
    "  >> [4-5 word headline]\n"
    "  * WHAT: [what the tech is + real-world use case]\n"
    "  * [specific financial impact or cost reduction with numbers]\n\n"
    "  [repeated for 3 items total]\n\n"
    "  [Closing question to invite comments]\n\n"
    "  #Hashtag1 #Hashtag2 #Hashtag3"
)
pdf.body(
    "To change the format or tone, edit the file prompts/system_prompt.txt in the repo."
)

pdf.output("D:\\Users\\Riyaz\\Projects\\LinkedInPost\\AutoLinkedIn_User_Guide.pdf")
print("PDF generated successfully.")
