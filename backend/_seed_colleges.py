"""
Seeds the database with 60+ real colleges across all 5 states,
then scrapes each website for genuine contact emails.
Run once: python _seed_colleges.py
"""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

COLLEGES = [
    # ── TELANGANA ────────────────────────────────────────────────
    ("JNTU Hyderabad", "Hyderabad", "TS", "https://jntuh.ac.in", "Engineering"),
    ("BITS Pilani Hyderabad", "Hyderabad", "TS", "https://www.bits-pilani.ac.in/hyderabad", "Engineering"),
    ("IIIT Hyderabad", "Hyderabad", "TS", "https://www.iiit.ac.in", "Engineering"),
    ("IIT Hyderabad", "Hyderabad", "TS", "https://iith.ac.in", "Engineering"),
    ("Osmania University", "Hyderabad", "TS", "https://osmania.ac.in", "Arts"),
    ("University of Hyderabad", "Hyderabad", "TS", "https://uohyd.ac.in", "Arts"),
    ("NIT Warangal", "Warangal", "TS", "https://www.nitw.ac.in", "Engineering"),
    ("Kakatiya University", "Warangal", "TS", "https://www.kakatiya.ac.in", "Arts"),
    ("NALSAR Law University", "Hyderabad", "TS", "https://nalsar.ac.in", "Law"),
    ("Chaitanya Bharathi Institute of Technology", "Hyderabad", "TS", "https://cbit.ac.in", "Engineering"),
    ("VNR VJIET", "Hyderabad", "TS", "https://vnrvjiet.ac.in", "Engineering"),
    ("GRIET Hyderabad", "Hyderabad", "TS", "https://www.griet.ac.in", "Engineering"),
    ("Vasavi College of Engineering", "Hyderabad", "TS", "https://www.vasavicollege.ac.in", "Engineering"),
    ("CVR College of Engineering", "Hyderabad", "TS", "https://cvr.ac.in", "Engineering"),
    ("MLR Institute of Technology", "Hyderabad", "TS", "https://www.mlrinstitutions.ac.in", "Engineering"),
    ("SR Engineering College", "Warangal", "TS", "https://www.srec.ac.in", "Engineering"),
    ("Telangana University", "Nizamabad", "TS", "https://www.telanganauniversity.ac.in", "Arts"),
    ("Mahatma Gandhi University Nalgonda", "Nalgonda", "TS", "https://mguniversity.ac.in", "Arts"),
    ("Hyderabad Business School GITAM", "Hyderabad", "TS", "https://www.gitam.edu", "Management"),
    ("Malla Reddy Institute of Technology", "Hyderabad", "TS", "https://mrits.ac.in", "Engineering"),
    # ── ANDHRA PRADESH ──────────────────────────────────────────
    ("Andhra University", "Visakhapatnam", "AP", "https://andhrauniversity.edu.in", "Arts"),
    ("JNTU Kakinada", "Kakinada", "AP", "https://jntuk.edu.in", "Engineering"),
    ("JNTU Anantapur", "Anantapur", "AP", "https://jntua.ac.in", "Engineering"),
    ("Sri Venkateswara University", "Tirupati", "AP", "https://www.svuniversity.edu.in", "Arts"),
    ("Acharya Nagarjuna University", "Guntur", "AP", "https://nagarjunauniversity.ac.in", "Arts"),
    ("Krishna University", "Machilipatnam", "AP", "https://krishnauniversity.ac.in", "Arts"),
    ("Vignan University", "Vadlamudi", "AP", "https://vignanuniversity.org", "Engineering"),
    ("VIT-AP University", "Amaravati", "AP", "https://vitap.ac.in", "Engineering"),
    ("SRM University AP", "Amaravati", "AP", "https://srmap.edu.in", "Engineering"),
    ("GITAM University Vizag", "Visakhapatnam", "AP", "https://www.gitam.edu/campus/vizag", "Engineering"),
    ("Dr BR Ambedkar University", "Srikakulam", "AP", "https://www.andhrauniversity.edu.in", "Arts"),
    ("Koneru Lakshmaiah University", "Guntur", "AP", "https://kluniversity.in", "Engineering"),
    ("Jawaharlal Nehru Architecture University", "Hyderabad", "AP", "https://jnafau.ac.in", "Arts"),
    ("Adikavi Nannaya University", "Rajahmundry", "AP", "https://aknu.edu.in", "Arts"),
    ("IIITDM Kurnool", "Kurnool", "AP", "https://iiitk.ac.in", "Engineering"),
    # ── BIHAR ───────────────────────────────────────────────────
    ("IIT Patna", "Patna", "BR", "https://www.iitp.ac.in", "Engineering"),
    ("NIT Patna", "Patna", "BR", "https://nitp.ac.in", "Engineering"),
    ("Patna University", "Patna", "BR", "https://www.patnauniversity.ac.in", "Arts"),
    ("Magadh University", "Bodh Gaya", "BR", "https://magadhuniversity.ac.in", "Arts"),
    ("Nalanda Open University", "Patna", "BR", "https://nalandaopenuniversity.com", "Arts"),
    ("BNMU Madhepura", "Madhepura", "BR", "https://bnmu.ac.in", "Arts"),
    ("JP University Chapra", "Chapra", "BR", "https://jpv.bih.nic.in", "Arts"),
    ("VKS University Ara", "Ara", "BR", "https://vksu.ac.in", "Arts"),
    ("Lalit Narayan Mithila University", "Darbhanga", "BR", "https://lnmu.ac.in", "Arts"),
    ("BN Mandal University", "Madhepura", "BR", "https://bnmu.ac.in", "Arts"),
    # ── JHARKHAND ───────────────────────────────────────────────
    ("IIT (ISM) Dhanbad", "Dhanbad", "JH", "https://iitism.ac.in", "Engineering"),
    ("NIT Jamshedpur", "Jamshedpur", "JH", "https://www.nitjsr.ac.in", "Engineering"),
    ("BIT Mesra", "Ranchi", "JH", "https://www.bitmesra.ac.in", "Engineering"),
    ("Ranchi University", "Ranchi", "JH", "https://ranchiuniversity.ac.in", "Arts"),
    ("Vinoba Bhave University", "Hazaribag", "JH", "https://vbu.ac.in", "Arts"),
    ("Birsa Institute of Technology", "Dhanbad", "JH", "https://bitsindri.ac.in", "Engineering"),
    ("Jharkhand Rai University", "Ranchi", "JH", "https://jru.edu.in", "Engineering"),
    ("XISS Ranchi", "Ranchi", "JH", "https://xiss.ac.in", "Management"),
    ("Kolhan University", "Chaibasa", "JH", "https://www.kolhanuniversity.ac.in", "Arts"),
    ("UPES Dehradun (JH campus)", "Ranchi", "JH", "https://cet.upes.ac.in", "Engineering"),
    # ── DELHI ───────────────────────────────────────────────────
    ("University of Delhi", "Delhi", "DL", "https://www.du.ac.in", "Arts"),
    ("IIT Delhi", "Delhi", "DL", "https://www.iitd.ac.in", "Engineering"),
    ("Delhi Technological University", "Delhi", "DL", "https://dtu.ac.in", "Engineering"),
    ("Netaji Subhas University of Technology", "Delhi", "DL", "https://www.nsut.ac.in", "Engineering"),
    ("Jamia Millia Islamia", "Delhi", "DL", "https://www.jmi.ac.in", "Arts"),
    ("Guru Gobind Singh IP University", "Delhi", "DL", "https://www.ipu.ac.in", "Engineering"),
    ("Jawaharlal Nehru University", "Delhi", "DL", "https://www.jnu.ac.in", "Arts"),
    ("Amity University Delhi", "Delhi", "DL", "https://www.amity.edu/delhi", "Engineering"),
    ("Indraprastha College for Women", "Delhi", "DL", "https://ipcollege.ac.in", "Arts"),
    ("Lady Shri Ram College", "Delhi", "DL", "https://lsr.edu.in", "Arts"),
]


