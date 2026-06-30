import time, argparse, json, multiprocessing, datetime, os, math
from openalea.caribu.CaribuScene import CaribuScene
from openalea.caribu.sky_tools import Sun
import matplotlib
import mpl_toolkits.mplot3d.art3d
import scene_modeling
import meteo

NB_THREADS = 8
OUTPUT_MIN_REPEAT_X = 3 # Min number of panel rows on the final output
OUTPUT_MIN_REPEAT_Y = 3 # Min number of panels per row on the final output
MIN_RAD = 0 # Min solar kWh received daily by square meter (max color for radiation map)
MAX_RAD = 5 # Max solar kWh received daily by square meter (min color for radiation map)

def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)

def error(message):
    log("ERROR - {0}".format(message))
    exit(1)

####### COMMAND LINE ARGUMENTS ############

def parse_args():
    # Parse command line
    parser = argparse.ArgumentParser(description='Please provide all parameters of the experiment so that we can model the experiment correctly')
    parser.add_argument('configuration_file', help='configuration file with panel parameters')
    parser.add_argument('-r', '--resolution', default=None, type=float, help='dimension of 1 pixel of the map in meters')
    args_parsed = parser.parse_args()
    # Read configuration file
    filename = args_parsed.configuration_file
    f = open(filename, "r")
    params = json.load(f)
    f.close()
    # Parameter verification
    param_names = [ "panel_length","panel_width","panel_height","panel_max_height","panel_min_height","average_crop_height","panel_spacing","panel_rows_spacing","panel_north_angle","panel_angle","panel_angle_right_left","latitude","longitude","date_start_crop","date_end_crop", "panel_angle_direction", "nb_panel_rows", "panel_opacity" ]
    can_be_null = [ "panel_height", "panel_max_height", "panel_min_height", "panel_spacing" ]
    for param_name in param_names:
        if not param_name in params:
            error("Parameter '{0}' is missing in configuration file".format(param_name))
        elif param_name == "date_start_crop" or param_name == "date_end_crop":
            try: # conventional date format (YYYY-mm-dd HH:MM:SS)
                datetime.datetime.strptime(params[param_name], "%Y-%m-%d %H:%M:%S")
            except:
                if not isinstance(params[param_name], int) or params[param_name] < 0  or params[param_name] > 365:
                    error("Parameter '{0}' must be a date (YYYY-mm-dd HH:MM:SS) or a day of year in configuration file".format(param_name))
                else: # Day of Year
                    # Taking last year's weather data as a reference
                    today = datetime.date.today()
                    year = str(today.year - 1)
                    # Converting from Day of Year to date
                    params[param_name] = datetime.datetime.strptime("{0}-{1}".format(year, params[param_name]), "%Y-%j").strftime("%Y-%m-%d 00:00:00")
            # If the specified year is future, use previous year for weather data
            specified_year = int(datetime.datetime.strptime(params[param_name], "%Y-%m-%d %H:%M:%S").strftime("%Y"))
            if specified_year >= datetime.date.today().year :
                new_year = datetime.date.today().year - 1
                params[param_name] = str(new_year) + params[param_name][4:]
        elif param_name == 'panel_north_angle':
            if not isinstance(params[param_name], (int ,float)) or params["panel_north_angle"] <= -90 or params["panel_north_angle"] > 90:
                error("Parameter 'panel_north_angle' must be between -90 and 90 degrees")
        elif param_name == 'nb_panel_rows':
            if not isinstance(params[param_name], int) or params[param_name] <= 0:
                error("Parameter 'nb_panel_rows' must be a positive integer")
        elif param_name == 'panel_opacity':
            if not isinstance(params[param_name], (int, float)) or params[param_name] <= 0 or params[param_name] > 1:
                error("Parameter 'panel_opacity' must be between 0 and 1")
        elif param_name == 'panel_angle_direction':
            if not (params["panel_angle_direction"] == "E" or params["panel_angle_direction"] == "W" or ((params["panel_north_angle"] >= 46 and params["panel_north_angle"] <= 90) or (params["panel_north_angle"] <= -46 and params["panel_north_angle"] >= -89) and params["panel_angle_direction"] == "S")):
                error("Parameter 'panel_angle_direction' must be E or W, or S when panel_north_angle is between 46° and 90° or between -89° and -46°")
        elif params[param_name] is None and not param_name in can_be_null:
            error("Parameter '{0}' must have a value in configuration file".format(param_name))
        elif not ((param_name in can_be_null and params[param_name] is None) or isinstance(params[param_name], (int, float))):
            error("Parameter '{0}' must be a float in configuration file".format(param_name))
    if params["panel_max_height"] is None and params["panel_min_height"] is None and params["panel_height"] is None:
         error("Parameters 'panel_max_height' and 'panel_min_height' must be specified if 'panel_height' has no value in configuration file")
    if params["panel_max_height"] is not None and params["panel_min_height"] is not None and params["panel_max_height"] < params["panel_min_height"]:
         error("Parameter 'panel_max_height' must be greater than 'panel_min_height' in configuration file")
    if params["date_start_crop"] > params["date_end_crop"]:
         error("Parameter 'date_end_crop' must be greater than 'date_start_crop' in configuration file")
    # Final parameters
    panel_height = params["panel_height"]
    if params["panel_max_height"] is not None and params["panel_min_height"] is not None:
        panel_height = (params["panel_max_height"] + params["panel_min_height"]) / 2
    panel_spacing = params["panel_spacing"]
    if params["panel_spacing"] is None:
        panel_spacing = 0 # case of contiguous panels
    rows_spacing = params["panel_rows_spacing"] + params["panel_width"] * math.cos(math.radians(params["panel_angle"])) # replacing border-to-border panel rows measure by center-to-center measures
    panel_angle = 0
    if (params["panel_angle_direction"] == "E" or (params["panel_angle_direction"] == "S" and params["panel_north_angle"] > 45 and params["panel_north_angle"] <= 90)):
        panel_angle = params["panel_angle"]
    elif (params["panel_angle_direction"] == "W" or (params["panel_angle_direction"] == "S" and params["panel_north_angle"] < -45 and params["panel_north_angle"] > -90)):
        panel_angle = 180 - params["panel_angle"]
    if args_parsed.resolution is None:
        args_parsed.resolution = (params["panel_rows_spacing"] + params["panel_width"]) / 80
    args = {
        "panel_length" : params["panel_length"],
        "panel_width" : params["panel_width"],
        "panel_height" : panel_height,
        "average_crop_height" : params["average_crop_height"],
        "panel_spacing" : panel_spacing + params["panel_length"], # replacing border-to-border panel measures by center-to-center measures
        "panel_rows_spacing" : rows_spacing,
        "panel_north_angle" : params["panel_north_angle"],
        "panel_angle_right_left" : params["panel_angle_right_left"],
        "panel_angle" : panel_angle,
        "latitude" : params["latitude"],
        "longitude" : params["longitude"],
        "date_start_crop" : params["date_start_crop"],
        "date_end_crop" : params["date_end_crop"],
        "panel_rows_orientation": "NS" if params["panel_north_angle"] >= -45 and params["panel_north_angle"] <= 45 else "EW",
        "resolution" : args_parsed.resolution,
        "conf_name": args_parsed.configuration_file.replace(".json", ""),
        "nb_panel_rows": params["nb_panel_rows"],
        "panel_opacity": params["panel_opacity"]
    }
    return args

