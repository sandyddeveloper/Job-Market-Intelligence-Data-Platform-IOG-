import re
from decimal import Decimal
import pandas as pd

class JobDataProcessor:
    """Class encapsulating validation, parsing, calculations, and data enrichment helpers."""

    COUNTRY_CURRENCY_MAP = {
        'us': 'USD', 'gb': 'GBP', 'de': 'EUR', 'fr': 'EUR', 'at': 'EUR', 'it': 'EUR', 'es': 'EUR', 
        'nl': 'EUR', 'be': 'EUR', 'ie': 'EUR', 'ch': 'CHF', 'ca': 'CAD', 'au': 'AUD', 'nz': 'NZD', 
        'in': 'INR', 'pl': 'PLN', 'br': 'BRL', 'za': 'ZAR', 'ru': 'RUB', 'mx': 'MXN', 'sg': 'SGD', 
        'my': 'MYR'
    }

    CURRENCY_TO_USD = {
        'USD': Decimal('1.0'),
        'GBP': Decimal('1.25'),
        'EUR': Decimal('1.08'),
        'CHF': Decimal('1.12'),
        'CAD': Decimal('0.73'),
        'AUD': Decimal('0.66'),
        'NZD': Decimal('0.61'),
        'INR': Decimal('0.012'),
        'PLN': Decimal('0.25'),
        'BRL': Decimal('0.19'),
        'ZAR': Decimal('0.054'),
        'RUB': Decimal('0.011'),
        'MXN': Decimal('0.058'),
        'SGD': Decimal('0.74'),
        'MYR': Decimal('0.21')
    }

    @staticmethod
    def parse_str(val, max_length=None):
        if val is None or pd.isna(val):
            return None
        val_stripped = str(val).strip()
        if val_stripped.lower() in ('nan', 'null', 'none', ''):
            return None
        if max_length is not None:
            return val_stripped[:max_length]
        return val_stripped

    @staticmethod
    def parse_int(val):
        clean_val = JobDataProcessor.parse_str(val)
        if clean_val is None:
            return None
        try:
            return int(float(clean_val))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def parse_decimal(val):
        clean_val = JobDataProcessor.parse_str(val)
        if clean_val is None:
            return None
        try:
            return Decimal(clean_val)
        except (ValueError, TypeError, Exception):
            return None

    @staticmethod
    def parse_bool(val):
        clean_val = JobDataProcessor.parse_str(val)
        if clean_val is None:
            return None
        return clean_val.lower() in ('true', '1', 'yes', 'y', 't')

    @staticmethod
    def clean_html_text(raw_text):
        if not raw_text:
            return ""
        clean = re.sub(r'<[^>]*>', ' ', raw_text)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()

    @staticmethod
    def infer_remote_allowed(title, description):
        text = f"{title or ''} {description or ''}".lower()
        remote_keywords = ['remote', 'work from home', 'wfh', 'telecommute', 'work-from-home']
        for kw in remote_keywords:
            if kw in text:
                return True
        return False

    @staticmethod
    def infer_work_type(title, description):
        text = f"{title or ''} {description or ''}".lower()
        if 'contract' in text or 'temporary' in text or 'temp' in text or 'freelance' in text or 'consultant' in text:
            return 'CONTRACT', 'Contract'
        elif 'part time' in text or 'part-time' in text or 'parttime' in text:
            return 'PART_TIME', 'Part-time'
        elif 'intern' in text or 'internship' in text or 'placement' in text or 'co-op' in text:
            return 'OTHER', 'Internship'
        else:
            return 'FULL_TIME', 'Full-time'

    @staticmethod
    def infer_experience_level(title, description):
        text = f"{title or ''} {description or ''}".lower()
        exec_keywords = ['director', 'vice president', 'vp', 'executive', 'chief', 'head of', 'cto', 'cio', 'cfo', 'ceo']
        sr_keywords = ['senior', 'sr', 'lead', 'principal', 'architect', 'manager']
        entry_keywords = ['junior', 'jr', 'entry', 'intern', 'fresher', 'graduate', 'trainee', 'apprentice']
        
        for kw in exec_keywords:
            if kw in text:
                return 'Executive'
        for kw in sr_keywords:
            if kw in text:
                return 'Mid-Senior level'
        for kw in entry_keywords:
            if kw in text:
                return 'Entry level'
        return 'Associate'

    @staticmethod
    def generate_deterministic_id(value):
        if not value:
            return None
        import hashlib
        return int(hashlib.md5(str(value).lower().strip().encode('utf-8')).hexdigest(), 16) & ((1 << 63) - 1)

    @staticmethod
    def calculate_average_salary(min_sal, max_sal):
        min_sal = JobDataProcessor.parse_decimal(min_sal)
        max_sal = JobDataProcessor.parse_decimal(max_sal)
        if min_sal is not None and max_sal is not None:
            return (min_sal + max_sal) / 2
        elif min_sal is not None:
            return min_sal
        elif max_sal is not None:
            return max_sal
        return None

    @staticmethod
    def normalize_api_salary(country, salary_val):
        val = JobDataProcessor.parse_decimal(salary_val)
        if not val or val <= 0:
            return None, None
            
        currency = JobDataProcessor.COUNTRY_CURRENCY_MAP.get(country.lower(), 'USD')
        
        if val < 200:
            val = val * 2000
        elif currency in ['USD', 'GBP', 'EUR', 'CHF', 'CAD', 'AUD', 'NZD', 'SGD'] and val < 8000:
            val = val * 12
            
        rate = JobDataProcessor.CURRENCY_TO_USD.get(currency, Decimal('1.0'))
        normalized_val = val * rate
        return currency, normalized_val
