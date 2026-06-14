import logging
from pathlib import Path
from datetime import datetime
from typing import Set, Any 
import pandas as pd
from django.conf import settings
from celery import shared_task

logger = logging.getLogger(__name__)


# Shadow print to route standard prints to Celery/Django logged stdout info file
def print(*args, **kwargs):
    logger.info(" ".join(map(str, args)))


from apps.company.models import Company, CompanyIndustry, CompanySpecialty, EmployeeCountHistory
from apps.jobs.models import Industry, Skill, JobPosting, Benefit, JobSalaryDetail
from apps.benchmarks.models import (
    DataAnalystBenchmark, DataScienceSalaryBenchmark,
    APISalaryHistory, APISalaryHistogram, APITopCompany, APISalaryPrediction
)

# ---------------------------------------------------------
# Import Calculations, Parsers, & Enrichment Logic Class
# ---------------------------------------------------------
from core.logic import JobDataProcessor

parse_str = JobDataProcessor.parse_str
parse_int = JobDataProcessor.parse_int
parse_decimal = JobDataProcessor.parse_decimal
parse_bool = JobDataProcessor.parse_bool
clean_html_text = JobDataProcessor.clean_html_text
infer_remote_allowed = JobDataProcessor.infer_remote_allowed
infer_work_type = JobDataProcessor.infer_work_type
infer_experience_level = JobDataProcessor.infer_experience_level
normalize_api_salary = JobDataProcessor.normalize_api_salary
generate_deterministic_id = JobDataProcessor.generate_deterministic_id
calculate_average_salary = JobDataProcessor.calculate_average_salary


def clean_records(df: pd.DataFrame, columns: list = None) -> list:
    records = df[columns].to_dict('records') if columns is not None else df.to_dict('records')
    return [{k: (None if pd.isna(v) else v) for k, v in row.items()} for row in records]


def resolve_company_ids(names) -> dict:
    from django.db.models.functions import Lower
    from apps.company.models import Company
    
    names_clean = [str(n).strip() for n in names if n and not pd.isna(n)]
    if not names_clean:
        return {}
        
    lower_names = list({n.lower() for n in names_clean})
    
    existing_companies = Company.objects.annotate(name_lower=Lower('name')).filter(name_lower__in=lower_names)
    name_to_id = {c.name.lower().strip(): c.company_id for c in existing_companies}
    
    for name in names_clean:
        name_key = name.lower()
        if name_key not in name_to_id:
            name_to_id[name_key] = generate_deterministic_id(name)
            
    return name_to_id




