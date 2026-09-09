# CheckBite AI

**CheckBite AI** is a modern, student-friendly Django web application designed to help users decode packaged food products by scanning barcodes or searching by product name. Powered by **Google Gemini 2.5 AI** and the **Open Food Facts API**, CheckBite AI analyzes ingredients, macronutrients, and allergen warnings to provide personalized, educational health insights.

---

## 🌟 Main Features

- 📷 **Barcode Camera Scanner**: Real-time barcode scanning using device camera (EAN-13, UPC, Code 128).
- 🔍 **Manual Barcode & Product Search**: Search packaged foods directly via Open Food Facts database.
- 🤖 **Gemini AI Health Analysis**: Educational insights on nutritional positives, concerns, and body impact.
- 👤 **Personalized Guidance**: Custom health condition checks and allergen warning alerts based on user profile.
- ⚖️ **Product Comparison**: Side-by-side comparison of two packaged food products with AI recommendations.
- ⭐ **Saved Favorite Foods**: Bookmark frequently scanned items for quick access.
- 📜 **Scan History**: Filterable, searchable history of all past product scans.
- 📊 **Dashboard Statistics & Analytics**: Rating distribution doughnut charts and 7-day scan frequency line graphs powered by Chart.js.
- 📱 **Progressive Web App (PWA)**: Installable web application with offline support.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.13, Django 5.0.1
- **Database**: PostgreSQL (Production) / SQLite or PostgreSQL (Development)
- **Frontend**: HTML5, Vanilla CSS, Tailwind CSS CDN, JavaScript
- **AI Engine**: Google Gemini API (`google-genai` SDK)
- **Data Source**: Open Food Facts API
- **Charts & Graphics**: Chart.js 4.4.1
- **WSGI / Static Server**: Gunicorn, WhiteNoise

---

## 🚀 Local Development Setup Instructions

### 1. Prerequisites
- Python 3.10+
- Git
- PostgreSQL (or local default settings)

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/barcode-app.git
cd barcode-app
```

### 3. Create & Activate Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your local details:
```bash
cp .env.example .env
```

Edit `.env`:
```env
SECRET_KEY=your-local-django-secret-key
DEBUG=True
DB_NAME=food_health_db
DB_USER=postgres
DB_PASSWORD=your-local-postgres-password
DB_HOST=localhost
DB_PORT=5432
GEMINI_API_KEY=your-gemini-api-key-here
ALLOWED_HOSTS=127.0.0.1,localhost
```

### 6. Run Database Migrations
```bash
python manage.py migrate
```

### 7. Collect Static Files (Optional)
```bash
python manage.py collectstatic --noinput
```

### 8. Start Development Server
```bash
python manage.py runserver
```

Open your browser and navigate to **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**.

---

## 🔒 Security & Medical Disclaimer

- **Educational Purpose Only**: CheckBite AI provides general nutrition information and does not provide medical diagnoses or replace professional medical advice.
- **Secrets Management**: Secrets, API keys, and database passwords are loaded exclusively from environment variables (`.env`) and are ignored by Git.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
