import csv
import logging
from pathlib import Path
from decimal import Decimal
import pandas as pd
from django.conf import settings
from celery import shared_task

logger = logging.getLogger(__name__)


# Shadow print to route standard prints to Celery/Django logged stdout info file
def print(*args, **kwargs):
    logger.info(" ".join(map(str, args)))


from apps.company.models import Company, CompanyIndustry, CompanySpecialty, EmployeeCountHistory
from apps.jobs.models import Industry, Skill, JobPosting, Benefit, JobSalaryDetail
from apps.benchmarks.models import DataAnalystBenchmark, DataScienceSalaryBenchmark


# ---------------------------------------------------------
# Safe Helper Parsers to Sanitise and Clean Data
# ---------------------------------------------------------
def parse_str(val, max_length=None):
    if val is None or pd.isna(val):
        return None
    val_stripped = str(val).strip()
    if val_stripped.lower() in ('nan', 'null', 'none', ''):
        return None
    if max_length is not None:
        return val_stripped[:max_length]
    return val_stripped


def parse_int(val):
    clean_val = parse_str(val)
    if clean_val is None:
        return None
    try:
        # float(clean_val) handle cases like "2.0"
        return int(float(clean_val))
    except (ValueError, TypeError):
        return None


def parse_decimal(val):
    clean_val = parse_str(val)
    if clean_val is None:
        return None
    try:
        return Decimal(clean_val)
    except (ValueError, TypeError, Exception):
        return None


def parse_bool(val):
    clean_val = parse_str(val)
    if clean_val is None:
        return None
    return clean_val.lower() in ('true', '1', 'yes', 'y', 't')