####### RADIATION COMPUTATION ############

def caribu_radiosity(scene, light_sources, args):
    # translate soil and panel meshes in Caribu format
    soil_triangles = []
    for soil_triangle in scene["soil_meshes"]:
        soil_triangles.append([tuple(soil_triangle[0]), tuple(soil_triangle[1]), tuple(soil_triangle[2])])
    panel_triangles = []
    for panel_triangle in scene["panel_meshes"]:
        panel_triangles.append([tuple(panel_triangle[0]), tuple(panel_triangle[1]), tuple(panel_triangle[2])])
    scene_triangles = {
        "soil" : soil_triangles,
        "panels" : panel_triangles
    }
    pattern = (0, 0, args["panel_rows_spacing"], args["panel_spacing"]) # bounds for scene infinite repetition
    opt = None if args["panel_opacity"] == 1 else { "default_band": { "panels": (0.06, 1 - args["panel_opacity"]), "soil": (0.06, 0) } }
    direct = args["panel_opacity"] == 1
    carib_scene = CaribuScene(scene=scene_triangles, light=light_sources, pattern=pattern, opt=opt)
    raw, _ = carib_scene.run(direct=direct, infinite=True, screen_size=768)
    # return the amount of radiation received by each soil mesh
    return raw['default_band']['Ei']['soil']

