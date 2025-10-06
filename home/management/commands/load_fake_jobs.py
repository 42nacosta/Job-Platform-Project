from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from home.models import Job
from accounts.models import Profile

class Command(BaseCommand):
    help = 'Load 15 fake jobs with realistic data'

    def handle(self, *args, **kwargs):
        # Create a recruiter user if needed
        recruiter, created = User.objects.get_or_create(
            username='recruiter_demo',
            defaults={
                'first_name': 'Sarah',
                'last_name': 'Thompson',
                'email': 'sarah.thompson@techcorp.com'
            }
        )
        if created:
            recruiter.set_password('demo123')
            recruiter.save()
            recruiter.profile.is_recruiter = True
            recruiter.profile.save()

        fake_jobs = [
            {
                'title': 'Senior Software Engineer',
                'description': 'We are seeking an experienced Senior Software Engineer to join our core platform team. You will work on designing and building scalable microservices using Python, Django, and PostgreSQL. Strong experience with REST APIs, Docker, and AWS is required. You will mentor junior developers and lead technical design reviews.',
                'salary': 145000,
                'location': 'San Francisco, CA',
                'category': 'Software Engineering'
            },
            {
                'title': 'Frontend Developer (React)',
                'description': 'Join our product team as a Frontend Developer specializing in React and TypeScript. You will build responsive, accessible user interfaces for our SaaS platform. Experience with Redux, React Query, and modern CSS frameworks is essential. We value clean code, component reusability, and user-centric design.',
                'salary': 115000,
                'location': 'Remote',
                'category': 'Frontend Development'
            },
            {
                'title': 'Data Scientist - Machine Learning',
                'description': 'Looking for a Data Scientist with strong ML experience to develop predictive models for our recommendation engine. You will work with Python, scikit-learn, TensorFlow, and large datasets. PhD or Masters in Computer Science, Statistics, or related field preferred. Experience with NLP and deep learning is a plus.',
                'salary': 160000,
                'location': 'New York, NY',
                'category': 'Data Science'
            },
            {
                'title': 'DevOps Engineer',
                'description': 'We need a DevOps Engineer to manage our cloud infrastructure and CI/CD pipelines. You will work with Kubernetes, Terraform, Jenkins, and AWS. Responsibilities include monitoring, incident response, and infrastructure automation. Strong Linux and scripting skills (Bash, Python) required.',
                'salary': 135000,
                'location': 'Austin, TX',
                'category': 'DevOps'
            },
            {
                'title': 'Full Stack Developer (Django + Vue.js)',
                'description': 'Full Stack Developer role focusing on Django backend and Vue.js frontend. You will build and maintain our customer-facing web applications. Experience with PostgreSQL, Redis, Celery, and RESTful API design required. Comfortable working across the stack and collaborating with designers.',
                'salary': 125000,
                'location': 'Seattle, WA',
                'category': 'Full Stack Development'
            },
            {
                'title': 'Mobile App Developer (iOS)',
                'description': 'iOS Developer position working on our flagship mobile app. Strong Swift and SwiftUI experience required. You will implement new features, optimize performance, and ensure high code quality. Experience with Core Data, Combine framework, and app store submission process essential.',
                'salary': 130000,
                'location': 'Los Angeles, CA',
                'category': 'Mobile Development'
            },
            {
                'title': 'Backend Engineer - Java/Spring Boot',
                'description': 'Backend Engineer role building microservices with Java and Spring Boot. You will design RESTful APIs, optimize database queries, and ensure system reliability. Experience with MySQL, RabbitMQ, and distributed systems required. Familiarity with microservices architecture and event-driven design is important.',
                'salary': 140000,
                'location': 'Boston, MA',
                'category': 'Backend Engineering'
            },
            {
                'title': 'Product Manager - B2B SaaS',
                'description': 'Product Manager for our B2B SaaS product line. You will define product roadmap, work with engineering and design teams, and drive feature prioritization. Strong analytical skills and experience with user research, A/B testing, and product analytics tools required. 3+ years PM experience in SaaS.',
                'salary': 155000,
                'location': 'Remote',
                'category': 'Product Management'
            },
            {
                'title': 'UX/UI Designer',
                'description': 'UX/UI Designer to create intuitive, beautiful interfaces for our web and mobile products. You will conduct user research, create wireframes and prototypes, and collaborate closely with developers. Proficiency in Figma, user testing methodologies, and design systems required. Portfolio showcasing shipped products essential.',
                'salary': 110000,
                'location': 'Chicago, IL',
                'category': 'Design'
            },
            {
                'title': 'Security Engineer',
                'description': 'Security Engineer to strengthen our application and infrastructure security. Responsibilities include security audits, penetration testing, incident response, and implementing security best practices. Experience with OWASP, encryption, authentication systems, and compliance frameworks (SOC2, GDPR) required.',
                'salary': 150000,
                'location': 'Washington, DC',
                'category': 'Cybersecurity'
            },
            {
                'title': 'QA Automation Engineer',
                'description': 'QA Automation Engineer to build and maintain automated test suites. You will work with Selenium, Pytest, and CI/CD pipelines. Experience with both API and UI testing required. Strong programming skills in Python and understanding of test-driven development essential.',
                'salary': 105000,
                'location': 'Denver, CO',
                'category': 'Quality Assurance'
            },
            {
                'title': 'Solutions Architect',
                'description': 'Solutions Architect to design enterprise-scale cloud architectures for our clients. You will work with AWS, Azure, and GCP to create scalable, secure, and cost-effective solutions. Strong communication skills and ability to present technical concepts to non-technical stakeholders required. 5+ years experience.',
                'salary': 165000,
                'location': 'Atlanta, GA',
                'category': 'Architecture'
            },
            {
                'title': 'Site Reliability Engineer (SRE)',
                'description': 'SRE position focused on ensuring high availability and performance of our production systems. You will implement monitoring, alerting, and incident management processes. Experience with Prometheus, Grafana, ELK stack, and chaos engineering principles required. On-call rotation participation expected.',
                'salary': 145000,
                'location': 'Portland, OR',
                'category': 'SRE'
            },
            {
                'title': 'Technical Writer',
                'description': 'Technical Writer to create developer documentation, API references, and user guides. You will work closely with engineering teams to document complex technical concepts clearly. Experience with Markdown, Git, and documentation-as-code workflows required. Background in software development helpful.',
                'salary': 95000,
                'location': 'Remote',
                'category': 'Technical Writing'
            },
            {
                'title': 'Engineering Manager',
                'description': 'Engineering Manager to lead a team of 6-8 software engineers. You will be responsible for team growth, project delivery, and technical direction. Strong people management skills, experience with agile methodologies, and hands-on technical background required. Experience managing distributed teams preferred.',
                'salary': 175000,
                'location': 'San Francisco, CA',
                'category': 'Engineering Management'
            }
        ]

        created_count = 0
        for job_data in fake_jobs:
            job, created = Job.objects.get_or_create(
                user=recruiter,
                title=job_data['title'],
                defaults=job_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {job.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'○ Already exists: {job.title}'))

        self.stdout.write(self.style.SUCCESS(f'\n{created_count} new jobs created!'))
        self.stdout.write(self.style.SUCCESS(f'Recruiter account: username="recruiter_demo", password="demo123"'))
