from django.db import models


class Industry(models.Model):
    industry_id = models.BigIntegerField(primary_key=True)
    industry_name = models.CharField(max_length=255)

    class Meta:
        db_table = "industries"
        verbose_name_plural = "industries"


class Skill(models.Model):
    skill_abr = models.CharField(max_length=10, primary_key=True)
    skill_name = models.CharField(max_length=150)

    class Meta:
        db_table = "skills"


class JobPosting(models.Model):
    job_id = models.BigIntegerField(primary_key=True)
    # Reference Company as a string to prevent circular dependency
    company = models.ForeignKey('company.Company', on_delete=models.SET_NULL, null=True, blank=True, related_name="job_postings")
    company_name = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    max_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    med_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    min_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pay_period = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    views = models.IntegerField(null=True, blank=True)
    applies = models.IntegerField(null=True, blank=True)
    original_listed_time = models.BigIntegerField(null=True, blank=True)
    listed_time = models.BigIntegerField(null=True, blank=True)
    expiry = models.BigIntegerField(null=True, blank=True)
    closed_time = models.BigIntegerField(null=True, blank=True)
    remote_allowed = models.BooleanField(null=True, blank=True, db_index=True)
    job_posting_url = models.URLField(max_length=500, blank=True, null=True)
    application_url = models.URLField(max_length=500, blank=True, null=True)
    application_type = models.CharField(max_length=100, blank=True, null=True)
    formatted_work_type = models.CharField(max_length=100, blank=True, null=True)
    work_type = models.CharField(max_length=50, blank=True, null=True)
    formatted_experience_level = models.CharField(max_length=100, blank=True, null=True)
    skills_desc = models.TextField(blank=True, null=True)
    posting_domain = models.CharField(max_length=255, blank=True, null=True)
    sponsored = models.BooleanField(default=False)
    currency = models.CharField(max_length=3, blank=True, null=True)
    compensation_type = models.CharField(max_length=50, blank=True, null=True)
    normalized_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, db_index=True)
    zip_code = models.CharField(max_length=100, blank=True, null=True)
    fips = models.CharField(max_length=50, blank=True, null=True)
    data_source = models.CharField(
        max_length=10,
        choices=(('CSV', 'CSV'), ('API', 'API')),
        default='CSV',
        db_index=True
    )

    
    # Many-to-Many Relationships
    industries = models.ManyToManyField(Industry, related_name="job_postings", db_table="job_industries")
    skills = models.ManyToManyField(Skill, related_name="job_postings", db_table="job_skills")

    class Meta:
        db_table = "postings"


class Benefit(models.Model):
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name="benefits")
    inferred = models.BooleanField(default=False)
    type = models.CharField(max_length=255)

    class Meta:
        db_table = "benefits"


class JobSalaryDetail(models.Model):
    salary_id = models.BigIntegerField(primary_key=True)
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name="salary_details")
    max_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    med_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    min_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pay_period = models.CharField(max_length=50, blank=True, null=True)
    currency = models.CharField(max_length=3, blank=True, null=True)
    compensation_type = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = "salaries"