def scene_illumination_thread(queue, start_pos, end_pos, day_of_years, total_days, ei_diffuse, sun, scene, meteo_data, is_log, args):
    ei_by_mesh = [0] * int(len(scene["soil_meshes"]) / 2)
    progress_prev = 0
    skipped = 0
    total = 0
    for day in range(start_pos, end_pos + 1):
        for hour in range(0, 24):
            # place sun depending on day and hour
            sun._set_pos_astro(day, hour, 3.14 / 180 * args["latitude"])
            # get direct and diffuse radiation intensity for current hour in meteo data
            direct_intensity = meteo_data[day][hour][0]
            diffuse_intensity = meteo_data[day][hour][1]
            if direct_intensity > 0 or diffuse_intensity > 0:
                ei_direct = caribu_radiosity(scene, scene_modeling.modelize_sun(direct_intensity, day_of_years[day], hour, args), args)
                for i in range(0, len(ei_direct)):
                    # manage abnormal irradiation values (due to border effects with Caribu)
                    total += 1
                    skip = False
                    if i == 0 and ei_direct[i+1] == 0.0 and ei_direct[i] > 1000: # Abnormal value on border
                        skip = True
                    elif i == len(ei_direct) - 1 and ei_direct[i-1] == 0.0 and ei_direct[i] > 1000: # Abnormal value on other border
                        skip = True
                    if i > 0 and i < len(ei_direct) - 1 and ei_direct[i-1] == 0.0 and ei_direct[i+1] == 0.0 and ei_direct[i] > 1000:  # Abnormal value in between
                        skip = True
                    if ei_direct[i] > 10000: # Abnormal radiation value
                        skip = True
                    if skip:
                        skipped += 1
                        continue
                    # add hourly radiation received to each soil mesh in order to get daily radiation received by mesh
                    # group triangular meshes 2 by 2 to have square pixels
                    ei_by_mesh[int(i / 2)] += (ei_direct[i] + (ei_diffuse[i] * diffuse_intensity)) / (1000 * total_days * 2)
        if is_log:
            # Logging progress every 10%
            progress  = int(100 * (day + 1 - start_pos) / (end_pos + 1 - start_pos) / 10) * 10
            if progress > progress_prev:
                log("Computation {0}%".format(progress))
            progress_prev = progress
    if skipped > 0:
        log("WARNING - {0}/{1} abnormal computed values skipped".format(skipped, total))
    queue.put(ei_by_mesh)

