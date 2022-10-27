import os
from django.core.management.base import BaseCommand
from bot import main


class Command(BaseCommand):
    help = 'This command runs telegram bot'

    def handle(self, *args, **options):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'uniar_bot.settings'
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

        main()
