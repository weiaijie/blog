import argparse
import math
import random
from pathlib import Path

import bpy


ASSET_PATHS = {
    "terrain-grassland": {
        "source": Path("src/render/assets/source/terrain/terrain-grassland.blend"),
        "lod0": Path("src/render/assets/terrain/terrain-grassland-lod0.glb"),
        "lod1": Path("src/render/assets/terrain/terrain-grassland-lod1.glb"),
    },
    "terrain-water": {
        "source": Path("src/render/assets/source/terrain/terrain-water.blend"),
        "lod0": Path("src/render/assets/terrain/terrain-water-lod0.glb"),
        "lod1": Path("src/render/assets/terrain/terrain-water-lod1.glb"),
    },
    "transition-shoreline": {
        "source": Path("src/render/assets/source/transitions/transition-shoreline.blend"),
        "lod0": Path("src/render/assets/transitions/transition-shoreline-lod0.glb"),
        "lod1": Path("src/render/assets/transitions/transition-shoreline-lod1.glb"),
    },
    "terrain-hill": {
        "source": Path("src/render/assets/source/terrain/terrain-hill.blend"),
        "lod0": Path("src/render/assets/terrain/terrain-hill-lod0.glb"),
        "lod1": Path("src/render/assets/terrain/terrain-hill-lod1.glb"),
    },
    "buildable-city-center": {
        "source": Path("src/render/assets/source/buildables/buildable-city-center.blend"),
        "lod0": Path("src/render/assets/buildables/buildable-city-center-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/buildable-city-center-lod1.glb"),
    },
    "city-module-tower": {
        "source": Path("src/render/assets/source/buildables/modules/city-module-tower.blend"),
        "lod0": Path("src/render/assets/buildables/modules/city-module-tower-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/modules/city-module-tower-lod1.glb"),
    },
    "city-module-gate": {
        "source": Path("src/render/assets/source/buildables/modules/city-module-gate.blend"),
        "lod0": Path("src/render/assets/buildables/modules/city-module-gate-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/modules/city-module-gate-lod1.glb"),
    },
    "city-module-wall": {
        "source": Path("src/render/assets/source/buildables/modules/city-module-wall.blend"),
        "lod0": Path("src/render/assets/buildables/modules/city-module-wall-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/modules/city-module-wall-lod1.glb"),
    },
    "city-module-keep": {
        "source": Path("src/render/assets/source/buildables/modules/city-module-keep.blend"),
        "lod0": Path("src/render/assets/buildables/modules/city-module-keep-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/modules/city-module-keep-lod1.glb"),
    },
    "city-module-banner": {
        "source": Path("src/render/assets/source/buildables/modules/city-module-banner.blend"),
        "lod0": Path("src/render/assets/buildables/modules/city-module-banner-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/modules/city-module-banner-lod1.glb"),
    },
    "city-module-window": {
        "source": Path("src/render/assets/source/buildables/modules/city-module-window.blend"),
        "lod0": Path("src/render/assets/buildables/modules/city-module-window-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/modules/city-module-window-lod1.glb"),
    },
    "city-module-door": {
        "source": Path("src/render/assets/source/buildables/modules/city-module-door.blend"),
        "lod0": Path("src/render/assets/buildables/modules/city-module-door-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/modules/city-module-door-lod1.glb"),
    },
    "city-module-stairs": {
        "source": Path("src/render/assets/source/buildables/modules/city-module-stairs.blend"),
        "lod0": Path("src/render/assets/buildables/modules/city-module-stairs-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/modules/city-module-stairs-lod1.glb"),
    },
    "city-module-platform": {
        "source": Path("src/render/assets/source/buildables/modules/city-module-platform.blend"),
        "lod0": Path("src/render/assets/buildables/modules/city-module-platform-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/modules/city-module-platform-lod1.glb"),
    },
    "city-module-corner": {
        "source": Path("src/render/assets/source/buildables/modules/city-module-corner.blend"),
        "lod0": Path("src/render/assets/buildables/modules/city-module-corner-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/modules/city-module-corner-lod1.glb"),
    },
    "city-module-merlon": {
        "source": Path("src/render/assets/source/buildables/modules/city-module-merlon.blend"),
        "lod0": Path("src/render/assets/buildables/modules/city-module-merlon-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/modules/city-module-merlon-lod1.glb"),
    },
    "city-module-arch": {
        "source": Path("src/render/assets/source/buildables/modules/city-module-arch.blend"),
        "lod0": Path("src/render/assets/buildables/modules/city-module-arch-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/modules/city-module-arch-lod1.glb"),
    },
    "city-module-roof-tile": {
        "source": Path("src/render/assets/source/buildables/modules/city-module-roof-tile.blend"),
        "lod0": Path("src/render/assets/buildables/modules/city-module-roof-tile-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/modules/city-module-roof-tile-lod1.glb"),
    },
    "city-module-torch": {
        "source": Path("src/render/assets/source/buildables/modules/city-module-torch.blend"),
        "lod0": Path("src/render/assets/buildables/modules/city-module-torch-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/modules/city-module-torch-lod1.glb"),
    },
    "city-module-shield": {
        "source": Path("src/render/assets/source/buildables/modules/city-module-shield.blend"),
        "lod0": Path("src/render/assets/buildables/modules/city-module-shield-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/modules/city-module-shield-lod1.glb"),
    },
    "city-module-flowerbed": {
        "source": Path("src/render/assets/source/buildables/modules/city-module-flowerbed.blend"),
        "lod0": Path("src/render/assets/buildables/modules/city-module-flowerbed-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/modules/city-module-flowerbed-lod1.glb"),
    },
    "city-module-kit": {
        "source": Path("src/render/assets/source/buildables/modules/city-module-kit.blend"),
        "lod0": Path("src/render/assets/buildables/modules/city-module-kit-lod0.glb"),
        "lod1": Path("src/render/assets/buildables/modules/city-module-kit-lod1.glb"),
    },
}

OUTPUT_TEXTURE_ROOT = None
GENERATION_SEED = 0


def main():
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    global OUTPUT_TEXTURE_ROOT, GENERATION_SEED
    GENERATION_SEED = args.seed if args.seed is not None else random.SystemRandom().randint(1, 2_147_483_647)
    OUTPUT_TEXTURE_ROOT = repo_root / "src/render/assets/textures"
    OUTPUT_TEXTURE_ROOT.mkdir(parents=True, exist_ok=True)
    print(f"Terrain asset generation seed: {GENERATION_SEED}")

    for asset_id in args.assets:
        if asset_id not in ASSET_PATHS:
            valid_assets = ", ".join(sorted(ASSET_PATHS))
            raise ValueError(f"Unknown asset '{asset_id}'. Valid assets: {valid_assets}")

        paths = {key: repo_root / value for key, value in ASSET_PATHS[asset_id].items()}
        for path in paths.values():
            path.parent.mkdir(parents=True, exist_ok=True)

        build_asset(asset_id, detailed=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(paths["source"]))
        export_selected_glb(paths["lod0"])

        build_asset(asset_id, detailed=False)
        export_selected_glb(paths["lod1"])

        print(f"Generated {asset_id}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--assets", nargs="+", default=list(ASSET_PATHS))
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args(argv_after_separator())


def argv_after_separator():
    import sys

    if "--" not in sys.argv:
        return []

    return sys.argv[sys.argv.index("--") + 1 :]


def build_asset(asset_id, detailed):
    reset_scene()

    if asset_id == "terrain-grassland":
        create_terrain_grassland(detailed)
    elif asset_id == "terrain-water":
        create_terrain_water(detailed)
    elif asset_id == "transition-shoreline":
        create_transition_shoreline(detailed)
    elif asset_id == "terrain-hill":
        create_terrain_hill(detailed)
    elif asset_id == "buildable-city-center":
        import importlib.util
        spec = importlib.util.spec_from_file_location("city_block_v2", Path(__file__).with_name("city_block_v2.py"))
        city_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(city_module)
        city_module.create_city_block(detailed)
    elif asset_id == "city-module-tower":
        create_city_module_tower(detailed)
    elif asset_id == "city-module-gate":
        create_city_module_gate(detailed)
    elif asset_id == "city-module-wall":
        create_city_module_wall(detailed)
    elif asset_id == "city-module-keep":
        create_city_module_keep(detailed)
    elif asset_id == "city-module-banner":
        create_city_module_banner(detailed)
    elif asset_id == "city-module-window":
        create_city_module_window(detailed)
    elif asset_id == "city-module-door":
        create_city_module_door(detailed)
    elif asset_id == "city-module-stairs":
        create_city_module_stairs(detailed)
    elif asset_id == "city-module-platform":
        create_city_module_platform(detailed)
    elif asset_id == "city-module-corner":
        create_city_module_corner(detailed)
    elif asset_id == "city-module-merlon":
        create_city_module_merlon(detailed)
    elif asset_id == "city-module-arch":
        create_city_module_arch(detailed)
    elif asset_id == "city-module-roof-tile":
        create_city_module_roof_tile(detailed)
    elif asset_id == "city-module-torch":
        create_city_module_torch(detailed)
    elif asset_id == "city-module-shield":
        create_city_module_shield(detailed)
    elif asset_id == "city-module-flowerbed":
        create_city_module_flowerbed(detailed)
    elif asset_id == "city-module-kit":
        create_city_module_kit(detailed)

    add_asset_lighting(asset_id)
    select_export_meshes()