# ---------------------------------------------------------
# Core ETL Pipeline Class
# ---------------------------------------------------------
class CSVETLPipeline:
    """ETL Pipeline to process Job Market datasets from raw CSVs to DB."""

    def __init__(self, chunk_size=2000):
        self.chunk_size = chunk_size
        self.base_dir = Path(settings.BASE_DIR) / 'core' / 'data' / 'raw'
        
        # Track inserted Primary Keys to prevent DB constraint errors
        self.loaded_industry_ids = set()
        self.loaded_skill_abrs = set()
        self.loaded_company_ids = set()
        self.loaded_job_ids = set()

    def get_csv_path(self, relative_path):
        return self.base_dir / relative_path

    def run(self):
        print("Starting ETL pipeline execution...")
        
        try:
            self.load_industries()
            self.load_skills()
            self.load_companies()
            self.load_company_industries()
            self.load_company_specialties()
            self.load_employee_counts()
            self.load_job_postings()
            self.load_job_skills()
            self.load_job_industries()
            self.load_benefits()
            self.load_salaries()
            self.load_data_analyst_benchmarks()
            self.load_data_science_benchmarks()
            print("ETL pipeline executed successfully!")
        except Exception as e:
            logger.error(f"ETL pipeline failed during execution: {e}", exc_info=True)
            raise e

    # 1. Load Industries
    def load_industries(self):
        csv_path = self.get_csv_path('info/industries.csv')
        if not csv_path.exists():
            print(f"Skipping Industries: file not found at {csv_path}")
            return
        
        print("Loading Industries...")
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['industry_id_clean'] = chunk['industry_id'].apply(lambda x: parse_int(x))
            chunk['industry_name_clean'] = chunk['industry_name'].apply(lambda x: parse_str(x, 255))
            
            chunk = chunk.dropna(subset=['industry_id_clean', 'industry_name_clean'])
            chunk = chunk.drop_duplicates(subset=['industry_id_clean'])
            chunk = chunk[~chunk['industry_id_clean'].isin(self.loaded_industry_ids)]
            
            if chunk.empty:
                continue
                
            self.loaded_industry_ids.update(chunk['industry_id_clean'].tolist())
            
            records = chunk.apply(lambda row: Industry(
                industry_id=row['industry_id_clean'],
                industry_name=row['industry_name_clean']
            ), axis=1).tolist()
            
            Industry.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {len(self.loaded_industry_ids)} industries.")

    # 2. Load Skills
    def load_skills(self):
        csv_path = self.get_csv_path('info/skills.csv')
        if not csv_path.exists():
            print(f"Skipping Skills: file not found at {csv_path}")
            return
        
        print("Loading Skills...")
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['skill_abr_clean'] = chunk['skill_abr'].apply(lambda x: parse_str(x, 10))
            chunk['skill_name_clean'] = chunk['skill_name'].apply(lambda x: parse_str(x, 150))
            
            chunk = chunk.dropna(subset=['skill_abr_clean', 'skill_name_clean'])
            chunk = chunk.drop_duplicates(subset=['skill_abr_clean'])
            chunk = chunk[~chunk['skill_abr_clean'].isin(self.loaded_skill_abrs)]
            
            if chunk.empty:
                continue
                
            self.loaded_skill_abrs.update(chunk['skill_abr_clean'].tolist())
            
            records = chunk.apply(lambda row: Skill(
                skill_abr=row['skill_abr_clean'],
                skill_name=row['skill_name_clean']
            ), axis=1).tolist()
            
            Skill.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {len(self.loaded_skill_abrs)} skills.")

    # 3. Load Companies
    def load_companies(self):
        csv_path = self.get_csv_path('companies/companies.csv')
        if not csv_path.exists():
            print(f"Skipping Companies: file not found at {csv_path}")
            return
        
        print("Loading Companies...")
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['company_id_clean'] = chunk['company_id'].apply(lambda x: parse_int(x))
            chunk['name_clean'] = chunk['name'].apply(lambda x: parse_str(x, 255))
            
            chunk = chunk.dropna(subset=['company_id_clean', 'name_clean'])
            chunk = chunk.drop_duplicates(subset=['company_id_clean'])
            chunk = chunk[~chunk['company_id_clean'].isin(self.loaded_company_ids)]
            
            if chunk.empty:
                continue
                
            self.loaded_company_ids.update(chunk['company_id_clean'].tolist())
            
            records = chunk.apply(lambda row: Company(
                company_id=row['company_id_clean'],
                name=row['name_clean'],
                description=parse_str(row.get('description')),
                company_size=parse_int(row.get('company_size')),
                state=parse_str(row.get('state'), 100),
                country=parse_str(row.get('country'), 100),
                city=parse_str(row.get('city'), 255),
                zip_code=parse_str(row.get('zip_code'), 100),
                address=parse_str(row.get('address')),
                url=parse_str(row.get('url'), 500)
            ), axis=1).tolist()
            
            Company.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {len(self.loaded_company_ids)} companies.")

    # 4. Load Company Industries
    def load_company_industries(self):
        csv_path = self.get_csv_path('companies/company_industries.csv')
        if not csv_path.exists():
            print(f"Skipping Company Industries: file not found at {csv_path}")
            return
        
        print("Loading Company Industries...")
        seen = set()
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['company_id_clean'] = chunk['company_id'].apply(lambda x: parse_int(x))
            chunk['industry_clean'] = chunk['industry'].apply(lambda x: parse_str(x, 255))
            
            chunk = chunk.dropna(subset=['company_id_clean', 'industry_clean'])
            chunk = chunk[chunk['company_id_clean'].isin(self.loaded_company_ids)]
            
            # Deduplicate by key pair using apply and lambda
            chunk['key'] = chunk.apply(lambda r: (r['company_id_clean'], r['industry_clean']), axis=1)
            chunk = chunk[~chunk['key'].isin(seen)]
            
            if chunk.empty:
                continue
                
            seen.update(chunk['key'].tolist())
            
            records = chunk.apply(lambda row: CompanyIndustry(
                company_id=row['company_id_clean'],
                industry=row['industry_clean']
            ), axis=1).tolist()
            
            CompanyIndustry.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {len(seen)} company-industry mappings.")

    # 5. Load Company Specialties
    def load_company_specialties(self):
        csv_path = self.get_csv_path('companies/company_specialities.csv')
        if not csv_path.exists():
            print(f"Skipping Company Specialties: file not found at {csv_path}")
            return
        
        print("Loading Company Specialties...")
        seen = set()
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['company_id_clean'] = chunk['company_id'].apply(lambda x: parse_int(x))
            chunk['speciality_clean'] = chunk['speciality'].apply(lambda x: parse_str(x, 255))
            
            chunk = chunk.dropna(subset=['company_id_clean', 'speciality_clean'])
            chunk = chunk[chunk['company_id_clean'].isin(self.loaded_company_ids)]
            
            chunk['key'] = chunk.apply(lambda r: (r['company_id_clean'], r['speciality_clean']), axis=1)
            chunk = chunk[~chunk['key'].isin(seen)]
            
            if chunk.empty:
                continue
                
            seen.update(chunk['key'].tolist())
            
            records = chunk.apply(lambda row: CompanySpecialty(
                company_id=row['company_id_clean'],
                speciality=row['speciality_clean']
            ), axis=1).tolist()
            
            CompanySpecialty.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {len(seen)} company specialties.")

    # 6. Load Employee Counts
    def load_employee_counts(self):
        csv_path = self.get_csv_path('companies/employee_counts.csv')
        if not csv_path.exists():
            print(f"Skipping Employee Counts: file not found at {csv_path}")
            return
        
        print("Loading Employee Counts...")
        count = 0
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['company_id_clean'] = chunk['company_id'].apply(lambda x: parse_int(x))
            chunk['employee_count_clean'] = chunk['employee_count'].apply(lambda x: parse_int(x))
            chunk['follower_count_clean'] = chunk['follower_count'].apply(lambda x: parse_int(x))
            chunk['time_recorded_clean'] = chunk['time_recorded'].apply(lambda x: parse_int(x))
            
            chunk = chunk.dropna(subset=['company_id_clean', 'employee_count_clean', 'follower_count_clean', 'time_recorded_clean'])
            chunk = chunk[chunk['company_id_clean'].isin(self.loaded_company_ids)]
            
            if chunk.empty:
                continue
                
            count += len(chunk)
            
            records = chunk.apply(lambda row: EmployeeCountHistory(
                company_id=row['company_id_clean'],
                employee_count=row['employee_count_clean'],
                follower_count=row['follower_count_clean'],
                time_recorded=row['time_recorded_clean']
            ), axis=1).tolist()
            
            EmployeeCountHistory.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {count} employee count entries.")

    # 7. Load Job Postings
    def load_job_postings(self):
        csv_path = self.get_csv_path('info/postings.csv')
        if not csv_path.exists():
            print(f"Skipping Job Postings: file not found at {csv_path}")
            return
        
        print("Loading Job Postings (this may take a few minutes)...")
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['job_id_clean'] = chunk['job_id'].apply(lambda x: parse_int(x))
            chunk['title_clean'] = chunk['title'].apply(lambda x: parse_str(x, 255))
            chunk['description_clean'] = chunk['description'].apply(lambda x: parse_str(x))
            
            chunk = chunk.dropna(subset=['job_id_clean', 'title_clean', 'description_clean'])
            chunk = chunk.drop_duplicates(subset=['job_id_clean'])
            chunk = chunk[~chunk['job_id_clean'].isin(self.loaded_job_ids)]
            
            if chunk.empty:
                continue
                
            self.loaded_job_ids.update(chunk['job_id_clean'].tolist())
            
            records = chunk.apply(lambda row: JobPosting(
                job_id=row['job_id_clean'],
                company_id=parse_int(row.get('company_id')) if parse_int(row.get('company_id')) in self.loaded_company_ids else None,
                company_name=parse_str(row.get('company_name'), 255),
                title=row['title_clean'],
                description=row['description_clean'],
                max_salary=parse_decimal(row.get('max_salary')),
                med_salary=parse_decimal(row.get('med_salary')),
                min_salary=parse_decimal(row.get('min_salary')),
                pay_period=parse_str(row.get('pay_period'), 50),
                location=parse_str(row.get('location'), 255),
                views=parse_int(row.get('views')),
                applies=parse_int(row.get('applies')),
                original_listed_time=parse_int(row.get('original_listed_time')),
                listed_time=parse_int(row.get('listed_time')),
                expiry=parse_int(row.get('expiry')),
                closed_time=parse_int(row.get('closed_time')),
                remote_allowed=parse_bool(row.get('remote_allowed')),
                job_posting_url=parse_str(row.get('job_posting_url'), 500),
                application_url=parse_str(row.get('application_url'), 500),
                application_type=parse_str(row.get('application_type'), 100),
                formatted_work_type=parse_str(row.get('formatted_work_type'), 100),
                work_type=parse_str(row.get('work_type'), 50),
                formatted_experience_level=parse_str(row.get('formatted_experience_level'), 100),
                skills_desc=parse_str(row.get('skills_desc')),
                posting_domain=parse_str(row.get('posting_domain'), 255),
                sponsored=parse_bool(row.get('sponsored')),
                currency=parse_str(row.get('currency'), 3),
                compensation_type=parse_str(row.get('compensation_type'), 50),
                normalized_salary=parse_decimal(row.get('normalized_salary')),
                zip_code=parse_str(row.get('zip_code'), 100),
                fips=parse_str(row.get('fips'), 50)
            ), axis=1).tolist()
            
            JobPosting.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {len(self.loaded_job_ids)} job postings.")

    # 8. Load Job Skills
    def load_job_skills(self):
        csv_path = self.get_csv_path('job/job_skills.csv')
        if not csv_path.exists():
            print(f"Skipping Job Skills: file not found at {csv_path}")
            return
        
        print("Loading Job Skills Junction...")
        seen = set()
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['job_id_clean'] = chunk['job_id'].apply(lambda x: parse_int(x))
            chunk['skill_id_clean'] = chunk['skill_abr'].apply(lambda x: parse_str(x, 10))
            
            chunk = chunk.dropna(subset=['job_id_clean', 'skill_id_clean'])
            chunk = chunk[chunk['job_id_clean'].isin(self.loaded_job_ids) & chunk['skill_id_clean'].isin(self.loaded_skill_abrs)]
            
            chunk['key'] = chunk.apply(lambda r: (r['job_id_clean'], r['skill_id_clean']), axis=1)
            chunk = chunk[~chunk['key'].isin(seen)]
            
            if chunk.empty:
                continue
                
            seen.update(chunk['key'].tolist())
            
            records = chunk.apply(lambda row: JobPosting.skills.through(
                jobposting_id=row['job_id_clean'],
                skill_id=row['skill_id_clean']
            ), axis=1).tolist()
            
            JobPosting.skills.through.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {len(seen)} job skills mappings.")

    # 9. Load Job Industries
    def load_job_industries(self):
        csv_path = self.get_csv_path('job/job_industries.csv')
        if not csv_path.exists():
            print(f"Skipping Job Industries: file not found at {csv_path}")
            return
        
        print("Loading Job Industries Junction...")
        seen = set()
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['job_id_clean'] = chunk['job_id'].apply(lambda x: parse_int(x))
            chunk['industry_id_clean'] = chunk['industry_id'].apply(lambda x: parse_int(x))
            
            chunk = chunk.dropna(subset=['job_id_clean', 'industry_id_clean'])
            chunk = chunk[chunk['job_id_clean'].isin(self.loaded_job_ids) & chunk['industry_id_clean'].isin(self.loaded_industry_ids)]
            
            chunk['key'] = chunk.apply(lambda r: (r['job_id_clean'], r['industry_id_clean']), axis=1)
            chunk = chunk[~chunk['key'].isin(seen)]
            
            if chunk.empty:
                continue
                
            seen.update(chunk['key'].tolist())
            
            records = chunk.apply(lambda row: JobPosting.industries.through(
                jobposting_id=row['job_id_clean'],
                industry_id=row['industry_id_clean']
            ), axis=1).tolist()
            
            JobPosting.industries.through.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {len(seen)} job industries mappings.")

    # 10. Load Benefits
    def load_benefits(self):
        csv_path = self.get_csv_path('job/benefits.csv')
        if not csv_path.exists():
            print(f"Skipping Benefits: file not found at {csv_path}")
            return
        
        print("Loading Benefits...")
        count = 0
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['job_id_clean'] = chunk['job_id'].apply(lambda x: parse_int(x))
            chunk['b_type_clean'] = chunk['type'].apply(lambda x: parse_str(x, 255))
            
            chunk = chunk.dropna(subset=['job_id_clean', 'b_type_clean'])
            chunk = chunk[chunk['job_id_clean'].isin(self.loaded_job_ids)]
            
            if chunk.empty:
                continue
                
            count += len(chunk)
            
            records = chunk.apply(lambda row: Benefit(
                job_id=row['job_id_clean'],
                inferred=parse_bool(row.get('inferred')),
                type=row['b_type_clean']
            ), axis=1).tolist()
            
            Benefit.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {count} benefit entries.")

    # 11. Load Salaries
    def load_salaries(self):
        csv_path = self.get_csv_path('job/salaries.csv')
        if not csv_path.exists():
            print(f"Skipping Salaries: file not found at {csv_path}")
            return
        
        print("Loading Salaries...")
        seen_salaries = set()
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['salary_id_clean'] = chunk['salary_id'].apply(lambda x: parse_int(x))
            chunk['job_id_clean'] = chunk['job_id'].apply(lambda x: parse_int(x))
            
            chunk = chunk.dropna(subset=['salary_id_clean', 'job_id_clean'])
            chunk = chunk[chunk['job_id_clean'].isin(self.loaded_job_ids)]
            chunk = chunk[~chunk['salary_id_clean'].isin(seen_salaries)]
            
            if chunk.empty:
                continue
                
            seen_salaries.update(chunk['salary_id_clean'].tolist())
            
            records = chunk.apply(lambda row: JobSalaryDetail(
                salary_id=row['salary_id_clean'],
                job_id=row['job_id_clean'],
                max_salary=parse_decimal(row.get('max_salary')),
                med_salary=parse_decimal(row.get('med_salary')),
                min_salary=parse_decimal(row.get('min_salary')),
                pay_period=parse_str(row.get('pay_period'), 50),
                currency=parse_str(row.get('currency'), 3),
                compensation_type=parse_str(row.get('compensation_type'), 50)
            ), axis=1).tolist()
            
            JobSalaryDetail.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {len(seen_salaries)} salary entries.")

    # 12. Load Data Analyst Benchmarks
    def load_data_analyst_benchmarks(self):
        csv_path = self.get_csv_path('analysis/DataAnalyst.csv')
        if not csv_path.exists():
            print(f"Skipping Data Analyst Benchmarks: file not found at {csv_path}")
            return
        
        print("Loading Data Analyst Benchmarks...")
        count = 0
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['job_title_clean'] = chunk['Job Title'].apply(lambda x: parse_str(x, 255))
            
            chunk = chunk.dropna(subset=['job_title_clean'])
            
            if chunk.empty:
                continue
                
            count += len(chunk)
            
            records = chunk.apply(lambda row: DataAnalystBenchmark(
                job_title=row['job_title_clean'],
                salary_estimate=parse_str(row.get('Salary Estimate'), 100),
                job_description=parse_str(row.get('Job Description')),
                rating=parse_decimal(row.get('Rating')),
                company_name=parse_str(row.get('Company Name'), 255),
                location=parse_str(row.get('Location'), 255),
                headquarters=parse_str(row.get('Headquarters'), 255),
                size=parse_str(row.get('Size'), 100),
                founded=parse_int(row.get('Founded')),
                type_of_ownership=parse_str(row.get('Type of ownership'), 255),
                industry=parse_str(row.get('Industry'), 255),
                sector=parse_str(row.get('Sector'), 255),
                revenue=parse_str(row.get('Revenue'), 100),
                competitors=parse_str(row.get('Competitors')),
                easy_apply=parse_str(row.get('Easy Apply'), 20)
            ), axis=1).tolist()
            
            DataAnalystBenchmark.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {count} Data Analyst benchmark records.")

    # 13. Load Data Science Benchmarks
    def load_data_science_benchmarks(self):
        csv_path = self.get_csv_path('analysis/ds_salaries.csv')
        if not csv_path.exists():
            print(f"Skipping Data Science Salary Benchmarks: file not found at {csv_path}")
            return
        
        print("Loading Data Science Salary Benchmarks...")
        count = 0
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['job_title_clean'] = chunk['job_title'].apply(lambda x: parse_str(x, 255))
            chunk['work_year_clean'] = chunk['work_year'].apply(lambda x: parse_int(x))
            chunk['salary_clean'] = chunk['salary'].apply(lambda x: parse_decimal(x))
            chunk['salary_in_usd_clean'] = chunk['salary_in_usd'].apply(lambda x: parse_decimal(x))
            
            chunk = chunk.dropna(subset=['job_title_clean', 'work_year_clean', 'salary_clean', 'salary_in_usd_clean'])
            
            if chunk.empty:
                continue
                
            count += len(chunk)
            
            records = chunk.apply(lambda row: DataScienceSalaryBenchmark(
                work_year=row['work_year_clean'],
                experience_level=parse_str(row.get('experience_level'), 10) or '',
                employment_type=parse_str(row.get('employment_type'), 10) or '',
                job_title=row['job_title_clean'],
                salary=row['salary_clean'],
                salary_currency=parse_str(row.get('salary_currency'), 3) or '',
                salary_in_usd=row['salary_in_usd_clean'],
                employee_residence=parse_str(row.get('employee_residence'), 10) or '',
                remote_ratio=parse_int(row.get('remote_ratio')) or 0,
                company_location=parse_str(row.get('company_location'), 10) or '',
                company_size=parse_str(row.get('company_size'), 3) or ''
            ), axis=1).tolist()
            
            DataScienceSalaryBenchmark.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {count} Data Science benchmark records.")