def scene_illumination(scene, meteo_data, day_of_years, args):
    ei_by_mesh = [0] * int(len(scene["soil_meshes"]) / 2)
    return_queue = multiprocessing.Queue()
    nb_days = int(len(day_of_years) / NB_THREADS)
    sun = Sun.Sun()
    total_days = len(day_of_years)
    # Computing diffuse radiosity (common across daily computations)
    ei_diffuse = caribu_radiosity(scene, scene_modeling.modelize_sky(1), args)
    # Starting threaded computation
    processes= []
    for i in range(NB_THREADS):
        start_pos = i * nb_days
        end_pos = (i+1) * nb_days - 1 if i < NB_THREADS - 1 else len(day_of_years) - 1 # Last thread must take all the remaining mesh entries
        is_log = (i == NB_THREADS - 1) # Logging only for last thread, which will take the most time
        p = multiprocessing.Process(target=scene_illumination_thread,args=(return_queue, start_pos, end_pos, day_of_years, total_days, ei_diffuse, sun, scene, meteo_data, is_log, args))
        processes.append(p)
        p.start()
    for i in range(NB_THREADS):
        thread_mesh = return_queue.get() # NB : need to move queue results even if blocking to avoid deadlock in processes join()
        for i in range(len(ei_by_mesh)):
            ei_by_mesh[i] += thread_mesh[i]
    for p in processes: # NB : just to make sure, normally threads will have finished on previous queue blocking call
        p.join()
    return ei_by_mesh

####### MAP AND COMPUTATION OUTPUTS ############

