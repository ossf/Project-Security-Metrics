import json
from django.test import TestCase
from django.test import Client
from app.models import Package, Metric
client = Client()

class ViewApiGetPackageTests(TestCase):
    
    registered_package_url = "pkg:github/rails/rails"
    registered_url = "https://github.com/rails/rails"
    metric_key = "openssf.security-review"
    metric_value = "test"
    metric_properties = "test"
    
    def setUp(self):
        package = Package.objects.create(package_url=self.registered_package_url)
        metric = Metric.objects.create(
            package=package, key=self.metric_key, value=self.metric_value, properties=self.metric_properties
        )

    def test_valid_package_url(self):
        response = client.get(f"/api/1/get-project?package_url={self.registered_package_url}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {
                "package_url": self.registered_package_url,
                "metrics": [
                    {
                        "key": self.metric_key,
                        "value": self.metric_value,
                        "properties": self.metric_properties
                    }
                ]
            }
        )

    def test_valid_url(self):
        response = client.get(f"/api/1/get-project?url={self.registered_url}")
        self.assertEqual(response.status_code, 200)

    def test_not_found(self):
        response = client.get("/api/1/get-project?package_url=pkg:github/not_found/not_found")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content)["message"], "Not Found.")

    def test_no_parameters(self):
        response = client.get("/api/1/get-project")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)["message"], "Required, package_url or url.")

    def test_invalid_package_url(self):
        response = client.get("/api/1/get-project?package_url=invalid")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)["message"], "Invalid Package URL.")

    def test_invalid_url(self):
        response = client.get("/api/1/get-project?url=invalid")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)["message"], "Invalid URL.")
