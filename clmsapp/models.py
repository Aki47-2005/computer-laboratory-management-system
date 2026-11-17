from django.db import models

class Lab(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()
    duration = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class Instructor(models.Model):
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    department = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name


class Computer(models.Model):
    name = models.CharField(max_length=50)
    brand = models.CharField(max_length=50)
    type = models.CharField(max_length=20)
    colour = models.CharField(max_length=30)
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='Active')

    def __str__(self):
        return self.name


class Specification(models.Model):
    computer = models.ForeignKey(Computer, on_delete=models.CASCADE)
    processor = models.CharField(max_length=100)
    ram = models.PositiveIntegerField()
    storage = models.PositiveIntegerField()
    operating_system = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.computer} specification"


class Schedule(models.Model):
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE)
    day = models.CharField(max_length=10)
    start_time = models.TimeField()
    end_time = models.TimeField()
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.lab} - {self.day}"


class Attendant(models.Model):
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE)
    shift = models.CharField(max_length=20)

    def __str__(self):
        return self.full_name


class Maintenance(models.Model):
    computer = models.ForeignKey(Computer, on_delete=models.CASCADE)
    item = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    date = models.DateField()
    cost = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.computer} - {self.item}"


class Disposal(models.Model):
    computer = models.ForeignKey(Computer, on_delete=models.CASCADE)
    date = models.DateField()
    reason = models.CharField(max_length=100)
    method = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.computer} disposal"
# Create your models here.