def output_map(scene, radiation_values, filename, args):
    # Compute number of repetitions of scene pattern
    output_repeat_x = OUTPUT_MIN_REPEAT_X
    output_repeat_y = OUTPUT_MIN_REPEAT_Y
    len_x = output_repeat_x * args["panel_rows_spacing"]
    len_y = output_repeat_y * args["panel_spacing"]
    if len_x < len_y: # Add repetitions to the smallest length to get a mostly square image
        while len_x < len_y - args["panel_rows_spacing"]:
            len_x += args["panel_rows_spacing"]
            output_repeat_x += 1
    else:
        while len_y < len_x - args["panel_spacing"]:
            len_y += args["panel_spacing"]
            output_repeat_y += 1
    # Matplotlib main figure
    fig = matplotlib.pyplot.figure()
    fig2 = matplotlib.pyplot.figure()
    ax2 = fig2.add_subplot(111, projection="3d")
    cmap = matplotlib.pyplot.get_cmap("jet") # Color map
    fig, ax = matplotlib.pyplot.subplots(layout="constrained") # Add color bar subplot to the main plot
    min_rad = MIN_RAD
    max_rad = MAX_RAD
    tick_color = "#777777"
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.set_frame_on(False)
    xmax = 0
    ymax = 0
    # Plot soil colored rectangles
    for index in range(len(scene["soil_rectangles"])):
        width = scene["soil_meshes"][2 * index][1][0] - scene["soil_meshes"][2 * index][0][0]
        height = scene["soil_meshes"][2 * index][1][1] - scene["soil_meshes"][2 * index][0][1]
        coords = scene["soil_rectangles"][index]
        rad = radiation_values[index]
        color = cmap((rad - min_rad) / (max_rad - min_rad))
        for i in range(output_repeat_x):
            for j in range(output_repeat_y):
                x = coords[0] + i * args["panel_rows_spacing"]
                y = coords[1] + j * args["panel_spacing"]
                rect = matplotlib.pyplot.Rectangle((x , y), width, height, fill = True, facecolor = color)
                rect2 = matplotlib.pyplot.Rectangle((x , y), width, height, fill = True, facecolor = color)
                if args["panel_rows_orientation"] == "EW" and args["panel_north_angle"] < 0:
                    y += height
                    image_width = output_repeat_y * args["panel_spacing"]
                    rect = matplotlib.pyplot.Rectangle((image_width - y, x), height, width, fill = True, facecolor = color)
                elif args["panel_rows_orientation"] == "EW" and args["panel_north_angle"] >= 0:
                    x += width
                    image_height = output_repeat_x * args["panel_rows_spacing"]
                    rect = matplotlib.pyplot.Rectangle((y, image_height - x), height, width, fill = True, facecolor = color)
                if x > xmax:
                    xmax = x
                if y > ymax:
                    ymax = y
                ax.add_patch(rect)
                ax2.add_patch(rect2)
                mpl_toolkits.mplot3d.art3d.pathpatch_2d_to_3d(rect2, z = args["average_crop_height"], zdir = "z")
    # Plotting panels as rectangles outlines
    corners = scene["panel_corners"]
    for i in range(output_repeat_x):
        for j in range(output_repeat_y):
            w = i * args["panel_rows_spacing"]
            h = j * args["panel_spacing"]
            x_coords = [ corners[0][0] + w, corners[1][0] + w, corners[2][0] + w, corners[3][0] + w, corners[0][0] + w ]
            y_coords = [ corners[0][1] + h, corners[1][1] + h, corners[2][1] + h, corners[3][1] + h, corners[0][1] + h ]
            z_coords = [ corners[0][2], corners[1][2], corners[2][2], corners[3][2], corners[0][2] ]
            vertices_3d = [ list(zip(x_coords,y_coords,z_coords)) ]
            ax2.add_collection3d(mpl_toolkits.mplot3d.art3d.Poly3DCollection(vertices_3d, facecolor = "#373737"))
            if args["panel_rows_orientation"] == "EW":
                y_coords = x_coords
                l = output_repeat_y * args["panel_spacing"]
                x_coords = [ l - (corners[0][1] + h), l - (corners[1][1] + h), l - (corners[2][1] + h), l - (corners[3][1] + h), l - (corners[0][1] + h) ]
                z_coords = [ corners[0][2], corners[1][2], corners[2][2], corners[3][2], corners[0][2] ]
            vertices_2d = [ list(zip(x_coords,y_coords)) ]
            ax.add_collection(matplotlib.collections.LineCollection(vertices_2d, colors = 'black', linewidths = 1))
    if args["panel_rows_orientation"] == "EW":
        temp = xmax
        xmax = ymax
        ymax = temp
    # Color bar
    colorbar_obj = matplotlib.cm.ScalarMappable(norm=matplotlib.colors.Normalize(vmin=min_rad * 2.02 * 1000 * 3600 / 1000000,  vmax=max_rad * 2.02 * 1000 * 3600 / 1000000), cmap=cmap) # NB : converting scale to mol / m2 / day
    colorbar_ratio = ax.get_position().height # Using map height to resize colobar
    colorbar = matplotlib.pyplot.colorbar(colorbar_obj, ax=ax, orientation='vertical', drawedges=False, shrink=colorbar_ratio)
    colorbar.ax.tick_params(which='both', color=tick_color, labelcolor=tick_color)
    colorbar.set_label('Rayonnement (mol/m².jour)', color=tick_color)
    # Scale
    trans = matplotlib.transforms.blended_transform_factory(ax.transData, ax.transAxes)
    matplotlib.pyplot.errorbar(1, 0.1, xerr=0.5, color="white", capsize=3, transform=trans)
    matplotlib.pyplot.text(1, 0.08, '1m', color="white", fontsize=8, horizontalalignment='center', verticalalignment='top', transform=trans)
    # North arrow
    rotation_degrees = rotation_degrees = 90 + args["panel_north_angle"] # arrow's angle relative to vertical position
    if args["panel_north_angle"] >= -45 and args ["panel_north_angle"] <= 45 :
        rotation_degrees = args["panel_north_angle"]
    elif args["panel_north_angle"] <= 90 and args["panel_north_angle"] > 45 :
        rotation_degrees = - 90 + args["panel_north_angle"]
    rotation = math.radians(rotation_degrees)
    if args["panel_rows_orientation"] == "NS" : # center the arrow
        x_origin = output_repeat_x / 2 * args["panel_rows_spacing"]
    else :
        x_origin = output_repeat_y / 2 * args["panel_spacing"]
    y_origin = 0
    x_point_before = x_origin # point of the arrow's position before rotation
    y_point_before = ymax / 15
    x_point = (x_point_before - x_origin) * math.cos(rotation) - (y_point_before - y_origin) * math.sin(rotation) + x_origin # arrow rotation
    y_point = (x_point_before - x_origin) * math.sin(rotation) + (y_point_before - y_origin) * math.cos(rotation) + y_origin
    y_origin = ymax - (ymax / 20) - (y_point - y_origin) # move arrow to top of map
    y_point = ymax - (ymax / 20)
    ax.annotate("", xytext=(x_origin, y_origin), xy=(x_point, y_point), arrowprops=dict(arrowstyle="->", color="white"))
    ax.annotate("N", xytext=(x_point, y_point), xy=(x_point, y_point), color="white")
    ax.set_aspect('equal', adjustable='box')
    fig.savefig(filename, bbox_inches='tight', transparent=True)
    # Additional 3D plot
    ax2.view_init(elev=20, azim=-30) # Projection angle
    ax2.grid(False) # No grid
    ax2.set_xticklabels([]) # No labels
    ax2.set_yticklabels([])
    ax2.set_zticklabels([])
    ax2.xaxis.line.set_visible(False) # No axis line
    ax2.yaxis.line.set_visible(False)
    ax2.zaxis.line.set_visible(False)
    ax2.set_xlim(0, xmax) # Extend lower pane size to fit scene
    ax2.set_ylim(0, ymax)
    ax2.xaxis._axinfo['tick']['inward_factor'] = 0.0 # Remove ticks
    ax2.xaxis._axinfo['tick']['outward_factor'] = 0.0
    ax2.yaxis._axinfo['tick']['inward_factor'] = 0.0
    ax2.yaxis._axinfo['tick']['outward_factor'] = 0.0
    ax2.zaxis._axinfo['tick']['inward_factor'] = 0.0
    ax2.zaxis._axinfo['tick']['outward_factor'] = 0.0
    ax2.xaxis.set_pane_color((1.0, 1.0, 1.0, 0)) # Hide YZ Plane
    ax2.yaxis.set_pane_color((1.0, 1.0, 1.0, 0)) # Hide XZ Plane
    ax2.zaxis.set_pane_color((211 / 255, 211 / 255, 211 / 255, 1.0)) # XY pane for grey soil
    ax2.set_aspect('equal', adjustable='box')
    fig2.savefig(filename.replace(".png", "_3d.png"), bbox_inches='tight', transparent=True)
    matplotlib.pyplot.close()

