from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Job(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default="")
    description = models.TextField(max_length=1023, default="")

    def __str__(self):
        return str(self.id) + ' - ' + self.title