from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Student(models.Model):
    name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=50, unique=True)
    # Storing 128-dimensional face encoding as a string
    encoding = models.TextField() 
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return self.name