def output_radiation_distribution(radiation_results, filename):
    cmap = matplotlib.pyplot.get_cmap("jet") # Color map
    colorscale_size = 100
    radiation_scale = [ MIN_RAD + x * (MAX_RAD - MIN_RAD) / colorscale_size for x in range(colorscale_size + 1) ] # Build a discrete scale of a fixed size for mapping radiations to colors
    min_rad = MIN_RAD
    max_rad = MAX_RAD
    colors = {}
    for rad in radiation_results:
        rad = min(radiation_scale, key=lambda x:abs(x - rad)) # Normalize radiation to a discrete color scale
        c = cmap((rad - min_rad) / (max_rad - min_rad))
        if not c in colors:
            colors[c] = [ c, 0, rad ]
        colors[c][1] += 1
    colors = list(colors.values())
    colors.sort(key = lambda x:x[2])
    bar_labels = []
    bar_counts = []
    bar_colors = []
    i = 0
    for color in colors:
        bar_colors.append(color[0])
        bar_counts.append(color[1] / len(radiation_results) * 100)
        bar_labels.append(i)
        i += 1
    fig, ax = matplotlib.pyplot.subplots(tight_layout=True)
    ax.get_xaxis().set_visible(False)
    ax.bar(bar_labels, bar_counts, color=bar_colors)
    fig.savefig(filename, bbox_inches='tight', transparent=True)

