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
- Flexible color handling for individual and composite boards

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
    color="DarkGoldenrod"  # Optional color specification
)
```

### Creating Double Boards

```python
# Create a double board with single color
double_board = factory.create_double_board(
    length=48.0,
    width=2.5,
    thickness=0.75,
    name="double_board",
    color="DarkGoldenrod"  # Same color for both boards
)

# Create a double board with different colors
colored_double = factory.create_double_board(
    length=48.0,
    width=2.5,
    thickness=0.75,
    name="colored_double",
    color=["Beige", "Tan"]  # Different colors for each board
)
```

### Creating Half-Lap Joints

```python
# Create a half-lap joint with different colors
half_lap = factory.create_double_board_half_lap_ends(
    length=48.0,
    width=2.5,
    thickness=0.75,
    name="half_lap",
    half_lap_length=4.0,
    color=["DarkGreen", "ForestGreen"]  # Colors for long and short pieces
)
```

### Creating Frames

```python
# Create a frame with different colors for each piece
frame = factory.create_frame(
    outer_length=50.0,
    outer_width=30.0,
    board_width=2.5,
    thickness=0.75,
    name="colored_frame",
    color=["Beige", "Tan", "SandyBrown", "Peru"]  # One color per frame piece
)
```

### Positioning and Combining Components

```python
from solid2 import union, translate

# Position components in 3D space
model = union()(
    board,  # First component at origin
    translate([0, 10, 0])(double_board),  # Offset in Y direction
    translate([0, 20, 0])(frame)  # Further offset in Y direction
)

# Save the OpenSCAD file
model.save_as_scad("my_project.scad")
```

### Example Projects

The repository includes example projects:

1. `desk-03.py` - A desk with space for drawers
2. `worktable-01.py` - A sturdy workshop table
3. `color-examples.py` - Examples of different color configurations

To run an example:
```bash
python examples/worktable-01.py
```

This will generate:
- An OpenSCAD file (.scad)
- A bill of materials in the console output

## Project Structure

- `board_tools.py` - Core library with board manipulation tools
- `examples/` - Example projects showing library usage
- `requirements.txt` - Python dependencies

## Dependencies

- solidpython2>=2.1.1 - For OpenSCAD integration
- dataclasses>=0.6 - For Python versions < 3.7
- typing-extensions>=4.0.0 - For enhanced type hinting
- sqlite3 - For board database (included in Python standard library)

## Development Dependencies

- pytest>=7.0.0
- black>=22.0.0
- mypy>=0.900
- pylint>=2.8.0

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Acknowledgments

- Based on Phillip Tiefenbacher's OpenSCAD module
- Inspired by real woodworking projects and needs