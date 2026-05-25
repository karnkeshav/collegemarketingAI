# CollegeMarketingAI

A local marketing-automation platform for discovering, validating, and emailing college officials (TPO, Principal, HOD, Dean, Chairman) across India. Designed for bulk outreach to Training & Placement Offices and institutional leadership at degree colleges in Telangana, Andhra Pradesh, Bihar, Jharkhand, Delhi — with room to add more states.

---

## Features

| Feature | Description |
|---|---|
| **College Discovery** | Scrapes AICTE approved-institution portal for engineering/pharmacy/management colleges. Crawls each college's website to extract real contact emails. |
| **Email Validation** | MX/DNS record check before storing any email — no fake or undeliverable addresses saved. |
| **Role Classification** | Automatically tags each email as TPO, Principal, Chairman, HOD, Dean, or General based on keyword proximity on the source page. |
| **CSV Export** | Download all contacts (or filtered subset) as a CSV for use in any other tool. |
| **Campaign Management** | Upload your own HTML email template, select recipients by state/role, send with one click. |
| **Gmail SMTP Sending** | Sends through your Gmail account (ready4industry@gmail.com) with a 2-second delay per email to stay within Gmail's daily limit (~500/day). |
| **Bounce Detection** | Polls your Gmail inbox via IMAP after sending. Detects NDR/Mailer-Daemon bounce-back emails and marks them in the dashboard. |
| **Dashboard** | Real-time stats: colleges found, contacts validated, emails sent, bounces, per-state breakdown. |
| **Unsubscribe** | One-click unsubscribe per contact; unsubscribed addresses are excluded from all future sends. |

---

## Project Structure

```
collegemarketingAI/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── database.py             # SQLAlchemy + SQLite (aiosqlite)
│   ├── models.py               # ORM: State, College, Contact, Campaign, CampaignSend
│   ├── schemas.py              # Pydantic request/response models
│   ├── config.py               # Settings loaded from .env
│   ├── scrapers/
│   │   ├── aicte_scraper.py    # AICTE portal API — fetches approved institutions by state
│   │   └── college_scraper.py  # Visits each college website, extracts emails + infers role
│   ├── services/
│   │   ├── email_validator.py  # Syntax + MX/DNS validation
│   │   ├── email_sender.py     # Gmail SMTP bulk sender with per-email delay
│   │   ├── bounce_checker.py   # Gmail IMAP NDR bounce detector
│   │   └── csv_service.py      # CSV generation for contacts and campaign reports
│   ├── api/
│   │   ├── colleges.py         # GET /api/colleges (paginated, filterable)
│   │   ├── contacts.py         # GET/POST /api/contacts (list, validate, export, unsubscribe)
│   │   ├── campaigns.py        # POST/GET /api/campaigns (create, send, status, bounces, export)
│   │   ├── scraper.py          # POST /api/scrape/start — background scrape with SSE progress
│   │   └── reports.py          # GET /api/reports/overview + per-campaign sends
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx   # Stats overview, bar/pie charts, scrape progress
│   │   │   ├── Colleges.tsx    # Browse colleges, trigger scrape per state
│   │   │   ├── Contacts.tsx    # Filter/select contacts, validate, export CSV
│   │   │   ├── Campaigns.tsx   # Upload template, configure recipients, send, preview
│   │   │   └── Reports.tsx     # Per-campaign drill-down, bounce list, export
│   │   ├── components/
│   │   │   ├── Sidebar.tsx     # Navigation
│   │   │   ├── StatsCard.tsx   # Metric card with icon
│   │   │   └── Badge.tsx       # Colour-coded status chips
│   │   ├── api/client.ts       # Axios wrappers for all backend endpoints
│   │   └── types/index.ts      # TypeScript interfaces
│   └── vite.config.ts          # Vite + Tailwind + proxy to :8000
├── templates/                  # Drop your HTML templates here (optional)
├── .env.example                # Environment variable template
├── start.ps1                   # One-click startup script
└── README.md
```

---

## Prerequisites

| Requirement | Version | Install |
|---|---|---|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Gmail account | — | Must be the sending address |
| Gmail App Password | — | See setup below |

---

## Setup

### 1. Clone the repo

