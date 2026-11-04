import os
import subprocess
import zipfile
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Downloads and extracts media.zip from Google Drive into /app/media"

    def handle(self, *args, **options):
        file_id = "1hFMU86AvlSRukbTUbAZspLVD9_huz75w"
        dest_zip = "/app/media.zip"

        self.stdout.write("Step 1: Installing gdown...")
        try:
            import gdown
        except ImportError:
            subprocess.check_call(["pip", "install", "gdown"])
            import gdown

        self.stdout.write("Step 2: Downloading media.zip from Google Drive (4.6 GB)...")
        url = f"https://drive.google.com/uc?id={file_id}"
        output = gdown.download(url, dest_zip, quiet=False)
        if not output or not os.path.exists(dest_zip):
            self.stdout.write(self.style.ERROR("Download failed!"))
            return

        self.stdout.write("Step 3: Extracting files into volume...")
        with zipfile.ZipFile(dest_zip, "r") as z:
            namelist = z.namelist()
            target = "/app" if any(n.startswith("media/") for n in namelist) else "/app/media"
            z.extractall(target)

        if os.path.exists(dest_zip):
            os.remove(dest_zip)

        self.stdout.write(self.style.SUCCESS("All media files (videos, flipbooks, audios) successfully extracted!"))
