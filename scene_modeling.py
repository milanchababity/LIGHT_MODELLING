import math
from openalea.caribu.sky_tools import GenSky, GetLight, Gensun, GetLightsSun

def orient_sun(sun_direction, angle):
    # rotates sun direction vector by "angle" degrees around z axis, using a rotation matrix
    angle = math.radians(angle)
    sun_direction = [sun_direction[0], sun_direction[1], sun_direction[2]]
    matrix_z = [[math.cos(angle), - math.sin(angle), 0], [math.sin(angle), math.cos(angle), 0], [0, 0, 1]]
    product = [0, 0, 0]
    for i in range(len(matrix_z)):
        for j in range(len(sun_direction)):
            product[i] = product[i] + matrix_z[i][j] * sun_direction[j]
    return tuple((product[0], product[1], product[2]))

def modelize_sky(energy):
    sky_string = GetLight.GetLight(GenSky.GenSky()(energy, 'soc', 12, 9))  #: (energy, 'soc'=standard sky / 'uoc'=ultraviolet sky, nb secteurs d'panel_north_angle, nb secteurs de zenith)
    # Convert string to list in order to be compatible with CaribuScene input format
    sky = []
    for string in sky_string.split('\n'):
        if len(string) != 0:
            string_split = string.split(' ')
            intensity = float(string_split[0])
            direction = tuple((float(string_split[1]), float(string_split[2]), float(string_split[3])))
            source = tuple((intensity, direction))
            sky.append(source)
    return sky

def modelize_sun(energy, DOY, hour, args):
    sun =  Gensun.Gensun()(energy, DOY, hour, args["latitude"])
    sunlight = GetLightsSun.GetLightsSun(sun)
    sun_str_split = sunlight.split(' ')
    sun_intensity = float(sun_str_split[0])
    sun_direction = tuple((float(sun_str_split[1]), float(sun_str_split[2]), float(sun_str_split[3])))
    # rotate sun vector depending on panel_north_angle in order to obtain correct shadow without rotating the scene
    sun_direction = orient_sun(sun_direction, 90 + args["panel_north_angle"])
    direct_light = tuple((sun_intensity * 1, sun_direction))# put sunlight to caribu format
    return [direct_light]

def canvass_soil(scene, args):
    # "cuts" the soil in little squares whose side is panel_spacing / resolution
    # then cuts the squares in half and generate a series of triangles
    # To understand better what this function does, cf annexes/scene_modeling.png
    AB_dist = args["panel_rows_spacing"]
    AC_dist = args["panel_spacing"]
    nb_squares_AB = math.ceil(AB_dist / args["resolution"])
    step = AB_dist / nb_squares_AB
    nb_squares_AC = int(AC_dist / step)
    i = [scene["soil_corners"][0][0], scene["soil_corners"][0][1], scene["soil_corners"][0][2]]
    points = []
    for n in range (0, nb_squares_AC):
        temp = []
        j = [i[0], i[1], i[2]]
        temp.append(j.copy())
        for k in range (0, nb_squares_AB):
            j[0] += step
            temp.append(j.copy())
        i[1] -= step
        points.append(temp.copy())
    temp = []
    j = [scene["soil_corners"][3][0], scene["soil_corners"][3][1], scene["soil_corners"][3][2]]
    temp.append(j.copy())
    for k in range (0, nb_squares_AB):
        j[0] += step
        temp.append(j.copy())
    points.append(temp.copy())
    for i in range (0, len(points) - 1):
        for j in range (0, len(points[0]) - 1):
            scene["soil_meshes"].append([points[i + 1][j], points[i][j + 1], points[i + 1][j + 1]]) # Lower triangle
            scene["soil_meshes"].append([points[i][j], points[i][j + 1], points[i + 1][j]]) # Upper complentary triangle
            scene["soil_rectangles"].append(points[i + 1][j]) # Rectangle bottom left corner

def translate(scene, args, x, y, z):
    for corner in scene["panel_corners"]:
        corner[0] += x
        corner[1] += y
        corner[2] += z
    for corner in scene["soil_corners"]:
        corner[0] += x
        corner[1] += y
        corner[2] += z
    canvass_soil(scene, args)
    scene["panel_meshes"] = [[scene["panel_corners"][0].copy(), scene["panel_corners"][1].copy(), scene["panel_corners"][3].copy()], \
                             [scene["panel_corners"][1].copy(), scene["panel_corners"][2].copy(), scene["panel_corners"][3].copy()]]

def matrix_product(matrix, vector):
    product = [0, 0, 0]
    for i in range(len(matrix)):
        for j in range(len(vector)):
            product[i] = product[i] + matrix[i][j] * vector[j]
    return product

def rotate(corners, angle_x, angle_y):
    center = [sum(corner[0] for corner in corners) / 4,
              sum(corner[1] for corner in corners) / 4,
              sum(corner[2] for corner in corners) / 4]
    # translate corners in order to place the center at origin
    corners_translated = [[corner[0] - center[0], corner[1] - center[1], corner[2] - center[2]] for corner in corners]
    angle_x = math.radians(angle_x)
    angle_y = math.radians(angle_y)
    matrix_x = [[1, 0, 0], [0, math.cos(angle_x), - math.sin(angle_x)], [0, math.sin(angle_x), math.cos(angle_x)]]
    matrix_y = [[math.cos(angle_y), 0, math.sin(angle_y)], [0, 1, 0], [- math.sin(angle_y), 0, math.cos(angle_y)]]
    for i in range(len(corners_translated)):
        corners_translated[i] = matrix_product(matrix_x, corners_translated[i])
        corners_translated[i] = matrix_product(matrix_y, corners_translated[i])
    corners_rotated = [[corner[0] + center[0], corner[1] + center[1], corner[2] + center[2]] for corner in corners_translated]
    return corners_rotated

def create_scene(args):
    scene = {
        "panel_corners" : [],
        "soil_corners" : [],
        "panel_meshes" : [],
        "soil_meshes" : [],
        "soil_rectangles": []
    }
    # To understand better how the scene is built : cf annexes/scene_modeling.png
    scene["panel_corners"] = [[- args["panel_width"] / 2, args["panel_length"] / 2, args["panel_height"]], \
                        [args["panel_width"] / 2, args["panel_length"] / 2, args["panel_height"]], \
                        [args["panel_width"] / 2, - args["panel_length"] / 2, args["panel_height"]], \
                        [- args["panel_width"] / 2, - args["panel_length"] / 2, args["panel_height"]]]
    scene["panel_corners"] = rotate(scene["panel_corners"], args["panel_angle_right_left"], args["panel_angle"])
    scene["soil_corners"] = [[- args["panel_rows_spacing"] / 2, args["panel_spacing"] / 2, args["average_crop_height"]], \
            [args["panel_rows_spacing"] / 2, args["panel_spacing"] / 2, args["average_crop_height"]], \
            [args["panel_rows_spacing"] / 2, - args["panel_spacing"] / 2, args["average_crop_height"]], \
            [- args["panel_rows_spacing"] / 2, - args["panel_spacing"] / 2, args["average_crop_height"]]]
    translate(scene, args, -scene["soil_corners"][3][0], -scene["soil_corners"][3][1], 0)
    return scene