# Code Grader API

This is a personal project I created while working as a Graduate Teaching Assistant (GTA) at my university. I built this system to solve a real problem we were facing with grading consistency across a large computer science course.

## The Problem

Our university has around 1600 students taking the introductory computer science course each semester. With 9 instructors, 17 GTAs, 40 TAs, and 1 program coordinator, maintaining consistency in grading was becoming a nightmare. Each grader had their own interpretation of the rubrics, leading to inconsistent feedback and scores for the same quality of work. Students were getting frustrated, and we were spending way too much time on grading.

## The Solution

I thought about using Large Language Models (LLMs) to provide consistent, rubric-based grading while saving us significant time. The idea was simple: instead of having multiple people grade the same type of assignment differently, we could use AI to follow strict rubrics and provide standardized feedback.

## Initial Architecture

The system works by taking student code submissions and processing them through a three-stage pipeline:

1. **Code Cleaning**: First, we clean and format the submitted code to ensure it's properly structured for analysis.

2. **Division into Parts**: We break down the code into logical sections (functions, classes, main logic, etc.) and send each part to a specialized LLM for evaluation.

3. **Multi-Stage Evaluation**: Each code section is evaluated by one LLM following strict rubrics, then a second LLM acts as an evaluator to review the first LLM's response and ensure it follows the rubric correctly and maintains consistent output format.

This approach ensures that every student gets evaluated using the same criteria, regardless of which TA or GTA would have graded their work.

## Additional Capabilities

As I developed the system, I realized we could add much more value beyond just grading. I built comprehensive analytics and metrics services that provide insights into:

- **Student Performance Analytics**: Track how students perform across different labs, sections, and semesters
- **Grading Consistency Metrics**: Monitor how well the system maintains consistency
- **Cost and Token Usage Tracking**: Keep track of API costs and usage patterns
- **Performance Monitoring**: System health, response times, and reliability metrics

These services help us understand not just individual student performance, but also course-wide trends and system effectiveness.

### Analytics Examples

The analytics system can answer complex questions about student performance using natural language. For example:

**Question**: "How is Alex Johnson performing in Lab2 compared to the class average?"

**LLM Response**: "Alex Johnson shows excellent progress in Lab2 with an average of 2.5 points lost compared to the class average of 4.1 points. Alex demonstrates strong array manipulation skills but struggles slightly with array boundary conditions. Overall, Alex is performing in the top 20% of the class for this lab."

**Question**: "What are the common issues students face in Lab3 across all sections?"

**LLM Response**: "Students in Lab3 commonly struggle with recursive function implementation, with 65% of students losing points on this criterion. The most frequent issues are: 1) Missing base cases in recursive functions (40% of students), 2) Incorrect parameter handling (35% of students), and 3) Infinite recursion due to improper termination conditions (25% of students). Section 14 shows the best performance with only 2.8 average points lost, while Section 17 needs additional support with 5.2 average points lost."

**Question**: "How has Jordan Smith's performance trended over the semester?"

**LLM Response**: "Jordan Smith shows a positive learning trajectory throughout the semester. Starting with Lab1 (3.5 points lost), Jordan has consistently improved, reaching Lab5 with only 1.8 points lost. Jordan excels in object-oriented programming concepts but needs additional practice with file handling operations. The trend suggests Jordan will likely perform well in advanced topics."

## Technical Infrastructure

The system uses Redis for caching to improve performance and reduce API costs. All API responses are cached for 2 hours, which significantly reduces the load on our LLM providers and speeds up response times for repeated queries.

The backend is built with Django and Django REST Framework, providing a robust API that can handle the high volume of requests from our large student body. We use PostgreSQL for data storage and Redis for caching and session management.

## API Endpoints

The system provides comprehensive APIs for:

**Evaluation Services:**
- POST /api/evaluation/evaluate/ - Main evaluation endpoint
- POST /api/evaluation/rubrics/create/ - Create new rubrics
- GET /api/evaluation/rubrics/ - Get all rubrics
- GET /api/evaluation/stats/ - Get evaluation statistics

**Analytics Services:**
- GET /api/analytics/labs/ - Get all labs with statistics
- GET /api/analytics/students/ - Get student information
- GET /api/analytics/performance/lab/{lab_name}/ - Lab performance analysis
- GET /api/analytics/performance/section/{section}/ - Section performance analysis
- GET /api/analytics/performance/semester/{semester}/ - Semester performance analysis

**Metrics Services:**
- GET /api/metrics/cost-analysis/ - Cost analysis
- GET /api/metrics/request-metrics/ - Request metrics
- GET /api/metrics/token-usage/ - Token usage analysis
- GET /api/metrics/cache-status/ - Cache status

**Health and Monitoring:**
- GET /api/evaluation/health/ - System health check

## Project Status

This is a personal project I developed to explore how AI could improve educational processes. While it demonstrates the potential for automated grading systems, it was never deployed in production. The project serves as a proof of concept for how LLMs could be used to maintain grading consistency in large educational institutions.

The system showcases modern web development practices including microservices architecture, comprehensive API design, caching strategies, and analytics capabilities. It's a good example of how to build scalable educational technology platforms. 