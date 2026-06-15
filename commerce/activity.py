from .models import ActivityLog


def registrar(user, action, detail="", request=None):
    ip = None
    if request:
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = x_forwarded.split(",")[0] if x_forwarded else request.META.get("REMOTE_ADDR")
    ActivityLog.objects.create(user=user, action=action, detail=detail, ip=ip)
    