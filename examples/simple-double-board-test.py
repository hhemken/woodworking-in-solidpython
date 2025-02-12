"""
Test script for board creation
"""
from board_tools import BoardFactory, BoardDatabase
from solid2 import union, translate

def main():
    # Create factory instance
    factory = BoardFactory(thickness=0.75, width=2.5)

    # Create test boards
    double_board = factory.create_double_board(
        length=24.0,
        width=4.0,
        thickness=0.75,
        name="double_board",
        color=["Red", "Blue"]
    )

    half_lap_board = factory.create_double_board_half_lap_ends(
        length=24.0,
        width=4.0,
        thickness=0.75,
        name="half_lap_board",
        half_lap_length=2.0,
        color=["Green", "Yellow"]
    )

    # Position boards for visualization
    model = union()(
        double_board,
        translate([0, 6, 0])(half_lap_board)  # Move half-lap board forward for visibility
    )

    # Save the model
    model.save_as_scad("test_boards.scad")

    # Print bill of materials
    print("\nBill of Materials:")
    factory.db.print_bom()

if __name__ == "__main__":
    main()