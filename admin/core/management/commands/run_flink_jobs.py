"""Django Management Command: run_flink_jobs.

VIBE COMPLIANT - Django pattern for Flink job submission.
Submits PyFlink SQL jobs to cluster.

Usage:
    python manage.py run_flink_jobs
    python manage.py run_flink_jobs --job=agent_act_aggregation
    python manage.py run_flink_jobs --list
"""

import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Submit Flink jobs to cluster."""

    help = "Submit Flink SQL jobs to cluster for stream processing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--job",
            type=str,
            default=None,
            help="Specific job to submit (default: all)",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="List available jobs",
        )
        parser.add_argument(
            "--flink-url",
            type=str,
            default="http://localhost:8081",
            help="Flink JobManager URL",
        )

    def handle(self, *args, **options):
        if options["list"]:
            self._list_jobs()
            return

        job_name = options["job"]
        flink_url = options["flink_url"]

        if job_name:
            self._submit_job(job_name, flink_url)
        else:
            self._submit_all_jobs(flink_url)

    def _list_jobs(self):
        """List available Flink jobs."""
        from admin.flink.somabrain_jobs import FLINK_JOBS

        self.stdout.write(self.style.SUCCESS("Available Flink jobs:"))
        for name, config in FLINK_JOBS.items():
            self.stdout.write(f"  - {name}: {config.get('description', 'No description')}")

    def _submit_job(self, job_name: str, flink_url: str):
        """Submit a single Flink job."""
        from admin.flink.somabrain_jobs import FLINK_JOBS, submit_job

        if job_name not in FLINK_JOBS:
            self.stdout.write(self.style.ERROR(f"Job '{job_name}' not found"))
            return

        self.stdout.write(f"Submitting job: {job_name} to {flink_url}")

        try:
            result = submit_job(job_name, flink_url)
            self.stdout.write(self.style.SUCCESS(f"Job submitted: {result}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to submit job: {e}"))

    def _submit_all_jobs(self, flink_url: str):
        """Submit all Flink jobs."""
        from admin.flink.somabrain_jobs import FLINK_JOBS, submit_job

        self.stdout.write(f"Submitting all jobs to {flink_url}")

        for job_name in FLINK_JOBS:
            try:
                result = submit_job(job_name, flink_url)
                self.stdout.write(self.style.SUCCESS(f"  ✓ {job_name}: {result}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ {job_name}: {e}"))
