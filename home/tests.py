from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Job, Application


class ApplyFlowTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pw")
        self.applicant = User.objects.create_user(username="joe", password="pw")
        self.job = Job.objects.create(
            user=self.owner,
            title="Data Analyst",
            description="...",
            salary=100000,
            location="ATL",
            category="Tech",
        )

    def test_guest_cannot_apply(self):
        url = reverse("home.apply", args=[self.job.id])
        resp = self.client.post(url, {"note": "hi"})
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    def test_user_can_apply_once(self):
        self.client.login(username="joe", password="pw")
        url = reverse("home.apply", args=[self.job.id])
        self.client.post(url, {"note": "first"})
        self.assertEqual(
            Application.objects.filter(job=self.job, applicant=self.applicant).count(),
            1,
        )
        app = Application.objects.get(job=self.job, applicant=self.applicant)
        self.assertEqual(app.note, "first")

    def test_duplicate_updates_note(self):
        self.client.login(username="joe", password="pw")
        url = reverse("home.apply", args=[self.job.id])
        self.client.post(url, {"note": "first"})
        self.client.post(url, {"note": "second"})
        app = Application.objects.get(job=self.job, applicant=self.applicant)
        self.assertEqual(Application.objects.count(), 1)
        self.assertEqual(app.note, "second")

    def test_owner_sees_applications_in_context(self):
        Application.objects.create(job=self.job, applicant=self.applicant, note="why me")
        self.client.login(username="owner", password="pw")
        resp = self.client.get(reverse("home.show", args=[self.job.id]))
        self.assertContains(resp, "Applications (1)")
