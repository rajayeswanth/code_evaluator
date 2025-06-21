# AI Code Evaluation System - Django REST Framework

A comprehensive Django REST Framework system for AI-powered code evaluation with database storage, monitoring, and analytics.

## Features

- **AI-Powered Code Evaluation**: Uses GPT-4.1-nano for intelligent code assessment
- **Database Storage**: PostgreSQL/SQLite support for persistent data
- **Student Tracking**: Complete student information and performance history
- **Rubric Management**: Dynamic rubric creation and management via API
- **Parallel Evaluation**: Multi-threaded evaluation of multiple files
- **Comprehensive Monitoring**: System metrics, error logging, and analytics
- **RESTful APIs**: Clean, well-documented API endpoints
- **Robust Error Handling**: Comprehensive error logging and recovery

## System Architecture

### Database Models

- **Rubric**: Evaluation criteria and point systems
- **Student**: Student information and metadata
- **Evaluation**: Individual file evaluation results
- **EvaluationSession**: Complete submission sessions
- **LLMResponse**: Detailed LLM interaction data
- **SystemMetrics**: Performance and usage metrics
- **ErrorLog**: Comprehensive error tracking

### Core Services

- **RubricService**: Rubric management and retrieval
- **StudentService**: Student data management
- **EvaluationService**: Core evaluation logic
- **MonitoringService**: Analytics and insights

## API Endpoints

### Rubric Management
- `GET /api/evaluation/rubrics/` - Get all rubrics
- `POST /api/evaluation/rubrics/` - Create new rubric
- `GET /api/evaluation/rubrics/{id}/` - Get specific rubric
- `PUT /api/evaluation/rubrics/{id}/` - Update rubric

### Student Management
- `GET /api/evaluation/students/` - Get all students
- `POST /api/evaluation/students/` - Create/update student

### Code Evaluation
- `POST /api/evaluation/evaluate/` - Evaluate code submission
- `GET /api/evaluation/evaluation-history/` - Get evaluation history
- `GET /api/evaluation/students/{id}/performance/` - Student performance analytics

### Monitoring & Analytics
- `GET /api/evaluation/monitoring/` - System metrics and statistics
- `GET /api/evaluation/errors/` - Error logs and debugging

### Legacy Support
- `POST /api/evaluation/legacy/evaluate/` - Backward compatibility endpoint

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key_here
DEBUG=True
SECRET_KEY=your_django_secret_key
DATABASE_URL=sqlite:///db.sqlite3
```

### 3. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Load Initial Rubrics
```bash
python manage.py load_rubrics
```

### 5. Run Development Server
```bash
python manage.py runserver
```

## Usage Examples

### 1. Create a Rubric
```bash
curl -X POST http://localhost:8000/api/evaluation/rubrics/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Lab 3A - Credit Card Calculator",
    "filename": "Lab3A.py",
    "total_points": 30,
    "criteria": {
      "input_variables": {"points": 8, "description": "Correct input handling"},
      "calculations": {"points": 12, "description": "Mathematical accuracy"},
      "output_formatting": {"points": 10, "description": "Proper output format"}
    }
  }'
```

### 2. Evaluate Code Submission
```bash
curl -X POST http://localhost:8000/api/evaluation/evaluate/ \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "S12345",
    "name": "John Doe",
    "section": "14",
    "term": "Spring 2025",
    "instructor_name": "Dr. Smith",
    "lab_name": "Lab 3",
    "input": "Lab3A.py\nDownload\n# Your code here...\n\nLab3B.py\nDownload\n# More code...",
    "submission_metadata": {
      "submission_time": "2025-01-15T10:30:00Z",
      "platform": "web"
    }
  }'
```

### 3. Get Student Performance
```bash
curl http://localhost:8000/api/evaluation/students/S12345/performance/
```

### 4. View System Monitoring
```bash
curl "http://localhost:8000/api/evaluation/monitoring/?days=7"
```

## Configuration

### OpenAI Settings
- **Model**: `gpt-4.1-nano`
- **Max Tokens**: 200
- **Temperature**: 0.1 (for consistent results)
- **Max Workers**: 3 (parallel evaluations)

### Evaluation Settings
- **Timeout**: 30 seconds per evaluation
- **Double-check**: Each evaluation is reviewed by a second LLM
- **Format Validation**: Strict output format enforcement

## Database Schema

### Key Relationships
- **Student** → **EvaluationSession** (one-to-many)
- **EvaluationSession** → **Evaluation** (one-to-many)
- **Evaluation** → **LLMResponse** (one-to-many)
- **Rubric** → **Evaluation** (one-to-many)

### Important Fields
- **Session Tracking**: Unique session IDs for each submission
- **Token Usage**: Detailed LLM token consumption tracking
- **Timing Data**: Evaluation and response time measurements
- **Error Context**: Comprehensive error logging with stack traces

## Monitoring & Analytics

### System Metrics
- **API Call Volume**: Request frequency and patterns
- **Token Usage**: LLM consumption tracking
- **Response Times**: Performance monitoring
- **Error Rates**: System health indicators

### Student Analytics
- **Performance Trends**: Individual student progress
- **Common Issues**: Frequently occurring problems
- **Success Rates**: Evaluation completion statistics

### Error Tracking
- **Error Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Error Types**: Categorized error classification
- **Context Data**: Request and session information
- **Stack Traces**: Detailed error debugging

## Development

### Project Structure
```
Code_grader/
├── code_grader_api/          # Django project settings
├── evaluation/               # Main app
│   ├── models.py            # Database models
│   ├── serializers.py       # API serializers
│   ├── services.py          # Business logic
│   ├── views.py             # API endpoints
│   └── management/          # Django commands
├── data/                    # File processing
├── evaluators/              # Evaluation logic
├── services/                # External services
├── utils/                   # Utilities
└── logs/                    # Application logs
```

### Adding New Features
1. **Models**: Add to `evaluation/models.py`
2. **Serializers**: Create in `evaluation/serializers.py`
3. **Services**: Implement in `evaluation/services.py`
4. **Views**: Add to `evaluation/views.py`
5. **URLs**: Update `evaluation/urls.py`

## Production Deployment

### Environment Variables
```env
DEBUG=False
SECRET_KEY=your_production_secret_key
DATABASE_URL=postgresql://user:pass@host:port/db
OPENAI_API_KEY=your_production_openai_key
ALLOWED_HOSTS=your-domain.com
```

### Security Considerations
- **API Authentication**: Implement token-based auth
- **Rate Limiting**: Add request throttling
- **Input Validation**: Sanitize all user inputs
- **Error Handling**: Don't expose sensitive data in errors

### Performance Optimization
- **Database Indexing**: Optimize query performance
- **Caching**: Implement Redis for frequent queries
- **Async Processing**: Use Celery for long-running tasks
- **Load Balancing**: Scale horizontally with multiple instances

## Troubleshooting

### Common Issues
1. **Missing Rubrics**: Run `python manage.py load_rubrics`
2. **Database Errors**: Check migrations with `python manage.py showmigrations`
3. **OpenAI Errors**: Verify API key and quota
4. **File Detection Issues**: Check input format and file boundaries

### Logs
- **Application Logs**: `logs/app.log`
- **Error Logs**: Database table `error_logs`
- **System Metrics**: Database table `system_metrics`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 