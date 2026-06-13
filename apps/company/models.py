from django.db import models


class Company(models.Model):
    company_id = models.BigIntegerField(primary_key=True, help_text="LinkedIn Company Page ID")
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, null=True)
    company_size = models.IntegerField(blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    zip_code = models.CharField(max_length=100, blank=True, null=True)

    address = models.TextField(blank=True, null=True)
    url = models.URLField(max_length=500, blank=True, null=True)
    data_source = models.CharField(
        max_length=10,
        choices=(('CSV', 'CSV'), ('API', 'API')),
        default='CSV',
        db_index=True
    )

    class Meta:
        db_table = "companies"
        verbose_name_plural = "companies"


class CompanyIndustry(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="industries")
    industry = models.CharField(max_length=255)

    class Meta:
        db_table = "company_industries"
        unique_together = (("company", "industry"),)


class CompanySpecialty(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="specialties")
    speciality = models.CharField(max_length=255)

    class Meta:
        db_table = "company_specialities"
        verbose_name_plural = "company specialities"
        unique_together = (("company", "speciality"),)


class EmployeeCountHistory(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="employee_counts")
    employee_count = models.IntegerField()
    follower_count = models.IntegerField()
    time_recorded = models.BigIntegerField(db_index=True)

    class Meta:
        db_table = "employee_counts"
        ordering = ["-time_recorded"]