# ---------------------------------------------------------
# Celery Cron Job Task Definition
# ---------------------------------------------------------
@shared_task(name="core.tasks.run_etl_pipeline")
def run_etl_pipeline():
    """Shared Celery Beat Task to run ETL once a month."""
    pipeline = CSVETLPipeline()
    pipeline.run()


# ---------------------------------------------------------
# Adzuna API Daily Ingestion Task
# ---------------------------------------------------------
@shared_task(name="core.tasks.run_adzuna_ingestion")
def run_adzuna_ingestion():
    """Shared Celery Beat Task to run Adzuna API ingestion daily at 1:00 AM."""
    import hashlib
    from datetime import datetime
    from integration.adzuna.client import AdzunaClient
    
    client = AdzunaClient()
    
    # Standard countries list supported by Adzuna
    countries = [
        'gb', 'us', 'de', 'fr', 'au', 'nz', 'ca', 'in', 'pl', 'br', 'at', 'za',
        'nl', 'it', 'es', 'ru', 'mx', 'sg', 'my', 'ie', 'ch', 'be'
    ]
    
    companies_created = 0
    jobs_created = 0
    
    logger.info("Starting daily Adzuna API ingestion...")
    
    for country in countries:
        logger.info(f"Ingesting Adzuna jobs for country: {country}")
        for page in range(1, 6):
            try:
                results = client.fetch_jobs(country=country, page=page, query="data engineer")
                if not results:
                    break
                
                for job_data in results:
                    job_id = parse_int(job_data.get('id'))
                    title = parse_str(job_data.get('title'), 255)
                    description = parse_str(job_data.get('description'))
                    
                    if not job_id or not title or not description:
                        continue
                    
                    # Deduplication: check if job listing exists
                    if JobPosting.objects.filter(job_id=job_id).exists():
                        continue
                    
                    # Company parsing and deterministic ID resolution
                    company_data = job_data.get('company', {})
                    company_name = parse_str(company_data.get('display_name'), 255)
                    company = None
                    
                    if company_name:
                        # Generate 63-bit integer PK from company name hash
                        company_pk = int(hashlib.md5(company_name.lower().strip().encode('utf-8')).hexdigest(), 16) & ((1 << 63) - 1)
                        company, created = Company.objects.get_or_create(
                            company_id=company_pk,
                            defaults={
                                'name': company_name,
                                'data_source': 'API'
                            }
                        )
                        if created:
                            companies_created += 1
                    
                    # Parse created time (date format: ISO "2013-11-08T18:07:39Z")
                    created_time = None
                    created_str = job_data.get('created')
                    if created_str:
                        try:
                            dt = datetime.strptime(created_str.strip(), "%Y-%m-%dT%H:%M:%SZ")
                            created_time = int(dt.timestamp())
                        except Exception:
                            pass
                    
                    # Location
                    loc_data = job_data.get('location', {})
                    location_display = parse_str(loc_data.get('display_name'), 255)
                    
                    # Create job posting
                    JobPosting.objects.create(
                        job_id=job_id,
                        company=company,
                        company_name=company_name,
                        title=title,
                        description=description,
                        min_salary=parse_decimal(job_data.get('salary_min')),
                        max_salary=parse_decimal(job_data.get('salary_max')),
                        job_posting_url=parse_str(job_data.get('redirect_url'), 500),
                        location=location_display,
                        listed_time=created_time,
                        data_source='API'
                    )
                    jobs_created += 1
            except Exception as e:
                logger.error(f"Error occurred during Adzuna ingestion for country {country} page {page}: {e}", exc_info=True)
                break
                
    logger.info(f"Daily Adzuna API ingestion completed! Created {companies_created} companies and {jobs_created} job postings.")