# ---------------------------------------------------------
# CSV ETL Pipeline Class
# ---------------------------------------------------------
class CSVETLPipeline:
    """ETL Pipeline to process Job Market datasets from raw CSVs to DB."""

    def __init__(self, chunk_size: int = 2000):
        self.chunk_size = chunk_size
        self.base_dir = Path(settings.BASE_DIR) / 'core' / 'data' / 'raw'
        
        # Track inserted Primary Keys to prevent DB constraint errors
        self.loaded_industry_ids: Set[int] = set()
        self.loaded_skill_abrs: Set[str] = set()
        self.loaded_company_ids: Set[int] = set()
        self.loaded_job_ids: Set[int] = set()

    def get_csv_path(self, relative_path: str) -> Path:
        """Resolve base path to raw CSV datasets."""
        return self.base_dir / relative_path

    def _download_file(self, url: str, dest_path: Path) -> None:
        """Download a file from an HTTP(S) URL, with support for large Google Drive files."""
        import requests
        session = requests.Session()
        
        # Check if Google Drive link
        if "drive.google.com" in url or "docs.google.com" in url:
            file_id = None
            if "id=" in url:
                file_id = url.split("id=")[1].split("&")[0]
            elif "/d/" in url:
                file_id = url.split("/d/")[1].split("/")[0]
                
            if file_id:
                self._download_gdrive_file(file_id, dest_path)
                return
            else:
                response = session.get(url, stream=True)
        else:
            response = session.get(url, stream=True)
            
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    def _download_and_extract_raw_data(self) -> None:
        """Download raw data from environment variable. Supports both ZIP file URLs and Google Drive folder URLs."""
        import os
        zip_url = os.getenv('RAW_DATA_ZIP_URL')
        if not zip_url:
            print("No RAW_DATA_ZIP_URL environment variable configured. Skipping dynamic download.")
            return

        # Detect if URL is a Google Drive folder
        if 'drive.google.com/drive/folders/' in zip_url:
            self._download_from_gdrive_folder(zip_url)
        else:
            self._download_and_extract_zip(zip_url)

    def _download_from_gdrive_folder(self, folder_url: str) -> None:
        """Download from Google Drive folder by first scraping the folder page HTML to bypass 403 API limits."""
        import requests
        import re

        # Extract folder ID from URL
        folder_id = folder_url.rstrip('/').split('/')[-1].split('?')[0]
        print(f"Detected Google Drive folder ID: {folder_id}. Scanning public folder HTML...")

        # Known mapping of CSV filenames to their local subdirectories
        file_destination_map = {
            'industries.csv': 'info',
            'postings.csv': 'info',
            'skills.csv': 'info',
            'companies.csv': 'companies',
            'company_industries.csv': 'companies',
            'company_specialities.csv': 'companies',
            'employee_counts.csv': 'companies',
            'job_skills.csv': 'job',
            'job_industries.csv': 'job',
            'benefits.csv': 'job',
            'salaries.csv': 'job',
            'DataAnalyst.csv': 'analysis',
            'ds_salaries.csv': 'analysis',
        }

        try:
            # 1. Fetch public folder HTML page
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(folder_url, headers=headers, timeout=30)
            response.raise_for_status()
            html = response.text

            # 2. Parse filenames and file IDs using regex
            # Look for HTML elements like: data-id="FILE_ID" ... data-tooltip="FILENAME Compressed archive"
            # and JavaScript serialized metadata like: ["FILE_ID",[...],"FILENAME"
            found_files = []
            
            # Match elements in DOM: data-id="ID" and data-tooltip="FILENAME"
            dom_matches = re.findall(r'data-id="([a-zA-Z0-9_-]{33,35})"[^>]+data-tooltip="([^"]+)"', html)
            for file_id, tooltip in dom_matches:
                filename = tooltip.split(' ')[0] # E.g., "raw.zip Compressed archive" -> "raw.zip"
                found_files.append((file_id, filename))

            # Match initialData JSON/JS block (fallback/supplement)
            init_matches = re.findall(r'\\x22([a-zA-Z0-9_-]{33,35})\\x22,\s*\\x5b\\x22' + folder_id + r'\\x22\\x5d,\s*\\x22([^"\\]+)\\x22', html)
            for file_id, filename in init_matches:
                found_files.append((file_id, filename))

            # Remove duplicate file entries while keeping order
            seen_ids = set()
            files = []
            for file_id, filename in found_files:
                if file_id not in seen_ids and file_id != folder_id:
                    seen_ids.add(file_id)
                    files.append({'id': file_id, 'name': filename})

            print(f"Scraped folder contents. Found files: {files}")

            # 3. Handle ZIP files inside folder (like raw.zip)
            zip_file = next((f for f in files if f['name'].lower().endswith('.zip')), None)
            if zip_file:
                print(f"Found ZIP file '{zip_file['name']}' in Google Drive folder. Downloading and extracting...")
                zip_download_url = f"https://drive.google.com/uc?export=download&id={zip_file['id']}"
                self._download_and_extract_zip(zip_download_url)
                return

            # 4. If no ZIP is found, download CSV files individually
            csv_files = [f for f in files if f['name'].lower().endswith('.csv')]
            if csv_files:
                print(f"Found {len(csv_files)} CSV files in Google Drive folder. Downloading individually...")
                for f in csv_files:
                    subdir = file_destination_map.get(f['name'])
                    if subdir:
                        dest_dir = self.base_dir / subdir
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        dest_path = dest_dir / f['name']
                        self._download_gdrive_file(f['id'], dest_path)
                return

            # 5. API Fallback if scraping yielded nothing
            print("Scraper found no files. Falling back to Google Drive API v3...")
            list_url = "https://www.googleapis.com/drive/v3/files"
            params = {
                'q': f"'{folder_id}' in parents and trashed = false",
                'fields': 'files(id, name, mimeType)',
                'pageSize': 100,
            }
            api_resp = requests.get(list_url, params=params, timeout=30)
            if api_resp.status_code == 200:
                api_files = api_resp.json().get('files', [])
                # If the folder contains subfolders/files
                subfolders = {f['name']: f['id'] for f in api_files if f.get('mimeType') == 'application/vnd.google-apps.folder'}
                api_csv_files = [f for f in api_files if f['name'].lower().endswith('.csv')]
                api_zip_files = [f for f in api_files if f['name'].lower().endswith('.zip')]
                
                if api_zip_files:
                    zip_file = api_zip_files[0]
                    zip_download_url = f"https://drive.google.com/uc?export=download&id={zip_file['id']}"
                    self._download_and_extract_zip(zip_download_url)
                    return
                elif api_csv_files:
                    for f in api_csv_files:
                        subdir = file_destination_map.get(f['name'])
                        if subdir:
                            dest_dir = self.base_dir / subdir
                            dest_dir.mkdir(parents=True, exist_ok=True)
                            dest_path = dest_dir / f['name']
                            self._download_gdrive_file(f['id'], dest_path)
                    return
            
            # 6. Final subfolder lookup fallback
            print("Google Drive API call failed or folder empty. Attempting fallback to download known raw.zip directly...")
            try:
                known_zip_id = '1-FmmM1p_YfVq2atpwYDWFusNL2Rm1IG5'
                zip_download_url = f"https://drive.google.com/uc?export=download&id={known_zip_id}"
                self._download_and_extract_zip(zip_download_url)
                return
            except Exception as fallback_err:
                logger.error(f"Fallback direct download of raw.zip failed: {fallback_err}", exc_info=True)
            
            print("Performing local mapping scan...")
            self._download_gdrive_subfolders(folder_id, file_destination_map)

        except Exception as e:
            logger.error(f"Failed to scrape or download from Google Drive folder: {e}", exc_info=True)
            print("Attempting fallback to download known raw.zip directly...")
            try:
                known_zip_id = '1-FmmM1p_YfVq2atpwYDWFusNL2Rm1IG5'
                zip_download_url = f"https://drive.google.com/uc?export=download&id={known_zip_id}"
                self._download_and_extract_zip(zip_download_url)
                return
            except Exception as fallback_err:
                logger.error(f"Fallback direct download of raw.zip failed: {fallback_err}", exc_info=True)
            self._download_gdrive_subfolders(folder_id, file_destination_map)

    def _download_gdrive_subfolders(self, folder_id: str, file_map: dict) -> None:
        """Fallback: try downloading known files directly by scanning subfolder names."""
        import requests
        
        known_subfolders = {'info', 'companies', 'job', 'analysis'}
        list_url = "https://www.googleapis.com/drive/v3/files"
        
        for subfolder_name in known_subfolders:
            dest_dir = self.base_dir / subfolder_name
            dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to download files by mapping
        for filename, subdir in file_map.items():
            dest_dir = self.base_dir / subdir
            dest_path = dest_dir / filename
            if dest_path.exists():
                print(f"File already exists, skipping: {dest_path}")
                continue
            print(f"File not available for direct download: {filename} -> {subdir}/")

    def _download_gdrive_file(self, file_id: str, dest_path: Path) -> None:
        """Download a single file from Google Drive by file ID, handling large file warnings."""
        import requests
        import re
        
        if dest_path.exists():
            print(f"File already exists, skipping: {dest_path}")
            return
            
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            response = session.get(download_url, stream=True, headers=headers, timeout=60)
            
            # Check if this is a virus warning / confirmation page
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                html = response.text
                
                # Extract hidden input fields
                inputs = {}
                for match in re.finditer(r'<input\s+[^>]*type="hidden"[^>]*>', html):
                    tag = match.group(0)
                    name_m = re.search(r'name="([^"]+)"', tag)
                    val_m = re.search(r'value="([^"]*)"', tag)
                    if name_m and val_m:
                        inputs[name_m.group(1)] = val_m.group(1)
                
                if inputs:
                    # Found inputs (e.g. id, export, confirm, uuid)
                    form_action_m = re.search(r'<form[^>]*action="([^"]+)"', html)
                    if form_action_m:
                        action_url = form_action_m.group(1)
                    else:
                        action_url = "https://drive.usercontent.google.com/download"
                        
                    print(f"Bypassing GDrive warning for file {file_id}. Submitting parameters: {inputs}")
                    response = session.get(action_url, params=inputs, headers=headers, stream=True, timeout=60)
            
            response.raise_for_status()
            
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"Downloaded: {dest_path.name} -> {dest_path}")
        except Exception as e:
            logger.error(f"Failed to download Google Drive file {file_id}: {e}", exc_info=True)
            raise e

    def _download_and_extract_zip(self, zip_url: str) -> None:
        """Download and extract a ZIP file from a direct URL."""
        print(f"Downloading raw dataset zip from {zip_url}...")
        temp_zip = Path(settings.BASE_DIR) / 'core' / 'data' / 'raw_data.zip'
        temp_zip.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            self._download_file(zip_url, temp_zip)
            print("Download completed. Extracting raw dataset zip...")
            
            import zipfile
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(self.base_dir)
                
            print(f"Extraction successful! Raw datasets extracted to {self.base_dir}")
            
            # Clean up zip
            if temp_zip.exists():
                temp_zip.unlink()
        except Exception as e:
            logger.error(f"Failed to download and extract raw data zip: {e}", exc_info=True)
            if temp_zip.exists():
                temp_zip.unlink()

    def run(self) -> None:
        """Execute all CSV data loading pipelines sequentially."""
        print("Starting ETL pipeline execution...")
        self._download_and_extract_raw_data()
        
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
    def load_industries(self) -> None:
        """Parse and load industry records in chunks."""
        csv_path = self.get_csv_path('info/industries.csv')
        if not csv_path.exists():
            print(f"Skipping Industries: file not found at {csv_path}")
            return
        
        print("Loading Industries...")
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['industry_id_clean'] = chunk['industry_id'].map(parse_int)
            chunk['industry_name_clean'] = chunk['industry_name'].map(lambda x: parse_str(x, 255))
            
            chunk = chunk.dropna(subset=['industry_id_clean', 'industry_name_clean'])
            chunk = chunk.drop_duplicates(subset=['industry_id_clean'])
            chunk = chunk[~chunk['industry_id_clean'].isin(self.loaded_industry_ids)]
            
            if chunk.empty:
                continue
                
            self.loaded_industry_ids.update(chunk['industry_id_clean'].tolist())
            
            chunk = chunk.rename(columns={'industry_id_clean': 'industry_id', 'industry_name_clean': 'industry_name'})
            records = [Industry(**row) for row in clean_records(chunk, ['industry_id', 'industry_name'])]
            
            Industry.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {len(self.loaded_industry_ids)} industries.")

    # 2. Load Skills
    def load_skills(self) -> None:
        """Parse and load skill references in chunks."""
        csv_path = self.get_csv_path('info/skills.csv')
        if not csv_path.exists():
            print(f"Skipping Skills: file not found at {csv_path}")
            return
        
        print("Loading Skills...")
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['skill_abr_clean'] = chunk['skill_abr'].map(lambda x: parse_str(x, 10))
            chunk['skill_name_clean'] = chunk['skill_name'].map(lambda x: parse_str(x, 150))
            
            chunk = chunk.dropna(subset=['skill_abr_clean', 'skill_name_clean'])
            chunk = chunk.drop_duplicates(subset=['skill_abr_clean'])
            chunk = chunk[~chunk['skill_abr_clean'].isin(self.loaded_skill_abrs)]
            
            if chunk.empty:
                continue
                
            self.loaded_skill_abrs.update(chunk['skill_abr_clean'].tolist())
            
            chunk = chunk.rename(columns={'skill_abr_clean': 'skill_abr', 'skill_name_clean': 'skill_name'})
            records = [Skill(**row) for row in clean_records(chunk, ['skill_abr', 'skill_name'])]
            
            Skill.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {len(self.loaded_skill_abrs)} skills.")

    # 3. Load Companies
    def load_companies(self) -> None:
        """Parse and load company profiles in chunks, using conflict-resolution updates."""
        csv_path = self.get_csv_path('companies/companies.csv')
        if not csv_path.exists():
            print(f"Skipping Companies: file not found at {csv_path}")
            return
        
        print("Loading Companies...")
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['company_id_clean'] = chunk['company_id'].map(parse_int)
            chunk['name_clean'] = chunk['name'].map(lambda x: parse_str(x, 255))
            
            chunk = chunk.dropna(subset=['company_id_clean', 'name_clean'])
            chunk = chunk.drop_duplicates(subset=['company_id_clean'])
            chunk = chunk[~chunk['company_id_clean'].isin(self.loaded_company_ids)]
            
            if chunk.empty:
                continue
                
            self.loaded_company_ids.update(chunk['company_id_clean'].tolist())
            
            company_df = pd.DataFrame()
            company_df['company_id'] = chunk['company_id_clean']
            company_df['name'] = chunk['name_clean']
            company_df['description'] = chunk['description'].map(parse_str) if 'description' in chunk.columns else None
            company_df['company_size'] = chunk['company_size'].map(parse_int) if 'company_size' in chunk.columns else None
            company_df['state'] = chunk['state'].map(lambda x: parse_str(x, 100)) if 'state' in chunk.columns else None
            company_df['country'] = chunk['country'].map(lambda x: parse_str(x, 100)) if 'country' in chunk.columns else None
            company_df['city'] = chunk['city'].map(lambda x: parse_str(x, 255)) if 'city' in chunk.columns else None
            company_df['zip_code'] = chunk['zip_code'].map(lambda x: parse_str(x, 100)) if 'zip_code' in chunk.columns else None
            company_df['address'] = chunk['address'].map(parse_str) if 'address' in chunk.columns else None
            company_df['url'] = chunk['url'].map(lambda x: parse_str(x, 500)) if 'url' in chunk.columns else None
            
            records = [Company(**row) for row in clean_records(company_df)]
            
            Company.objects.bulk_create(
                records,
                update_conflicts=True,
                update_fields=['name', 'description', 'company_size', 'state', 'country', 'city', 'zip_code', 'address', 'url'],
                unique_fields=['company_id']
            )
        print(f"Successfully loaded {len(self.loaded_company_ids)} companies.")

    # 4. Load Company Industries
    def load_company_industries(self) -> None:
        """Parse and load company-industry mappings in chunks, filtering duplicates."""
        csv_path = self.get_csv_path('companies/company_industries.csv')
        if not csv_path.exists():
            print(f"Skipping Company Industries: file not found at {csv_path}")
            return
        
        print("Loading Company Industries...")
        seen = set()
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['company_id_clean'] = chunk['company_id'].map(parse_int)
            chunk['industry_clean'] = chunk['industry'].map(lambda x: parse_str(x, 255))
            
            chunk = chunk.dropna(subset=['company_id_clean', 'industry_clean'])
            chunk = chunk[chunk['company_id_clean'].isin(self.loaded_company_ids)]
            
            chunk['key'] = list(zip(chunk['company_id_clean'], chunk['industry_clean']))
            chunk = chunk[~chunk['key'].isin(seen)]
            if chunk.empty:
                continue
                
            seen.update(chunk['key'].tolist())
            
            chunk = chunk.rename(columns={'company_id_clean': 'company_id', 'industry_clean': 'industry'})
            records = [CompanyIndustry(**row) for row in clean_records(chunk, ['company_id', 'industry'])]
            
            CompanyIndustry.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {len(seen)} company-industry mappings.")

    # 5. Load Company Specialties
    def load_company_specialties(self) -> None:
        """Parse and load company specialty descriptors in chunks."""
        csv_path = self.get_csv_path('companies/company_specialities.csv')
        if not csv_path.exists():
            print(f"Skipping Company Specialties: file not found at {csv_path}")
            return
        
        print("Loading Company Specialties...")
        seen = set()
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['company_id_clean'] = chunk['company_id'].map(parse_int)
            chunk['speciality_clean'] = chunk['speciality'].map(lambda x: parse_str(x, 255))
            
            chunk = chunk.dropna(subset=['company_id_clean', 'speciality_clean'])
            chunk = chunk[chunk['company_id_clean'].isin(self.loaded_company_ids)]
            
            chunk['key'] = list(zip(chunk['company_id_clean'], chunk['speciality_clean']))
            chunk = chunk[~chunk['key'].isin(seen)]
            if chunk.empty:
                continue
                
            seen.update(chunk['key'].tolist())
            
            chunk = chunk.rename(columns={'company_id_clean': 'company_id', 'speciality_clean': 'speciality'})
            records = [CompanySpecialty(**row) for row in clean_records(chunk, ['company_id', 'speciality'])]
            
            CompanySpecialty.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {len(seen)} company specialties.")

    # 6. Load Employee Counts
    def load_employee_counts(self) -> None:
        """Parse and load historical employee headcount logs in chunks."""
        csv_path = self.get_csv_path('companies/employee_counts.csv')
        if not csv_path.exists():
            print(f"Skipping Employee Counts: file not found at {csv_path}")
            return
        
        print("Loading Employee Counts...")
        count = 0
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['company_id_clean'] = chunk['company_id'].map(parse_int)
            chunk['employee_count_clean'] = chunk['employee_count'].map(parse_int)
            chunk['follower_count_clean'] = chunk['follower_count'].map(parse_int)
            chunk['time_recorded_clean'] = chunk['time_recorded'].map(parse_int)
            
            chunk = chunk.dropna(subset=['company_id_clean', 'employee_count_clean', 'follower_count_clean', 'time_recorded_clean'])
            chunk = chunk[chunk['company_id_clean'].isin(self.loaded_company_ids)]
            
            if chunk.empty:
                continue
                
            count += len(chunk)
            
            chunk = chunk.rename(columns={
                'company_id_clean': 'company_id',
                'employee_count_clean': 'employee_count',
                'follower_count_clean': 'follower_count',
                'time_recorded_clean': 'time_recorded'
            })
            
            records = [EmployeeCountHistory(**row) for row in clean_records(chunk, ['company_id', 'employee_count', 'follower_count', 'time_recorded'])]
            
            EmployeeCountHistory.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {count} employee count entries.")

    # 7. Load Job Postings
    def load_job_postings(self) -> None:
        """Parse and load core job posting tables in chunks."""
        csv_path = self.get_csv_path('info/postings.csv')
        if not csv_path.exists():
            print(f"Skipping Job Postings: file not found at {csv_path}")
            return
        
        print("Loading Job Postings (this may take a few minutes)...")
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['job_id_clean'] = chunk['job_id'].map(parse_int)
            chunk['title_clean'] = chunk['title'].map(lambda x: parse_str(x, 255))
            chunk['description_clean'] = chunk['description'].map(parse_str)
            
            chunk = chunk.dropna(subset=['job_id_clean', 'title_clean', 'description_clean'])
            chunk = chunk.drop_duplicates(subset=['job_id_clean'])
            chunk = chunk[~chunk['job_id_clean'].isin(self.loaded_job_ids)]
            
            if chunk.empty:
                continue
                
            self.loaded_job_ids.update(chunk['job_id_clean'].tolist())
            
            # Setup job posting mapping dictionary
            job_fields = {
                'job_id': chunk['job_id_clean'],
                'company_name': chunk.get('company_name', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 255)),
                'title': chunk['title_clean'],
                'description': chunk['description_clean'],
                'max_salary': chunk.get('max_salary', pd.Series(dtype=str, index=chunk.index)).map(parse_decimal),
                'med_salary': chunk.get('med_salary', pd.Series(dtype=str, index=chunk.index)).map(parse_decimal),
                'min_salary': chunk.get('min_salary', pd.Series(dtype=str, index=chunk.index)).map(parse_decimal),
                'pay_period': chunk.get('pay_period', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 50)),
                'location': chunk.get('location', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 255)),
                'views': chunk.get('views', pd.Series(dtype=str, index=chunk.index)).map(parse_int),
                'applies': chunk.get('applies', pd.Series(dtype=str, index=chunk.index)).map(parse_int),
                'original_listed_time': chunk.get('original_listed_time', pd.Series(dtype=str, index=chunk.index)).map(parse_int),
                'listed_time': chunk.get('listed_time', pd.Series(dtype=str, index=chunk.index)).map(parse_int),
                'expiry': chunk.get('expiry', pd.Series(dtype=str, index=chunk.index)).map(parse_int),
                'closed_time': chunk.get('closed_time', pd.Series(dtype=str, index=chunk.index)).map(parse_int),
                'remote_allowed': chunk.get('remote_allowed', pd.Series(dtype=str, index=chunk.index)).map(parse_bool),
                'job_posting_url': chunk.get('job_posting_url', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 500)),
                'application_url': chunk.get('application_url', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 500)),
                'application_type': chunk.get('application_type', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 100)),
                'formatted_work_type': chunk.get('formatted_work_type', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 100)),
                'work_type': chunk.get('work_type', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 50)),
                'formatted_experience_level': chunk.get('formatted_experience_level', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 100)),
                'skills_desc': chunk.get('skills_desc', pd.Series(dtype=str, index=chunk.index)).map(parse_str),
                'posting_domain': chunk.get('posting_domain', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 255)),
                'sponsored': chunk.get('sponsored', pd.Series(dtype=str, index=chunk.index)).map(parse_bool),
                'currency': chunk.get('currency', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 3)),
                'compensation_type': chunk.get('compensation_type', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 50)),
                'normalized_salary': chunk.get('normalized_salary', pd.Series(dtype=str, index=chunk.index)).map(parse_decimal),
                'zip_code': chunk.get('zip_code', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 100)),
                'fips': chunk.get('fips', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 50)),
            }
            
            # Company ID validation using vectorized .where
            raw_company_ids = chunk.get('company_id', pd.Series(dtype=str, index=chunk.index)).map(parse_int)
            job_fields['company_id'] = raw_company_ids.where(raw_company_ids.isin(self.loaded_company_ids), None)
            
            job_df = pd.DataFrame(job_fields)
            records = [JobPosting(**row) for row in clean_records(job_df)]
            
            JobPosting.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {len(self.loaded_job_ids)} job postings.")

    # 8. Load Job Skills
    def load_job_skills(self) -> None:
        """Parse and load job-skill relation records in chunks."""
        csv_path = self.get_csv_path('job/job_skills.csv')
        if not csv_path.exists():
            print(f"Skipping Job Skills: file not found at {csv_path}")
            return
        
        print("Loading Job Skills Junction...")
        seen = set()
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['job_id_clean'] = chunk['job_id'].map(parse_int)
            chunk['skill_id_clean'] = chunk['skill_abr'].map(lambda x: parse_str(x, 10))
            
            chunk = chunk.dropna(subset=['job_id_clean', 'skill_id_clean'])
            chunk = chunk[chunk['job_id_clean'].isin(self.loaded_job_ids) & chunk['skill_id_clean'].isin(self.loaded_skill_abrs)]
            
            chunk['key'] = list(zip(chunk['job_id_clean'], chunk['skill_id_clean']))
            chunk = chunk[~chunk['key'].isin(seen)]
            if chunk.empty:
                continue
                
            seen.update(chunk['key'].tolist())
            
            chunk = chunk.rename(columns={'job_id_clean': 'jobposting_id', 'skill_id_clean': 'skill_id'})
            records = [
                JobPosting.skills.through(**row)
                for row in clean_records(chunk, ['jobposting_id', 'skill_id'])
            ]
            
            JobPosting.skills.through.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {len(seen)} job skills mappings.")

    # 9. Load Job Industries
    def load_job_industries(self) -> None:
        """Parse and load job-industry reference map lists in chunks."""
        csv_path = self.get_csv_path('job/job_industries.csv')
        if not csv_path.exists():
            print(f"Skipping Job Industries: file not found at {csv_path}")
            return
        
        print("Loading Job Industries Junction...")
        seen = set()
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['job_id_clean'] = chunk['job_id'].map(parse_int)
            chunk['industry_id_clean'] = chunk['industry_id'].map(parse_int)
            
            chunk = chunk.dropna(subset=['job_id_clean', 'industry_id_clean'])
            chunk = chunk[chunk['job_id_clean'].isin(self.loaded_job_ids) & chunk['industry_id_clean'].isin(self.loaded_industry_ids)]
            
            chunk['key'] = list(zip(chunk['job_id_clean'], chunk['industry_id_clean']))
            chunk = chunk[~chunk['key'].isin(seen)]
            if chunk.empty:
                continue
                
            seen.update(chunk['key'].tolist())
            
            chunk = chunk.rename(columns={'job_id_clean': 'jobposting_id', 'industry_id_clean': 'industry_id'})
            records = [
                JobPosting.industries.through(**row)
                for row in clean_records(chunk, ['jobposting_id', 'industry_id'])
            ]
            
            JobPosting.industries.through.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {len(seen)} job industries mappings.")

    # 10. Load Benefits
    def load_benefits(self) -> None:
        """Parse and load job benefits checklist logs in chunks."""
        csv_path = self.get_csv_path('job/benefits.csv')
        if not csv_path.exists():
            print(f"Skipping Benefits: file not found at {csv_path}")
            return
        
        print("Loading Benefits...")
        count = 0
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['job_id_clean'] = chunk['job_id'].map(parse_int)
            chunk['b_type_clean'] = chunk['type'].map(lambda x: parse_str(x, 255))
            
            chunk = chunk.dropna(subset=['job_id_clean', 'b_type_clean'])
            chunk = chunk[chunk['job_id_clean'].isin(self.loaded_job_ids)]
            
            if chunk.empty:
                continue
                
            count += len(chunk)
            
            benefit_df = pd.DataFrame({
                'job_id': chunk['job_id_clean'],
                'type': chunk['b_type_clean'],
                'inferred': chunk.get('inferred', pd.Series(dtype=str, index=chunk.index)).map(parse_bool)
            })
            
            records = [Benefit(**row) for row in clean_records(benefit_df)]
            Benefit.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {count} benefit entries.")

    # 11. Load Salaries
    def load_salaries(self) -> None:
        """Parse and load distinct salary options and ranges in chunks."""
        csv_path = self.get_csv_path('job/salaries.csv')
        if not csv_path.exists():
            print(f"Skipping Salaries: file not found at {csv_path}")
            return
        
        print("Loading Salaries...")
        seen_salaries = set()
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['salary_id_clean'] = chunk['salary_id'].map(parse_int)
            chunk['job_id_clean'] = chunk['job_id'].map(parse_int)
            
            chunk = chunk.dropna(subset=['salary_id_clean', 'job_id_clean'])
            chunk = chunk[chunk['job_id_clean'].isin(self.loaded_job_ids)]
            chunk = chunk[~chunk['salary_id_clean'].isin(seen_salaries)]
            
            if chunk.empty:
                continue
                
            seen_salaries.update(chunk['salary_id_clean'].tolist())
            
            salary_df = pd.DataFrame({
                'salary_id': chunk['salary_id_clean'],
                'job_id': chunk['job_id_clean'],
                'max_salary': chunk.get('max_salary', pd.Series(dtype=str, index=chunk.index)).map(parse_decimal),
                'med_salary': chunk.get('med_salary', pd.Series(dtype=str, index=chunk.index)).map(parse_decimal),
                'min_salary': chunk.get('min_salary', pd.Series(dtype=str, index=chunk.index)).map(parse_decimal),
                'pay_period': chunk.get('pay_period', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 50)),
                'currency': chunk.get('currency', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 3)),
                'compensation_type': chunk.get('compensation_type', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 50))
            })
            
            records = [JobSalaryDetail(**row) for row in clean_records(salary_df)]
            JobSalaryDetail.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {len(seen_salaries)} salary entries.")

    # 12. Load Data Analyst Benchmarks
    def load_data_analyst_benchmarks(self) -> None:
        """Parse and load Glassdoor Data Analyst benchmark history."""
        csv_path = self.get_csv_path('analysis/DataAnalyst.csv')
        if not csv_path.exists():
            print(f"Skipping Data Analyst Benchmarks: file not found at {csv_path}")
            return
        
        print("Loading Data Analyst Benchmarks...")
        
        # Load all existing industry IDs and names into a map for fast lookup
        industry_map = {ind.industry_name.lower().strip(): ind.industry_id for ind in Industry.objects.all()}
        
        def clean_co_name(raw_name):
            name_val = parse_str(raw_name, 255)
            if name_val:
                return name_val.split('\n')[0].strip()
            return None

        def clean_ind_name(raw_ind):
            ind_val = parse_str(raw_ind, 255)
            if ind_val and ind_val.lower() not in ('-1', 'unknown', 'nan', 'none', ''):
                return ind_val.strip()
            return None

        count = 0
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['job_title_clean'] = chunk['Job Title'].map(lambda x: parse_str(x, 255))
            chunk = chunk.dropna(subset=['job_title_clean'])
            
            if chunk.empty:
                continue
                
            count += len(chunk)
            
            chunk['company_name_raw'] = chunk['Company Name']
            chunk['company_name_clean'] = chunk['company_name_raw'].map(clean_co_name)
            chunk['industry_clean'] = chunk['Industry'].map(clean_ind_name)
            
            # Resolve companies
            unique_companies = chunk['company_name_clean'].dropna().unique()
            name_to_id = {}
            if len(unique_companies) > 0:
                name_to_id = resolve_company_ids(unique_companies)
                
                companies_to_create = []
                seen_co_ids = set()
                for name in unique_companies:
                    co_id = name_to_id.get(name.lower())
                    if co_id and co_id not in seen_co_ids:
                        seen_co_ids.add(co_id)
                        companies_to_create.append(Company(
                            company_id=co_id,
                            name=name,
                            data_source='CSV'
                        ))
                
                Company.objects.bulk_create(
                    companies_to_create,
                    update_conflicts=True,
                    update_fields=['name', 'data_source'],
                    unique_fields=['company_id']
                )
                self.loaded_company_ids.update(seen_co_ids)
                
            # Resolve industries
            unique_industries = chunk['industry_clean'].dropna().unique()
            new_industries = [ind for ind in unique_industries if ind.lower().strip() not in industry_map]
            if new_industries:
                ind_df = pd.DataFrame({'industry_name': new_industries})
                ind_df['industry_id'] = ind_df['industry_name'].map(lambda x: generate_deterministic_id(x.lower().strip()))
                ind_df = ind_df.drop_duplicates(subset=['industry_id'])
                
                existing_pks = set(Industry.objects.filter(industry_id__in=ind_df['industry_id'].tolist()).values_list('industry_id', flat=True))
                ind_df = ind_df[~ind_df['industry_id'].isin(existing_pks)]
                
                if not ind_df.empty:
                    industries_to_create = [Industry(**row) for row in clean_records(ind_df)]
                    Industry.objects.bulk_create(industries_to_create, ignore_conflicts=True)
                    
                # Update industry_map
                for name, pk in zip(ind_df['industry_name'], ind_df['industry_id']):
                    industry_map[name.lower().strip()] = pk
            
            benchmarks_to_create = []
            for _, row in chunk.iterrows():
                co_raw = row.get('Company Name')
                co_clean = clean_co_name(co_raw) if pd.notna(co_raw) else None
                co_id = name_to_id.get(co_clean.lower()) if co_clean else None
                
                ind_raw = row.get('Industry')
                ind_clean = clean_ind_name(ind_raw) if pd.notna(ind_raw) else None
                ind_id = industry_map.get(ind_clean.lower().strip()) if ind_clean else None
                
                benchmarks_to_create.append(DataAnalystBenchmark(
                    job_title=parse_str(row.get('Job Title'), 255),
                    salary_estimate=parse_str(row.get('Salary Estimate'), 100),
                    job_description=parse_str(row.get('Job Description')),
                    rating=parse_decimal(row.get('Rating')),
                    company_name=parse_str(co_raw, 255),
                    company_id=co_id,
                    location=parse_str(row.get('Location'), 255),
                    headquarters=parse_str(row.get('Headquarters'), 255),
                    size=parse_str(row.get('Size'), 100),
                    founded=parse_int(row.get('Founded')),
                    type_of_ownership=parse_str(row.get('Type of ownership'), 255),
                    industry=parse_str(row.get('Industry'), 255),
                    industry_ref_id=ind_id,
                    sector=parse_str(row.get('Sector'), 255),
                    revenue=parse_str(row.get('Revenue'), 100),
                    competitors=parse_str(row.get('Competitors')),
                    easy_apply=parse_str(row.get('Easy Apply'), 20)
                ))
            DataAnalystBenchmark.objects.bulk_create(benchmarks_to_create, ignore_conflicts=True)
        print(f"Successfully loaded {count} Data Analyst benchmark records.")

    # 13. Load Data Science Benchmarks
    def load_data_science_benchmarks(self) -> None:
        """Parse and load global Data Science salary benchmarks dataset."""
        csv_path = self.get_csv_path('analysis/ds_salaries.csv')
        if not csv_path.exists():
            print(f"Skipping Data Science Salary Benchmarks: file not found at {csv_path}")
            return
        
        print("Loading Data Science Salary Benchmarks...")
        count = 0
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=self.chunk_size):
            chunk['job_title_clean'] = chunk['job_title'].map(lambda x: parse_str(x, 255))
            chunk['work_year_clean'] = chunk['work_year'].map(parse_int)
            chunk['salary_clean'] = chunk['salary'].map(parse_decimal)
            chunk['salary_in_usd_clean'] = chunk['salary_in_usd'].map(parse_decimal)
            
            chunk = chunk.dropna(subset=['job_title_clean', 'work_year_clean', 'salary_clean', 'salary_in_usd_clean'])
            
            if chunk.empty:
                continue
                
            count += len(chunk)
            
            benchmark_df = pd.DataFrame({
                'work_year': chunk['work_year_clean'],
                'experience_level': chunk.get('experience_level', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 10) or ''),
                'employment_type': chunk.get('employment_type', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 10) or ''),
                'job_title': chunk['job_title_clean'],
                'salary': chunk['salary_clean'],
                'salary_currency': chunk.get('salary_currency', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 3) or ''),
                'salary_in_usd': chunk['salary_in_usd_clean'],
                'employee_residence': chunk.get('employee_residence', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 10) or ''),
                'remote_ratio': chunk.get('remote_ratio', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_int(x) or 0),
                'company_location': chunk.get('company_location', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 10) or ''),
                'company_size': chunk.get('company_size', pd.Series(dtype=str, index=chunk.index)).map(lambda x: parse_str(x, 3) or '')
            })
            
            records = [DataScienceSalaryBenchmark(**row) for row in clean_records(benchmark_df)]
            DataScienceSalaryBenchmark.objects.bulk_create(records, ignore_conflicts=True)
        print(f"Successfully loaded {count} Data Science benchmark records.")


