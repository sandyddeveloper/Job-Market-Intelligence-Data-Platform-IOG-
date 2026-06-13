from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, parsers
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from api.v1.user.serializer import (
    UserLoginSerializer, TokenResponseSerializer,
    JobPostSerializer, ResumeUploadSerializer
)

class UserLoginView(APIView):
    """
    Endpoint for user authentication.
    Returns a JWT Bearer token upon successful verification of credentials.
    """
    serializer_class = UserLoginSerializer

    @extend_schema(
        summary="User Authentication",
        description="Verify credentials and generate a JSON Web Token (JWT) for secure requests.",
        request=UserLoginSerializer,
        responses={
            200: TokenResponseSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Auth Response",
                value={
                    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "user_id": 42,
                    "email": "admin@jobmarketintelligence.com",
                    "expires_in": 3600
                },
                response_only=True
            ),
            OpenApiExample(
                "Invalid Credentials Response",
                value={"error": "Invalid email or password."},
                status_codes=[401],
                response_only=True
            )
        ],
        tags=["Authentication"]
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get("email")
            password = serializer.validated_data.get("password")
            if email == "admin@jobmarketintelligence.com":
                return Response({
                    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo0MiwidXNlcm5hbWUiOiJhZG1pbiJ9.mock_signature",
                    "user_id": 42,
                    "email": email,
                    "expires_in": 3600
                }, status=status.HTTP_200_OK)
            return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class JobPostListView(APIView):
    """
    Search and browse Job Postings indexed on the platform.
    """
    
    @extend_schema(
        summary="List Job Postings",
        description="Query the index of jobs with search terms, location filters, and minimum salary estimates.",
        parameters=[
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="General search query for matching title, description or company.",
                required=False
            ),
            OpenApiParameter(
                name="location",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter listings by location (e.g. 'New York', 'Remote', 'London').",
                required=False
            ),
            OpenApiParameter(
                name="min_salary",
                type=OpenApiTypes.DECIMAL,
                location=OpenApiParameter.QUERY,
                description="Minimum salary threshold for returned job listings.",
                required=False
            ),
            OpenApiParameter(
                name="X-Client-Version",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                description="Optional header stating client build version (e.g., 'v1.2.0').",
                required=False
            )
        ],
        responses={
            200: JobPostSerializer(many=True),
            400: OpenApiTypes.OBJECT
        },
        tags=["Job Postings"]
    )
    def get(self, request, *args, **kwargs):
        # Static mock database
        mock_jobs = [
            {
                "id": 101,
                "title": "Senior Machine Learning Engineer",
                "company": "Cognitive Nexus Inc.",
                "location": "Remote",
                "description": "We are seeking a senior engineer to deploy deep learning models to production.",
                "skills_required": ["Python", "PyTorch", "Transformers", "Docker"],
                "salary_range": {
                    "min_salary": 140000.00,
                    "max_salary": 195000.00,
                    "currency": "USD"
                },
                "created_at": "2026-06-12T14:32:00Z"
            },
            {
                "id": 102,
                "title": "Lead Job Analyst",
                "company": "LaborStat Analytics",
                "location": "New York, NY",
                "description": "Analyze macro-economic trends and job market supply chain data.",
                "skills_required": ["SQL", "Pandas", "Tableau", "Econometrics"],
                "salary_range": {
                    "min_salary": 110000.00,
                    "max_salary": 145000.00,
                    "currency": "USD"
                },
                "created_at": "2026-06-13T09:15:00Z"
            }
        ]
        
        q = request.query_params.get("q")
        location = request.query_params.get("location")
        min_salary = request.query_params.get("min_salary")
        
        filtered_jobs = mock_jobs
        if q:
            filtered_jobs = [j for j in filtered_jobs if q.lower() in j["title"].lower() or q.lower() in j["company"].lower()]
        if location:
            filtered_jobs = [j for j in filtered_jobs if location.lower() in j["location"].lower()]
        if min_salary:
            try:
                min_sal_val = float(min_salary)
                filtered_jobs = [j for j in filtered_jobs if float(j["salary_range"]["min_salary"]) >= min_sal_val]
            except ValueError:
                return Response({"error": "Invalid min_salary query parameter value."}, status=status.HTTP_400_BAD_REQUEST)
                
        return Response(filtered_jobs, status=status.HTTP_200_OK)

class ResumeUploadView(APIView):
    """
    Upload resume file and trigger analysis pipelines.
    Uses Multipart parsing.
    """
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)
    serializer_class = ResumeUploadSerializer

    @extend_schema(
        summary="Upload and Parse Resume",
        description=(
            "Accepts a binary document (PDF/DOCX/TXT), parses text, and "
            "uses Named Entity Recognition (NER) models to extract skill entities, education background, and job history."
        ),
        request=ResumeUploadSerializer,
        responses={
            201: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            415: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Successful Extraction Response",
                value={
                    "status": "success",
                    "filename": "john_doe_resume.pdf",
                    "parsed_data": {
                        "candidate_name": "John Doe",
                        "detected_skills": ["Python", "Django", "PostgreSQL", "REST APIs", "AWS"],
                        "highest_degree": "Master of Science in Computer Science",
                        "institutions": ["Stanford University"],
                        "confidence_score": 0.94
                    }
                },
                status_codes=[201],
                response_only=True
            ),
            OpenApiExample(
                "Unsupported File Type",
                value={"error": "Unsupported Media Type. Only PDF, DOCX, and TXT files are accepted."},
                status_codes=[415],
                response_only=True
            )
        ],
        tags=["Resume Analytics"]
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            resume_file = serializer.validated_data.get("resume_file")
            
            filename = resume_file.name
            if not filename.endswith(('.pdf', '.docx', '.txt')):
                return Response(
                    {"error": "Unsupported Media Type. Only PDF, DOCX, and TXT files are accepted."},
                    status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
                )
                
            return Response({
                "status": "success",
                "filename": filename,
                "parsed_data": {
                    "candidate_name": "John Doe",
                    "detected_skills": ["Python", "Django", "PostgreSQL", "REST APIs", "AWS"] if serializer.validated_data.get("extract_skills") else [],
                    "highest_degree": "Master of Science in Computer Science" if serializer.validated_data.get("extract_education") else "Not requested",
                    "institutions": ["Stanford University"] if serializer.validated_data.get("extract_education") else [],
                    "confidence_score": 0.94
                }
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
