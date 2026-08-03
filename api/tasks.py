# cameras/tasks.py
import logging
import requests
from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone

from .models import Camera, CameraCapture
from .services import capture_snapshot, HikConnectError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def capture_camera_snapshot(self, camera_id: int):
    try:
        camera = Camera.objects.get(id=camera_id, is_active=True)
    except Camera.DoesNotExist:
        return

    try:
        capture_url = capture_snapshot(camera.device_serial, camera.channel_no)
        image_resp = requests.get(capture_url, timeout=15)
        image_resp.raise_for_status()
    except (HikConnectError, requests.RequestException) as exc:
        logger.warning(f"Snapshot failed for {camera.device_serial}: {exc}")
        raise self.retry(exc=exc)

    filename = f"{camera.device_serial}_{timezone.now():%Y%m%d%H%M%S}.jpg"
    CameraCapture.objects.create(
        camera=camera,
        image=ContentFile(image_resp.content, name=filename),
    )


@shared_task
def capture_all_camera_snapshots():
    camera_ids = Camera.objects.filter(is_active=True).values_list("id", flat=True)
    for camera_id in camera_ids:
        capture_camera_snapshot.delay(camera_id)