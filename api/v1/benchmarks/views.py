from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Avg
from apps.benchmarks.models import (
    DataScienceSalaryBenchmark, DataAnalystBenchmark,
    APISalaryHistory, APISalaryHistogram, APITopCompany
)
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

class DataScienceBenchmarkTrendsView(APIView):
    """
    Get Data Science Salary Benchmark trends grouped by work year and experience level.
    """
    @extend_schema(
        summary="Data Science Salary Trends",
        description="Fetch average salaries in USD over years grouped by experience level.",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Salary Benchmarks"]
    )
    def get(self, request, *args, **kwargs):
        trends = list(
            DataScienceSalaryBenchmark.objects.values('work_year', 'experience_level')
            .annotate(avg_salary_usd=Avg('salary_in_usd'), count=Count('id'))
            .order_by('work_year', 'experience_level')
        )
        return Response(trends, status=status.HTTP_200_OK)

class DataAnalystBenchmarkStatsView(APIView):
    """
    Get Data Analyst Benchmark statistics grouped by sector.
    """
    @extend_schema(
        summary="Data Analyst Stats by Sector",
        description="Fetch average rating and count of analyst jobs grouped by sector.",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Salary Benchmarks"]
    )
    def get(self, request, *args, **kwargs):
        stats = list(
            DataAnalystBenchmark.objects.values('sector')
            .exclude(sector__in=['-1', 'Unknown', 'nan', None, ''])
            .annotate(avg_rating=Avg('rating'), count=Count('id'))
            .order_by('-count')[:15]
        )
        return Response(stats, status=status.HTTP_200_OK)

class APISalaryHistoryView(APIView):
    """
    Get MoM average salary history from Adzuna daily history recordings.
    """
    @extend_schema(
        summary="Adzuna MoM Salary History",
        description="Fetch MoM average salaries by country.",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Salary Benchmarks"]
    )
    def get(self, request, *args, **kwargs):
        country = request.query_params.get("country", "gb")
        history = list(
            APISalaryHistory.objects.filter(country=country)
            .values('month', 'category')
            .annotate(avg_salary=Avg('average_salary'))
            .order_by('month')
        )
        return Response(history, status=status.HTTP_200_OK)

class APISalaryHistogramView(APIView):
    """
    Get vacancies distribution per salary bracket from Adzuna daily recordings.
    """
    @extend_schema(
        summary="Adzuna Salary Bracket Histogram",
        description="Fetch vacancy count per salary bracket for a specific country.",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Salary Benchmarks"]
    )
    def get(self, request, *args, **kwargs):
        country = request.query_params.get("country", "gb")
        histogram = list(
            APISalaryHistogram.objects.filter(country=country)
            .values('salary_bracket')
            .annotate(vacancy_count=Avg('vacancy_count'))
            .order_by('salary_bracket')
        )
        return Response(histogram, status=status.HTTP_200_OK)

class APITopCompanyStandingsView(APIView):
    """
    Get Top Hiring Companies standings from Adzuna daily standings.
    """
    @extend_schema(
        summary="Adzuna Top Hiring Companies",
        description="Fetch list of top companies by vacancy count and average salary.",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Salary Benchmarks"]
    )
    def get(self, request, *args, **kwargs):
        country = request.query_params.get("country", "gb")
        standings = list(
            APITopCompany.objects.filter(country=country)
            .values('company_name', 'vacancy_count', 'average_salary')
            .order_by('-vacancy_count')[:15]
        )
        return Response(standings, status=status.HTTP_200_OK)
