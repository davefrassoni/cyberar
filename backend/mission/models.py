import uuid
from django.db import models
from django.utils import timezone


class DemoScenario(models.Model):
    name = models.CharField(max_length=80, default="Operación Atlántico")
    version = models.PositiveIntegerField(default=1)
    duration = models.PositiveIntegerField(default=150)
    configuration = models.JSONField(default=dict)
    scenario_key = models.CharField(max_length=32, default="atlantic")
    fleet_size = models.PositiveSmallIntegerField(default=1)

    class Meta:
        constraints = [models.CheckConstraint(check=models.Q(fleet_size__gte=1) & models.Q(fleet_size__lte=3), name="fleet_size_range")]


class Mission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner_session = models.CharField(max_length=40, db_index=True)
    scenario = models.ForeignKey(DemoScenario, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class MissionState(models.Model):
    mission = models.OneToOneField(Mission, on_delete=models.CASCADE, related_name="live")
    state = models.JSONField(default=dict)
    running = models.BooleanField(default=False, db_index=True)
    speed = models.PositiveSmallIntegerField(default=1)
    revision = models.PositiveIntegerField(default=0)
    generation = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)


class TelemetrySnapshot(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    elapsed = models.PositiveIntegerField()
    data = models.JSONField()


class CommunicationSnapshot(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    elapsed = models.PositiveIntegerField()
    data = models.JSONField()


class MissionEvent(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    sequence = models.PositiveIntegerField()
    elapsed = models.PositiveIntegerField()
    kind = models.CharField(max_length=24)
    message = models.CharField(max_length=240)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["mission", "sequence"], name="unique_mission_event")]


class RateLimit(models.Model):
    key = models.CharField(max_length=100, primary_key=True)
    window = models.BigIntegerField(default=0)
    count = models.PositiveIntegerField(default=0)


class AIFlight(models.Model):
    """One durable broker slot for this producer, including ambiguous timeouts."""
    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    generation = models.PositiveIntegerField()
    incident = models.PositiveIntegerField()
    key = models.CharField(max_length=160)
    job_id = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=16, default="PENDING")
    snapshot = models.JSONField(default=dict)
    attempts = models.PositiveIntegerField(default=0)
    next_attempt = models.DateTimeField(default=timezone.now)


class DebriefFlight(models.Model):
    """Segundo slot de vuelo único: análisis de debriefing posterior a la misión, separado de AIFlight."""
    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    generation = models.PositiveIntegerField()
    key = models.CharField(max_length=160)
    job_id = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=16, default="PENDING")
    snapshot = models.JSONField(default=dict)
    result = models.JSONField(null=True, blank=True)
    source = models.CharField(max_length=8, default="LOCAL")
    attempts = models.PositiveIntegerField(default=0)
    next_attempt = models.DateTimeField(default=timezone.now)
    requested_at = models.DateTimeField(null=True, blank=True)
