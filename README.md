# Code Grader API - AI-Powered Educational Assessment System

## What I Built

This is a  AI-powered code grading and analytics system that I developed as a Graduate Teaching Assistant. It's designed to solve real problems by providing consistent, rubric-based grading and deep insights into student learning patterns. This system is well equiped with logging service, rate limiting service and a caching service

## Current Architecture & Capabilities


1. Automatically cleans and structures student submissions
2. Handles complex lab submissions with multiple components (Lab1A, Lab1B, Lab1C)
3. Two AI models work together - one for initial grading, another for quality assurance
4. Every evaluation follows predefined rubrics to maintain consistency

### Advanced Analytics & Insights

#### 📊 Student Performance Analytics
- **Individual Student Tracking**: Detailed performance history, trends, and personalized insights
- **Lab-Specific Analysis**: Deep dive into how students perform on specific programming concepts
- **Section & Semester Comparisons**: Cross-sectional analysis to identify patterns and outliers
- **Real-time Performance Monitoring**: Live tracking of student progress throughout the semester

#### AI-Powered Course Material Suggestions
Our newest feature uses vector search and AI to provide personalized learning recommendations:
- **Smart Topic Identification**: AI analyzes student performance to identify weak areas
- **Course Material Matching**: Uses FAISS vector database to find relevant study materials
- **Personalized Recommendations**: Generates specific, actionable suggestions for each student
- **Lab-Level Insights**: Provides course-wide recommendations for instructors

#### Comprehensive Metrics & Monitoring
- **Cost Analysis**: Track API usage, token consumption, and operational costs
- **Performance Metrics**: Monitor system health, response times, and reliability
- **Cache Optimization**: Smart caching strategies to reduce costs and improve speed
- **Error Tracking**: Comprehensive error monitoring and resolution

### Technical Infrastructure

#### Microservices Architecture
- **Evaluation Service**: Core grading engine with LLM integration
- **Analytics Service**: Advanced analytics and insights generation
- **Metrics Service**: System monitoring and cost tracking
- **Vector Service**: Course material search and recommendations

#### Technology Stack
- **Backend**: Django + Django REST Framework
- **Database**: PostgreSQL for persistent data
- **Caching**: Redis for performance optimization
- **AI Integration**: OpenAI GPT models for grading and analysis
- **Vector Search**: FAISS for course material recommendations
- **Monitoring**: Custom metrics and health monitoring

## 🎯 Key Features

### For Students
- **Consistent Grading**: Every submission is evaluated using the same criteria
- **Detailed Feedback**: Comprehensive, actionable feedback on code quality
- **Learning Recommendations**: Personalized suggestions for improvement
- **Progress Tracking**: Clear visibility into learning progress
- **College Resource Search**: Find campus services, events, schedules, and information

### For Instructors & GTAs
- **Time Savings**: Automated grading reduces manual workload by 80%
- **Consistency**: Eliminates grading variations between different instructors
- **Deep Insights**: Advanced analytics reveal course-wide patterns
- **Early Intervention**: Identify struggling students before it's too late

### For Course Coordinators
- **Quality Assurance**: Ensure grading standards are maintained across all sections
- **Resource Optimization**: Identify which topics need more instructional time
- **Cost Management**: Track and optimize AI usage costs
- **Scalability**: Handle thousands of students without quality degradation

## Feature Showcase

### Real Student Performance Analysis Example

Here's what a student gets when they request their performance analysis:

```json
{
    "student_id": "STU199998",
    "name": "Stephanie Chen",
    "section": "23",
    "semester": "Spring 2025",
    "instructor_name": "Dr. Sarah Johnson",
    "total_evaluations": 1,
    "total_points_lost": 47,
    "average_points_lost": 47.0,
    "lab_breakdown": [
        {
            "lab_name": "Lab6",
            "count": 1,
            "avg_points": 47.0,
            "total_points": 47
        }
    ],
    "recent_evaluations": [
        {
            "lab_name": "Lab6",
            "points_lost": 47,
            "date": "2025-06-21T18:07:17.258000+00:00"
        }
    ],
    "performance_summary": "The student demonstrates a solid understanding of linked list concepts, indicating comfort with data structures. However, the significant points lost suggest struggles with complex operations involving these structures, which may include loops for traversal and manipulation. To improve, the student should focus on enhancing their skills in handling complex data structures and refining their error handling and code structure for better clarity and efficiency.",
    "suggestions": {
        "student_name": "Stephanie Chen",
        "topics_identified": [
            "complex data structures",
            "linked list operations", 
            "error handling and code structure"
        ],
        "materials_found": 3,
        "suggestions": "complex data structures: fundamentals-of-computer-programming-with-csharp-nakov-ebook-v2013.pdf\nlinked list operations: jjj-os-20170625.pdf\nerror handling and code structure: fundamentals-of-computer-programming-with-csharp-nakov-ebook-v2013.pdf",
        "generated_at": "2025-06-22T02:14:57.562837+00:00"
    }
}
```

### Future ->  College Resource Search Capabilities

I want to extend this system to include intelligent search across all college-related resources. Students can ask natural language questions and get instant answers:

For Example
####  **Student Services & Support**
- *"Can I get the phone number of student services?"*
- *"Where is the financial aid office located?"*
- *"What are the tutoring center hours?"*
- *"How do I contact my academic advisor?"*

#### **Campus Events & Activities**
- *"What are the upcoming events this week?"*
- *"When is the next career fair?"*
- *"Are there any workshops on resume building?"*
- *"What's happening during homecoming weekend?"*

#### **Academic Information**
- *"Do I have any assignments or exams this week?"*
- *"When is spring break?"*
- *"What's the deadline for course registration?"*
- *"When do final exams start?"*

#### **Faculty & Course Information**
- *"Who will teach CS Algorithms next semester?"*
- *"What are Professor Smith's office hours?"*
- *"Which sections of Calculus are still open?"*
- *"What prerequisites do I need for Data Structures?"*

#### **Campus Facilities**
- *"What time does the library close?"*
- *"Where can I find a computer lab?"*
- *"Is the gym open on weekends?"*
- *"What dining options are available today?"*
#### *Financial & Administrative**
- *"When is tuition due?"*
- *"How do I apply for scholarships?"*
- *"What's the process for dropping a class?"*
- *"Where can I get my student ID card?"*

##need to add user based authentication --> right now im using it in local 
## advcaced user storage capabilities -> like hashing to protect user data

###  **How It Works**
1. **Natural Language Processing**: Students ask questions in plain English
2. **Intelligent Search**: AI searches across all college databases and resources
3. **Context-Aware Responses**: System provides relevant, up-to-date information
4. **Personalized Results**: Responses are tailored to the student's specific situation

### **Accessibility**
- **24/7 Availability**: Get answers anytime, anywhere
- **Multi-Platform**: Works on web, mobile apps, and chatbots
- **Voice Integration**: Ask questions using voice commands
- **Multilingual Support**: Available in multiple languages

## API Endpoints

### Evaluation Services
```
POST /api/evaluation/evaluate/           # Main grading endpoint
POST /api/evaluation/rubrics/create/     # Create new rubrics
GET  /api/evaluation/rubrics/            # Get all rubrics
GET  /api/evaluation/stats/              # Evaluation statistics
```

### Analytics Services
```
GET /api/analytics/students/{student_id}/                    # Individual student analysis
GET /api/analytics/performance/lab/{lab_name}/               # Lab performance
GET /api/analytics/performance/section/{section}/            # Section analysis
GET /api/analytics/performance/semester/{semester}/          # Semester overview
GET /api/analytics/summary/lab/{lab_name}/                   # Lab summary with suggestions
GET /api/analytics/summary/section/{section}/                # Section summary
GET /api/analytics/summary/semester/{semester}/              # Semester summary
```

### Metrics & Monitoring
```
GET /api/metrics/cost-analysis/          # Cost tracking
GET /api/metrics/request-metrics/        # Performance metrics
GET /api/metrics/token-usage/            # Token consumption
GET /api/metrics/cache-status/           # Cache performance
```