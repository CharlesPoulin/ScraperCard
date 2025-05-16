# Brainscape to Anki Converter

A Python application that scrapes flashcards from Brainscape websites and converts them to Anki format (.csv).

## Features

- Scrape flashcards from Brainscape decks
- Convert to Anki-compatible CSV format
- Drag and drop multiple Brainscape links
- Simple and intuitive GUI
- One CSV file generated per link

## Requirements

- Python 3.10 or higher
- Poetry for dependency management

## Installation

1. Clone this repository
2. Install dependencies with Poetry:

`shell
poetry install
`

3. Install TkinterDnD2 (required for drag and drop functionality):

`shell
pip install git+https://github.com/pmgagne/tkinterdnd2.git
`

## Usage

1. Run the application:

`shell
poetry run brainscape-to-anki
`

2. Drag and drop Brainscape deck links into the app
3. CSV files will be created in the selected output directory (default: Downloads folder)

## Architecture

The application follows Clean Architecture principles:

- **Domain Layer**: Core business logic and entities
- **Application Layer**: Use cases and services
- **Infrastructure Layer**: Implementation details (scrapers, exporters)
- **Presentation Layer**: User interface

## License

MIT
