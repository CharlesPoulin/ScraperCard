# Brainscape to Anki Converter

A Python application that scrapes flashcards from B***scape websites and converts them to Anki format (.csv).

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

```shell
poetry install
```

## Usage

1. Run the application:

```shell
poetry run brainscape-to-anki
```

2. Drag and drop Brainscape deck links into the app
3. CSV files will be created in the selected output directory (default: Downloads folder)

## Architecture

The application follows Clean Architecture principles:

- **Domain Layer**: Core business logic and entities
- **Application Layer**: Use cases and services
- **Infrastructure Layer**: Implementation details (scrapers, exporters)
- **Presentation Layer**: User interface

## Development

To contribute to the project:

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Submit a pull request

## License

MIT
