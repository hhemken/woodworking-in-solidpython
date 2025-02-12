"""
Example script demonstrating various ways to color composite boards.
Shows different joint types and color configurations.
"""

from board_tools import BoardFactory, BoardDatabase
from solid2 import union, translate

def create_example_boards(factory: BoardFactory):
    """Creates example boards with different color configurations"""

    # Example 1: Single color double board
    simple_double = factory.create_double_board(
        length=48.0,
        width=4.0,
        thickness=0.75,
        name="simple_double",
        color="DarkGoldenrod"  # Single color for both boards
    )

    # Example 2: Two-colored double board
    colored_double = factory.create_double_board(
        length=48.0,
        width=4.0,
        thickness=0.75,
        name="colored_double",
        color=["Beige", "Tan"]  # Different color for each board
    )

    # Example 3: Multi-colored frame
    colored_frame = factory.create_frame(
        outer_length=50.0,
        outer_width=30.0,
        board_width=4.0,
        thickness=0.75,
        name="colored_frame",
        color=["Beige", "Tan", "SandyBrown", "Peru"]  # One color per frame piece
    )

    # Example 4: Half-lap joint with different colors
    half_lap = factory.create_double_board_half_lap_ends(
        length=48.0,
        width=4.0,
        thickness=0.75,
        name="half_lap",
        half_lap_length=4.0,
        color=["DarkGreen", "ForestGreen"]  # Different colors for long and short pieces
    )

    # Position all examples in 3D space with good spacing
    model = union()(
        # Simple double board at origin
        simple_double,

        # Colored double board offset in Y
        translate([0, 15, 0])(colored_double),

        # Colored frame offset in Y further
        translate([0, 60, 0])(colored_frame),

        # Half-lap joint offset in X
        translate([0, 105, 0])(half_lap)
    )

    return model

def main():
    # Create factory instance
    db = BoardDatabase(":memory:")
    factory = BoardFactory(thickness=0.75, width=2.5, db=db)

    # Create and save the model
    model = create_example_boards(factory)
    model.save_as_scad("color_examples.scad")

    # Print bill of materials
    print("\nBill of Materials:")
    factory.list_bom()

    # Print example descriptions
    print("\nExample Descriptions:")
    print("1. Simple Double Board:")
    print("   - Two boards stacked face-to-face")
    print("   - Single color (DarkGoldenrod) applied to both boards")
    print("\n2. Colored Double Board:")
    print("   - Two boards stacked face-to-face")
    print("   - First board colored Beige")
    print("   - Second board colored Tan")
    print("\n3. Colored Frame:")
    print("   - Four pieces forming a rectangular frame")
    print("   - Each piece has a unique color")
    print("   - Colors: Beige, Tan, SandyBrown, Peru")
    print("\n4. Half-Lap Joint:")
    print("   - Two overlapping boards with half-lap joint")
    print("   - Long board colored DarkGreen")
    print("   - Short board colored ForestGreen")

if __name__ == "__main__":
    main()