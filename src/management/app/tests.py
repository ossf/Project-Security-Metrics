from django.test import TestCase
from django.test import Client
from app.models import Package
client = Client()

class ViewApiGetPackageTests(TestCase):
    
    registered_package_url = "pkg:github/rails/rails"
    registered_url = "https://github.com/rails/rails"
    def setUp(self):
        Package.objects.create(package_url=self.registered_package_url)

    def test_valid_package_url(self):
        response = client.get(f"/api/1/get-project?package_url={self.registered_package_url}")
        self.assertEqual(response.status_code, 200)

    def test_valid_url(self):
        response = client.get(f"/api/1/get-project?url={self.registered_url}")
        self.assertEqual(response.status_code, 200)

    def test_not_found(self):
        response = client.get("/api/1/get-project?package_url=pkg:github/not_found/not_found")
        print(response.content)
        self.assertEqual(response.status_code, 404)

    def test_no_parameters(self):
        response = client.get("/api/1/get-project")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"Required, package_url or url.")

    def test_invalid_package_url(self):
        response = client.get("/api/1/get-project?package_url=invalid")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"Invalid Package URL.")

    def test_invalid_url(self):
        response = client.get("/api/1/get-project?url=invalid")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"Invalid URL.")
