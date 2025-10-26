from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from home.models import Job
from accounts.models import Profile

class Command(BaseCommand):
    help = 'Seed additional diverse job postings (25 more jobs)'

    def handle(self, *args, **kwargs):
        # Get or create recruiter user
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

        additional_jobs = [
            {
                'title': 'Junior Python Developer',
                'description': 'Entry-level Python developer position. Learn Django, Flask, and modern web development. Work with PostgreSQL databases and REST APIs. Ideal for recent graduates or career switchers. We provide mentorship and training.',
                'salary': 75000,
                'location': 'Remote',
                'category': 'Software Engineering'
            },
            {
                'title': 'React Native Developer',
                'description': 'Build cross-platform mobile apps with React Native. Experience with JavaScript, TypeScript, and mobile UI/UX required. Knowledge of iOS and Android deployment processes. Work on consumer-facing apps with millions of users.',
                'salary': 120000,
                'location': 'Austin, TX',
                'category': 'Mobile Development'
            },
            {
                'title': 'Data Engineer - AWS',
                'description': 'Build and maintain data pipelines using AWS services including S3, Glue, Redshift, and Lambda. Strong Python and SQL skills required. Experience with Airflow, Spark, and data warehouse design preferred.',
                'salary': 145000,
                'location': 'Seattle, WA',
                'category': 'Data Engineering'
            },
            {
                'title': 'Cloud Solutions Architect - Azure',
                'description': 'Design and implement enterprise cloud solutions on Microsoft Azure. Experience with Azure DevOps, Kubernetes, and infrastructure as code. Work with clients to migrate legacy systems to the cloud.',
                'salary': 160000,
                'location': 'Chicago, IL',
                'category': 'Cloud Architecture'
            },
            {
                'title': 'Machine Learning Engineer',
                'description': 'Deploy ML models to production using TensorFlow, PyTorch, and scikit-learn. Build scalable ML pipelines with Docker and Kubernetes. Experience with computer vision or NLP preferred. Strong Python and algorithm skills required.',
                'salary': 155000,
                'location': 'San Francisco, CA',
                'category': 'Machine Learning'
            },
            {
                'title': 'Golang Backend Developer',
                'description': 'Build high-performance microservices with Go. Experience with gRPC, PostgreSQL, Redis, and message queues. Strong understanding of concurrency and distributed systems. Work on real-time data processing.',
                'salary': 140000,
                'location': 'New York, NY',
                'category': 'Backend Engineering'
            },
            {
                'title': 'UI/UX Designer - SaaS',
                'description': 'Design beautiful, intuitive interfaces for B2B SaaS products. Create wireframes, prototypes, and high-fidelity mockups in Figma. Conduct user research and usability testing. Collaborate with product and engineering teams.',
                'salary': 115000,
                'location': 'Remote',
                'category': 'Design'
            },
            {
                'title': 'Cybersecurity Analyst',
                'description': 'Monitor and respond to security threats. Conduct vulnerability assessments and penetration testing. Experience with SIEM tools, firewalls, and intrusion detection systems. Knowledge of compliance standards (SOC2, ISO 27001).',
                'salary': 130000,
                'location': 'Washington, DC',
                'category': 'Cybersecurity'
            },
            {
                'title': 'Blockchain Developer',
                'description': 'Develop smart contracts and decentralized applications. Strong Solidity, Web3.js, and Ethereum experience required. Work on DeFi protocols and NFT platforms. Knowledge of Rust and other blockchain platforms a plus.',
                'salary': 165000,
                'location': 'Miami, FL',
                'category': 'Blockchain'
            },
            {
                'title': 'Android Developer (Kotlin)',
                'description': 'Build native Android apps using Kotlin and Jetpack Compose. Experience with MVVM architecture, Room database, and Retrofit. Work on fintech mobile app with strict security requirements.',
                'salary': 125000,
                'location': 'San Francisco, CA',
                'category': 'Mobile Development'
            },
            {
                'title': 'SQL Database Administrator',
                'description': 'Manage and optimize SQL Server and PostgreSQL databases. Handle backup/recovery, performance tuning, and high availability setup. Experience with replication, clustering, and database migrations.',
                'salary': 120000,
                'location': 'Dallas, TX',
                'category': 'Database Administration'
            },
            {
                'title': 'Vue.js Frontend Engineer',
                'description': 'Build responsive web applications with Vue 3 and TypeScript. Use Vuex/Pinia for state management and Vite for build tooling. Strong CSS/SCSS skills and experience with component libraries required.',
                'salary': 110000,
                'location': 'Denver, CO',
                'category': 'Frontend Development'
            },
            {
                'title': 'Site Reliability Engineer - Platform',
                'description': 'Ensure reliability and scalability of cloud infrastructure. Work with Kubernetes, Terraform, and monitoring tools like Prometheus and Datadog. Implement chaos engineering and disaster recovery procedures.',
                'salary': 150000,
                'location': 'Seattle, WA',
                'category': 'SRE'
            },
            {
                'title': 'Java Spring Developer',
                'description': 'Build enterprise applications with Java and Spring Boot. Experience with Spring Security, Spring Data JPA, and microservices architecture. Work with Kafka, RabbitMQ, and distributed caching solutions.',
                'salary': 135000,
                'location': 'Boston, MA',
                'category': 'Backend Engineering'
            },
            {
                'title': 'AI Research Scientist',
                'description': 'Conduct cutting-edge research in natural language processing and computer vision. PhD in Computer Science or related field required. Publish papers and implement novel algorithms. Experience with transformers and large language models.',
                'salary': 180000,
                'location': 'Palo Alto, CA',
                'category': 'AI Research'
            },
            {
                'title': 'Salesforce Developer',
                'description': 'Develop custom Salesforce solutions using Apex, Visualforce, and Lightning components. Integrate Salesforce with external systems via REST APIs. Experience with Sales Cloud, Service Cloud, and CPQ.',
                'salary': 125000,
                'location': 'Remote',
                'category': 'CRM Development'
            },
            {
                'title': 'Ruby on Rails Developer',
                'description': 'Build web applications with Ruby on Rails and PostgreSQL. Strong MVC pattern understanding and RESTful API design. Experience with background jobs (Sidekiq), caching (Redis), and modern JavaScript frameworks.',
                'salary': 115000,
                'location': 'Portland, OR',
                'category': 'Full Stack Development'
            },
            {
                'title': 'GraphQL API Developer',
                'description': 'Design and implement GraphQL APIs with Node.js and Apollo Server. Work with MongoDB and PostgreSQL databases. Optimize query performance and implement caching strategies. Strong TypeScript skills required.',
                'salary': 130000,
                'location': 'Austin, TX',
                'category': 'Backend Engineering'
            },
            {
                'title': 'Technical Product Manager',
                'description': 'Lead product development for developer tools and APIs. Strong technical background required (previous engineering experience). Define roadmap, write specs, and work closely with engineering teams. Experience with agile methodologies.',
                'salary': 145000,
                'location': 'San Francisco, CA',
                'category': 'Product Management'
            },
            {
                'title': 'Embedded Systems Engineer',
                'description': 'Develop firmware for IoT devices using C/C++. Work with ARM microcontrollers, sensors, and wireless protocols (BLE, WiFi). Experience with RTOS and low-power design. Hardware debugging skills essential.',
                'salary': 125000,
                'location': 'San Diego, CA',
                'category': 'Embedded Systems'
            },
            {
                'title': 'Test Automation Engineer - Selenium',
                'description': 'Build automated test frameworks using Selenium, Pytest, and Cucumber. Create CI/CD pipelines with Jenkins or GitHub Actions. Experience with performance testing and API testing tools (JMeter, Postman).',
                'salary': 110000,
                'location': 'Remote',
                'category': 'QA Engineering'
            },
            {
                'title': 'Infrastructure Engineer - Terraform',
                'description': 'Manage cloud infrastructure using Terraform and AWS/GCP. Implement infrastructure as code best practices. Work with Docker, Kubernetes, and service mesh technologies. Strong Linux and networking knowledge.',
                'salary': 140000,
                'location': 'New York, NY',
                'category': 'Infrastructure'
            },
            {
                'title': 'Scala Backend Developer',
                'description': 'Build functional programming applications with Scala and Akka. Work on high-throughput streaming data pipelines. Experience with Kafka, Spark, and distributed systems. Strong understanding of concurrency models.',
                'salary': 145000,
                'location': 'San Francisco, CA',
                'category': 'Backend Engineering'
            },
            {
                'title': 'WordPress Developer',
                'description': 'Develop custom WordPress themes and plugins. Strong PHP, JavaScript, and MySQL skills. Experience with WooCommerce, Elementor, and modern page builders. Knowledge of WordPress security best practices.',
                'salary': 90000,
                'location': 'Remote',
                'category': 'Web Development'
            },
            {
                'title': 'Computer Vision Engineer',
                'description': 'Develop image processing and object detection systems. Experience with OpenCV, TensorFlow, and PyTorch. Work on real-time video analytics and autonomous systems. Strong Python and C++ skills required.',
                'salary': 150000,
                'location': 'Boston, MA',
                'category': 'Computer Vision'
            }
        ]

        created_count = 0
        for job_data in additional_jobs:
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

        self.stdout.write(self.style.SUCCESS(f'\n✓ {created_count} new jobs created!'))
        self.stdout.write(self.style.SUCCESS(f'Total jobs in database: {Job.objects.count()}'))
