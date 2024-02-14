
from django.contrib.auth.decorators import user_passes_test
from base import models


def manager_only_check(user: models.User) -> bool:
    return user.is_staff # type: ignore

manager_only = user_passes_test(manager_only_check)

