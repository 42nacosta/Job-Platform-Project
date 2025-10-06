from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile

class Command(BaseCommand):
    help = 'Load fake job seeker profiles with realistic data'

    def handle(self, *args, **kwargs):
        fake_candidates = [
            {
                'username': 'alex_chen',
                'first_name': 'Alex',
                'last_name': 'Chen',
                'email': 'alex.chen@email.com',
                'password': 'demo123',
                'profile': {
                    'skills': 'python django react postgresql docker aws rest api microservices redis celery',
                    'location': 'San Francisco, CA',
                    'experience': '3 years building scalable web applications with Django and React. Experience with microservices architecture, REST API design, and cloud deployment on AWS.',
                    'education': 'BS in Computer Science, Georgia Tech',
                    'show_skills_to_recruiters': True,
                    'show_location_to_recruiters': True,
                    'show_experience_to_recruiters': True,
                    'show_education_to_recruiters': True,
                    'show_firstName_to_recruiters': True,
                    'show_lastName_to_recruiters': True,
                    'visibility': Profile.Visibility.RECRUITERS
                }
            },
            {
                'username': 'maria_rodriguez',
                'first_name': 'Maria',
                'last_name': 'Rodriguez',
                'email': 'maria.rodriguez@email.com',
                'password': 'demo123',
                'profile': {
                    'skills': 'java spring boot mysql rabbitmq kubernetes jenkins ci/cd microservices maven gradle',
                    'location': 'Boston, MA',
                    'experience': '5 years backend engineering with focus on microservices architecture. Led migration from monolith to microservices for 2M+ user platform.',
                    'education': 'MS in Software Engineering, MIT',
                    'show_skills_to_recruiters': True,
                    'show_location_to_recruiters': True,
                    'show_experience_to_recruiters': True,
                    'show_education_to_recruiters': True,
                    'show_firstName_to_recruiters': True,
                    'show_lastName_to_recruiters': True,
                    'visibility': Profile.Visibility.RECRUITERS
                }
            },
            {
                'username': 'james_kim',
                'first_name': 'James',
                'last_name': 'Kim',
                'email': 'james.kim@email.com',
                'password': 'demo123',
                'profile': {
                    'skills': 'machine learning python tensorflow pytorch scikit-learn nlp deep learning pandas numpy jupyter',
                    'location': 'New York, NY',
                    'experience': '4 years building production ML models for recommendation systems and NLP applications. Published 6 papers in top-tier ML conferences.',
                    'education': 'PhD in Computer Science (Machine Learning), Stanford University',
                    'show_skills_to_recruiters': True,
                    'show_location_to_recruiters': True,
                    'show_experience_to_recruiters': True,
                    'show_education_to_recruiters': True,
                    'show_firstName_to_recruiters': True,
                    'show_lastName_to_recruiters': True,
                    'visibility': Profile.Visibility.RECRUITERS
                }
            },
            {
                'username': 'emily_taylor',
                'first_name': 'Emily',
                'last_name': 'Taylor',
                'email': 'emily.taylor@email.com',
                'password': 'demo123',
                'profile': {
                    'skills': 'react vue typescript javascript html css figma ui ux design responsive webpack vite',
                    'location': 'Remote',
                    'experience': '6 years frontend development and UI/UX design. Built design systems used by 50+ engineers. Expert in React, Vue, and modern CSS frameworks.',
                    'education': 'BA in Design + Certificate in Web Development, RISD',
                    'show_skills_to_recruiters': True,
                    'show_location_to_recruiters': True,
                    'show_experience_to_recruiters': True,
                    'show_education_to_recruiters': True,
                    'show_firstName_to_recruiters': True,
                    'show_lastName_to_recruiters': True,
                    'visibility': Profile.Visibility.RECRUITERS
                }
            },
            {
                'username': 'david_park',
                'first_name': 'David',
                'last_name': 'Park',
                'email': 'david.park@email.com',
                'password': 'demo123',
                'profile': {
                    'skills': 'devops kubernetes terraform aws linux bash python monitoring grafana prometheus ansible jenkins',
                    'location': 'Austin, TX',
                    'experience': '4 years managing cloud infrastructure and automation. Reduced deployment time by 70% through CI/CD improvements. Expert in Kubernetes and AWS.',
                    'education': 'BS in Information Systems, UT Austin',
                    'show_skills_to_recruiters': True,
                    'show_location_to_recruiters': True,
                    'show_experience_to_recruiters': True,
                    'show_education_to_recruiters': True,
                    'show_firstName_to_recruiters': True,
                    'show_lastName_to_recruiters': True,
                    'visibility': Profile.Visibility.RECRUITERS
                }
            },
            {
                'username': 'sarah_johnson',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'email': 'sarah.johnson@email.com',
                'password': 'demo123',
                'profile': {
                    'skills': 'swift swiftui ios objective-c xcode core data combine realm firebase',
                    'location': 'Los Angeles, CA',
                    'experience': '5 years iOS development. Shipped 8 apps to App Store with 1M+ combined downloads. Strong focus on SwiftUI and modern iOS architecture.',
                    'education': 'BS in Computer Science, UCLA',
                    'show_skills_to_recruiters': True,
                    'show_location_to_recruiters': True,
                    'show_experience_to_recruiters': True,
                    'show_education_to_recruiters': True,
                    'show_firstName_to_recruiters': True,
                    'show_lastName_to_recruiters': True,
                    'visibility': Profile.Visibility.RECRUITERS
                }
            },
            {
                'username': 'robert_martinez',
                'first_name': 'Robert',
                'last_name': 'Martinez',
                'email': 'robert.martinez@email.com',
                'password': 'demo123',
                'profile': {
                    'skills': 'cybersecurity penetration testing owasp cryptography incident response soc2 gdpr compliance nessus burp',
                    'location': 'Washington, DC',
                    'experience': '6 years in application and infrastructure security. Led SOC2 compliance efforts. Expert in penetration testing and security audits.',
                    'education': 'MS in Cybersecurity, Johns Hopkins',
                    'show_skills_to_recruiters': True,
                    'show_location_to_recruiters': True,
                    'show_experience_to_recruiters': True,
                    'show_education_to_recruiters': True,
                    'show_firstName_to_recruiters': True,
                    'show_lastName_to_recruiters': True,
                    'visibility': Profile.Visibility.RECRUITERS
                }
            },
            {
                'username': 'lisa_wang',
                'first_name': 'Lisa',
                'last_name': 'Wang',
                'email': 'lisa.wang@email.com',
                'password': 'demo123',
                'profile': {
                    'skills': 'product management agile scrum user research analytics mixpanel amplitude jira roadmapping prioritization',
                    'location': 'Remote',
                    'experience': '4 years product management for B2B SaaS products. Led 3 successful product launches. Strong data-driven decision making and user research skills.',
                    'education': 'MBA, Wharton + BS in Computer Science',
                    'show_skills_to_recruiters': True,
                    'show_location_to_recruiters': True,
                    'show_experience_to_recruiters': True,
                    'show_education_to_recruiters': True,
                    'show_firstName_to_recruiters': True,
                    'show_lastName_to_recruiters': True,
                    'visibility': Profile.Visibility.RECRUITERS
                }
            }
        ]

        created_count = 0
        for candidate_data in fake_candidates:
            profile_data = candidate_data.pop('profile')
            password = candidate_data.pop('password')

            user, created = User.objects.get_or_create(
                username=candidate_data['username'],
                defaults=candidate_data
            )

            if created:
                user.set_password(password)
                user.save()

                # Update profile
                profile = user.profile
                for key, value in profile_data.items():
                    setattr(profile, key, value)
                profile.is_recruiter = False
                profile.save()

                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {user.username}'))
            else:
                self.stdout.write(self.style.WARNING(f'○ Already exists: {user.username}'))

        self.stdout.write(self.style.SUCCESS(f'\n{created_count} new candidate profiles created!'))
        self.stdout.write(self.style.SUCCESS(f'All passwords: "demo123"'))
        self.stdout.write(self.style.SUCCESS(f'\nNow log in as recruiter_demo to create a job and see recommendations!'))