```powershell
git clone https://github.com/karnkeshav/collegemarketingAI.git
cd collegemarketingAI
```

### 2. Configure Gmail App Password

Gmail SMTP requires an **App Password** (not your normal Gmail password).

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already on
3. Go to **App passwords** (search for it in the security page)
4. Create an app password: App = "Mail", Device = "Windows Computer"
5. Copy the 16-character password

### 3. Create the `.env` file

```powershell
Copy-Item .env.example backend\.env
```

Edit `backend\.env`:

```
GMAIL_USER=ready4industry@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

### 4. Launch the app

```powershell
.\start.ps1
```

This installs all dependencies and opens two terminal windows:
- **Backend** on `http://127.0.0.1:8000`
- **Frontend** on `http://localhost:5173`

Open `http://localhost:5173` in your browser.

---

## Complete Workflow

### Step 1 — Discover Colleges

1. Navigate to **Colleges** in the sidebar
2. Click **"Scrape [State Name]"** for each state you want
   - The scraper hits the AICTE approved-institution portal for that state
   - Then visits each college's website: `/contact`, `/placement`, `/administration`, `/faculty` pages
   - Extracts all emails and scores them by proximity to keywords like "placement", "principal", "hod"
3. Watch the progress bar on the Dashboard while scraping runs

**States available:** Telangana, Andhra Pradesh, Bihar, Jharkhand, Delhi

**To add a new state:** In `backend/database.py`, add a new entry to `states_data` in `_seed_states()`:
```python
{"name": "Maharashtra", "code": "MH"},
```

### Step 2 — Validate Emails

1. Go to **Contacts**
2. Use filters to select a subset (e.g. State = Telangana, Role = TPO)
3. Tick the checkboxes (or select all)
4. Click **"Validate"** — the system does a DNS/MX record lookup for each email's domain
5. Emails with no valid MX record are marked **invalid** and excluded from sends

> Validation does NOT send any test emails. It only checks if the domain has mail servers configured.

### Step 3 — Export CSV

On the **Contacts** page, apply your desired filters and click **"Export CSV"**. The downloaded file contains:

```
id, college_name, state, city, college_type, contact_name, role, department,
email, phone, validation_status, source_url, created_at
```

Use this CSV for import into any CRM or external mail tool.

### Step 4 — Create a Campaign

1. Go to **Campaigns** → **New Campaign**
2. Enter a campaign name and email subject line
3. Upload your HTML email template (`.html` file)
   - Preview renders in the modal before you save
4. Click **Create Campaign**

**Template tips:**
- Use standard HTML — Gmail renders most HTML email formats
- Keep images hosted externally (not inline base64) for better deliverability
- Personalization tokens are not yet supported — use generic copy for bulk sends

### Step 5 — Send the Campaign

1. On the **Campaigns** page, find your campaign and click **Send**
2. Select target states and/or roles (leave blank for all contacts)
3. Review the confirmation and click **Confirm & Send**
4. Sending runs as a background task — emails go out at 2 seconds per email
5. Watch send count increment in real time on the Campaigns page

**Gmail daily limit:** ~500 emails/day. For larger volumes, use a dedicated SMTP provider like SendGrid or Mailgun (update `email_sender.py`).

### Step 6 — Check Bounces

After a campaign is sent:

1. On the **Campaigns** page, click **"Check Bounces"** next to the sent campaign
2. The system connects to your Gmail inbox via IMAP and searches for:
   - Emails from `mailer-daemon@*`
   - Subjects containing "Delivery Status Notification", "Mail delivery failed", "Undelivered"
3. Any matched recipient addresses are marked as **bounced** in the database
4. Bounced contacts are excluded from future sends

**Run bounce checks periodically** — bounces often arrive hours after the send.

### Step 7 — Review Reports

1. Go to **Reports**
2. Click any campaign to expand its full send log
3. **Bounced Emails** panel shows all detected bounces with a "Remove" button
4. Clicking **Remove** marks the contact as unsubscribed — they won't receive future campaigns
5. Download the full send log as CSV with the download icon

---

## API Reference

