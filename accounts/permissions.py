from django.contrib.auth.decorators import user_passes_test


def in_groups(group_names):
    def _check(user):
        return user.is_authenticated and (
            user.is_superuser
            or user.groups.filter(name__in=group_names).exists()
        )

    return user_passes_test(_check)