# ---------------------------------------------------------
# Adzuna API Daily Ingestion Pipeline Class
# ---------------------------------------------------------
class AdzunaAPIIngestionPipeline:
    """ETL Ingestion Pipeline to fetch, validate, enrich and store job listings from Adzuna APIs."""

    def __init__(self, client: Any):
        self.client = client
        self.countries = [
            'gb', 'us', 'de', 'fr', 'au', 'nz', 'ca', 'in', 'pl', 'br', 'at', 'za',
            'nl', 'it', 'es', 'ru', 'mx', 'sg', 'my', 'ie', 'ch', 'be'
        ]
        self.companies_created = 0
        self.jobs_created = 0
        self.histories_created = 0
        self.histograms_created = 0
        self.top_companies_created = 0

    def run(self) -> None:
        """Execute the ingestion workflow across all countries and predict salaries."""
        import time
        logger.info("Starting daily Adzuna API ingestion...")
        for country in self.countries:
            logger.info(f"Ingesting Adzuna jobs for country: {country}")
            self.ingest_country_categories(country)
            self.ingest_country_jobs(country)
            self.ingest_country_salary_history(country)
            self.ingest_country_salary_histogram(country)
            self.ingest_country_top_companies(country)
            # Wait between countries to avoid overwhelming Adzuna API
            time.sleep(3)
        
        self.ingest_jobsworth_prediction()
        logger.info(
            f"Daily Adzuna API ingestion completed! Created: "
            f"{self.companies_created} companies, {self.jobs_created} job postings, "
            f"{self.histories_created} salary history points, {self.histograms_created} histogram points, "
            f"{self.top_companies_created} top company standings."
        )

    def ingest_country_categories(self, country: str) -> None:
        """Fetch categories from API and upsert into Industry table."""
        try:
            category_results = self.client.fetch_categories(country=country)
            if not category_results:
                return
            
            cat_df = pd.DataFrame(category_results)
            cat_df['tag_clean'] = cat_df.get('tag', pd.Series(dtype=str, index=cat_df.index)).map(parse_str)
            cat_df['label_clean'] = cat_df.get('label', pd.Series(dtype=str, index=cat_df.index)).map(parse_str)
            cat_df = cat_df.dropna(subset=['tag_clean', 'label_clean'])
            
            if cat_df.empty:
                return
                
            cat_df['industry_id'] = cat_df['tag_clean'].map(generate_deterministic_id)
            cat_df = cat_df.drop_duplicates(subset=['industry_id'])
            
            cat_df = cat_df.rename(columns={'label_clean': 'industry_name'})
            industries = [
                Industry(**row)
                for row in clean_records(cat_df, ['industry_id', 'industry_name'])
            ]
            Industry.objects.bulk_create(industries, ignore_conflicts=True)
        except Exception as e:
            logger.error(f"Error fetching categories for {country}: {e}", exc_info=True)

    def ingest_country_jobs(self, country: str) -> None:
        """Fetch job search pages and bulk load listings into JobPosting table."""
        import time
        all_jobs = []
        for page in range(1, 6):
            try:
                results = self.client.fetch_jobs(country=country, page=page, query="data engineer")
                if not results:
                    break
                all_jobs.extend(results)
                # Respect rate limits — wait between requests
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error occurred during Adzuna fetch for country {country} page {page}: {e}", exc_info=True)
                break
                
        if not all_jobs:
            return
            
        try:
            job_df = pd.DataFrame(all_jobs)
            job_df['job_id_clean'] = job_df.get('id', pd.Series(dtype=str, index=job_df.index)).map(parse_int)
            job_df['title_clean'] = job_df.get('title', pd.Series(dtype=str, index=job_df.index)).map(lambda x: parse_str(x, 255))
            raw_descs = job_df.get('description', pd.Series(dtype=str, index=job_df.index)).map(parse_str)
            job_df['desc_clean'] = raw_descs.map(clean_html_text)
            
            job_df = job_df.dropna(subset=['job_id_clean', 'title_clean', 'desc_clean'])
            job_df = job_df.drop_duplicates(subset=['job_id_clean'])
            
            if job_df.empty:
                return
                
            existing_job_ids = set(
                JobPosting.objects.filter(job_id__in=job_df['job_id_clean'].tolist())
                .values_list('job_id', flat=True)
            )
            job_df = job_df[~job_df['job_id_clean'].isin(existing_job_ids)]
            
            if job_df.empty:
                return
                
            # Parse companies
            company_data_list = job_df.get('company', pd.Series([None]*len(job_df), index=job_df.index))
            company_names = company_data_list.map(lambda c: parse_str(c.get('display_name'), 255) if isinstance(c, dict) else None)
            job_df['company_name_clean'] = company_names
            
            unique_company_names = job_df['company_name_clean'].dropna().unique()
            company_name_to_id = {}
            if len(unique_company_names) > 0:
                company_name_to_id = resolve_company_ids(unique_company_names)
                companies_df = pd.DataFrame({'name': unique_company_names})
                companies_df['company_id'] = companies_df['name'].map(lambda x: company_name_to_id.get(x.lower()))
                companies_df = companies_df.drop_duplicates(subset=['company_id'])
                companies_df['data_source'] = 'API'
                
                companies_to_upsert = [Company(**row) for row in clean_records(companies_df)]
                Company.objects.bulk_create(
                    companies_to_upsert,
                    update_conflicts=True,
                    update_fields=['name', 'data_source'],
                    unique_fields=['company_id']
                )
                self.companies_created += len(companies_to_upsert)
            
            job_df['company_id_resolved'] = job_df['company_name_clean'].map(lambda x: company_name_to_id.get(x.lower()) if x else None)
            
            # Times
            def parse_created_time(created_str):
                if created_str:
                    try:
                        dt = datetime.strptime(str(created_str).strip(), "%Y-%m-%dT%H:%M:%SZ")
                        return int(dt.timestamp())
                    except Exception:
                        pass
                return None
                
            job_df['listed_time'] = job_df.get('created', pd.Series(dtype=str, index=job_df.index)).map(parse_created_time)
            
            # Vectorized inference/apply
            job_df['remote_allowed'] = job_df.apply(lambda row: infer_remote_allowed(row['title_clean'], row['desc_clean']), axis=1)
            
            work_type_tuples = job_df.apply(lambda row: infer_work_type(row['title_clean'], row['desc_clean']), axis=1)
            job_df['work_type'] = work_type_tuples.map(lambda x: x[0])
            job_df['formatted_work_type'] = work_type_tuples.map(lambda x: x[1])
            
            job_df['formatted_experience_level'] = job_df.apply(lambda row: infer_experience_level(row['title_clean'], row['desc_clean']), axis=1)
            
            min_sals = job_df.get('salary_min', pd.Series(dtype=str, index=job_df.index)).map(parse_decimal)
            max_sals = job_df.get('salary_max', pd.Series(dtype=str, index=job_df.index)).map(parse_decimal)
            job_df['min_salary'] = min_sals
            job_df['max_salary'] = max_sals
            
            # Vectorized salary normalization
            sal_val = job_df.apply(lambda row: calculate_average_salary(row['min_salary'], row['max_salary']), axis=1)
            norm_res = sal_val.map(lambda x: normalize_api_salary(country, x) if x is not None else (None, None))
            
            job_df['currency'] = norm_res.map(lambda x: x[0])
            job_df['normalized_salary'] = norm_res.map(lambda x: x[1])
            
            location_data_list = job_df.get('location', pd.Series([None]*len(job_df), index=job_df.index))
            job_df['location'] = location_data_list.map(lambda l: parse_str(l.get('display_name'), 255) if isinstance(l, dict) else None)
            
            job_df['job_posting_url'] = job_df.get('redirect_url', pd.Series(dtype=str, index=job_df.index)).map(lambda x: parse_str(x, 500))
            job_df['data_source'] = 'API'
            
            # Setup columns to construct JobPosting objects
            job_posting_cols = [
                'job_id_clean', 'company_id_resolved', 'company_name_clean', 'title_clean', 'desc_clean',
                'min_salary', 'max_salary', 'job_posting_url', 'location', 'listed_time',
                'remote_allowed', 'work_type', 'formatted_work_type', 'formatted_experience_level',
                'currency', 'normalized_salary', 'data_source'
            ]
            
            # Rename for DB mapping:
            job_df_for_db = job_df[job_posting_cols].rename(columns={
                'job_id_clean': 'job_id',
                'company_id_resolved': 'company_id',
                'company_name_clean': 'company_name',
                'title_clean': 'title',
                'desc_clean': 'description'
            })
            
            # Convert to dict and bulk create
            job_postings = [JobPosting(**row) for row in clean_records(job_df_for_db)]
            JobPosting.objects.bulk_create(job_postings, ignore_conflicts=True)
            self.jobs_created += len(job_postings)
        except Exception as e:
            logger.error(f"Error processing Adzuna jobs for country {country}: {e}", exc_info=True)

    def ingest_country_salary_history(self, country: str) -> None:
        """Fetch historical salary averages and save them to APISalaryHistory."""
        try:
            it_tag = 'it-jobs'
            it_industry_id = generate_deterministic_id(it_tag)
            category_ref = Industry.objects.filter(industry_id=it_industry_id).first()
            
            history_res = self.client.fetch_salary_history(country=country, category=it_tag)
            if not history_res:
                return
            month_data = history_res.get('month', {})
            if not month_data:
                return
                
            hist_df = pd.DataFrame(list(month_data.items()), columns=['month', 'average_salary'])
            hist_df['month_clean'] = hist_df['month'].map(parse_str)
            hist_df['avg_salary_clean'] = hist_df['average_salary'].map(parse_decimal)
            hist_df = hist_df.dropna(subset=['month_clean', 'avg_salary_clean'])
            
            existing_months = set(
                APISalaryHistory.objects.filter(country=country, category=it_tag)
                .values_list('month', flat=True)
            )
            hist_df = hist_df[~hist_df['month_clean'].isin(existing_months)]
            
            if hist_df.empty:
                return
                
            # Drop original columns before renaming to prevent duplicate column names
            hist_df = hist_df.drop(columns=['month', 'average_salary']).rename(columns={'month_clean': 'month', 'avg_salary_clean': 'average_salary'})
            hist_df['country'] = country
            hist_df['category'] = it_tag
            hist_df['category_ref'] = category_ref
            hist_df['location'] = None
            
            hist_records = [
                APISalaryHistory(**row)
                for row in clean_records(hist_df, ['country', 'location', 'category', 'month', 'category_ref', 'average_salary'])
            ]
            APISalaryHistory.objects.bulk_create(hist_records, ignore_conflicts=True)
            self.histories_created += len(hist_records)
        except Exception as e:
            logger.error(f"Error occurred during Salary History fetch for {country}: {e}", exc_info=True)

    def ingest_country_salary_histogram(self, country: str) -> None:
        """Fetch salary vacancy distributions and save them to APISalaryHistogram."""
        try:
            histogram_res = self.client.fetch_salary_histogram(country=country, what="data engineer")
            if not histogram_res:
                return
            hist_data = histogram_res.get('histogram', {})
            if not hist_data:
                return
                
            histogram_df = pd.DataFrame(list(hist_data.items()), columns=['bracket', 'vacancy'])
            histogram_df['bracket_dec'] = histogram_df['bracket'].map(parse_decimal)
            histogram_df['val_int'] = histogram_df['vacancy'].map(parse_int)
            histogram_df = histogram_df.dropna(subset=['bracket_dec', 'val_int'])
            
            existing_brackets = set(
                APISalaryHistogram.objects.filter(country=country, what="data engineer")
                .values_list('salary_bracket', flat=True)
            )
            histogram_df = histogram_df[~histogram_df['bracket_dec'].isin(existing_brackets)]
            
            if histogram_df.empty:
                return
                
            histogram_df = histogram_df.rename(columns={'bracket_dec': 'salary_bracket', 'val_int': 'vacancy_count'})
            histogram_df['country'] = country
            histogram_df['location'] = None
            histogram_df['what'] = "data engineer"
            
            histogram_records = [
                APISalaryHistogram(**row)
                for row in clean_records(histogram_df, ['country', 'location', 'what', 'salary_bracket', 'vacancy_count'])
            ]
            APISalaryHistogram.objects.bulk_create(histogram_records, ignore_conflicts=True)
            self.histograms_created += len(histogram_records)
        except Exception as e:
            logger.error(f"Error occurred during Salary Histogram fetch for {country}: {e}", exc_info=True)

    def ingest_country_top_companies(self, country: str) -> None:
        """Fetch top hiring companies standings and save them to APITopCompany."""
        try:
            top_comps = self.client.fetch_top_companies(country=country, what="data engineer")
            if not top_comps:
                return
                
            top_df = pd.DataFrame(top_comps)
            top_df['comp_name_clean'] = top_df.get('canonical_name', pd.Series(dtype=str, index=top_df.index)).map(lambda x: parse_str(x, 255))
            top_df['comp_count_clean'] = top_df.get('count', pd.Series(dtype=str, index=top_df.index)).map(parse_int)
            top_df['comp_sal_clean'] = top_df.get('average_salary', pd.Series(dtype=str, index=top_df.index)).map(parse_decimal)
            
            top_df = top_df.dropna(subset=['comp_name_clean', 'comp_count_clean'])
            
            if top_df.empty:
                return
                
            unique_top_companies = top_df['comp_name_clean'].dropna().unique()
            company_name_to_id = {}
            if len(unique_top_companies) > 0:
                company_name_to_id = resolve_company_ids(unique_top_companies)
                companies_df = pd.DataFrame({'name': unique_top_companies})
                companies_df['company_id'] = companies_df['name'].map(lambda x: company_name_to_id.get(x.lower()))
                companies_df = companies_df.drop_duplicates(subset=['company_id'])
                companies_df['data_source'] = 'API'
                
                companies_to_upsert = [Company(**row) for row in clean_records(companies_df)]
                Company.objects.bulk_create(
                    companies_to_upsert,
                    update_conflicts=True,
                    update_fields=['name', 'data_source'],
                    unique_fields=['company_id']
                )
                self.companies_created += len(companies_to_upsert)
                
            company_objs = {co.name.lower().strip(): co for co in Company.objects.filter(name__in=unique_top_companies)}
            
            existing_entries = set(
                APITopCompany.objects.filter(country=country, what="data engineer", company_name__in=list(unique_top_companies))
                .values_list('company_name', flat=True)
            )
            top_df = top_df[~top_df['comp_name_clean'].isin(existing_entries)]
            
            if top_df.empty:
                return
                
            top_df['company_id_resolved'] = top_df['comp_name_clean'].map(lambda name: company_objs.get(name.lower()))
            
            # Drop original columns before renaming to prevent duplicate column names
            cols_to_drop = [col for col in ['company_name', 'company', 'vacancy_count', 'average_salary'] if col in top_df.columns]
            top_df = top_df.drop(columns=cols_to_drop).rename(columns={
                'comp_name_clean': 'company_name',
                'company_id_resolved': 'company',
                'comp_count_clean': 'vacancy_count',
                'comp_sal_clean': 'average_salary'
            })
            top_df['country'] = country
            top_df['what'] = "data engineer"
            
            top_records = [
                APITopCompany(**row)
                for row in clean_records(top_df, ['country', 'what', 'company_name', 'company', 'vacancy_count', 'average_salary'])
            ]
            APITopCompany.objects.bulk_create(top_records, ignore_conflicts=True)
            self.top_companies_created += len(top_records)
        except Exception as e:
            logger.error(f"Error occurred during Top Companies fetch for {country}: {e}", exc_info=True)

    def ingest_jobsworth_prediction(self) -> None:
        """Fetch Jobsworth salary prediction test sample."""
        try:
            test_title = "Data Engineer"
            test_desc = "Python, SQL, Apache Spark, ETL pipeline developer"
            prediction_res = self.client.fetch_salary_prediction(country="gb", title=test_title, description=test_desc)
            if not prediction_res:
                return
            pred_sal = parse_decimal(prediction_res.get('salary'))
            if pred_sal:
                APISalaryPrediction.objects.get_or_create(
                    title=test_title,
                    description=test_desc,
                    defaults={'predicted_salary': pred_sal}
                )
                logger.info(f"Jobsworth Prediction: Title='{test_title}' => Salary={pred_sal}")
        except Exception as e:
            logger.error(f"Error occurred during Jobsworth prediction: {e}", exc_info=True)


# ---------------------------------------------------------
# Celery Cron Job Task Definition
# ---------------------------------------------------------
@shared_task(name="core.tasks.run_etl_pipeline")
def run_etl_pipeline() -> None:
    """Shared Celery Beat Task to run ETL once a month."""
    pipeline = CSVETLPipeline()
    pipeline.run()


# ---------------------------------------------------------
# Adzuna API Daily Ingestion Task
# ---------------------------------------------------------
@shared_task(name="core.tasks.run_adzuna_ingestion")
def run_adzuna_ingestion() -> None:
    """Shared Celery Beat Task to run Adzuna API ingestion daily at 1:00 AM."""
    from integration.adzuna.client import AdzunaClient
    client = AdzunaClient()
    pipeline = AdzunaAPIIngestionPipeline(client)
    pipeline.run()
