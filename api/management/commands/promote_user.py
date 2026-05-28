from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Promote a normal user to admin role. Public registration cannot create admin users."

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, help="Email of the user to promote")
        parser.add_argument("--username", type=str, help="Username of the user to promote")
        parser.add_argument(
            "--superuser",
            action="store_true",
            help="Also grant Django superuser privileges (admin site full permissions)",
        )

    def handle(self, *args, **options):
        email = options.get("email")
        username = options.get("username")
        upgrade_superuser = options.get("superuser", False)

        if bool(email) == bool(username):
            raise CommandError("Provide exactly one of --email or --username.")

        User = get_user_model()

        lookup = {"email": email} if email else {"username": username}
        try:
            user = User.objects.get(**lookup)
        except User.DoesNotExist as exc:
            field, value = next(iter(lookup.items()))
            raise CommandError(f"User not found by {field}={value!r}.") from exc

        before_role = user.role
        before_is_superuser = user.is_superuser

        update_fields = ["role", "updated_at"]
        user.role = "admin"

        if upgrade_superuser and not user.is_superuser:
            user.is_superuser = True
            update_fields.append("is_superuser")

        user.save(update_fields=update_fields)

        self.stdout.write(
            self.style.SUCCESS(
                f"Promoted user id={user.id}, email={user.email}, username={user.username} "
                f"role: {before_role} -> {user.role}, "
                f"is_superuser: {before_is_superuser} -> {user.is_superuser}"
            )
        )

