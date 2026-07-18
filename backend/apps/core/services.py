from apps.core.models import ActionLog


def log_action(user, action, details=''):
  ActionLog.objects.create(user=user, action=action, details=details)
