from rest_framework import serializers

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="The corporate email address of the user.",
        default="admin@jobmarketintelligence.com"
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="The secure password of the user."
    )

class TokenResponseSerializer(serializers.Serializer):
    token = serializers.CharField(help_text="JWT Authorization token to be used in Bearer Auth header.")
    user_id = serializers.IntegerField(help_text="Unique database ID of the logged in user.")
    email = serializers.EmailField(help_text="The email address associated with the account.")
    expires_in = serializers.IntegerField(default=3600, help_text="Token expiration duration in seconds.")

class SalaryRangeSerializer(serializers.Serializer):
    min_salary = serializers.DecimalField(
        max_digits=12, decimal_places=2, help_text="Minimum estimated salary (e.g. 80000.00)"
    )
    max_salary = serializers.DecimalField(
        max_digits=12, decimal_places=2, help_text="Maximum estimated salary (e.g. 120000.00)"
    )
    currency = serializers.CharField(max_length=3, default="USD", help_text="Three-letter ISO currency code.")

class JobPostSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="Unique auto-generated ID of the job posting.")
    title = serializers.CharField(max_length=255, help_text="Title of the job role (e.g. Senior Machine Learning Engineer).")
    company = serializers.CharField(max_length=255, help_text="Company offering the position.")
    location = serializers.CharField(max_length=255, help_text="Geographical location or 'Remote'.")
    description = serializers.CharField(help_text="Full markdown-formatted description of the job profile and requirements.")
    skills_required = serializers.ListField(
        child=serializers.CharField(max_length=100),
        help_text="List of key technical or soft skills required."
    )
    salary_range = SalaryRangeSerializer(help_text="Estimated compensation details.")
    created_at = serializers.DateTimeField(read_only=True, help_text="Timestamp when this job posting was indexed.")

class ResumeUploadSerializer(serializers.Serializer):
    resume_file = serializers.FileField(
        help_text="The resume file in PDF, DOCX, or text format to be uploaded and parsed."
    )
    extract_skills = serializers.BooleanField(
        default=True,
        help_text="Whether to execute the skills extraction pipeline on the uploaded document."
    )
    extract_education = serializers.BooleanField(
        default=True,
        help_text="Whether to extract academic histories and degrees."
    )
