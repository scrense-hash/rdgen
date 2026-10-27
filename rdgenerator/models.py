from django.db import models

class GithubRun(models.Model):
    id = models.IntegerField(verbose_name="ID",primary_key=True)
    uuid = models.CharField(verbose_name="uuid", max_length=100)
    status = models.CharField(verbose_name="status", max_length=100)
    github_run_id = models.BigIntegerField(null=True, blank=True)
    # Build targets requested for this run, stored so the status page can
    # offer download links only for what was actually asked for.
    formats = models.CharField(verbose_name="formats", max_length=200, blank=True, default='')
    arches = models.CharField(verbose_name="arches", max_length=200, blank=True, default='')
