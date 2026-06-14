from django.db import models


class DataAnalystBenchmark(models.Model):
    job_title = models.CharField(max_length=255)
    salary_estimate = models.CharField(max_length=100, blank=True, null=True)
    job_description = models.TextField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company = models.ForeignKey('company.Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='data_analyst_benchmarks')
    location = models.CharField(max_length=255, blank=True, null=True)
    headquarters = models.CharField(max_length=255, blank=True, null=True)
    size = models.CharField(max_length=100, blank=True, null=True)
    founded = models.IntegerField(null=True, blank=True)
    type_of_ownership = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=255, blank=True, null=True)
    industry_ref = models.ForeignKey('jobs.Industry', on_delete=models.SET_NULL, null=True, blank=True, related_name='data_analyst_benchmarks')
    sector = models.CharField(max_length=255, blank=True, null=True)
    revenue = models.CharField(max_length=100, blank=True, null=True)
    competitors = models.TextField(blank=True, null=True)
    easy_apply = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = "data_analyst_benchmark"


class DataScienceSalaryBenchmark(models.Model):
    work_year = models.IntegerField()
    experience_level = models.CharField(max_length=10)
    employment_type = models.CharField(max_length=10)
    job_title = models.CharField(max_length=255)
    salary = models.DecimalField(max_digits=15, decimal_places=2)
    salary_currency = models.CharField(max_length=3)
    salary_in_usd = models.DecimalField(max_digits=12, decimal_places=2)
    employee_residence = models.CharField(max_length=10)
    remote_ratio = models.IntegerField()
    company_location = models.CharField(max_length=10)
    company_size = models.CharField(max_length=3)

    class Meta:
        db_table = "ds_salaries_benchmark"


class APISalaryHistory(models.Model):
    country = models.CharField(max_length=10)
    location = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    category_ref = models.ForeignKey('jobs.Industry', on_delete=models.SET_NULL, related_name='api_salary_histories', null=True, blank=True)
    month = models.CharField(max_length=7)  # format: YYYY-MM
    average_salary = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "api_salary_history"
        unique_together = (("country", "location", "category", "month"),)


class APISalaryHistogram(models.Model):
    country = models.CharField(max_length=10)
    location = models.CharField(max_length=255, blank=True, null=True)
    what = models.CharField(max_length=255, blank=True, null=True)
    salary_bracket = models.DecimalField(max_digits=12, decimal_places=2)
    vacancy_count = models.IntegerField()

    class Meta:
        db_table = "api_salary_histogram"
        unique_together = (("country", "location", "what", "salary_bracket"),)


class APITopCompany(models.Model):
    country = models.CharField(max_length=10)
    what = models.CharField(max_length=255, blank=True, null=True)
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, related_name='api_top_standings', null=True, blank=True)
    company_name = models.CharField(max_length=255)
    vacancy_count = models.IntegerField()
    average_salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = "api_top_companies"
        unique_together = (("country", "what", "company_name"),)


class APISalaryPrediction(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    predicted_salary = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "api_salary_predictions"
        unique_together = (("title", "description"),)

