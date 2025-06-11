# Property Manager

A hobby project to learn end-to-end application development with Python, Django & DRF, modern best practices, and AWS infrastructure. The app accepts property listing URLs (starting with Rightmove), scrapes configurable fields, and writes them to Google Sheets (MVP). Future phases will migrate to MySQL, add multiple providers, CI/CD, Terraform-driven AWS deployment, and OAuth authentication.

---

## Features

- **MVP endpoint** (`POST /api/scrape/`) to submit a listing URL and receive back stubbed data  
- **Configurable field mappings** via `ProviderConfig` model and admin CRUD API  
- **Modular scraper architecture** with adapter interface (`.fetch(url) → dict`)  
- **Google Sheets integration** (stubbed for now)  
- **Django REST Framework** for API & serializers  
- **Pipenv**-managed environment with Python 3.13  
- **Jenkinsfile** for lint & test pipeline (flake8 + pytest)  

---

## Tech Stack

- **Language & Framework**: Python 3.13, Django 5.x, Django REST Framework  
- **Scraping**: `requests` + `beautifulsoup4`  
- **Sheets**: `google-auth`, `google-api-python-client`  
- **Async (future)**: Celery or RQ  
- **CI/CD**: Jenkins  
- **Infrastructure (future)**: Terraform → AWS ECS/EKS + RDS MySQL  
- **Auth (future)**: OAuth with Microsoft Entra ID via Django Allauth  

---

## Installation

1. **Clone the repo**  
   ```bash
   git clone https://github.com/yourusername/property-manager.git
   cd property-manager
   ```

2. **Install dependencies**  
   ```bash
   pipenv install --dev
   pipenv shell
   ```

3. **Configure environment**  
   Create a `.env` file in the project root with:

   ```env
   DJANGO_SECRET_KEY=your-secret-key
   DJANGO_DEBUG=True
   DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

   # Google Sheets credentials
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id
   ```

4. **Apply migrations & run**  
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

5. **Access**  
   - API root: [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)  
   - Scrape endpoint: `POST /api/scrape/` with JSON `{"url": "<listing-URL>"}`  
   - Admin (for ProviderConfig): create a superuser and log in at `/admin/`

6. **Usage Example**  
   ```bash
   curl -X POST http://127.0.0.1:8000/api/scrape/ \
        -H "Content-Type: application/json" \
        -d '{"url":"https://www.rightmove.co.uk/property-for-sale/example-1234"}'
   ```

   **Response**
   ```json
   {
      "url": "https://www.rightmove.co.uk/properties/123456",
      "address": "Jahanam Dare, London, E6",
      "price": "£425,000",
      "beds": "2",
      "bathrooms": "2",
      "summary": "2 bedroom flat for sale in Jahanam Dare, London, E6 - Rightmove.",
      "service_charge": "£2,134"
   }
   ```

7. **Testing**  
   Run the following commands in your Pipenv shell:
   ```bash
   pytest --maxfail=1 --disable-warnings -q
   flake8 .
   ```

   Or use the provided scripts for full test and coverage runs:

   - On Windows:
     ```cmd
     scripts\run_all_unittests.bat
     ```
   - On Linux/macOS:
     ```bash
     ./scripts/run_all_unittests.sh
     ```

   These scripts run all unit tests with coverage reporting and are the recommended way to check code quality before commits.

---

## To Do List

- [x] Implement real parsing in RightmoveAdapter using BeautifulSoup selectors.
- [ ] Hook up Google Sheets API in apps/sheets/sheets.py.
- [ ] Migrate database from SQLite to MySQL.
- [ ] Introduce async task queue (Celery/RQ) and retry logic.
- [ ] Dockerize & CI/CD with Jenkins → AWS deployment.
- [ ] Terraform to provision AWS infra (ECS/EKS, RDS, IAM).
- [ ] OAuth authentication for public access.
- [ ] React front end for URL submission & status tracking.

