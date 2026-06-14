from rest_framework import serializers
from apps.jobs.models import Industry, Skill, JobPosting
from apps.company.models import Company

class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = ['industry_id', 'industry_name']

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['skill_abr', 'skill_name']

class CompanySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['company_id', 'name', 'company_size', 'state', 'country', 'city', 'url']

class JobPostingSerializer(serializers.ModelSerializer):
    company = CompanySimpleSerializer(read_only=True)
    industries = IndustrySerializer(many=True, read_only=True)
    skills = SkillSerializer(many=True, read_only=True)

    class Meta:
        model = JobPosting
        fields = [
            'job_id', 'company', 'company_name', 'title', 'description',
            'min_salary', 'max_salary', 'med_salary', 'pay_period', 'location',
            'views', 'applies', 'original_listed_time', 'listed_time', 'expiry',
            'closed_time', 'remote_allowed', 'job_posting_url', 'application_url',
            'application_type', 'formatted_work_type', 'work_type',
            'formatted_experience_level', 'skills_desc', 'posting_domain',
            'sponsored', 'currency', 'compensation_type', 'normalized_salary',
            'zip_code', 'fips', 'data_source', 'industries', 'skills'
        ]
