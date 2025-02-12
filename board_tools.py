"""
Enhanced board tools module for woodworking projects.
Provides tools for creating and managing wooden board designs with OpenSCAD.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Union, Dict, Tuple
import sqlite3
from contextlib import contextmanager
from solid2 import cube, color, rotate, translate, mirror, union


# ------------------------------
# Enums and Configurations
# ------------------------------
class JoinType(Enum):
    """Types of joints between boards"""
    EDGE_TO_EDGE = auto()  # Boards joined along their edges
    FACE_TO_FACE = auto()  # Boards stacked on top of each other
    HALF_LAP = auto()  # Half lap joint
    BUTT_JOINT = auto()  # Simple butt joint
    MITER = auto()  # Miter joint (e.g., for frames)


@dataclass
class JointConfig:
    """Configuration for how boards are joined together"""
    join_type: JoinType
    offset: float = 0.0  # Offset between boards
    angle: float = 0.0  # For miter joints
    lap_length: float = 0.0  # For half lap joints


@dataclass
class BoardConfig:
    """Configuration for board appearance and properties"""
    color: Union[str, List[str]] = 'DarkGoldenrod'  # Single color or list of colors
    grain_direction: str = 'length'  # 'length', 'width', or 'thickness'
    is_visible: bool = True
    material: str = 'pine'  # For future BOM categorization

    def get_color(self, index: int = 0) -> str:
        """Get color for specific board index in composite"""
        if isinstance(self.color, str):
            return self.color
        elif isinstance(self.color, list) and len(self.color) > 0:
            return self.color[index % len(self.color)]  # Cycle through colors if needed
        else:
            return 'DarkGoldenrod'  # Default fallback


class BoardError(Exception):
    """Base exception for board-related errors"""
    pass


class JointError(BoardError):
    """Exception raised for joint-related errors"""
    pass


class DimensionError(BoardError):
    """Exception raised for dimension-related errors"""
    pass


# ------------------------------
# Composite Board Definition
# ------------------------------
class CompositeBoardDefinition:
    """Defines how multiple boards are joined together to create a composite piece"""

    def __init__(self, name: str):
        self.name: str = name
        self.components: List[Tuple['Board', JointConfig]] = []

    def add_board(self, board: 'Board', joint_config: JointConfig) -> None:
        """
        Add a board with its joint configuration to the composite

        Args:
            board: The board to add
            joint_config: Configuration for how this board joins with others

        Raises:
            JointError: If the joint configuration is invalid
        """
        if not isinstance(board, Board):
            raise TypeError("board must be a Board instance")
        if not isinstance(joint_config, JointConfig):
            raise TypeError("joint_config must be a JointConfig instance")

        # Validate joint configuration
        if joint_config.join_type == JoinType.MITER and joint_config.angle == 0:
            raise JointError("Miter joints require a non-zero angle")
        if joint_config.join_type == JoinType.HALF_LAP and joint_config.lap_length == 0:
            raise JointError("Half lap joints require a non-zero lap length")

        self.components.append((board, joint_config))

    def get_total_dimensions(self) -> Tuple[float, float, float]:
        """
        Calculate overall dimensions based on component arrangement

        Returns:
            Tuple of (length, width, thickness)
        """
        if not self.components:
            return (0.0, 0.0, 0.0)

        lengths: List[float] = []
        widths: List[float] = []
        thicknesses: List[float] = []

        for board, config in self.components:
            if config.join_type == JoinType.EDGE_TO_EDGE:
                lengths.append(board.length)
                widths.append(board.width)
                thicknesses.append(board.thickness)
            elif config.join_type == JoinType.FACE_TO_FACE:
                lengths.append(board.length)
                widths.append(board.width)
                thicknesses.append(board.thickness)
            elif config.join_type == JoinType.HALF_LAP:
                # For half lap, consider the lap length
                lengths.append(board.length - config.lap_length)
                widths.append(board.width)
                thicknesses.append(board.thickness)

        return (max(lengths) if lengths else 0.0,
                max(widths) if widths else 0.0,
                sum(thicknesses) if thicknesses else 0.0)


# ------------------------------
# Enhanced Board Class
# ------------------------------
class Board:
    """Enhanced Board class with support for both simple and composite boards"""

    def __init__(self, length: float, width: float, thickness: float, name: str,
                 config: Optional[BoardConfig] = None):
        if length <= 0 or width <= 0 or thickness <= 0:
            raise DimensionError("All dimensions must be positive")
        if not name:
            raise ValueError("Board name cannot be empty")

        self.properties = {
            "length": length,
            "width": width,
            "thickness": thickness,
            "name": name
        }
        self.config = config or BoardConfig()
        self.composite_definition: Optional[CompositeBoardDefinition] = None

    @property
    def length(self) -> float:
        return self.properties["length"]

    @property
    def width(self) -> float:
        return self.properties["width"]

    @property
    def thickness(self) -> float:
        return self.properties["thickness"]

    @property
    def name(self) -> str:
        return self.properties["name"]

    @property
    def is_composite(self) -> bool:
        return self.composite_definition is not None

    def to_scad(self, factory: 'BoardFactory'):
        """Convert board to SCAD representation"""
        if not self.is_composite:
            # For simple boards, create a colored cube
            board_color = self.config.color if isinstance(self.config.color, str) else self.config.color[0]
            # Note: In OpenSCAD, Y is depth (front-to-back), Z is height
            return color(c=board_color)(
                cube([self.length, self.thickness, self.width])
            )
        else:
            return self._build_composite_scad(factory)

    def _build_composite_scad(self, factory: 'BoardFactory'):
        """Generate SCAD for composite board structures"""
        if not self.composite_definition:
            raise ValueError("No composite definition found")

        components = []
        current_offset = [0, 0, 0]  # [x=length, y=width, z=thickness]
        print(f"\nBuilding composite SCAD for {self.name}")

        for i, (board, joint_config) in enumerate(self.composite_definition.components):
            # Create the basic board shape with correct color
            board_color = (board.config.color if isinstance(board.config.color, str)
                           else board.config.color[min(i, len(board.config.color) - 1)])

            print(f"  Board {i}: {board.name}")
            print(f"    Dimensions: {board.length} x {board.width} x {board.thickness}")
            print(f"    Color: {board_color}")
            print(f"    Current offset before: {current_offset}")

            # Create cube with dimensions in OpenSCAD order [x=length, y=width, z=thickness]
            scad = color(c=board_color)(
                cube([board.length, board.width, board.thickness])
            )

            # Apply joint-specific transformations and offsets
            if i > 0:  # Skip offset for first board
                if joint_config.join_type == JoinType.FACE_TO_FACE:
                    # For face-to-face, offset in Z (thickness) direction
                    # Get the thickness of the previous board
                    prev_thickness = self.composite_definition.components[i - 1][0].thickness
                    current_offset[2] += prev_thickness
                    print(f"    Adding face-to-face offset: {prev_thickness}")
                elif joint_config.join_type == JoinType.EDGE_TO_EDGE:
                    # For edge-to-edge, offset in Y (width) direction
                    current_offset[1] += board.width
                elif joint_config.join_type == JoinType.HALF_LAP:
                    if joint_config.lap_length > 0:
                        current_offset[0] += joint_config.lap_length
                elif joint_config.join_type == JoinType.MITER:
                    scad = rotate(a=[0, 0, joint_config.angle])(scad)

            print(f"    Current offset after: {current_offset}")
            print(f"    Joint type: {joint_config.join_type}")

            # Add the transformed component
            components.append(translate(v=current_offset)(scad))

        return union()(*components)

# ------------------------------
# SQLite Database Class
# ------------------------------
class BoardDatabase:
    """Provides an SQLite-backed storage for Board objects"""

    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize the database

        Args:
            db_path: Path to SQLite database file, defaults to in-memory
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_table_if_not_exists()

    def __del__(self):
        """Ensure database connection is closed on cleanup"""
        if hasattr(self, 'conn'):
            self.conn.close()

    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cursor.close()

    def create_table_if_not_exists(self) -> None:
        """Create the boards table if it doesn't exist"""
        with self.transaction() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS boards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    length REAL NOT NULL,
                    width REAL NOT NULL,
                    thickness REAL NOT NULL,
                    material TEXT,
                    color TEXT,
                    grain_direction TEXT
                )
            """)

    def insert_board(self, board: Board) -> None:
        """
        Insert a new board record into the database

        Args:
            board: The Board instance to insert
        """
        # Convert color to string representation for storage
        if isinstance(board.config.color, list):
            color_str = ",".join(board.config.color)
        else:
            color_str = str(board.config.color)

        with self.transaction() as c:
            c.execute("""
                 INSERT INTO boards (name, length, width, thickness, material, color, grain_direction)
                 VALUES (?, ?, ?, ?, ?, ?, ?)
             """, (board.name, board.length, board.width, board.thickness,
                   board.config.material, color_str, board.config.grain_direction))

    def update_board(self, board_id: int, **kwargs) -> None:
        """
        Update board fields by board_id

        Args:
            board_id: ID of the board to update
            **kwargs: Fields to update and their new values
        """
        valid_keys = {"name", "length", "width", "thickness", "material", "color", "grain_direction"}
        fields = []
        values = []

        for k, v in kwargs.items():
            if k in valid_keys:
                fields.append(f"{k} = ?")
                values.append(v)

        if not fields:
            return

        values.append(board_id)
        with self.transaction() as c:
            c.execute(f"UPDATE boards SET {', '.join(fields)} WHERE id = ?", values)

    def delete_board(self, board_id: int) -> None:
        """Delete a board from the database"""
        with self.transaction() as c:
            c.execute("DELETE FROM boards WHERE id = ?", (board_id,))

    def get_board_by_id(self, board_id: int) -> Optional[Dict]:
        """Retrieve a single board record by its ID"""
        with self.transaction() as c:
            c.execute("""
                SELECT id, name, length, width, thickness, material, color, grain_direction 
                FROM boards WHERE id = ?
            """, (board_id,))
            row = c.fetchone()

        if row:
            return {
                "id": row[0],
                "name": row[1],
                "length": row[2],
                "width": row[3],
                "thickness": row[4],
                "material": row[5],
                "color": row[6],
                "grain_direction": row[7]
            }
        return None

    def get_all_boards(self) -> List[tuple]:
        """Retrieve all boards, sorted by name"""
        with self.transaction() as c:
            c.execute("""
                SELECT id, name, length, width, thickness, material, color, grain_direction
                FROM boards ORDER BY name
            """)
            return c.fetchall()

    def print_bom(self) -> None:
        """Print a Bill Of Materials from all boards in the database"""
        boards = self.get_all_boards()
        print("---- Bill of Materials (Sorted by Name) ----")
        if not boards:
            print("(No boards found in database.)")
            return

        print('name                                length    width    thickness  material')
        for board_rec in boards:
            board_id, name, length, width, thickness, material, _, _ = board_rec
            print(f"{name:32}   {length:-6.2f}   {width:-6.2f}   {thickness:-6.2f}   {material or 'pine'}")
        print("--------------------------------------------")

        # Additional summary: boards by length
        boards_by_length = {}
        for board_id, name, length, *_ in boards:
            if length not in boards_by_length:
                boards_by_length[length] = []
            boards_by_length[length].append(name)

        print("---- Board Count & Names by Length ----")
        for length_val, name_list in sorted(boards_by_length.items()):
            count = len(name_list)
            names_str = ", ".join(name_list)
            print(f"Length = {length_val:.2f}\" => {count} boards: {names_str}")
        print("--------------------------------------------")


# ------------------------------
# Enhanced Board Factory
# ------------------------------
class BoardFactory:
    """Enhanced factory with support for both simple and composite boards"""

    def __init__(self, thickness: float, width: float, db: Optional[BoardDatabase] = None):
        if thickness <= 0 or width <= 0:
            raise DimensionError("Thickness and width must be positive")

        self._thickness = thickness
        self._width = width
        self.db = db if db else BoardDatabase(db_path=":memory:")

    @property
    def thickness(self) -> float:
        return self._thickness

    @property
    def width(self) -> float:
        return self._width

    def add_board_to_bom(self, board: Board) -> None:
        """Add board to in-memory BOM and database"""
        if board.name not in self.bill_of_materials:
            self.bill_of_materials[board.name] = []
        self.bill_of_materials[board.name].append(board)
        self.db.insert_board(board)

    def create_composite_board(self, name: str) -> CompositeBoardDefinition:
        """Start defining a new composite board"""
        return CompositeBoardDefinition(name)

    def create_board(self, length: float, width: float, thickness: float,
                     name: str, color: Union[str, List[str]] = 'DarkGoldenrod'):
        """Create a single board with SCAD geometry"""
        # Add to BOM and DB
        board_color = color if isinstance(color, str) else color[0]
        board = Board(length, width, thickness, name, BoardConfig(color=board_color))
        self.db.insert_board(board)

        # Create and return SCAD geometry
        return cube([length, thickness, width]).color(board_color)

    def create_double_board(self, length: float, width: float, thickness: float,
                            name: str, color: Union[str, List[str]] = 'DarkGoldenrod'):
        """Stack two boards in the Y-direction, offset by thickness"""
        if isinstance(color, str):
            color1 = color2 = color
        else:
            color1 = color[0] if len(color) > 0 else 'DarkGoldenrod'
            color2 = color[1] if len(color) > 1 else color1

        # Create first board at origin
        board1 = self.create_board(length, width, thickness, f"{name}_1", color1)

        # Create second board translated by thickness
        board2 = (self.create_board(length, width, thickness, f"{name}_2", color2)
                  .translate([0, thickness, 0]))

        return union()(board1 + board2)

    def create_double_board_half_lap_ends(self, length: float, width: float,
                                          thickness: float, name: str,
                                          half_lap_length: float,
                                          only_one_end: bool = False,
                                          color: Union[str, List[str]] = 'DarkGoldenrod'):
        """Creates two overlapping boards with half-lap joints at the ends"""
        if isinstance(color, str):
            color_long = color_short = color
        else:
            color_long = color[0] if len(color) > 0 else 'DarkGoldenrod'
            color_short = color[1] if len(color) > 1 else color_long

        half_lap = 2 * half_lap_length if not only_one_end else half_lap_length

        # Create long board at origin
        board1 = self.create_board(length, width, thickness, f"{name}_long", color_long)

        # Create short board translated by half_lap_length and thickness
        board2 = (self.create_board(length - half_lap, width, thickness, f"{name}_short", color_short)
                  .translate([half_lap_length, thickness, 0]))

        return union()(board1 + board2)

    def create_frame(self, outer_length: float, outer_width: float, board_width: float,
                     thickness: float, name: str,
                     color: Union[str, List[str]] = 'DarkGoldenrod'):
        """Create a rectangular frame from four boards with miter joints"""
        if isinstance(color, str):
            colors = [color] * 4
        else:
            colors = color
            if len(colors) < 4:
                colors.extend(['DarkGoldenrod'] * (4 - len(colors)))

        # Calculate board lengths for 45-degree miters
        length_boards = [
            self.create_board(outer_length, board_width, thickness,
                              f"{name}_length_1", colors[0]),
            self.create_board(outer_length, board_width, thickness,
                              f"{name}_length_2", colors[1])
        ]

        width_boards = [
            self.create_board(outer_width - 2 * board_width, board_width, thickness,
                              f"{name}_width_1", colors[2]),
            self.create_board(outer_width - 2 * board_width, board_width, thickness,
                              f"{name}_width_2", colors[3])
        ]

        mitered_boards = []
        for i, board in enumerate(length_boards + width_boards):
            # Apply appropriate transformations for each board position
            if i < 2:  # Length boards
                transformed = board
            else:  # Width boards
                transformed = (board
                               .translate([board_width, 0, 0])
                               .rotate([0, 0, 90]))
            mitered_boards.append(transformed)

        return union()(*mitered_boards)

    def create_panel(self, length: float, width: float, thickness: float,
                     board_width: float, name: str,
                     color: Union[str, List[str]] = 'DarkGoldenrod') -> Board:
        """Create a panel from boards joined edge-to-edge"""
        panel_def = self.create_composite_board(name)
        config = BoardConfig(color=color)

        # Calculate number of boards needed
        num_boards = int(width / board_width) + (1 if width % board_width else 0)
        remaining_width = width

        for i in range(num_boards):
            # Calculate the width of this board
            this_board_width = min(board_width, remaining_width)
            remaining_width -= this_board_width

            board = self.create_board(length, this_board_width, thickness,
                                      f"{name}_board_{i + 1}",
                                      BoardConfig(color=config.get_color(i)))
            panel_def.add_board(board, JointConfig(JoinType.EDGE_TO_EDGE))

        composite = Board(length, width, thickness, name, config)
        composite.composite_definition = panel_def
        return composite

    def create_layered_board(self, length: float, width: float,
                             layer_thicknesses: List[float], name: str,
                             colors: Optional[List[str]] = None) -> Board:
        """Create a board made of multiple layers stacked face-to-face"""
        layered_def = self.create_composite_board(name)
        total_thickness = sum(layer_thicknesses)

        if colors is None:
            colors = ['DarkGoldenrod'] * len(layer_thicknesses)
        elif len(colors) < len(layer_thicknesses):
            colors.extend(['DarkGoldenrod'] * (len(layer_thicknesses) - len(colors)))

        for i, (thickness, color) in enumerate(zip(layer_thicknesses, colors)):
            config = BoardConfig(color=color)
            board = self.create_board(length, width, thickness,
                                      f"{name}_layer_{i + 1}", config)
            layered_def.add_board(board, JointConfig(JoinType.FACE_TO_FACE))

        composite = Board(length, width, total_thickness, name)
        composite.composite_definition = layered_def
        return composite

    def list_bom(self) -> None:
        """Print BOM from the database"""
        self.db.print_bom()


# ------------------------------
# Woodworking Patterns
# ------------------------------
class WoodworkingPattern:
    """Base class for common woodworking patterns"""

    def apply(self, factory: BoardFactory, **kwargs) -> Board:
        raise NotImplementedError


class BoxPattern(WoodworkingPattern):
    """Pattern for creating box structures"""

    def apply(self, factory: BoardFactory,
              length: float, width: float, height: float,
              thickness: float, name: str,
              include_top: bool = True) -> Board:
        """
        Creates a box structure with optional top.

        Args:
            factory: The BoardFactory instance to use
            length: Length of the box (X dimension)
            width: Width of the box (Y dimension)
            height: Height of the box (Z dimension)
            thickness: Thickness of the boards to use
            name: Name prefix for the box and its components
            include_top: Whether to include a top panel (default: True)

        Returns:
            A composite Board representing the complete box

        Raises:
            DimensionError: If any dimension is invalid
        """
        if length <= 0 or width <= 0 or height <= 0 or thickness <= 0:
            raise DimensionError("All dimensions must be positive")

        box_def = factory.create_composite_board(f"{name}_box")

        # Create panels for each side
        bottom = factory.create_panel(length, width, thickness, f"{name}_bottom")
        if include_top:
            top = factory.create_panel(length, width, thickness, f"{name}_top")

        # Side panels account for thickness of top/bottom
        front = factory.create_panel(length, height - 2 * thickness, thickness, f"{name}_front")
        back = factory.create_panel(length, height - 2 * thickness, thickness, f"{name}_back")
        left = factory.create_panel(width - 2 * thickness, height - 2 * thickness, thickness, f"{name}_left")
        right = factory.create_panel(width - 2 * thickness, height - 2 * thickness, thickness, f"{name}_right")

        # Add bottom
        box_def.add_board(bottom, JointConfig(JoinType.BUTT_JOINT))

        # Add sides
        box_def.add_board(front, JointConfig(JoinType.BUTT_JOINT))
        box_def.add_board(back, JointConfig(JoinType.BUTT_JOINT))
        box_def.add_board(left, JointConfig(JoinType.BUTT_JOINT))
        box_def.add_board(right, JointConfig(JoinType.BUTT_JOINT))

        # Add top if requested
        if include_top:
            box_def.add_board(top, JointConfig(JoinType.BUTT_JOINT))

        composite = Board(length, width, height, name)
        composite.composite_definition = box_def
        return composite