def output_computations(scene, meteo_station, results_control, computation_time, filename, args):
    results = {}
    panel_projected_length = abs(scene["panel_corners"][1][0] - scene["panel_corners"][0][0])
    row_gap = args["panel_rows_spacing"] - panel_projected_length
    # Computing panels cover rate (legal formula) : projected panel surface / soil surface, so simplified : 1 / (1 + (panel_rows_spacing / projected_panel_length) * ((nb_panel_rows - 1) / nb_panel_rows)
    results["taux_de_couverture_legal"] = round(100 * 1 / (1 + (row_gap / (panel_projected_length + 0.001)) * (args["nb_panel_rows"] -1) / args["nb_panel_rows"]), 1) # NB adding 0.001 for non zero value in vertical panels
    # Computing panels cover rate (Dupraz formula) : total panel surface / soil surface, so simplified : 1 / (1 + (panel_rows_spacing / panel_length) * ((nb_panel_rows - 1) / nb_panel_rows)
    results["taux_de_couverture_dupraz"] = round(100 * 1 / (1 + (row_gap / (args["panel_width"] + 0.001)) * (args["nb_panel_rows"] -1) / args["nb_panel_rows"]), 1)
    # Computing distance to weather station
    results["station_meteo_latitude"] = meteo_station["latitude"]
    results["station_meteo_longitude"] = meteo_station["longitude"]
    # Cf https://stackoverflow.com/questions/365826/calculate-distance-between-2-gps-coordinates
    dLat = math.radians(args["latitude"] - meteo_station["latitude"])
    dLon = math.radians(args["longitude"] - meteo_station["longitude"])
    lat1 = math.radians(meteo_station["latitude"])
    lat2 = math.radians(args["latitude"])
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.sin(dLon/2) * math.sin(dLon/2) * math.cos(lat1) * math.cos(lat2)
    distance = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)) * 6371
    results["station_meteo_distance_km"] = round(distance, 2)
    results["temps_de_calcul_s"] = computation_time
    # Compute radiation control
    rad = results_control[0]
    cmap = matplotlib.pyplot.get_cmap("jet") # Color map
    color = cmap((rad - MIN_RAD) / (MAX_RAD - MIN_RAD))
    radiation = round(rad * 2.02 * 1000 * 3600 / 1000000, 2)
    results["radiation_control"] = radiation
    results["radiation_control_color"] = matplotlib.colors.rgb2hex(color)
    f = open(filename, "w")
    f.write(json.dumps(results, indent=4))
    f.close()

if __name__ == "__main__":
    t1 = time.time()
    args = parse_args()
    log("Starting process for configuration {0}.json".format(os.path.basename(args["conf_name"])))
    log("Creating 3D scene")
    scene = scene_modeling.create_scene(args)
    args_control = { "panel_width":0, "panel_length": 0, "panel_height": 0, "panel_angle_right_left": 0, "panel_angle": 0, "panel_rows_spacing": 1, "panel_spacing": 1, "average_crop_height": args["average_crop_height"], "resolution": 1 }
    scene_control = scene_modeling.create_scene(args_control)
    log("Retrieving weather data")
    meteo_file = args["conf_name"] + "_meteo.json"
    day_of_years, meteo_data, meteo_station = meteo.read_meteo(meteo_file, args)
    log("Computing solar radiation on scene with {0} threads".format(NB_THREADS))
    results = scene_illumination(scene, meteo_data, day_of_years, args)
    log("Computing solar radiation on control with {0} threads".format(NB_THREADS))
    results_control = scene_illumination(scene_control, meteo_data, day_of_years, args)
    log("Outputing solar radiation map")
    map_filename = args["conf_name"] + ".png"
    output_map(scene, results, map_filename, args)
    log("Outputing radiation distribution diagram")
    distribution_filename = args["conf_name"] + "_distribution.png"
    output_radiation_distribution(results, distribution_filename)
    t2 = time.time()
    elapsed = int((t2 - t1) * 10) / 10
    log("Outputing computation results")
    computations_filename = args["conf_name"] + "_calculs.json"
    output_computations(scene, meteo_station, results_control, elapsed, computations_filename, args)
    log("Process for configuration {0}.json finished, total time : {1}s".format(os.path.basename(args["conf_name"]), elapsed))
