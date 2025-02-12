# Woodworking in SolidPython

A Python library for designing wooden furniture and generating OpenSCAD models. This project provides tools to define, visualize, and generate bills of materials for woodworking projects.

## Features

- Create and manipulate wooden boards with precise dimensions
- Support for various joint types (edge-to-edge, face-to-face, half-lap, butt, miter)
- Automatic bill of materials generation
- SQLite-backed storage for board definitions
- Color-coded visualization in OpenSCAD
- Support for composite board structures
- Common woodworking patterns (boxes, frames, panels)

## Installation

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure you have OpenSCAD installed on your system.

## Usage

### Basic Board Creation

```python
from board_tools import BoardFactory, BoardConfig

# Create a factory with default board dimensions
factory = BoardFactory(thickness=0.75, width=2.5)

# Create a simple board
board = factory.create_board(
    length=48.0,
    width=2.5,
    thickness=0.75,
    name="shelf_board",
    config=BoardConfig(color='DarkGoldenrod')
)
```

### Creating Composite Structures

```python
# Create a panel from multiple boards
panel = factory.create_panel(
    length=48.0,
    width=24.0,
    thickness=0.75,
    board_width=6.0,  # Width of individual boards in panel
    name="table_top"
)

# Create a frame
frame = factory.create_frame(
    outer_length=50.0,
    outer_width=30.0,
    board_width=2.5,
    thickness=0.75,
    name="support_frame"
)
```

### Using Patterns

```python
from board_tools import BoxPattern

# Create a box
box_pattern = BoxPattern()
box = box_pattern.apply(
    factory,
    length=24.0,
    width=12.0,
    height=8.0,
    thickness=0.75,
    name="storage_box",
    include_top=True
)
```

### Example Projects

The repository includes example projects:

1. `desk-03.py` - A desk with drawers
2. `worktable-01.py` - A sturdy workshop table

To run an example:
```bash
python worktable-01.py
```

This will generate:
- An OpenSCAD file (.scad)
- A bill of materials in the console output

## Project Structure

- `board_tools.py` - Core library with board manipulation tools
- `examples/` - Example projects showing library usage
- `requirements.txt` - Python dependencies

## Development

To contribute to the project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Dependencies

- solidpython2>=2.1.1 - For OpenSCAD integration
- dataclasses>=0.6 - For Python versions < 3.7
- typing-extensions>=4.0.0 - For enhanced type hinting

## Development Dependencies

- pytest>=7.0.0
- black>=22.0.0
- mypy>=0.900
- pylint>=2.8.0

## Acknowledgments

- Based on Phillip Tiefenbacher's OpenSCAD module
- Inspired by real woodworking projects and needs