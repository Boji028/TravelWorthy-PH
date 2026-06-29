# Travel Worthy PH

A Flask-based travel agency web application with an admin panel, tour packages,
booking system, blog, visa information, and user authentication.

## Setup & Run

### 1. Create and activate a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file in the project root:

SECRET_KEY=your_strong_secret_key_here
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=your_strong_password_here
DATABASE_URL=sqlite:///travel_agency.db

> ⚠️ Never commit `.env` to version control. It is already listed in `.gitignore`.

### 4. Run the application
```bash
python run.py
```

### 5. Open in browser

http://localhost:5000

The database and default admin account are created automatically on first run.

---

## Project Structure

travel_agency/
├── app.py                  # Flask app factory & config
├── run.py                  # Entry point - run this!
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (do not commit)
├── .gitignore
├── models/
│   ├── user.py             # User model
│   ├── package.py          # TourPackage model
│   ├── booking.py          # Booking model
│   ├── inquiry.py          # Plan My Trip inquiries
│   ├── contact.py          # Contact form messages
│   ├── blog.py             # Blog posts
│   ├── continent.py        # Continents
│   ├── country.py          # Countries
│   ├── testimonial.py      # Customer reviews
│   └── visa.py             # Visa information
├── routes/
│   ├── main.py             # Home, About, Contact, Reviews
│   ├── auth.py             # Login, Register, Profile
│   ├── packages.py         # Package listing, details, visa
│   ├── bookings.py         # Book, manage bookings, plan my trip
│   ├── blog.py             # Blog listing & detail
│   └── admin.py            # Admin dashboard & management
├── templates/
│   ├── base.html           # Base layout
│   ├── 404.html
│   ├── 500.html
│   ├── main/               # Home, About, Contact, Reviews
│   ├── auth/               # Login, Register, Profile
│   ├── packages/           # Package list, detail, visa
│   ├── bookings/           # Book, my bookings, plan my trip
│   ├── blog/               # Blog list & detail
│   └── admin/              # All admin panel pages
└── static/
├── css/main.css
├── js/
└── images/             # Uploaded tour & review images

---

## Features

### Customer-facing
- 🔐 User registration, login, and profile
- 🗺️ Browse and search tour packages by continent, country, or destination
- 📅 Book packages with travel date and group size
- 📋 View and cancel bookings
- ✈️ Plan My Trip — submit a custom trip inquiry
- 🛂 Visa information by country
- 📝 Blog with travel articles
- ⭐ Customer reviews with star ratings and photo uploads
- 📬 Contact form

### Admin panel (`/admin`)
- 📊 Dashboard with stats (users, bookings, pending, inquiries)
- 📦 Manage tour packages (add, edit, delete, image upload)
- 📅 Manage bookings (view, update status)
- 👥 View all registered users
- 📋 Manage trip inquiries (update status, delete)
- 📬 View contact messages
- 📝 Manage blog posts (add, edit, delete)
- 🌍 Manage continents and countries
- 🛂 Manage visa entries (add, edit, delete, PDF upload)

---

## Tech Stack
- **Backend:** Python, Flask 3, SQLAlchemy, Flask-Login, Flask-WTF
- **Database:** SQLite (auto-created on first run)
- **Frontend:** Jinja2 templates, vanilla CSS & JS
- **Auth:** Werkzeug password hashing, CSRF protection

---

## Security Notes
- All POST forms are CSRF-protected via Flask-WTF
- Passwords are hashed using Werkzeug's `generate_password_hash`
- Admin routes are protected by a custom `@admin_required` decorator
- File uploads are validated by extension and saved with `secure_filename`
- Never share or commit your `.env` file

### Email verification (production)

Set in `.env` before deploying:

```env
FLASK_ENV=production
REQUIRE_EMAIL_VERIFICATION=true
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
```

When enabled, new users must click the link in their verification email before they can log in. It defaults to **on** when `FLASK_ENV=production`, and **off** in development. Admin accounts are always treated as verified.