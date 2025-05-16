import logging
import sys

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Import after setting up logging
import customtkinter as ctk

from brainscape_to_anki.application.services.export_service import ExportService
from brainscape_to_anki.application.services.scraper_service import ScraperService
from brainscape_to_anki.application.use_cases.scrape_to_anki import ScrapeToAnkiUseCase
from brainscape_to_anki.infrastructure.exporters.anki_exporter import AnkiExporter
from brainscape_to_anki.infrastructure.scrapers.brainscape_scraper import BrainscapeScraper
from brainscape_to_anki.presentation.gui.main_window import MainWindow

import os
import sys

logger = logging.getLogger(__name__)


def check_package_structure():
    """Verify all necessary directories and files exist."""
    required_dirs = [
        'brainscape_to_anki',
        'brainscape_to_anki/domain',
        'brainscape_to_anki/domain/interfaces',
        'brainscape_to_anki/domain/models',
        'brainscape_to_anki/application',
        'brainscape_to_anki/application/services',
        'brainscape_to_anki/application/use_cases',
        'brainscape_to_anki/infrastructure',
        'brainscape_to_anki/infrastructure/scrapers',
        'brainscape_to_anki/infrastructure/exporters',
        'brainscape_to_anki/presentation',
        'brainscape_to_anki/presentation/gui',
        'brainscape_to_anki/presentation/gui/components',
    ]

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logger.info(f"Checking package structure in: {base_dir}")

    missing_dirs = []
    for directory in required_dirs:
        dir_path = os.path.join(base_dir, *directory.split('/'))
        if not os.path.isdir(dir_path):
            missing_dirs.append(directory)

    required_init_files = [f"{d}/__init__.py" for d in required_dirs]

    missing_inits = []
    for init_file in required_init_files:
        file_path = os.path.join(base_dir, *init_file.split('/'))
        if not os.path.isfile(file_path):
            missing_inits.append(init_file)

    if missing_dirs or missing_inits:
        logger.error("Missing required directories or __init__.py files:")
        for d in missing_dirs:
            logger.error(f"- Missing directory: {d}")
        for f in missing_inits:
            logger.error(f"- Missing file: {f}")
        logger.error("\nPlease create these directories and files before running the application.")
        sys.exit(1)

    logger.info("Package structure check passed!")


def setup_dependency_injection():
    logger.info("Setting up dependency injection...")
    scraper = BrainscapeScraper()
    exporter = AnkiExporter()

    scraper_service = ScraperService(scraper)
    export_service = ExportService(exporter)

    use_case = ScrapeToAnkiUseCase(scraper_service, export_service)
    logger.info("Dependency injection complete")

    return use_case


def main():
    try:
        logger.info("Starting Brainscape to Anki Converter application")

        # Verify package structure first
        check_package_structure()

        # Setup dependencies
        use_case = setup_dependency_injection()

        # Configure customtkinter
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Start the application
        logger.info("Initializing main window...")
        app = MainWindow(use_case)
        logger.info("Starting main event loop...")
        app.mainloop()
    except Exception as e:
        logger.exception(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()