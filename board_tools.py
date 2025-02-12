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
    HALF_LAP = auto()      # Half lap joint
    BUTT_JOINT = auto()    # Simple butt joint
    MITER = auto()         # Miter joint (e.g., for frames)


@dataclass
class JointConfig:
    """Configuration for how boards are joined together"""
    join_type: JoinType
    offset: float = 0.0    # Offset between boards
    angle: float = 0.0     # For miter joints
    lap_length: float = 0.0  # For half lap joints


@dataclass
class BoardConfig:
    """Configuration for board appearance and properties"""
    color: str = 'DarkGoldenrod'
    grain_direction: str = 'length'  # 'length', 'width', or 'thickness'
    is_visible: bool = True
    material: str = 'pine'  # For future BOM categorization


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

    def to_scad(self, factory: 'BoardFactory') -> cube:
        """
        Convert board to SCAD representation

        Args:
            factory: The BoardFactory instance creating this board

        Returns:
            SCAD cube object representing this board
        """
        if not self.is_composite:
            return (cube([self.length, self.thickness, self.width])
                    .color(self.config.color))
        else:
            return self._build_composite_scad(factory)

    def _build_composite_scad(self, factory: 'BoardFactory') -> union:
        """
        Generate SCAD for composite board structures

        Args:
            factory: The BoardFactory instance creating this board

        Returns:
            SCAD union object representing the composite structure

        Raises:
            ValueError: If no composite definition exists
        """
        if not self.composite_definition:
            raise ValueError("No composite definition found")

        components = []
        current_offset = [0, 0, 0]

        for board, joint_config in self.composite_definition.components:
            scad = board.to_scad(factory)

            if joint_config.join_type == JoinType.FACE_TO_FACE:
                current_offset[1] += board.thickness
            elif joint_config.join_type == JoinType.EDGE_TO_EDGE:
                current_offset[2] += board.width
            elif joint_config.join_type == JoinType.HALF_LAP:
                if joint_config.lap_length > 0:
                    current_offset[0] += joint_config.lap_length
            elif joint_config.join_type == JoinType.MITER:
                # Apply miter angle rotation
                scad = scad.rotate([0, 0, joint_config.angle])

            components.append(scad.translate(current_offset))

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
        with self.transaction() as c:
            c.execute("""
                INSERT INTO boards (name, length, width, thickness, material, color, grain_direction)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (board.name, board.length, board.width, board.thickness,
                  board.config.material, board.config.color, board.config.grain_direction))

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
        self.bill_of_materials: Dict[str, List[Board]] = {}

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

    def create_board(self, length: float, width: float, thickness: float,
                     name: str, config: Optional[BoardConfig] = None) -> Board:
        """Create a single board with optional configuration"""
        board = Board(length, width, thickness, name, config)
        self.add_board_to_bom(board)
        return board

    def create_composite_board(self, name: str) -> CompositeBoardDefinition:
        """Start defining a new composite board"""
        return CompositeBoardDefinition(name)

    def create_double_board(self, length: float, width: float, thickness: float,
                            name: str, color: str = 'DarkGoldenrod') -> Board:
        """Stack two boards in the Y-direction"""
        config = BoardConfig(color=color)
        composite_def = self.create_composite_board(name)

        board1 = self.create_board(length, width, thickness, f"{name}_1", config)
        board2 = self.create_board(length, width, thickness, f"{name}_2", config)

        composite_def.add_board(board1, JointConfig(JoinType.FACE_TO_FACE))
        composite_def.add_board(board2, JointConfig(JoinType.FACE_TO_FACE))

        result = Board(length, width, thickness * 2, name, config)
        result.composite_definition = composite_def
        return result

    def create_double_board_half_lap_ends(self, length: float, width: float,
                                          thickness: float, name: str,
                                          half_lap_length: float,
                                          only_one_end: bool = False,
                                          color_long: str = 'Beige',
                                          color_short: str = 'Tan') -> Board:
        """Creates two overlapping boards with half-lap joints at the ends"""
        half_lap = 2 * half_lap_length if not only_one_end else half_lap_length

        config_long = BoardConfig(color=color_long)
        config_short = BoardConfig(color=color_short)
        composite_def = self.create_composite_board(name)

        board1 = self.create_board(length, width, thickness, f"{name}_long", config_long)
        board2 = self.create_board(length - half_lap, width, thickness, f"{name}_short", config_short)

        composite_def.add_board(board1, JointConfig(JoinType.FACE_TO_FACE))
        composite_def.add_board(board2, JointConfig(JoinType.HALF_LAP, lap_length=half_lap_length))

        result = Board(length, width, thickness * 2, name)
        result.composite_definition = composite_def
        return result

    def create_frame(self, outer_length: float, outer_width: float, board_width: float,
                     thickness: float, name: str) -> Board:
        """Create a rectangular frame from four boards with miter joints"""
        frame_def = self.create_composite_board(name)

        # Calculate board lengths for 45-degree miters
        length_boards = [
            self.create_board(outer_length, board_width, thickness, f"{name}_length_1"),
            self.create_board(outer_length, board_width, thickness, f"{name}_length_2")
        ]

        width_boards = [
            self.create_board(outer_width - 2 * board_width, board_width, thickness,
                              f"{name}_width_1"),
            self.create_board(outer_width - 2 * board_width, board_width, thickness,
                              f"{name}_width_2")
        ]

        # Add boards with miter joints
        for board in length_boards + width_boards:
            frame_def.add_board(board, JointConfig(JoinType.MITER, angle=45))

        composite = Board(outer_length, outer_width, thickness, name)
        composite.composite_definition = frame_def
        return composite

    def create_panel(self, length: float, width: float, thickness: float,
                     board_width: float, name: str) -> Board:
        """Create a panel from boards joined edge-to-edge"""
        panel_def = self.create_composite_board(name)

        # Calculate number of boards needed
        num_boards = int(width / board_width) + (1 if width % board_width else 0)
        remaining_width = width

        for i in range(num_boards):
            # Calculate the width of this board (handle the last board being potentially narrower)
            this_board_width = min(board_width, remaining_width)
            remaining_width -= this_board_width

            board = self.create_board(length, this_board_width, thickness,
                                      f"{name}_board_{i + 1}")
            panel_def.add_board(board, JointConfig(JoinType.EDGE_TO_EDGE))

        composite = Board(length, width, thickness, name)
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
