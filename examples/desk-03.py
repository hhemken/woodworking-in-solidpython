"""
Desk design script using enhanced board tools.
Creates a desk with drawers and support structures.
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
class DeskConfig:
    """Configuration parameters for desk dimensions"""
    board_thickness: float = 0.75
    board_width: float = 2.5
    foot_length: float = 4.0
    leg_segment_length: float = 23.0
    one_third_length: float = 16.0
    sheet_thickness: float = 0.5
    shelf_part_length: float = 9.75
    table_height: float = 34.0
    table_length: float = 50.0
    table_width: float = 25.0
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
    'drawer_support': 'SkyBlue'
}


def create_cross_member(factory: BoardFactory, config: DeskConfig,
                        name: str, x_pos: float, z_pos: float, color: str) -> union:
    """Create a cross member board with standard dimensions"""
    width = config.short_width - 2 * (config.board_width + config.board_thickness)
    board_config = BoardConfig(color=color)

    cross = (factory.create_board(width, config.board_width, config.board_thickness, name, board_config)
             .to_scad(factory)
             .rotate([0, 0, 90]))

    return cross.translate([
        x_pos,
        config.top_overhang + config.board_width + config.board_thickness,
        z_pos
    ])


def desk_end_assembly(factory: BoardFactory, config: DeskConfig, tag: str = 'a') -> union:
    """Build one end of the desk using the provided factory."""

    # Create the front leg assembly
    front_leg = (factory.create_double_board(
        config.leg_segment_length, config.board_width, config.board_thickness,
        f'front leg end {tag}', color=COLORS['leg'])
                 .to_scad(factory)
                 .rotate([90, -90, 0])
                 .translate([3 * config.board_thickness, config.board_width + config.top_overhang, 0]))

    front_foot = (factory.create_board(
        config.foot_length, config.board_width, config.board_thickness,
        f'front leg end {tag} foot', BoardConfig(color=COLORS['foot']))
                  .to_scad(factory)
                  .rotate([90, -90, 0])
                  .translate([config.board_thickness, config.board_width + config.top_overhang, 0]))

    # Create the back leg assembly
    back_leg = (factory.create_double_board(
        config.leg_segment_length, config.board_width, config.board_thickness,
        f'back leg end {tag}', color=COLORS['leg'])
                .to_scad(factory)
                .rotate([90, -90, 0])
                .translate([3 * config.board_thickness, config.top_overhang + config.short_width, 0]))

    back_foot = (factory.create_board(
        config.foot_length, config.board_width, config.board_thickness,
        f'back leg end {tag} foot', BoardConfig(color=COLORS['foot']))
                 .to_scad(factory)
                 .rotate([90, -90, 0])
                 .translate([config.board_thickness, config.top_overhang + config.short_width, 0]))

    # Create bottom crossbeam
    bottom_crossbeam = (factory.create_double_board_half_lap_ends(
        config.short_width, config.board_width, config.board_thickness,
        f'bottom crossbeam end {tag}', config.board_width,
        color_long=COLORS['crossbeam'], color_short=COLORS['crossbeam_short'])
                        .to_scad(factory)
                        .rotate([180, 0, 90])
                        .translate([0, 0, config.board_width + config.foot_length])
                        .translate([0, config.top_overhang, 0]))

    # Create top crossbeam
    top_crossbeam = (factory.create_double_board_half_lap_ends(
        config.short_width, config.board_width, config.board_thickness,
        f'top crossbeam end {tag}', config.board_width,
        color_long=COLORS['crossbeam'], color_short=COLORS['crossbeam_short'])
                     .to_scad(factory)
                     .rotate([180, 0, 90])
                     .translate([0, 0, config.board_width + config.foot_length])
                     .translate([0, config.top_overhang,
                                 config.leg_segment_length - (config.foot_length + 2 * config.board_width)]))

    # Create top crossbeam feet
    top_front_foot = (factory.create_board(
        config.foot_length, config.board_width, config.board_thickness,
        f'top crossbeam end {tag} front foot', BoardConfig(color=COLORS['top_foot']))
                      .to_scad(factory)
                      .rotate([90, -90, 0])
                      .translate([config.board_thickness, config.board_width + config.top_overhang, 0])
                      .translate([0, 0, config.leg_segment_length - (2 * config.board_width + config.foot_length)]))

    top_back_foot = (factory.create_board(
        config.foot_length, config.board_width, config.board_thickness,
        f'top crossbeam end {tag} back foot', BoardConfig(color=COLORS['top_foot']))
                     .to_scad(factory)
                     .rotate([90, -90, 0])
                     .translate([config.board_thickness, config.board_width + config.top_overhang, 0])
                     .translate([0, 0, config.leg_segment_length - (2 * config.board_width + config.foot_length)])
                     .translate([0, config.short_width - config.board_width, 0]))

    # Combine all components
    return union()(
        front_leg + front_foot + back_leg + back_foot +
        bottom_crossbeam + top_crossbeam +
        top_front_foot + top_back_foot
    )


def create_drawer_support(factory: BoardFactory, config: DeskConfig,
                          x_pos: float) -> union:
    """Create a set of drawer support rails"""
    rail_length = config.short_width - 2 * (config.board_width + config.board_thickness)
    board_config = BoardConfig(color=COLORS['drawer_support'])

    left_rail = (factory.create_board(rail_length, config.board_width, config.board_thickness,
                                      f'drawer_rail_left_{x_pos}', board_config)
                 .to_scad(factory)
                 .rotate([0, 0, 90])
                 .translate([x_pos,
                             config.top_overhang + config.board_width + config.board_thickness,
                             config.leg_segment_length * 0.6]))

    right_rail = (factory.create_board(rail_length, config.board_width, config.board_thickness,
                                       f'drawer_rail_right_{x_pos}', board_config)
                  .to_scad(factory)
                  .rotate([0, 0, 90])
                  .translate([x_pos + config.drawer_space_width,
                              config.top_overhang + config.board_width + config.board_thickness,
                              config.leg_segment_length * 0.6]))

    return union()(left_rail + right_rail)


def assemble_desk(config: DeskConfig) -> Tuple[union, BoardFactory]:
    """Creates a complete desk assembly using the enhanced board tools."""

    # Create shared database and factory
    db = BoardDatabase(db_path=":memory:")
    factory = BoardFactory(thickness=config.board_thickness, width=config.board_width, db=db)

    # Build desk ends
    end_a = desk_end_assembly(factory, config, 'a')
    end_b = (desk_end_assembly(factory, config, 'b')
             .rotate([0, 0, 180])
             .translate([config.short_length, 0, 0])
             .translate([0, 2 * config.top_overhang + config.short_width, 0]))

    # Create top structure
    top_back = (factory.create_double_board_half_lap_ends(
        config.short_length, config.board_width, config.board_thickness,
        'top back crossbeam', 3 * config.board_thickness,
        color_long=COLORS['crossbeam'], color_short=COLORS['crossbeam_short'])
                .to_scad(factory)
                .rotate([180, 0, 0])
                .translate([0, config.board_width + config.top_overhang + config.board_thickness, 0])
                .translate([0, 0, config.leg_segment_length]))

    top_front = (factory.create_double_board_half_lap_ends(
        config.short_length, config.board_width, config.board_thickness,
        'top front crossbeam', 3 * config.board_thickness,
        color_long=COLORS['crossbeam'], color_short=COLORS['crossbeam_short'])
                 .to_scad(factory)
                 .translate([0, config.short_width + config.top_overhang - config.board_width -
                             config.board_thickness, config.leg_segment_length - config.board_width]))

    # Create cross members
    cross_members = union()(
        create_cross_member(
            factory, config, 'top leftmost cross member',
            3 * config.board_thickness,
            config.leg_segment_length - config.board_width,
            COLORS['cross_member']
        ) +
        create_cross_member(
            factory, config, 'top first middle cross member',
            config.drawer_space_width + 3 * config.board_thickness,
            config.leg_segment_length - config.board_width,
            COLORS['cross_member']
        ) +
        create_cross_member(
            factory, config, 'top rightmost cross member',
            config.short_length - 2 * config.board_thickness,
            config.leg_segment_length - config.board_width,
            COLORS['cross_member']
        )
    )

    # Create drawer supports
    drawer_supports = union()(
        create_drawer_support(factory, config, 3 * config.board_thickness) +
        create_drawer_support(factory, config,
                              config.short_length - config.drawer_space_width -
                              3 * config.board_thickness)
    )

    # Create desk top
    desk_top = (factory.create_panel(
        config.table_length, config.table_width, config.board_thickness,
        config.board_width * 2.4,  # Use wider boards for the top
        "desk_top")
                .to_scad(factory)
                .translate([0, 0, config.leg_segment_length + config.board_thickness]))

    # Combine all components
    model = union()(
        end_a + end_b +
        top_back + top_front +
        cross_members +
        drawer_supports +
        desk_top
    )

    return model, factory


# ------------------------------
# Main
# ------------------------------
if __name__ == "__main__":
    config = DeskConfig()
    model, factory = assemble_desk(config)

    # Save the final SCAD model
    model.save_as_scad(filename='desk-03.scad', outdir='.')

    # Print BOM from the shared in-memory DB instance
    factory.list_bom()
