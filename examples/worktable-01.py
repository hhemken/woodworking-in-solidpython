"""
Worktable design script using enhanced board tools.
Creates a workshop table with top and bottom support structures.
"""

from dataclasses import dataclass
from typing import Dict, Tuple
from solid2 import union, translate, rotate
from board_tools import (
    BoardFactory, BoardDatabase, BoardConfig,
    JointConfig, JoinType, Board
)

# ------------------------------
# Configuration
# ------------------------------
@dataclass
class TableConfig:
    """Configuration parameters for table dimensions"""
    board_thickness: float = 0.75
    board_width: float = 2.5
    foot_length: float = 4.0
    leg_segment_length: float = 27.0
    one_third_length: float = 16.0
    sheet_thickness: float = 0.5
    shelf_part_length: float = 9.75
    table_height: float = 34.0
    table_length: float = 59.0
    table_width: float = 33.75
    top_overhang: float = 1.0
    drawer_space_width: float = 16.0

    @property
    def short_length(self) -> float:
        return self.table_length - (2 * self.top_overhang)

    @property
    def short_width(self) -> float:
        return self.table_width - (2 * self.top_overhang)

# ------------------------------
# Component Colors
# ------------------------------
COLORS = {
    'leg': 'SlateBlue',
    'foot': 'Bisque',
    'crossbeam': 'Beige',
    'crossbeam_short': 'Tan',
    'top_foot': 'Maroon',
    'cross_member': 'IndianRed',
    'bottom_beam_long': 'SkyBlue',
    'bottom_beam_short': 'CornflowerBlue',
    'bottom_cross': 'SlateBlue'
}

def create_cross_member(factory: BoardFactory, config: TableConfig,
                       name: str, x_pos: float, z_pos: float, color: str):
    """Create a cross member board with standard dimensions"""
    width = config.short_width - 2 * (config.board_width + config.board_thickness)

    cross = factory.create_board(
        width, config.board_width, config.board_thickness,
        name, color
    )

    return (cross
            .rotate([0, 0, 90])
            .translate([x_pos,
                       config.top_overhang + config.board_width + config.board_thickness,
                       z_pos]))

def desk_end_assembly(factory: BoardFactory, config: TableConfig, tag: str = 'a'):
    """Build one end of the table using the provided factory."""

    # Create the front leg assembly
    front_leg = (factory.create_double_board(
        config.leg_segment_length, config.board_width, config.board_thickness,
        f'front leg end {tag}', [COLORS['leg'], COLORS['leg']])
        .rotate([90, -90, 0])
        .translate([3 * config.board_thickness,
                   config.board_width + config.top_overhang,
                   0]))

    front_foot = (factory.create_board(
        config.foot_length, config.board_width, config.board_thickness,
        f'front leg end {tag} foot', COLORS['foot'])
        .rotate([90, -90, 0])
        .translate([config.board_thickness,
                   config.board_width + config.top_overhang,
                   0]))

    # Create the back leg assembly
    back_leg = (factory.create_double_board(
        config.leg_segment_length, config.board_width, config.board_thickness,
        f'back leg end {tag}', [COLORS['leg'], COLORS['leg']])
        .rotate([90, -90, 0])
        .translate([3 * config.board_thickness,
                   config.top_overhang + config.short_width,
                   0]))

    back_foot = (factory.create_board(
        config.foot_length, config.board_width, config.board_thickness,
        f'back leg end {tag} foot', COLORS['foot'])
        .rotate([90, -90, 0])
        .translate([config.board_thickness,
                   config.top_overhang + config.short_width,
                   0]))

    # Create bottom crossbeam
    bottom_crossbeam = (factory.create_double_board_half_lap_ends(
        config.short_width, config.board_width, config.board_thickness,
        f'bottom crossbeam end {tag}', config.board_width,
        color=[COLORS['crossbeam'], COLORS['crossbeam_short']])
        .rotate([180, 0, 90])
        .translate([0, 0, config.board_width + config.foot_length])
        .translate([0, config.top_overhang, 0]))

    # Create top crossbeam
    top_crossbeam = (factory.create_double_board_half_lap_ends(
        config.short_width, config.board_width, config.board_thickness,
        f'top crossbeam end {tag}', config.board_width,
        color=[COLORS['crossbeam'], COLORS['crossbeam_short']])
        .rotate([180, 0, 90])
        .translate([0, 0, config.board_width + config.foot_length])
        .translate([0, config.top_overhang,
                   config.leg_segment_length - (config.foot_length + 2 * config.board_width)]))

    # Create top crossbeam feet
    top_front_foot = (factory.create_board(
        config.foot_length, config.board_width, config.board_thickness,
        f'top crossbeam end {tag} front foot', COLORS['top_foot'])
        .rotate([90, -90, 0])
        .translate([config.board_thickness,
                   config.board_width + config.top_overhang,
                   0])
        .translate([0, 0,
                   config.leg_segment_length - (2 * config.board_width + config.foot_length)]))

    top_back_foot = (factory.create_board(
        config.foot_length, config.board_width, config.board_thickness,
        f'top crossbeam end {tag} back foot', COLORS['top_foot'])
        .rotate([90, -90, 0])
        .translate([config.board_thickness,
                   config.board_width + config.top_overhang,
                   0])
        .translate([0, 0,
                   config.leg_segment_length - (2 * config.board_width + config.foot_length)])
        .translate([0, config.short_width - config.board_width, 0]))

    # Combine all components
    return union()(
        front_leg + front_foot + back_leg + back_foot +
        bottom_crossbeam + top_crossbeam +
        top_front_foot + top_back_foot
    )