async def seed_and_scrape():
    from database import init_db, AsyncSessionLocal
    from models import College, Contact, State
    from sqlalchemy import select
    from scrapers.college_scraper import scrape_college_emails
    from services.email_validator import validate_email_address
    from datetime import datetime

    await init_db()

    async with AsyncSessionLocal() as db:
        # Load state map
        result = await db.execute(select(State))
        state_map = {s.code: s for s in result.scalars().all()}

    # Insert colleges
    print(f"Seeding {len(COLLEGES)} colleges...")
    college_ids = []
    async with AsyncSessionLocal() as db:
        for name, city, code, website, ctype in COLLEGES:
            state = state_map.get(code)
            if not state:
                continue
            exists = (await db.execute(
                select(College).where(College.name == name, College.state_id == state.id)
            )).scalar_one_or_none()
            if exists:
                college_ids.append((exists.id, name, website))
                continue
            c = College(
                name=name, state_id=state.id, city=city,
                website=website, college_type=ctype, scrape_status="pending",
            )
            db.add(c)
            await db.flush()
            college_ids.append((c.id, name, website))
        await db.commit()
    print(f"  {len(college_ids)} colleges ready in DB")

    # Scrape each college
    total_saved = 0
    for college_id, name, website in college_ids:
        if not website:
            continue
        print(f"\nScraping: {name}")
        print(f"  URL: {website}")

        try:
            contacts = await scrape_college_emails(website, name)
        except Exception as e:
            print(f"  ERROR: {e}")
            contacts = []

        saved = 0
        async with AsyncSessionLocal() as db:
            college = await db.get(College, college_id)
            for c in contacts:
                email = c['email'].lower().strip()
                if not email:
                    continue
                valid, reason = await validate_email_address(email)
                if not valid:
                    continue
                exists = (await db.execute(
                    select(Contact).where(Contact.email == email)
                )).scalar_one_or_none()
                if exists:
                    continue
                db.add(Contact(
                    college_id=college_id,
                    email=email,
                    name=c.get('name', ''),
                    role=c.get('role', 'General'),
                    source_url=c.get('source_url', ''),
                    validation_status='valid',
                    mx_valid=True,
                ))
                saved += 1

            if college:
                college.scrape_status = 'done'
                college.last_scraped = datetime.utcnow()
                db.add(college)
            await db.commit()

        total_saved += saved
        print(f"  Saved {saved} valid emails  (running total: {total_saved})")

    print(f"\n{'='*60}")
    print(f"  SEEDING COMPLETE")
    print(f"  Colleges: {len(college_ids)}")
    print(f"  Emails saved to DB: {total_saved}")
    print(f"  Open http://localhost:5173 and refresh Dashboard")
    print(f"{'='*60}")


asyncio.run(seed_and_scrape())