The backend exposes a full REST API. Interactive docs at: `http://127.0.0.1:8000/docs`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/states` | List all states |
| GET | `/api/colleges` | List colleges (params: `state_code`, `college_type`, `search`, `page`, `limit`) |
| POST | `/api/scrape/start` | Start background scrape (`{"state_code": "TS"}`) |
| GET | `/api/scrape/status` | Current scrape progress |
| GET | `/api/scrape/stream/{state_code}` | SSE stream of real-time scrape progress |
| GET | `/api/contacts` | List contacts (params: `state_code`, `role`, `validation_status`, `search`) |
| POST | `/api/contacts/validate` | MX-validate contact IDs (`{"contact_ids": [1,2,3]}`) |
| GET | `/api/contacts/export` | Download contacts CSV |
| PATCH | `/api/contacts/{id}/unsubscribe` | Unsubscribe a contact |
| POST | `/api/campaigns` | Create campaign (multipart: `name`, `subject`, `template` file) |
| GET | `/api/campaigns` | List all campaigns |
| GET | `/api/campaigns/{id}` | Get campaign detail including HTML template |
| POST | `/api/campaigns/{id}/send` | Send campaign to recipients |
| GET | `/api/campaigns/{id}/status` | Live send stats |
| POST | `/api/campaigns/{id}/check-bounces` | Poll Gmail IMAP for bounces |
| GET | `/api/campaigns/{id}/report/export` | Download campaign report CSV |
| GET | `/api/reports/overview` | Dashboard aggregate stats |
| GET | `/api/reports/campaigns/{id}/sends` | Per-send records for a campaign |

---

## Scraping Details

### AICTE Portal
- URL: `https://facilities.aicte-india.org/dashboard/pages/getinstitutes.php`
- Covers: Engineering, Pharmacy, Architecture, Management, Applied Arts colleges
- Provides: college name, city, website URL, AICTE code, sometimes a direct contact email

### College Website Crawler
For each college URL discovered via AICTE, the crawler visits these paths:
`/contact`, `/contact-us`, `/administration`, `/placement`, `/placement-cell`, `/training-placement`, `/faculty`, `/staff`, `/team`

Email scoring (role assignment):
- Score +10 for keywords: `placement officer`, `tpo`, `training placement`, `placement cell`
- Score +8 for: `principal`, `director`, `vice chancellor`
- Score +5 for: `head of department`, `hod`, `dean`

Only emails whose domain has a valid MX record (confirmed via DNS lookup) are stored.

---

## Troubleshooting

**Backend fails to start**
```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```
Check the error. Most common: `aiosqlite` or `dnspython` install failed.

**Gmail SMTP authentication error**
- Confirm 2-Step Verification is enabled on your Google account
- App Password must be the 16-character code from Google, not your regular password
- Check that `GMAIL_APP_PASSWORD` in `backend\.env` has no spaces (Google shows it with spaces — remove them)

**No colleges found after scraping**
- AICTE's portal sometimes returns empty results if their API is under maintenance
- Try scraping one state at a time rather than all at once
- Check `http://127.0.0.1:8000/docs` → `POST /api/scrape/start` to test manually

**Bounce check finds nothing**
- Make sure at least 30 minutes have passed after sending (bounces take time to arrive)
- Check that your Gmail inbox (not Spam/Promotions) received the NDR emails
- Increase `since_days` in `bounce_checker.py` if you're checking after a week

---

## Adding More States

1. Open `backend/database.py`
2. Add to the `states_data` list in `_seed_states()`:
   ```python
   {"name": "Maharashtra", "code": "MH"},
   ```
3. Restart the backend
4. The new state appears in all dropdowns immediately
5. Use the AICTE state name exactly as it appears on the portal (e.g. "MAHARASHTRA")
6. Update `STATE_MAP` in `backend/scrapers/aicte_scraper.py`:
   ```python
   "MH": "MAHARASHTRA",
   ```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS v4 + Recharts |
| Backend | Python 3.11 + FastAPI + Uvicorn |
| Database | SQLite via SQLAlchemy (async / aiosqlite) |
| Scraping | httpx + BeautifulSoup4 + lxml |
| Email Validation | email-validator + dnspython (MX lookup) |
| Email Sending | Gmail SMTP (smtplib / STARTTLS) |
| Bounce Detection | Gmail IMAP (imapclient) |
| CSV | Python stdlib `csv` module |

---

## License

Private use. Not for redistribution.