def assemble_table(config: TableConfig) -> Tuple[union, BoardFactory]:
    """Creates a complete table assembly using the enhanced board tools."""

    # Create shared database and factory
    db = BoardDatabase(":memory:")
    factory = BoardFactory(thickness=config.board_thickness,
                         width=config.board_width,
                         db=db)

    # Build table ends
    end_a = desk_end_assembly(factory, config, 'a')
    end_b = (desk_end_assembly(factory, config, 'b')
             .rotate([0, 0, 180])
             .translate([config.short_length, 0, 0])
             .translate([0, 2 * config.top_overhang + config.short_width, 0]))

    # Create top structure
    top_back = (factory.create_double_board_half_lap_ends(
        config.short_length, config.board_width, config.board_thickness,
        'top back crossbeam', 3 * config.board_thickness,
        color=[COLORS['bottom_beam_long'], COLORS['bottom_beam_short']])
        .rotate([180, 0, 0])
        .translate([0,
                   config.board_width + config.top_overhang + config.board_thickness,
                   0])
        .translate([0, 0, config.leg_segment_length]))

    top_front = (factory.create_double_board_half_lap_ends(
        config.short_length, config.board_width, config.board_thickness,
        'top front crossbeam', 3 * config.board_thickness,
        color=[COLORS['bottom_beam_long'], COLORS['bottom_beam_short']])
        .translate([0,
                   config.short_width + config.top_overhang - config.board_width -
                   config.board_thickness,
                   config.leg_segment_length - config.board_width]))

    # Create cross members
    cross_members = union()(*[
        create_cross_member(
            factory, config,
            f'top cross member {i+1}',
            (3 * config.board_thickness if i == 0 else
             config.short_length - 2 * config.board_thickness if i == 3 else
             config.short_length * pos),
            config.leg_segment_length - config.board_width,
            COLORS['cross_member']
        )
        for i, pos in enumerate([0.0, 0.333, 0.667, 1.0])
    ])

    # Create bottom structure
    bottom_back = (factory.create_double_board_half_lap_ends(
        config.short_length, config.board_width, config.board_thickness,
        'bottom back crossbeam', 3 * config.board_thickness,
        color=[COLORS['bottom_beam_long'], COLORS['bottom_beam_short']])
        .rotate([180, 0, 0])
        .translate([0,
                   config.board_width + config.top_overhang + config.board_thickness,
                   config.foot_length + 2 * config.board_width]))

    bottom_front = (factory.create_double_board_half_lap_ends(
        config.short_length, config.board_width, config.board_thickness,
        'bottom front crossbeam', 3 * config.board_thickness,
        color=[COLORS['bottom_beam_long'], COLORS['bottom_beam_short']])
        .translate([0,
                   config.short_width + config.top_overhang - config.board_width -
                   config.board_thickness,
                   config.foot_length + config.board_width]))

    # Create bottom cross members
    bottom_cross_members = union()(*[
        create_cross_member(
            factory, config,
            f'bottom cross member {i+1}',
            (3 * config.board_thickness if i == 0 else
             config.short_length - 2 * config.board_thickness if i == 3 else
             config.short_length * pos),
            config.foot_length + config.board_width,
            COLORS['bottom_cross']
        )
        for i, pos in enumerate([0.0, 0.333, 0.667, 1.0])
    ])

    # Create table top
    table_top = (factory.create_board(
        config.table_length, config.table_width, config.board_thickness,
        "table_top", "DarkGoldenrod")
        .translate([0, 0, config.leg_segment_length + config.board_thickness]))

    # Combine all components
    model = union()(
        end_a + end_b +
        top_back + top_front +
        cross_members +
        bottom_back + bottom_front +
        bottom_cross_members +
        table_top
    )

    return model, factory

# ------------------------------
# Main
# ------------------------------
if __name__ == "__main__":
    config = TableConfig()
    model, factory = assemble_table(config)

    # Save the final SCAD model
    model.save_as_scad('worktable-01.scad')

    # Print BOM from the shared in-memory DB instance
    print("\nBill of Materials:")
    factory.list_bom()
