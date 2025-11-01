# ServeWell

An AI-powered customer feedback and analytics platform for restaurants that automatically collects reviews via WhatsApp, performs sentiment analysis, and generates actionable insights through natural language queries.

---

## Technologies Used

### Backend
- **Python 3.x** - Primary programming language
- **Django** - Web framework for building the REST API
- **Django REST Framework** - For building RESTful APIs
- **PostgreSQL** - Primary database
- **Redis** - Message broker and caching
- **Celery** - Distributed task queue for async processing
- **Celery Beat** - Periodic task scheduler
- **Gunicorn** - WSGI HTTP server
- **SQLAlchemy** - SQL toolkit for database operations

### Frontend
- **Next.js 15** - React framework for building the UI
- **React 18** - JavaScript library for building user interfaces
- **Bootstrap 5** - CSS framework for responsive design
- **ApexCharts** - Interactive data visualizations
- **React Toastify** - Notification system
- **jQuery & DataTables** - Data table management
- **FullCalendar** - Calendar component

### DevOps & Infrastructure
- **Docker** - Containerization platform
- **Docker Compose** - Multi-container orchestration
- **Makefile** - Build automation

### Data Processing & Analytics
- **Pandas** - Data manipulation and analysis
- **Pillow** - Image processing library
- **Faker** - Test data generation

---

## 3rd Party Services

### Communication Services
- **WAAPI (WhatsApp API)** - WhatsApp messaging integration for automated customer outreach and feedback collection
  - Used for: Sending review requests, receiving customer responses, audio message handling

### Audio Processing
- **LemonFox AI** - Audio transcription service
  - Used for: Converting voice message responses to text for sentiment analysis

---

## AI Services

### AI Models & Platforms

1. **Groq AI (Primary LLM Provider)**
   - **Model**: `compound-beta-mini`
   - **Use Cases**:
     - SQL query generation from natural language
     - Customer review sentiment analysis
     - Emotion detection and classification
     - Product/keyword extraction from feedback
     - Automated question generation for customer follow-ups
   - **Configuration**: Requires `GROQ_API_KEY` environment variable

2. **E2B Code Interpreter**
   - **Use Case**: Sandboxed code execution for data visualization
   - **Configuration**: Requires `E2B_API_KEY` environment variable

### AI Features Built

1. **SQL Generator Agent** (`backend/agent.py`)
   - Converts natural language queries to PostgreSQL commands
   - Self-evaluation and query refinement system
   - Automatic data visualization generation
   - Schema-aware query generation with validation

2. **Sentiment Analysis Engine**
   - Multi-label sentiment classification (positive/negative/neutral/mixed)
   - Emotion detection (happy, sad, angry, surprised, disappointed, etc.)
   - Product mention extraction
   - Keyword extraction for actionable insights

3. **Automated Review Collection System**
   - Scheduled review requests via WhatsApp
   - Dynamic question generation based on previous responses
   - Multi-modal support (text and audio responses)
   - Intelligent conversation tracking

4. **Natural Language Analytics API**
   - Query restaurant data using plain English
   - Automatic visualization generation
   - Real-time data processing and formatting

---

## How to Run the Project

### Prerequisites

Ensure you have the following installed on your system:
- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)

### Environment Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd serve-well
```

2. **Create environment file**

Create a `.env` file in the root directory with the following variables:

```env
# Django Configuration
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=*

# Database Configuration
POSTGRES_DB=servewell_db
POSTGRES_USER=servewell_user
POSTGRES_PASSWORD=your-secure-password
POSTGRES_HOST=db
POSTGRES_PORT=5432
DB_HOST=db
DB_PORT=5432

# Redis Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# AI Services API Keys
GROQ_API_KEY=your-groq-api-key
E2B_API_KEY=your-e2b-api-key
LEMON_FOX_API_KEY=your-lemonfox-api-key
```

### Running with Docker (Recommended)

1. **Build the containers**
```bash
docker-compose build
```

2. **Start all services**
```bash
docker-compose up
```

Or run in detached mode:
```bash
docker-compose up -d
```

3. **Apply database migrations**
```bash
docker-compose exec django python manage.py migrate
```

4. **Create a superuser (admin account)**
```bash
docker-compose exec django python manage.py createsuperuser
```

5. **Load test data (optional)**
```bash
docker-compose exec django python manage.py ingest_test_data
docker-compose exec django python manage.py generate_test_orders
```

### Using Makefile Commands

For convenience, you can use the provided Makefile:

```bash
# Build the project
make build

# Start services
make up

# Stop services
make down

# Restart services
make restart

# View logs
make logs

# Access Django shell
make shell

# Run migrations
make migrate

# Create superuser
make createsuperuser

# Restart Celery workers
make restart-celery
```

### Accessing the Application

- **Backend API**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
- **Frontend (Next.js)**: Navigate to `frontend/` directory and run:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
  Then access at http://localhost:3000

### Service Architecture

The application runs with the following containers:
- **django** - Main Django application (port 8000)
- **db** - PostgreSQL database (port 5432)
- **redis** - Redis cache and message broker (port 6379)
- **celery** - Celery worker for async tasks
- **celery-beat** - Celery beat scheduler for periodic tasks

### Stopping the Application

```bash
docker-compose down
```

To remove volumes as well:
```bash
docker-compose down -v
```

---

## API Endpoints

### Webhook Endpoint
- `POST /api/webhook/<security_token>/` - WhatsApp webhook for receiving messages

### Analytics Endpoint
- `POST /api/natural-language-query/` - Query data using natural language
  - Authentication: Required (JWT Token)
  - Body: `{"query": "Show me all negative reviews from last week"}`

---

## Project Structure

```
serve-well/
├── backend/              # Django application
│   ├── models.py        # Database models
│   ├── views.py         # API views
│   ├── tasks.py         # Celery tasks
│   ├── agent.py         # AI agent for SQL generation
│   ├── utils.py         # Utility functions
│   └── helpers.py       # Helper functions
├── frontend/            # Next.js application
│   └── src/            # Source files
├── servewell/          # Django project settings
├── docker-compose.yml  # Docker orchestration
├── Dockerfile          # Docker image definition
├── requirements.txt    # Python dependencies
└── Makefile           # Build automation

```

---

## Notes

- Ensure all API keys are configured before starting the application
- The system automatically schedules review requests every 6 hours for completed orders
- Sentiment analysis runs hourly via Celery Beat
- Audio messages are automatically transcribed before processing
- The SQL Generator Agent validates and refines queries before execution

---

## License