def seeded_rng(label, detailed):
    label_seed = 0

    for index, char in enumerate(label):
        label_seed += (index + 1) * ord(char)

    detail_offset = 100_003 if detailed else 300_007
    return random.Random(GENERATION_SEED + label_seed + detail_offset)


def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    purge_orphan_data()
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1


def purge_orphan_data():
    for data_block in (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.images,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for item in list(data_block):
            if item.users == 0:
                data_block.remove(item)


def material(name, color, roughness=0.8, metallic=0.0, alpha=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Alpha"].default_value = alpha
    bsdf.inputs["Base Color"].default_value = color
    mat.blend_method = "BLEND" if alpha < 1.0 else "OPAQUE"
    if hasattr(mat, "use_screen_refraction"):
        mat.use_screen_refraction = alpha < 1.0
    return mat


def image_material(name, image, roughness=0.92):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = roughness
    mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def palette():
    return {
        "deep_water": material("water_deep_blue_green", (0.08, 0.38, 0.52, 1), 0.38, 0.0, 0.82),
        "water_highlight": material("water_soft_highlight", (0.72, 0.95, 0.92, 1), 0.28, 0.0, 0.7),
        "shore_sand": material("shore_warm_sand", (0.78, 0.70, 0.46, 1), 0.86),
        "wet_ground": material("shore_wet_ground", (0.36, 0.45, 0.34, 1), 0.9),
        "grass_cap": material("grassland_top_moss_grass", (0.19, 0.30, 0.07, 1), 0.94),
        "grass": material("terrain_grass_mixed", (0.25, 0.39, 0.10, 1), 0.92),
        "grass_light": material("terrain_grass_light", (0.48, 0.60, 0.18, 1), 0.9),
        "grass_dark": material("terrain_grass_shadow", (0.08, 0.18, 0.05, 1), 0.95),
        "flower_white": material("grassland_wildflower_white", (0.92, 0.90, 0.80, 1), 0.72),
        "flower_yellow": material("grassland_wildflower_yellow", (0.86, 0.65, 0.16, 1), 0.72),
        "flower_purple": material("grassland_wildflower_purple", (0.58, 0.42, 0.72, 1), 0.74),
        "loam": material("side_layer_loam", (0.28, 0.16, 0.08, 1), 0.94),
        "clay": material("side_layer_clay", (0.52, 0.34, 0.14, 1), 0.92),
        "gravel": material("side_layer_gravel", (0.26, 0.24, 0.20, 1), 0.88),
        "bedrock": material("side_layer_bedrock", (0.16, 0.17, 0.16, 1), 0.9),
        "dry_soil": material("grassland_dry_soil_patch", (0.40, 0.29, 0.13, 1), 0.96),
        "earth": material("hill_earth_slope", (0.50, 0.34, 0.20, 1), 0.9),
        "rock": material("hill_warm_rock", (0.63, 0.54, 0.40, 1), 0.82),
        "rock_shadow": material("hill_shadow_rock", (0.28, 0.22, 0.18, 1), 0.9),
        "foam": material("shore_foam_soft", (0.92, 0.92, 0.78, 1), 0.48, 0.0, 0.76),
        "reed": material("shore_reed_green", (0.42, 0.53, 0.26, 1), 0.84),
    }


def create_terrain_grassland(detailed):
    mats = palette()
    rng = seeded_rng("terrain-grassland-main", detailed)
    top_material = create_grassland_texture_material(detailed)

    create_grassland_side_band("bedrock_layer", -0.24, -0.15, 1.11, mats["bedrock"], rng)
    create_grassland_side_band("gravel_layer", -0.15, -0.075, 1.12, mats["gravel"], rng)
    create_grassland_side_band("clay_layer", -0.075, -0.005, 1.13, mats["clay"], rng)
    create_grassland_side_band("loam_layer", -0.005, 0.06, 1.125, mats["loam"], rng)
    create_grassland_side_band("turf_edge", 0.06, 0.105, 1.12, mats["grass_cap"], rng)
    create_grassland_top_mesh("grassland_dense_top_surface", top_material, rng)
    create_grassland_side_strata(mats, rng, detailed)

    edge_tufts = create_scattered_annulus_points(rng, 24 if detailed else 8, 0.72, 1.0, min_distance=0.13)
    for index, point in enumerate(edge_tufts):
        x, y = point
        create_grass_tuft(f"edge_grass_clump_{index + 1}", x, y, rng.uniform(-math.pi, math.pi), mats, scale=rng.uniform(0.54, 0.95))

    inner_tufts = create_scattered_points(rng, 11 if detailed else 4, 0.68, min_distance=0.2)
    for index, point in enumerate(inner_tufts):
        x, y = point
        create_grass_tuft(f"inner_grass_clump_{index + 1}", x, y, rng.uniform(-math.pi, math.pi), mats, scale=rng.uniform(0.42, 0.68))

    grass_speckles = create_scattered_points(rng, 220 if detailed else 58, 0.96, min_distance=0.03)
    for index, point in enumerate(grass_speckles):
        x, y = point
        mat = rng.choice([mats["grass"], mats["grass_light"], mats["grass_dark"]])
        create_micro_blade(f"short_grass_blade_{index + 1}", x, y, rng.uniform(-math.pi, math.pi), rng.uniform(0.018, 0.042), mat)

    rock_specs = [
        (-0.58, 0.38, 0.075, 0.038),
        (-0.50, 0.32, 0.035, 0.022),
        (0.18, 0.32, 0.052, 0.027),
        (0.52, -0.36, 0.068, 0.034),
        (0.45, -0.42, 0.032, 0.02),
        (-0.2, -0.12, 0.038, 0.021),
        (0.66, 0.10, 0.034, 0.018),
    ]
    for index, spec in enumerate(rock_specs if detailed else rock_specs[:3]):
        x, y, radius, height = spec
        create_rock(f"grouped_embedded_stone_{index + 1}", x, y, radius, height, mats["rock"])

    if detailed:
        flower_points = create_clustered_flower_points(rng)
        flower_mats = [mats["flower_white"], mats["flower_yellow"], mats["flower_purple"]]

        for index, point in enumerate(flower_points):
            x, y = point
            create_flat_flower_dot(f"wildflower_dot_cluster_{index + 1}", x, y, flower_mats[index % len(flower_mats)])


def create_terrain_water(detailed):
    mats = palette()
    create_hex_cylinder("hex_basin_side", 1.15, 0.24, -0.15, mats["deep_water"])
    create_hex_cylinder("shallow_sand_ring", 1.02, 0.035, -0.005, mats["shore_sand"])
    create_cylinder("water_surface", 0.82, 0.026, 0.035, 48 if detailed else 24, mats["deep_water"])

    if detailed:
        for index, spec in enumerate(
            [
                (-0.28, -0.18, 0.46, 0.034, 0.14),
                (0.18, 0.02, 0.58, 0.034, -0.1),
                (-0.06, 0.24, 0.38, 0.03, 0.28),
            ]
        ):
            x, y, length, width, rotation = spec
            create_box(f"wave_decal_{index + 1}", (length, width, 0.012), (x, y, 0.062), mats["water_highlight"], rotation)

        for index, spec in enumerate([(-0.72, 0.22, 0.18, 0.16), (0.68, -0.2, -0.2, 0.14)]):
            x, y, lean, height = spec
            create_cylinder(
                f"reed_or_rock_props_reed_{index + 1}",
                0.014,
                height,
                0.08 + height / 2,
                6,
                mats["reed"],
                location=(x, y),
                rotation=(lean, 0, 0),
            )


def create_transition_shoreline(detailed):
    mats = palette()
    create_box("sand_shelf", (1.22, 0.34, 0.04), (0, 0, 0.02), mats["shore_sand"], 0)
    create_box("wet_ground", (1.18, 0.22, 0.035), (0, 0.18, 0.052), mats["wet_ground"], 0)
    create_box("foam_strip", (1.12, 0.055, 0.018), (0, -0.18, 0.076), mats["foam"], 0.04)

    if detailed:
        for index, x in enumerate([-0.42, 0.0, 0.42]):
            create_box(
                f"foam_break_{index + 1}",
                (0.17, 0.032, 0.018),
                (x, -0.23 + 0.02 * (index % 2), 0.088),
                mats["foam"],
                0.1 * (-1 if index % 2 else 1),
            )

        for index, spec in enumerate([(-0.5, 0.26, 0.12), (0.56, 0.22, -0.2)]):
            x, y, rotation = spec
            create_box(f"edge_props_grass_{index + 1}", (0.18, 0.04, 0.08), (x, y, 0.09), mats["grass_light"], rotation)


def create_terrain_hill(detailed):
    mats = palette()
    create_hex_cylinder("raised_hex_base", 1.12, 0.34, -0.12, mats["earth"])
    create_hill_slope_mesh("hill_slope", mats["earth"])
    create_box("ridge_line", (0.86, 0.09, 0.08), (0.06, -0.02, 0.55), mats["rock"], -0.45)

    if detailed:
        create_box("rock_faces_front", (0.54, 0.08, 0.18), (-0.18, -0.38, 0.31), mats["rock_shadow"], -0.2)
        create_box("rock_faces_side", (0.42, 0.08, 0.16), (0.36, 0.26, 0.36), mats["rock"], 0.46)
        create_box("foot_blend_grass", (1.05, 0.16, 0.045), (-0.02, 0.54, 0.085), mats["grass"], 0.04)
        create_box("foot_blend_earth", (0.74, 0.12, 0.045), (0.2, -0.62, 0.085), mats["earth"], -0.18)
    else:
        create_box("foot_blend", (1.0, 0.18, 0.04), (0.02, 0.52, 0.08), mats["grass"], 0)


def create_buildable_city_center(detailed):
    mats = palette()
    city_mats = create_city_materials(detailed)

    create_hex_cylinder("city_hex_bedrock_side", 1.16, 0.16, -0.17, mats["bedrock"])
    create_hex_cylinder("city_hex_clay_side", 1.14, 0.14, -0.02, mats["clay"])
    create_hex_cylinder("city_grass_top", 1.09, 0.05, 0.075, mats["grass"])
    create_hex_cylinder("city_inner_lawn", 0.94, 0.018, 0.114, mats["grass_light"])

    create_box("main_city_moat_front", (0.74, 0.070, 0.018), (0, -0.300, 0.149), mats["deep_water"], 0.0)
    create_box("main_city_moat_back", (0.70, 0.056, 0.016), (0, 0.305, 0.148), mats["deep_water"], 0.0)
    create_box("main_city_moat_left", (0.055, 0.56, 0.016), (-0.310, 0.000, 0.148), mats["deep_water"], 0.0)
    create_box("main_city_moat_right", (0.055, 0.56, 0.016), (0.310, 0.000, 0.148), mats["deep_water"], 0.0)
    create_box("main_city_moat_front_highlight", (0.62, 0.018, 0.010), (0.030, -0.325, 0.164), mats["water_highlight"], -0.06)
    create_box("main_city_moat_right_highlight", (0.018, 0.42, 0.010), (0.334, 0.020, 0.163), mats["water_highlight"], 0.0)

    create_box("main_city_road_north_south", (0.13, 1.38, 0.018), (0, 0, 0.138), city_mats["path"], 0.0)
    create_box("main_city_road_west_east", (1.12, 0.12, 0.018), (0, 0, 0.14), city_mats["path"], 0.0)
    create_box("main_city_front_bridge", (0.160, 0.250, 0.024), (0, -0.300, 0.170), city_mats["path"], 0.0)
    for index, x in enumerate([-0.050, 0.000, 0.050]):
        create_box(f"main_city_bridge_slab_{index + 1}", (0.038, 0.228, 0.010), (x, -0.300, 0.187), city_mats["stone_light"], 0.0)

    create_city_wall_segment("castle_wall_front", (0, -0.27), 0.68, 0, city_mats, detailed)
    create_city_wall_segment("castle_wall_back", (0, 0.27), 0.68, 0, city_mats, detailed)
    create_city_wall_segment("castle_wall_left", (-0.34, 0), 0.54, math.pi / 2, city_mats, detailed)
    create_city_wall_segment("castle_wall_right", (0.34, 0), 0.54, math.pi / 2, city_mats, detailed)
    create_city_gatehouse("city_gate", (0, -0.335), city_mats, detailed)

    if detailed:
        create_courtyard_pavers(city_mats)

    tower_points = [(-0.34, -0.27), (0.34, -0.27), (-0.34, 0.27), (0.34, 0.27)]
    for index, point in enumerate(tower_points):
        create_city_tower(f"corner_watchtower_{index + 1}", point[0], point[1], city_mats, tall=index in (2, 3))

    create_box("central_keep_base", (0.34, 0.30, 0.18), (0, 0.03, 0.28), city_mats["stone_dark"], 0.0)
    create_box("central_keep_upper", (0.25, 0.22, 0.28), (0, 0.03, 0.47), city_mats["stone_facade"], 0.0)
    create_box("central_keep_cap_trim", (0.30, 0.26, 0.035), (0, 0.03, 0.63), city_mats["stone_dark"], 0.0)
    create_pyramid_roof("central_keep_blue_roof", 0.36, 0.32, 0.18, (0, 0.03, 0.65), city_mats["roof_light"], math.pi / 4)
    create_cylinder("central_keep_gold_spire", 0.010, 0.12, 0.85, 8, city_mats["gold"], location=(0, 0.03))
    create_cone("central_keep_gold_tip", 0.032, 0.07, 0.945, 8, city_mats["gold"], location=(0, 0.03))
    create_cylinder("central_banner_pole", 0.008, 0.22, 0.90, 6, city_mats["wood"], location=(0.08, 0.03))
    create_box("central_banner_flag", (0.11, 0.01, 0.052), (0.135, 0.03, 0.97), city_mats["banner"], 0.0)

    if detailed:
        create_roof_trim("central_keep_roof_trim_front", (0, -0.145, 0.66), 0.30, city_mats["roof"], 0.0)
        create_roof_trim("central_keep_roof_trim_right", (0.16, 0.03, 0.66), 0.25, city_mats["roof"], math.pi / 2)

    house_specs = [
        (-0.18, -0.04, 0.15, 0.11, 0.18),
        (0.19, -0.06, 0.14, 0.11, -0.1),
        (-0.16, 0.16, 0.13, 0.10, -0.34),
        (0.17, 0.16, 0.13, 0.10, 0.24),
    ]
    for index, spec in enumerate(house_specs if detailed else house_specs[:2]):
        x, y, sx, sy, rotation = spec
        create_city_house(f"inner_courtyard_house_{index + 1}", x, y, sx, sy, rotation, city_mats)

    scale_city_core(0.44, 0.68)
    create_city_block_detail_overlays(city_mats)

    if detailed:
        for index, spec in enumerate([(0.67, -0.08, 0.2), (0.74, 0.16, -0.18), (-0.72, 0.18, 0.12), (-0.68, -0.18, -0.16), (0.14, 0.68, 0.28)]):
            x, y, rotation = spec
            create_city_pine(f"city_edge_pine_{index + 1}", x, y, rotation, mats)

        for index, spec in enumerate([(-0.62, -0.62), (-0.38, -0.65), (-0.14, -0.64), (0.55, 0.62), (0.72, 0.48), (0.42, -0.64), (0.66, -0.52)]):
            x, y = spec
            create_box(f"golden_field_plot_{index + 1}", (0.18, 0.13, 0.035), (x, y, 0.16), city_mats["wheat"], 0.06 * index)

        for index, spec in enumerate([(-0.84, -0.02, 0.045), (0.82, -0.34, 0.055), (0.18, 0.72, 0.042)]):
            x, y, radius = spec
            create_rock(f"city_edge_rock_{index + 1}", x, y, radius, 0.035, mats["rock"])


def create_city_materials(detailed):
    return {
        "stone": material("city_warm_limestone", (0.68, 0.55, 0.34, 1), 0.82),
        "stone_facade": create_city_facade_texture_material(detailed),
        "stone_light": material("city_light_chipped_limestone", (0.78, 0.69, 0.50, 1), 0.82),
        "stone_dark": material("city_shadow_stone", (0.42, 0.32, 0.20, 1), 0.88),
        "roof": material("city_roof_saturated_blue", (0.02, 0.23, 0.64, 1), 0.58),
        "roof_light": material("city_roof_highlight_blue", (0.05, 0.42, 0.92, 1), 0.52),
        "roof_shadow": material("city_roof_shadow_blue", (0.01, 0.11, 0.32, 1), 0.66),
        "wood": material("city_gate_warm_wood", (0.43, 0.25, 0.10, 1), 0.84),
        "banner": material("city_banner_royal_blue", (0.02, 0.25, 0.74, 1), 0.62),
        "gold": material("city_gold_trim", (0.95, 0.68, 0.16, 1), 0.48, 0.0),
        "glass": material("city_blue_glass", (0.06, 0.33, 0.66, 0.82), 0.28, 0.0, 0.82),
        "flame_orange": material("city_torch_orange_flame", (1.00, 0.40, 0.07, 1), 0.42),
        "flame_red": material("city_torch_red_core", (0.82, 0.08, 0.02, 1), 0.46),
        "leaf": material("city_flowerbed_leaf", (0.18, 0.42, 0.10, 1), 0.78),
        "flower": material("city_flowerbed_blossom", (0.96, 0.72, 0.25, 1), 0.66),
        "path": material("city_pale_stone_road", (0.74, 0.66, 0.46, 1), 0.88),
        "wheat": material("city_wheat_field_gold", (0.88, 0.65, 0.18, 1), 0.86),
    }


def create_city_block_detail_overlays(city_mats):
    create_shield_mesh("city_detail_gate_blue_shield", 0.000, -0.172, 0.262, 0.065, 0.084, city_mats["banner"])
    create_box("city_detail_gate_shield_crown", (0.032, 0.006, 0.010), (0.000, -0.178, 0.270), city_mats["gold"], 0)
    create_box("city_detail_gate_gold_bar", (0.080, 0.007, 0.010), (0.000, -0.180, 0.238), city_mats["gold"], 0)

    for index, x in enumerate([-0.088, 0.088]):
        create_cylinder(f"city_detail_gate_torch_post_{index + 1}", 0.006, 0.072, 0.277, 6, city_mats["gold"], location=(x, -0.178))
        create_cone(f"city_detail_gate_torch_flame_{index + 1}", 0.016, 0.048, 0.337, 7, city_mats["flame_orange"], location=(x, -0.178), rotation=(0, 0, 0.2 * index))

    for index, x in enumerate([-0.040, 0.040]):
        create_box(f"city_detail_keep_window_{index + 1}", (0.020, 0.006, 0.045), (x, -0.040, 0.366), city_mats["glass"], 0)
        create_box(f"city_detail_keep_window_bar_{index + 1}", (0.024, 0.007, 0.006), (x, -0.044, 0.366), city_mats["gold"], 0)

    for index, x in enumerate([-0.150, 0.150]):
        create_box(f"city_detail_wall_banner_{index + 1}", (0.030, 0.006, 0.068), (x, -0.140, 0.250), city_mats["banner"], 0)
        create_box(f"city_detail_wall_banner_gold_{index + 1}", (0.036, 0.007, 0.008), (x, -0.144, 0.284), city_mats["gold"], 0)


def create_city_module_tower(detailed):
    city_mats = create_city_materials(detailed)
    create_city_tower("module_tower", 0, 0, city_mats, tall=detailed)


def create_city_module_gate(detailed):
    city_mats = create_city_materials(detailed)
    create_city_gatehouse("module_gate", (0, 0), city_mats, detailed)


def create_city_module_wall(detailed):
    city_mats = create_city_materials(detailed)
    create_city_wall_segment("module_wall", (0, 0), 0.46, 0, city_mats, detailed)
    if detailed:
        create_box("module_wall_banner_plate", (0.08, 0.014, 0.12), (0, -0.052, 0.245), city_mats["banner"], 0)


def create_city_module_keep(detailed):
    city_mats = create_city_materials(detailed)
    create_box("module_keep_base", (0.36, 0.31, 0.18), (0, 0, 0.22), city_mats["stone_dark"], 0)
    create_box("module_keep_upper", (0.26, 0.23, 0.30), (0, 0, 0.44), city_mats["stone_facade"], 0)
    create_box("module_keep_roof_cap", (0.31, 0.27, 0.035), (0, 0, 0.61), city_mats["stone_dark"], 0)
    create_pyramid_roof("module_keep_blue_roof", 0.38, 0.34, 0.19, (0, 0, 0.63), city_mats["roof_light"], math.pi / 4)
    if detailed:
        create_cylinder("module_keep_flag_pole", 0.008, 0.26, 0.85, 6, city_mats["wood"], location=(0.10, 0.0))
        create_box("module_keep_flag", (0.12, 0.01, 0.06), (0.16, 0, 0.93), city_mats["banner"], 0)


def create_city_module_banner(detailed):
    city_mats = create_city_materials(detailed)
    create_cylinder("module_banner_pole", 0.012, 0.42, 0.34, 8, city_mats["wood"], location=(0, 0))
    create_box("module_banner_cloth", (0.18, 0.012, 0.20), (0.09, 0, 0.44), city_mats["banner"], 0)
    if detailed:
        create_box("module_banner_gold_top", (0.05, 0.05, 0.05), (0, 0, 0.57), city_mats["roof_light"], math.pi / 4)


def create_city_module_window(detailed):
    city_mats = create_city_materials(detailed)
    create_arch_frame("module_window", 0, 0, 0.30, 0.34, 0.050, 0.12, city_mats, inner_mat=city_mats["glass"])
    create_box("module_window_wood_vertical", (0.018, 0.010, 0.180), (0, -0.041, 0.245), city_mats["wood"], 0)
    create_box("module_window_wood_horizontal", (0.105, 0.010, 0.016), (0, -0.043, 0.240), city_mats["wood"], 0)
    if detailed:
        create_box("module_window_gold_sill", (0.165, 0.024, 0.026), (0, -0.040, 0.115), city_mats["gold"], 0)


def create_city_module_door(detailed):
    city_mats = create_city_materials(detailed)
    create_arch_frame("module_door_frame", 0, 0, 0.38, 0.42, 0.060, 0.10, city_mats, inner_mat=city_mats["wood"])
    create_box("module_door_left_plank", (0.055, 0.018, 0.235), (-0.030, -0.056, 0.220), city_mats["wood"], 0)
    create_box("module_door_right_plank", (0.055, 0.018, 0.235), (0.030, -0.056, 0.220), city_mats["wood"], 0)
    for index, z in enumerate([0.165, 0.245] if detailed else [0.210]):
        create_box(f"module_door_gold_hinge_{index + 1}", (0.140, 0.016, 0.016), (0, -0.069, z), city_mats["gold"], 0)
    create_cylinder("module_door_gold_knob", 0.012, 0.010, 0.210, 8, city_mats["gold"], location=(0.038, -0.074), rotation=(math.pi / 2, 0, 0))


def create_city_module_stairs(detailed):
    city_mats = create_city_materials(detailed)
    step_count = 5 if detailed else 3
    for index in range(step_count):
        width = 0.42 - index * 0.035
        depth = 0.070
        z = 0.035 + index * 0.030
        y = -0.135 + index * 0.056
        create_box(f"module_stairs_step_{index + 1}", (width, depth, 0.040), (0, y, z), city_mats["stone_facade"], 0)
        if detailed and index % 2 == 0:
            create_box(f"module_stairs_front_chipped_edge_{index + 1}", (width * 0.78, 0.010, 0.010), (0, y - depth / 2 - 0.006, z + 0.018), city_mats["stone_light"], 0)
    create_box("module_stairs_left_cheek", (0.045, 0.34, 0.13), (-0.245, 0.005, 0.082), city_mats["stone_dark"], 0)
    create_box("module_stairs_right_cheek", (0.045, 0.34, 0.13), (0.245, 0.005, 0.082), city_mats["stone_dark"], 0)


def create_city_module_platform(detailed):
    city_mats = create_city_materials(detailed)
    create_box("module_platform_base", (0.44, 0.44, 0.055), (0, 0, 0.035), city_mats["stone_dark"], 0)
    tile_count = 4 if detailed else 3
    tile_size = 0.096 if detailed else 0.126
    spacing = 0.102 if detailed else 0.132
    for row in range(tile_count):
        for col in range(tile_count):
            x = (col - (tile_count - 1) / 2) * spacing
            y = (row - (tile_count - 1) / 2) * spacing
            mat = city_mats["stone_light"] if (row + col) % 2 == 0 else city_mats["path"]
            create_box(f"module_platform_tile_{row + 1}_{col + 1}", (tile_size, tile_size, 0.012), (x, y, 0.071), mat, 0)


def create_city_module_corner(detailed):
    city_mats = create_city_materials(detailed)
    create_city_wall_segment("module_corner_wall_a", (-0.105, 0), 0.38, 0, city_mats, detailed)
    create_city_wall_segment("module_corner_wall_b", (0.095, 0.150), 0.34, math.pi / 2, city_mats, detailed)
    create_box("module_corner_square_pier", (0.115, 0.115, 0.225), (0.095, 0.000, 0.245), city_mats["stone_dark"], 0)
    if detailed:
        create_box("module_corner_pier_cap", (0.145, 0.145, 0.038), (0.095, 0.000, 0.375), city_mats["stone"], 0)


def create_city_module_merlon(detailed):
    city_mats = create_city_materials(detailed)
    create_box("module_merlon_base_wall", (0.42, 0.085, 0.110), (0, 0, 0.095), city_mats["stone_facade"], 0)
    count = 5 if detailed else 3
    for index in range(count):
        x = (index - (count - 1) / 2) * (0.40 / count)
        create_box(f"module_merlon_tooth_{index + 1}", (0.050, 0.075, 0.072), (x, 0, 0.190), city_mats["stone_light"], 0)
    if detailed:
        for index in range(4):
            x = (index - 1.5) * 0.090
            create_box(f"module_merlon_shadow_gap_{index + 1}", (0.026, 0.088, 0.038), (x, -0.006, 0.192), city_mats["stone_dark"], 0)


def create_city_module_arch(detailed):
    city_mats = create_city_materials(detailed)
    create_arch_frame("module_freestanding_arch", 0, 0, 0.40, 0.42, 0.070, 0.07, city_mats, inner_mat=None)
    if detailed:
        create_box("module_arch_gold_keystone", (0.050, 0.078, 0.055), (0, -0.002, 0.420), city_mats["gold"], 0)


def create_city_module_roof_tile(detailed):
    city_mats = create_city_materials(detailed)
    create_box("module_roof_tile_stone_socket", (0.30, 0.30, 0.040), (0, 0, 0.040), city_mats["stone_dark"], 0)
    create_pyramid_roof("module_roof_tile_blue_pyramid", 0.32, 0.32, 0.28, (0, 0, 0.060), city_mats["roof_light"], math.pi / 4)
    create_cone("module_roof_tile_gold_tip", 0.035, 0.080, 0.380, 4, city_mats["gold"], location=(0, 0), rotation=(0, 0, math.pi / 4))
    if detailed:
        for index, y in enumerate([-0.070, 0.000, 0.070]):
            create_box(f"module_roof_tile_blue_rib_{index + 1}", (0.220 - abs(y) * 0.9, 0.012, 0.012), (0, y, 0.165 + abs(y) * 0.40), city_mats["roof_shadow"], 0)


def create_city_module_torch(detailed):
    city_mats = create_city_materials(detailed)
    create_box("module_torch_wall_bracket", (0.090, 0.080, 0.045), (0, 0, 0.100), city_mats["stone_dark"], 0)
    create_cylinder("module_torch_post", 0.020, 0.220, 0.220, 6, city_mats["gold"], location=(0, 0))
    create_cylinder("module_torch_bowl", 0.055, 0.045, 0.350, 8, city_mats["gold"], location=(0, 0))
    create_cone("module_torch_outer_flame", 0.060, 0.180, 0.455, 7, city_mats["flame_orange"], location=(0, 0), rotation=(0, 0, 0.2))
    if detailed:
        create_cone("module_torch_inner_flame", 0.034, 0.145, 0.475, 7, city_mats["flame_red"], location=(0, 0), rotation=(0, 0, -0.15))


def create_city_module_shield(detailed):
    city_mats = create_city_materials(detailed)
    create_shield_mesh("module_shield_gold_rim", 0, 0.000, 0.260, 0.315, 0.370, city_mats["gold"])
    create_shield_mesh("module_shield_blue_plate", 0, -0.018, 0.260, 0.260, 0.310, city_mats["banner"])
    create_box("module_shield_crown_base", (0.120, 0.012, 0.030), (0, -0.028, 0.285), city_mats["gold"], 0)
    create_cone("module_shield_crown_tip_center", 0.030, 0.075, 0.340, 4, city_mats["gold"], location=(0, -0.031), rotation=(0, 0, math.pi / 4))
    if detailed:
        create_cone("module_shield_crown_tip_left", 0.022, 0.058, 0.328, 4, city_mats["gold"], location=(-0.050, -0.031), rotation=(0, 0, math.pi / 4))
        create_cone("module_shield_crown_tip_right", 0.022, 0.058, 0.328, 4, city_mats["gold"], location=(0.050, -0.031), rotation=(0, 0, math.pi / 4))


def create_city_module_flowerbed(detailed):
    city_mats = create_city_materials(detailed)
    create_cylinder("module_flowerbed_stone_ring", 0.210, 0.065, 0.055, 8, city_mats["stone_dark"], location=(0, 0), rotation=(0, 0, math.pi / 8))
    create_cylinder("module_flowerbed_soil", 0.165, 0.035, 0.095, 12, city_mats["wood"], location=(0, 0))
    for index in range(7 if detailed else 4):
        angle = index * math.tau / (7 if detailed else 4)
        radius = 0.075 if index % 2 else 0.035
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius
        create_cone(f"module_flowerbed_leaf_{index + 1}", 0.055, 0.085, 0.150, 7, city_mats["leaf"], location=(x, y), rotation=(0, 0, angle))
    for index, (x, y) in enumerate([(0.000, 0.010), (0.060, -0.035), (-0.065, -0.020)] if detailed else [(0.000, 0.010)]):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, radius=0.026, location=(x, y, 0.185))
        obj = bpy.context.object
        obj.name = f"module_flowerbed_blossom_{index + 1}"
        obj.scale = (1.0, 1.0, 0.55)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.data.materials.append(city_mats["flower"])


def create_city_module_kit(detailed):
    module_builders = [
        create_city_module_tower,
        create_city_module_gate,
        create_city_module_wall,
        create_city_module_roof_tile,
        create_city_module_banner,
        create_city_module_window,
        create_city_module_door,
        create_city_module_stairs,
        create_city_module_platform,
        create_city_module_corner,
        create_city_module_merlon,
        create_city_module_arch,
        create_city_module_torch,
        create_city_module_shield,
        create_city_module_flowerbed,
    ]
    columns = 5
    spacing_x = 0.72
    spacing_y = 0.68

    for index, builder in enumerate(module_builders):
        row = index // columns
        col = index % columns
        target_x = (col - (columns - 1) / 2) * spacing_x
        target_y = ((len(module_builders) - 1) // columns / 2 - row) * spacing_y
        marker = len(bpy.context.scene.objects)
        builder(detailed)
        translate_objects_since(marker, target_x, target_y, 0)


def translate_objects_since(start_index, offset_x, offset_y, offset_z):
    for obj in list(bpy.context.scene.objects)[start_index:]:
        if obj.type != "MESH":
            continue

        obj.location.x += offset_x
        obj.location.y += offset_y
        obj.location.z += offset_z


def create_arch_frame(name, x, y, width, height, depth, base_z, mats, inner_mat):
    side_width = width * 0.18
    opening_width = width - side_width * 2
    side_height = height * 0.62
    create_box(f"{name}_left_pier", (side_width, depth, side_height), (x - opening_width / 2, y, base_z + side_height / 2), mats["stone_facade"], 0)
    create_box(f"{name}_right_pier", (side_width, depth, side_height), (x + opening_width / 2, y, base_z + side_height / 2), mats["stone_facade"], 0)
    create_box(f"{name}_sill", (width, depth * 1.08, height * 0.10), (x, y, base_z + height * 0.05), mats["stone_dark"], 0)

    arch_radius = opening_width / 2
    stone_count = 7
    for index in range(stone_count):
        t = index / (stone_count - 1)
        angle = math.pi * (1 - t)
        stone_x = x + math.cos(angle) * arch_radius
        stone_z = base_z + side_height + math.sin(angle) * arch_radius * 0.95
        create_box(
            f"{name}_arch_stone_{index + 1}",
            (width * 0.125, depth * 1.10, height * 0.125),
            (stone_x, y, stone_z),
            mats["stone_light"] if index % 2 == 0 else mats["stone_facade"],
            -angle + math.pi / 2,
        )

    if inner_mat is not None:
        create_box(f"{name}_inner_panel", (opening_width * 0.70, depth * 0.45, height * 0.58), (x, y - depth * 0.32, base_z + height * 0.36), inner_mat, 0)


def create_shield_mesh(name, x, y, center_z, width, height, mat):
    depth = 0.010
    half_w = width / 2
    half_h = height / 2
    verts_front = [
        (x - half_w, y - depth / 2, center_z + half_h * 0.80),
        (x + half_w, y - depth / 2, center_z + half_h * 0.80),
        (x + half_w * 0.82, y - depth / 2, center_z - half_h * 0.25),
        (x, y - depth / 2, center_z - half_h),
        (x - half_w * 0.82, y - depth / 2, center_z - half_h * 0.25),
    ]
    verts_back = [(vx, y + depth / 2, vz) for vx, _, vz in verts_front]
    faces = [(0, 1, 2, 3, 4), (9, 8, 7, 6, 5)]
    for index in range(5):
        faces.append((index, (index + 1) % 5, 5 + ((index + 1) % 5), 5 + index))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts_front + verts_back, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    bpy.context.collection.objects.link(obj)
    return obj


def create_hill_slope_mesh(name, mat):
    verts = [(0, 0, 0.72)]
    inner_radius = 0.44
    outer_radius = 0.96

    for index in range(6):
        angle = math.pi / 6 + index * math.tau / 6
        ridge_bias = 0.12 if index in (1, 4) else 0.0
        verts.append((math.cos(angle) * inner_radius, math.sin(angle) * inner_radius, 0.44 + ridge_bias))

    for index in range(6):
        angle = math.pi / 6 + index * math.tau / 6
        verts.append((math.cos(angle) * outer_radius, math.sin(angle) * outer_radius, 0.16))

    faces = []
    for index in range(6):
        next_index = 1 + ((index + 1) % 6)
        current = 1 + index
        faces.append((0, current, next_index))

    for index in range(6):
        current_inner = 1 + index
        next_inner = 1 + ((index + 1) % 6)
        current_outer = 7 + index
        next_outer = 7 + ((index + 1) % 6)
        faces.append((current_inner, current_outer, next_outer, next_inner))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    bpy.context.collection.objects.link(obj)
    return obj


def create_grassland_side_band(name, bottom_z, top_z, radius, mat, rng):
    outline = create_hex_outline_points(radius, subdivisions=8)
    verts = []
    faces = []

    for index, (x, y) in enumerate(outline):
        jitter = 1 + rng.uniform(-0.012, 0.012)
        verts.append((x * jitter, y * jitter, bottom_z + rng.uniform(-0.006, 0.006)))
        verts.append((x * (jitter + rng.uniform(-0.004, 0.006)), y * (jitter + rng.uniform(-0.004, 0.006)), top_z + rng.uniform(-0.004, 0.004)))

        next_index = (index + 1) % len(outline)
        faces.append((index * 2, next_index * 2, next_index * 2 + 1, index * 2 + 1))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    bpy.context.collection.objects.link(obj)
    return obj


def create_grassland_top_mesh(name, mat, rng):
    verts = [(0, 0, 0.128)]
    uv_points = [(0.5, 0.5)]
    rings = 16
    outline_steps = 72

    for ring in range(1, rings + 1):
        ring_radius = ring / rings
        outline = create_hex_outline_points(1.12 * ring_radius, subdivisions=outline_steps // 6)

        for index, (x, y) in enumerate(outline):
            edge_falloff = ring / rings
            z = 0.126 + math.sin(index * 1.35 + ring * 0.48) * 0.0025 * edge_falloff + rng.uniform(-0.0012, 0.0012)
            verts.append((x, y, z))
            uv_points.append((0.5 + x / 2.28, 0.5 + y / 2.28))

    faces = []
    ring_start = 1
    previous_start = 0

    for ring in range(1, rings + 1):
        steps = outline_steps

        if ring == 1:
            for index in range(steps):
                faces.append((0, ring_start + index, ring_start + ((index + 1) % steps)))
        else:
            for index in range(steps):
                current = ring_start + index
                current_next = ring_start + ((index + 1) % steps)
                previous = previous_start + index
                previous_next = previous_start + ((index + 1) % steps)
                faces.append((previous, current, current_next, previous_next))

        previous_start = ring_start
        ring_start += steps

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    uv_layer = mesh.uv_layers.new(name="grassland_top_uv")

    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = uv_points[vertex_index]

    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    bpy.context.collection.objects.link(obj)
    return obj


def create_hex_outline_points(radius, subdivisions):
    corners = []

    for index in range(6):
        angle = math.pi / 6 + index * math.tau / 6
        corners.append((math.cos(angle) * radius, math.sin(angle) * radius))

    points = []
    for index in range(6):
        start = corners[index]
        end = corners[(index + 1) % 6]

        for step in range(subdivisions):
            t = step / subdivisions
            points.append((start[0] * (1 - t) + end[0] * t, start[1] * (1 - t) + end[1] * t))

    return points


def create_grassland_side_strata(mats, rng, detailed):
    row_specs = [
        (-0.205, mats["bedrock"], 0.036, 0.016),
        (-0.128, mats["gravel"], 0.044, 0.014),
        (-0.052, mats["clay"], 0.052, 0.012),
        (0.018, mats["loam"], 0.060, 0.010),
    ]
    per_edge = 7 if detailed else 3
    radius = 1.14

    for edge in range(6):
        start_angle = math.pi / 6 + edge * math.tau / 6
        end_angle = math.pi / 6 + (edge + 1) * math.tau / 6
        start = (math.cos(start_angle) * radius, math.sin(start_angle) * radius)
        end = (math.cos(end_angle) * radius, math.sin(end_angle) * radius)
        edge_angle = math.atan2(end[1] - start[1], end[0] - start[0])
        normal_angle = edge_angle - math.pi / 2

        for layer_index, (z, mat, length_base, height_base) in enumerate(row_specs):
            for segment in range(per_edge):
                if detailed and rng.random() < 0.22:
                    continue

                t = (segment + 0.5) / per_edge
                x = start[0] * (1 - t) + end[0] * t + math.cos(normal_angle) * rng.uniform(0.002, 0.010)
                y = start[1] * (1 - t) + end[1] * t + math.sin(normal_angle) * rng.uniform(0.002, 0.010)
                create_box(
                    f"embedded_side_detail_{edge + 1}_{layer_index + 1}_{segment + 1}",
                    (length_base * rng.uniform(0.55, 1.08), 0.010, height_base * rng.uniform(0.60, 1.10)),
                    (x, y, z + rng.uniform(-0.006, 0.006)),
                    mat,
                    edge_angle + rng.uniform(-0.08, 0.08),
                )


def create_grassland_surface_mesh(name, mat):
    verts = [(0, 0, 0.136)]
    radius = 1.02

    for index in range(6):
        angle = math.pi / 6 + index * math.tau / 6
        height = 0.124 + (0.01 if index in (1, 4) else 0.0) - (0.006 if index == 3 else 0.0)
        verts.append((math.cos(angle) * radius, math.sin(angle) * radius, height))

    faces = []
    for index in range(6):
        faces.append((0, 1 + index, 1 + ((index + 1) % 6)))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="grassland_top_uv")

    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            vx, vy, _ = mesh.vertices[vertex_index].co
            uv_layer.data[loop_index].uv = (0.5 + vx / 2.05, 0.5 + vy / 2.05)

    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    bpy.context.collection.objects.link(obj)
    return obj


def create_grassland_side_blocks(mats, detailed):
    row_specs = [
        ("bedrock_block", -0.18, 0.07, mats["bedrock"], 3),
        ("gravel_block", -0.105, 0.055, mats["gravel"], 4),
        ("clay_block", -0.038, 0.052, mats["clay"], 4),
        ("loam_block", 0.032, 0.048, mats["loam"], 5),
        ("turf_lip", 0.09, 0.036, mats["grass_cap"], 5),
    ]
    radius = 1.13
    rng = seeded_rng("terrain-grassland-side-blocks", detailed)

    for edge_index in range(6):
        angle_a = math.pi / 6 + edge_index * math.tau / 6
        angle_b = math.pi / 6 + ((edge_index + 1) % 6) * math.tau / 6
        ax, ay = math.cos(angle_a) * radius, math.sin(angle_a) * radius
        bx, by = math.cos(angle_b) * radius, math.sin(angle_b) * radius
        edge_angle = math.atan2(by - ay, bx - ax)
        edge_length = math.hypot(bx - ax, by - ay)
        normal_angle = edge_angle - math.pi / 2
        mid_x, mid_y = (ax + bx) / 2, (ay + by) / 2

        for row_name, z, height, mat, divisions in row_specs:
            segment_count = divisions if detailed else max(2, divisions - 2)
            segment_length = edge_length / segment_count

            for segment in range(segment_count):
                offset = (segment - (segment_count - 1) / 2) * segment_length
                jitter = rng.uniform(-0.025, 0.025) if detailed else 0
                x = mid_x + math.cos(edge_angle) * offset + math.cos(normal_angle) * (0.035 + jitter)
                y = mid_y + math.sin(edge_angle) * offset + math.sin(normal_angle) * (0.035 + jitter)
                length = segment_length * rng.uniform(0.82, 0.98)
                thickness = rng.uniform(0.075, 0.105)
                block_height = height * rng.uniform(0.86, 1.12)
                create_box(
                    f"{row_name}_edge_{edge_index + 1}_{segment + 1}",
                    (length, thickness, block_height),
                    (x, y, z),
                    mat,
                    edge_angle,
                )


def create_grassland_texture_material(detailed):
    size = 768 if detailed else 384
    rng = seeded_rng("terrain-grassland-texture", detailed)
    base = (0.22, 0.34, 0.08)
    image = bpy.data.images.new("terrain_grassland_baked_albedo", width=size, height=size, alpha=True)
    dirt_patches = [
        (0.36, 0.35, 0.20, 0.055, -0.28),
        (0.60, 0.43, 0.18, 0.050, 0.20),
        (0.30, 0.61, 0.14, 0.040, 0.42),
        (0.52, 0.28, 0.13, 0.036, -0.54),
    ]
    moss_patches = [
        (0.42, 0.25, 0.22, 0.08, 0.18),
        (0.58, 0.70, 0.20, 0.075, -0.28),
        (0.19, 0.55, 0.18, 0.055, 0.38),
        (0.70, 0.53, 0.15, 0.05, -0.45),
    ]
    flowers = [(rng.random(), rng.random(), rng.choice([(0.92, 0.88, 0.74), (0.84, 0.62, 0.14), (0.48, 0.36, 0.70)])) for _ in range(260 if detailed else 80)]
    pebbles = [(rng.random(), rng.random(), rng.uniform(0.004, 0.011)) for _ in range(130 if detailed else 40)]
    pixels = []

    for y in range(size):
        v = y / (size - 1)
        for x in range(size):
            u = x / (size - 1)
            noise = value_noise(u, v)
            color = [
                clamp(base[0] + noise * 0.055 + rng.uniform(-0.012, 0.012)),
                clamp(base[1] + noise * 0.075 + rng.uniform(-0.012, 0.012)),
                clamp(base[2] + noise * 0.030 + rng.uniform(-0.008, 0.008)),
            ]
            fine_noise = value_noise(u * 2.7 + 0.11, v * 2.7 - 0.29)
            blade_noise = math.sin(u * 720.0 + fine_noise * 8.0) * 0.010 + math.sin(v * 680.0) * 0.006
            color = [
                clamp(color[0] + blade_noise * 0.5),
                clamp(color[1] + blade_noise),
                clamp(color[2] + blade_noise * 0.25),
            ]

            for patch_u, patch_v, radius_x, radius_y, angle in moss_patches:
                weight = ellipse_weight(u, v, patch_u, patch_v, radius_x, radius_y, angle)
                if weight > 0:
                    irregular = clamp((value_noise(u * 3.4 + patch_u, v * 3.4 + patch_v) + 0.55) * 0.75)
                    feather = weight * irregular
                    color = mix_color(color, (0.32, 0.45, 0.13), feather * 0.34)

            for patch_u, patch_v, radius_x, radius_y, angle in dirt_patches:
                weight = ellipse_weight(u, v, patch_u, patch_v, radius_x, radius_y, angle)
                if weight > 0:
                    irregular = clamp((value_noise(u * 4.1 - patch_v, v * 4.1 + patch_u) + 0.46) * 0.72)
                    broken_edge = weight * irregular
                    color = mix_color(color, (0.34, 0.25, 0.13), broken_edge * 0.38)

            pixels.extend([color[0], color[1], color[2], 1.0])

    for pebble_u, pebble_v, radius in pebbles:
        paint_disc(pixels, size, pebble_u, pebble_v, radius, (0.50, 0.48, 0.40), 0.82)

    for flower_u, flower_v, flower_color in flowers:
        paint_disc(pixels, size, flower_u, flower_v, 0.0048, flower_color, 0.9)

    image.pixels.foreach_set(pixels)
    image.pack()

    if OUTPUT_TEXTURE_ROOT is not None:
        image.filepath_raw = str(OUTPUT_TEXTURE_ROOT / "terrain-grassland-albedo.png")
        image.file_format = "PNG"
        image.save()

    return image_material("terrain_grassland_baked_top", image)


def create_city_facade_texture_material(detailed):
    size = 512 if detailed else 256
    rng = random.Random(911 if detailed else 119)
    image = bpy.data.images.new("buildable_city_center_facade_albedo", width=size, height=size, alpha=True)
    pixels = []

    for y in range(size):
        v = y / (size - 1)
        for x in range(size):
            u = x / (size - 1)
            mortar_x = 1.0 if abs((u * 9) % 1 - 0.02) < 0.018 else 0.0
            mortar_y = 1.0 if abs((v * 7) % 1 - 0.02) < 0.018 else 0.0
            noise = value_noise(u, v) * 0.035 + rng.uniform(-0.01, 0.01)
            base = [0.66 + noise, 0.54 + noise * 0.7, 0.35 + noise * 0.45]

            if mortar_x or mortar_y:
                base = mix_color(base, (0.46, 0.38, 0.25), 0.65)

            for window_u, window_v, window_w, window_h in [
                (0.25, 0.38, 0.045, 0.12),
                (0.50, 0.34, 0.045, 0.12),
                (0.74, 0.40, 0.045, 0.12),
                (0.36, 0.62, 0.04, 0.10),
                (0.64, 0.64, 0.04, 0.10),
            ]:
                if abs(u - window_u) <= window_w and abs(v - window_v) <= window_h:
                    base = mix_color(base, (0.18, 0.15, 0.12), 0.9)

            if 0.08 < v < 0.16 and int(u * 15) % 2 == 0:
                base = mix_color(base, (0.42, 0.34, 0.22), 0.62)

            pixels.extend([clamp(base[0]), clamp(base[1]), clamp(base[2]), 1.0])

    image.pixels.foreach_set(pixels)
    image.pack()

    if OUTPUT_TEXTURE_ROOT is not None:
        image.filepath_raw = str(OUTPUT_TEXTURE_ROOT / "buildable-city-center-facade.png")
        image.file_format = "PNG"
        image.save()

    return image_material("buildable_city_center_facade", image)


def paint_disc(pixels, size, center_u, center_v, radius, color, alpha):
    center_x = int(center_u * (size - 1))
    center_y = int(center_v * (size - 1))
    pixel_radius = max(1, int(radius * size))

    for y in range(max(0, center_y - pixel_radius), min(size, center_y + pixel_radius + 1)):
        for x in range(max(0, center_x - pixel_radius), min(size, center_x + pixel_radius + 1)):
            distance = math.hypot(x - center_x, y - center_y) / pixel_radius

            if distance > 1:
                continue

            weight = alpha * (1 - distance)
            offset = (y * size + x) * 4
            mixed = mix_color(pixels[offset : offset + 3], color, weight)
            pixels[offset : offset + 3] = mixed


def value_noise(u, v):
    return (
        math.sin(u * 57.0 + v * 13.0) * 0.45
        + math.sin(u * 111.0 - v * 47.0) * 0.25
        + math.sin((u + v) * 173.0) * 0.18
    )


def ellipse_weight(u, v, center_u, center_v, radius_u, radius_v, angle):
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    du = u - center_u
    dv = v - center_v
    local_u = du * cos_a - dv * sin_a
    local_v = du * sin_a + dv * cos_a
    distance = (local_u / radius_u) ** 2 + (local_v / radius_v) ** 2

    if distance >= 1:
        return 0

    return (1 - distance) ** 1.6


def mix_color(left, right, weight):
    return [left[index] * (1 - weight) + right[index] * weight for index in range(3)]


def clamp(value):
    return max(0.0, min(1.0, value))


def create_scattered_points(rng, count, radius, min_distance):
    points = []
    attempts = 0

    while len(points) < count and attempts < count * 80:
        attempts += 1
        x = rng.uniform(-radius, radius)
        y = rng.uniform(-radius, radius)

        if not point_inside_hex(x, y, radius):
            continue

        if all(math.hypot(x - px, y - py) >= min_distance for px, py in points):
            points.append((x, y))

    return points


def create_scattered_annulus_points(rng, count, inner_radius, outer_radius, min_distance):
    points = []
    attempts = 0

    while len(points) < count and attempts < count * 110:
        attempts += 1
        x = rng.uniform(-outer_radius, outer_radius)
        y = rng.uniform(-outer_radius, outer_radius)
        radial_distance = math.hypot(x, y)

        if radial_distance < inner_radius or radial_distance > outer_radius:
            continue

        if not point_inside_hex(x, y, outer_radius):
            continue

        if all(math.hypot(x - px, y - py) >= min_distance for px, py in points):
            points.append((x, y))

    return points


def create_clustered_flower_points(rng):
    clusters = [
        (-0.48, 0.22, 8, 0.085, 0.055),
        (0.18, 0.34, 7, 0.075, 0.05),
        (0.44, -0.18, 7, 0.08, 0.052),
        (-0.12, -0.42, 6, 0.07, 0.048),
        (0.58, 0.20, 5, 0.065, 0.045),
    ]
    points = []

    for center_x, center_y, count, spread_x, spread_y in clusters:
        for _ in range(count):
            for _attempt in range(24):
                x = center_x + rng.uniform(-spread_x, spread_x)
                y = center_y + rng.uniform(-spread_y, spread_y)

                if point_inside_hex(x, y, 0.92):
                    points.append((x, y))
                    break

    return points


def create_grassland_surface_zones(mats, detailed):
    rng = seeded_rng("terrain-grassland-surface-zones", detailed)
    patch_mats = {
        "light": material("grassland_subtle_light_grass_overlay", (0.36, 0.46, 0.14, 0.38), 0.96, 0.0, 0.38),
        "dark": material("grassland_subtle_dark_grass_overlay", (0.10, 0.19, 0.06, 0.34), 0.98, 0.0, 0.34),
        "soil": material("grassland_subtle_dry_soil_overlay", (0.36, 0.27, 0.15, 0.50), 0.98, 0.0, 0.50),
    }
    clusters = [
        ("open_center_light_grass", -0.12, 0.10, 0.23, 0.075, -0.18, patch_mats["light"], 4),
        ("dark_moist_grass_patch", 0.34, 0.21, 0.20, 0.062, 0.52, patch_mats["dark"], 4),
        ("dry_soil_track", 0.35, -0.30, 0.22, 0.042, -0.23, patch_mats["soil"], 5),
        ("small_dry_soil_break", -0.49, -0.05, 0.12, 0.034, 0.38, patch_mats["soil"], 3),
        ("edge_light_grass_patch", -0.55, 0.42, 0.12, 0.038, -0.40, patch_mats["light"], 3),
        ("shadow_edge_grass_patch", 0.62, -0.03, 0.12, 0.040, 0.10, patch_mats["dark"], 3),
    ]

    if detailed:
        clusters.extend(
            [
                ("thin_bare_scuff_a", -0.20, -0.28, 0.12, 0.024, 0.72, patch_mats["soil"], 3),
                ("thin_bare_scuff_b", 0.06, -0.06, 0.11, 0.022, -0.58, patch_mats["soil"], 3),
                ("small_light_grass_island", 0.05, 0.52, 0.10, 0.030, 0.18, patch_mats["light"], 3),
            ]
        )

    for name, x, y, radius_x, radius_y, rotation, mat, count in clusters:
        for index in range(count):
            local_x = x + rng.uniform(-radius_x * 0.34, radius_x * 0.34)
            local_y = y + rng.uniform(-radius_y * 0.72, radius_y * 0.72)

            if not point_inside_hex(local_x, local_y, 0.98):
                continue

            create_ellipse_disc(
                f"terrain_grassland_{name}_{index + 1}",
                radius_x * rng.uniform(0.46, 0.76),
                radius_y * rng.uniform(0.55, 0.95),
                0.134 + index * 0.0002,
                (local_x, local_y),
                rotation + rng.uniform(-0.38, 0.38),
                mat,
            )


def point_inside_hex(x, y, radius):
    qx = abs(x)
    qy = abs(y)
    return qx <= radius * 0.86 and qy <= radius and (math.sqrt(3) * qx + qy) <= math.sqrt(3) * radius


def create_ellipse_disc(name, radius_x, radius_y, center_z, location, rotation_z, mat):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=18,
        radius=1,
        depth=0.006,
        location=(location[0], location[1], center_z),
        rotation=(0, 0, rotation_z),
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = (radius_x, radius_y, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def create_grass_tuft(name, x, y, rotation, mats, scale=1.0):
    blade_specs = [
        (-0.032, 0.0, 0.028, 0.12, rotation - 0.58, mats["grass_light"]),
        (0.0, 0.014, 0.026, 0.15, rotation - 0.12, mats["grass"]),
        (0.03, -0.004, 0.026, 0.115, rotation + 0.38, mats["grass_dark"]),
        (0.012, -0.026, 0.02, 0.095, rotation + 0.78, mats["grass_light"]),
        (-0.018, 0.028, 0.018, 0.085, rotation - 0.96, mats["grass"]),
        (0.026, 0.028, 0.018, 0.09, rotation + 1.08, mats["grass_dark"]),
    ]

    for index, spec in enumerate(blade_specs):
        offset_x, offset_y, width, height, blade_rotation, mat = spec
        create_grass_blade_mesh(
            f"{name}_blade_{index + 1}",
            x + offset_x * scale,
            y + offset_y * scale,
            blade_rotation,
            height * scale,
            width * scale,
            mat,
        )


def create_micro_blade(name, x, y, rotation, height, mat):
    create_grass_blade_mesh(name, x, y, rotation, height, 0.012, mat)


def create_flat_flower_dot(name, x, y, mat):
    create_ellipse_disc(name, 0.015, 0.011, 0.136, (x, y), 0.0, mat)


def create_grass_blade_mesh(name, x, y, rotation, height, width, mat):
    lean = height * 0.26
    side_x = math.cos(rotation + math.pi / 2) * width / 2
    side_y = math.sin(rotation + math.pi / 2) * width / 2
    tip_x = x + math.cos(rotation) * lean
    tip_y = y + math.sin(rotation) * lean
    base_z = 0.126

    verts = [
        (x - side_x, y - side_y, base_z),
        (x + side_x, y + side_y, base_z),
        (tip_x, tip_y, base_z + height),
    ]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], [(0, 1, 2)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    bpy.context.collection.objects.link(obj)
    return obj


def create_flower_dot(name, x, y, mat):
    stem_mat = bpy.data.materials.get("shore_reed_green") or material("shore_reed_green", (0.42, 0.53, 0.26, 1), 0.84)
    create_cylinder(f"{name}_stem", 0.006, 0.045, 0.152, 6, stem_mat, location=(x, y))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, radius=0.018, location=(x, y, 0.18))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (1.2, 1.2, 0.55)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def create_rock(name, x, y, radius, height, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=radius, location=(x, y, 0.13 + height / 2))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (1.35, 0.86, height / radius)
    obj.rotation_euler[2] = (x + y) * 0.7
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def create_city_tower(name, x, y, mats, tall):
    height = 0.34 if tall else 0.29
    create_cylinder(f"{name}_plinth", 0.112, 0.055, 0.157, 6, mats["stone_dark"], location=(x, y))
    create_cylinder(f"{name}_stone_body", 0.088, height, 0.185 + height / 2, 8, mats["stone_facade"], location=(x, y))
    create_cylinder(f"{name}_top_stone_ring", 0.105, 0.035, 0.185 + height + 0.018, 8, mats["stone_dark"], location=(x, y))
    create_pyramid_roof(f"{name}_blue_roof", 0.20, 0.20, 0.14, (x, y, 0.185 + height), mats["roof"], math.pi / 4)
    create_roof_trim(f"{name}_roof_front_trim", (x, y - 0.088, 0.196 + height), 0.17, mats["roof_shadow"], 0)
    create_cylinder(f"{name}_gold_spire", 0.008, 0.07, 0.185 + height + 0.18, 8, mats["gold"], location=(x, y))
    create_cone(f"{name}_gold_tip", 0.024, 0.055, 0.185 + height + 0.24, 8, mats["gold"], location=(x, y))
    create_box(f"{name}_window_shadow_front", (0.026, 0.009, 0.052), (x, y - 0.091, 0.285), mats["stone_dark"], 0.0)
    if tall:
        create_box(f"{name}_banner_strip", (0.030, 0.010, 0.115), (x + 0.052, y - 0.088, 0.34), mats["banner"], 0)


def create_city_house(name, x, y, size_x, size_y, rotation, mats):
    create_box(f"{name}_body", (size_x, size_y, 0.11), (x, y, 0.205), mats["stone"], rotation)
    create_pyramid_roof(f"{name}_roof", size_x * 1.12, size_y * 1.12, 0.09, (x, y, 0.26), mats["roof"], rotation + math.pi / 4)
    create_box(f"{name}_door_shadow", (size_x * 0.18, 0.01, 0.05), (x, y - size_y * 0.54, 0.19), mats["stone_dark"], rotation)


def create_city_wall_segment(name, center, length, rotation, mats, detailed):
    x, y = center
    create_box(f"{name}_facade", (length, 0.070, 0.17), (x, y, 0.225), mats["stone_facade"], rotation)
    create_box(f"{name}_top_walkway", (length + 0.04, 0.095, 0.035), (x, y, 0.327), mats["stone_dark"], rotation)

    if detailed:
        crenel_count = max(3, int(length / 0.09))
        for index in range(crenel_count):
            offset = (index - (crenel_count - 1) / 2) * (length / crenel_count)
            local_x = math.cos(rotation) * offset
            local_y = math.sin(rotation) * offset
            create_box(
                f"{name}_crenel_{index + 1}",
                (0.038, 0.050, 0.052),
                (x + local_x, y + local_y, 0.372),
                mats["stone"],
                rotation,
            )


def create_city_gatehouse(name, center, mats, detailed):
    x, y = center
    create_box(f"{name}_stone_arch", (0.24, 0.12, 0.24), (x, y, 0.25), mats["stone_facade"], 0.0)
    create_box(f"{name}_dark_arch_opening", (0.135, 0.028, 0.145), (x, y - 0.063, 0.225), mats["stone_dark"], 0.0)
    create_box(f"{name}_wood_door", (0.112, 0.020, 0.125), (x, y - 0.079, 0.205), mats["wood"], 0.0)
    create_box(f"{name}_gold_crossbar", (0.126, 0.014, 0.018), (x, y - 0.091, 0.245), mats["gold"], 0.0)
    create_pyramid_roof(f"{name}_blue_roof", 0.285, 0.18, 0.11, (x, y, 0.365), mats["roof"], math.pi / 4)

    if detailed:
        create_box(f"{name}_left_banner", (0.032, 0.012, 0.100), (x - 0.095, y - 0.064, 0.244), mats["banner"], 0.0)
        create_box(f"{name}_right_banner", (0.032, 0.012, 0.100), (x + 0.095, y - 0.064, 0.244), mats["banner"], 0.0)


def scale_city_core(scale_xy, scale_z):
    core_prefixes = (
        "castle_wall_",
        "city_gate",
        "corner_watchtower_",
        "central_keep_",
        "central_banner_",
        "inner_courtyard_house_",
        "courtyard_paver_",
    )
    ground_z = 0.14

    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or not obj.name.startswith(core_prefixes):
            continue

        obj.location.x *= scale_xy
        obj.location.y *= scale_xy
        obj.location.z = ground_z + (obj.location.z - ground_z) * scale_z
        obj.scale.x *= scale_xy
        obj.scale.y *= scale_xy
        obj.scale.z *= scale_z


def create_courtyard_pavers(mats):
    paver_specs = [
        (-0.18, -0.18, 0.09, 0.055, 0.02),
        (-0.04, -0.18, 0.08, 0.05, -0.04),
        (0.12, -0.18, 0.10, 0.052, 0.03),
        (-0.17, 0.10, 0.07, 0.05, -0.02),
        (0.02, 0.12, 0.10, 0.05, 0.04),
        (0.18, 0.08, 0.08, 0.045, -0.04),
    ]

    for index, spec in enumerate(paver_specs):
        x, y, sx, sy, rotation = spec
        create_box(f"courtyard_paver_{index + 1}", (sx, sy, 0.01), (x, y, 0.151), mats["path"], rotation)


def create_roof_trim(name, location, length, mat, rotation):
    create_box(name, (length, 0.018, 0.016), location, mat, rotation)


def create_city_pine(name, x, y, rotation, mats):
    create_cylinder(f"{name}_trunk", 0.018, 0.12, 0.21, 6, mats["earth"], location=(x, y))
    create_cone(f"{name}_lower_crown", 0.11, 0.22, 0.35, 8, mats["grass_dark"], location=(x, y), rotation=(0, 0, rotation))
    create_cone(f"{name}_upper_crown", 0.085, 0.18, 0.48, 8, mats["grass"], location=(x, y), rotation=(0, 0, rotation + 0.22))


def create_pyramid_roof(name, size_x, size_y, height, location, mat, rotation_z):
    verts = [
        (-size_x / 2, -size_y / 2, 0),
        (size_x / 2, -size_y / 2, 0),
        (size_x / 2, size_y / 2, 0),
        (-size_x / 2, size_y / 2, 0),
        (0, 0, height),
    ]
    faces = [(0, 1, 2, 3), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.rotation_euler[2] = rotation_z
    obj.data.materials.append(mat)
    bpy.context.collection.objects.link(obj)
    return obj


def create_hex_cylinder(name, radius, depth, center_z, mat):
    return create_cylinder(name, radius, depth, center_z, 6, mat, rotation=(0, 0, math.pi / 6))


def create_cylinder(name, radius, depth, center_z, vertices, mat, location=(0, 0), rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=(location[0], location[1], center_z),
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def create_cone(name, radius, depth, center_z, vertices, mat, location=(0, 0), rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=radius,
        radius2=0,
        depth=depth,
        location=(location[0], location[1], center_z),
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def create_box(name, size, location, mat, rotation_z):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location, rotation=(0, 0, rotation_z))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def add_asset_lighting(asset_id):
    bpy.ops.object.light_add(type="AREA", location=(0, -3, 4))
    key = bpy.context.object
    key.name = "asset_preview_key_light"
    key.data.energy = 350
    key.data.size = 4
    if asset_id == "buildable-city-center":
        bpy.ops.object.camera_add(location=(3.8, -4.4, 3.2), rotation=(math.radians(60), 0, math.radians(40)))
        camera = bpy.context.object
        camera.data.lens = 48
    elif asset_id == "city-module-kit":
        bpy.ops.object.camera_add(location=(4.8, -5.2, 4.0), rotation=(math.radians(60), 0, math.radians(42)))
        camera = bpy.context.object
        camera.data.lens = 38
    else:
        bpy.ops.object.camera_add(location=(2.8, -3.4, 2.4), rotation=(math.radians(62), 0, math.radians(39)))
        camera = bpy.context.object
    bpy.context.scene.camera = camera


def select_export_meshes():
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.select_set(True)
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if mesh_objects:
        bpy.context.view_layer.objects.active = mesh_objects[0]


def export_selected_glb(path):
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
    )


if __name__ == "__main__":
    main()
