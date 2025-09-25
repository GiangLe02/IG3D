
"""
======================================================================
 Title:                   T1 MRI Head Reconstruction Lab – Pseudocode Template
 Creating Author:         Janan ARSLAN
 Creation Date:           [05-03-2025]
 Latest Modification:     [13-03-2025]
 Modification Author:     Janan ARSLAN
 E-mail:                  janan.arslan@icm-institute.org
 Version:                 1.1pseudo
======================================================================


This is a pseudocode provided to students at Sorbonne Université in the IG3D course.

The objective is to replace TODO items with code that will render a 3D MRI model in Blender.

Complete code will be provided to students via Moodle following all lab submissions.


"""

# This pseudocode is provided as a starting point.

# The following imports are available by default
import bpy
import os
import numpy as np
from mathutils import Vector
import math
import sys
import time
import scipy

filepath = bpy.data.filepath
dir_path = os.path.dirname(filepath)
# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()


# The following allows you to install packages directly
def install_package(package_name):
    """Install a package using pip if it's not already installed"""
    try:
        __import__(package_name)
        print(f"{package_name} is already installed")
    except ImportError:
        print(f"{package_name} not found, attempting to install...")
        python_exe = sys.executable
        import subprocess
        subprocess.check_call([python_exe, "-m", "pip", "install", package_name])
        print(f"Installed {package_name}")

# Using the above to install tifffile and scikit-image
try:
    install_package("tifffile")
    import tifffile
except Exception as e:
    print(f"Error installing tifffile: {e}")
    print("You may need to manually install tifffile.")

try:
    install_package("scikit-image")
    from skimage import measure
    has_skimage = True
except Exception as e:
    print(f"Error installing scikit-image: {e}")
    has_skimage = False

#####################################################################################################
# Function: import_t1_head(file_path, downsample)
# Purpose: Load the T1 MRI head from a TIFF file into a normalized, downsampled 3D numpy array.
def import_t1_head(file_path, downsample=4):
    # TODO: Verify that file_path exists; if not, raise an error.
    verify = os.path.exists(file_path)
    if verify == False:
        raise FileNotFoundError(f"Error: The file '{file_path}' does not exist.")
    # TODO: Open the TIFF file using "with tifffile.TiffFile(file_path) as tif:".
    with tifffile.TiffFile(file_path) as tif:
    # TODO: Determine the number of slices (depth) and get the image dimensions from the first page.
        depth = len(tif.pages)
        first_page = tif.pages[0]
        height, width = first_page.shape

    # TODO: Loop over tif.pages, converting each page to a float32 array.
        image = []
        for page in tif.pages:
            image.append(page.asarray().astype(np.float32))
    # TODO: Optionally, print min/max values for the first and last slices for debugging.
    # TODO: Stack all slices into a 3D numpy array.
        image = np.array(image, np.float32)
    # TODO: Normalize the entire volume using: (volume - min) / (max - min).
        min_val = np.min(image)
        max_val = np.max(image)
        if max_val == min_val:
            image = np.zeros_like(image, dtype=np.float32)  # Avoid division by zero
        else:
            image = (image  - min_val) / (max_val - min_val)
    # TODO: If downsample > 1, apply slicing: volume[::downsample, ::downsample, ::downsample].
        if downsample > 1:
            image = image[::downsample, ::downsample, ::downsample]
    # TODO: Print final volume shape and min/max values for verification.
        print("Final volume shape:", image.shape)
        print("Min values of volume:", min_val)
        print("Max values of volume:", max_val)
        return image
    pass
#####################################################################################################


#####################################################################################################
# Function: create_t1_material(name)
# Purpose: Create a Blender material for T1 MRI visualization.
def create_t1_material(name="T1_Material"):
    # TODO: Create a new material with: mat = bpy.data.materials.new(name=name).
    mat = bpy.data.materials.new(name=name)
    # TODO: Enable nodes by setting mat.use_nodes = True.
    mat.use_nodes = True
    # TODO: Remove all default nodes from mat.node_tree.nodes.
    nodes = mat.node_tree.nodes
    nodes.clear()
    # TODO: Add a new Diffuse BSDF node, set its color to (0.9, 0.9, 0.85, 1.0) and roughness to around 0.3.
    diffuse = nodes.new(type="ShaderNodeBsdfDiffuse")
    diffuse.inputs["Color"].default_value = (0.9, 0.9, 0.85, 1.0)  # RGBA
    diffuse.inputs["Roughness"].default_value = 0.3
    
    # TODO: Add a Material Output node and link the Diffuse BSDF output to the Material Output input.
    output = nodes.new(type="ShaderNodeOutputMaterial")
    links = mat.node_tree.links
    links.new(diffuse.outputs["BSDF"], output.inputs["Surface"])
    return mat
    pass
#####################################################################################################


#####################################################################################################
# Function: extract_skull_surface_improved(volume_data, threshold, name, smooth_iterations)
# Purpose: Extract the skull surface from the volume data using image processing and marching cubes.
def extract_skull_surface_improved(volume_data, threshold=0.65, name="T1_Skull", smooth_iterations=3):
    # TODO: Print a message indicating the start of skull extraction with the given threshold.
    print("Starting skull extraction with threshold", threshold, "...")
    # TODO: If scikit-image is unavailable, add a placeholder cube (using bpy.ops.mesh.primitive_cube_add) and return it.
    
    # TODO: Invert the volume data with: inv_data = 1.0 - volume_data.
    inv_data = 1.0 - volume_data
    # TODO: Apply a Gaussian filter (e.g., scipy.ndimage.gaussian_filter with sigma=0.7) to inv_data.
    filtered_data = scipy.ndimage.gaussian_filter(inv_data, sigma=0.7)
    # TODO: Create a binary volume by thresholding the smoothed data: binary_data = smoothed_volume > threshold.
    binary_data = filtered_data > threshold
    
    from skimage import morphology
    # TODO: Use binary closing with a 3x3x3 structuring element to fill small holes in the binary data.
    structuring_element = morphology.ball(1)
    closed_data = morphology.binary_closing(binary_data, structuring_element)
    
    # TODO: Run the marching cubes algorithm (measure.marching_cubes) on the processed volume.
    try:
        verts, faces, normals, values = measure.marching_cubes(closed_data, level=0.5)
        # Invert for the face being in the front
        verts[:,2] = -verts[:,2]
    # TODO: If marching cubes fails, create and return a placeholder cube.
    except:
        bpy.ops.mesh.primitive_cube_add(size=2)
        print("Marching cube fails...")
        return bpy.context.object
    # TODO: Otherwise, create a new Blender mesh from the vertices and faces obtained.
    print("Marching cube suceeds")
    
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    col = bpy.data.collections["Collection"]
    col.objects.link(obj)
    bpy.context.view_layer.objects.active = obj

    # Convert vertices and faces to Blender format
    mesh.from_pydata(verts, [], faces)
#    mesh.update()
    obj.select_set(True)
    # TODO: Set smooth shading on the mesh, assign the material from create_t1_material, and center the object (set origin to center of volume).
    for poly in obj.data.polygons:
            poly.use_smooth = True
    mat = create_t1_material()
    obj.data.materials.append(mat)
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME',center='BOUNDS')
    obj.location= (0,0,0)
    
    # TODO: Optionally, add a Smooth modifier (with iterations=smooth_iterations) and a Solidify modifier.
    mod = obj.modifiers.new(name="Smooth", type='SMOOTH')
    mod.factor = 0.5
    mod.iterations = smooth_iterations
    modifier_solidify = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
    return obj
    pass
#####################################################################################################


#####################################################################################################
# Function: setup_medical_lighting()
# Purpose: Set up a three-point lighting configuration for the scene.
def setup_medical_lighting():
    # TODO: Check if bpy.context.scene.world exists; if not, create a new world and assign it to the scene.
    if not bpy.context.scene.world:
        bpy.context.scene.world = bpy.data.worlds.new(name="NewWorld")
        
    # TODO: Enable nodes for the world and set the Background node's color to (0, 0, 0, 1).
    world = bpy.context.scene.world
    world.use_nodes = True
    
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs[0].default_value = (0, 0, 0, 1)
        
    # TODO: Add three area lights at locations such as (5, -5, 5), (-5, -5, 3), and (0, 5, 5).
    # TODO: Set the energy for each light (e.g., 500, 200, and 300 respectively).
    light_data = [
        {"location": (5*10, -5*10, 5*10), "energy": 10000},
        {"location": (-5*10, -5*10, 3*10), "energy": 10000},
        {"location": (0*10, 5*10, 5*10), "energy": 10000},
    ]
    
    for i, light in enumerate(light_data):
        light_obj = bpy.data.objects.new(f"MedicalLight_{i}", bpy.data.lights.new(f"MedicalLight_{i}", 'AREA'))
        light_obj.location = light["location"]
        light_obj.data.energy = light["energy"]
        bpy.context.collection.objects.link(light_obj)
        
    # TODO: Set the render engine to 'CYCLES' and attempt to enable GPU rendering, with a fallback to CPU.
    bpy.context.scene.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    available_devices = [device.type for device in prefs.devices]
#    print(available_devices)
    if 'GPU' in available_devices:
        prefs.compute_device_type = 'GPU'
        bpy.context.scene.cycles.device = 'GPU'
        print("Enable GPU rendering")
    elif "METAL" in available_devices:
        prefs.compute_device_type = 'METAL'
        bpy.context.scene.cycles.device = 'GPU'
        print("Enable METAL rendering")
    else:
        bpy.context.scene.cycles.device = 'CPU'
        print("Fallback to CPU")
        
    # TODO: Optionally, configure render resolution and sample count.
#    bpy.context.scene.render.resolution_x = 1920
#    bpy.context.scene.render.resolution_y = 1080
#    bpy.context.scene.cycles.samples = 128
    pass
#####################################################################################################


#####################################################################################################
# Function: setup_t1_head_cameras()
# Purpose: Create multiple camera views for the T1 MRI head.
def setup_t1_head_cameras():
    # TODO: Create a new empty object named "Target" at (0, 0, 0) and link it to the scene.
    target = bpy.data.objects.new("Target", None)
    target.location = (0, 0, 0)
    bpy.context.collection.objects.link(target)
    
    # TODO: Define camera positions for views such as sagittal (7, 0, 0), coronal (0, -7, 0), axial (0, 0, 7), and perspective (5, -5, 5).
    camera_positions = {
#        "Sagittal": (7*300, 0, 0),
#        "Coronal": (0, -7*100, 0),
#        "Axial": (0, 0, 7*24),
#        "Perspective": (7, -7, 7),
        "Sagittal": (7*30, 0, 0),
        "Coronal": (0, -7*30, 0),
        "Axial": (0, 0, 7*30),
        "Perspective": (5*30, -5*30, 5*30),
    }

    cameras = []
    
    # TODO: For each view, add a camera at the specified location, name it accordingly, and add a TRACK_TO constraint targeting "Target".
    for view_name, position in camera_positions.items():
        # Create a new camera
        cam_data = bpy.data.cameras.new(name=f"{view_name}_Cam")
        cam_obj = bpy.data.objects.new(f"{view_name}_Cam", cam_data)
        bpy.context.collection.objects.link(cam_obj)
        cam_obj.location = position

        # Add a TRACK_TO constraint to the camera
        track_to_constraint = cam_obj.constraints.new(type='TRACK_TO')
        track_to_constraint.target = target
#        track_to_constraint.up_axis = 'UP_Z'
#        track_to_constraint.track_axis = 'TRACK_NEGATIVE_Z'

        # Add the camera to the cameras list for later use
        cameras.append(cam_obj)
        
    # TODO: Set the perspective camera as the active scene camera.
    perspective_camera = cameras[-1]
    bpy.context.scene.camera = perspective_camera
    return cameras
    pass
#####################################################################################################


#####################################################################################################
# Function: process_t1_head(file_path, output_path, downsample, threshold, absolute_scale)
# Purpose: Process and visualize the T1 MRI head by loading data, extracting the skull, applying modifiers, and rendering images.
def process_t1_head(file_path, output_path, downsample=4, threshold=0.65, absolute_scale=24.0):
    # TODO: Print starting information: file path, output path, threshold, downsample factor, and absolute scale.
    print("File path", file_path)
    print("Output path", output_path)
    print("Downsample", downsample)
    print("Threshold", threshold)
    print("Absolute scale", absolute_scale)
    
    # TODO: Call import_t1_head() with file_path and downsample to load volume_data.
    volume_data = import_t1_head(file_path, downsample=downsample)
    # TODO: Call extract_skull_surface_improved(volume_data, threshold) to obtain the skull mesh object.
    skull = extract_skull_surface_improved(volume_data, threshold=threshold, smooth_iterations=3) 
    # TODO: Set the skull object's scale to (absolute_scale, absolute_scale, absolute_scale).
    skull.select_set(True)
    skull.scale = (absolute_scale, absolute_scale, absolute_scale)
    # TODO: Add a Smooth modifier (e.g., factor 0.5 and iterations 3-5) to enhance surface quality.
    modifier_smooth = skull.modifiers.new(name="Smooth", type='SMOOTH')
    modifier_smooth.factor = 0.7
    modifier_smooth.iterations = 5

    print("Smooth shading, material assignment, and centering complete.")
    
    print("Remesh")
    
    # TODO: Add a Solidify modifier with a thickness (e.g., 0.2) to add volume to the mesh.
    modifier_solidify = skull.modifiers.new(name="Solidify", type='SOLIDIFY')
    modifier_solidify.thickness = 0.8
    modifier_solidify.use_rim = True
    print("Solidify modifier")
    
    # TODO: Optionally, add a Remesh modifier for a more uniform mesh.
    modifier_remesh = skull.modifiers.new(name="Remesh", type='REMESH')
    modifier_remesh.mode = 'SHARP'
    modifier_remesh.octree_depth = 8
    modifier_remesh.scale = 0.7
    print("Remesh")
    
    # TODO: Call setup_medical_lighting() to configure the scene lighting.
    setup_medical_lighting()
    # TODO: Call setup_t1_head_cameras() to create and position the cameras.
    cameras = setup_t1_head_cameras()
    
    # TODO: Create the output directory if it does not exist.
    if os.path.exists(output_path)==False:
        os.makedirs(output_path)
    # TODO: Loop through each camera view:
    #         - Set the active camera.
    #         - Modify the render output filepath to include the view name.
    #         - Render the image and save it.
    camera_view_names = ["Sagittal_Cam", "Coronal_Cam","Axial_Cam", "Perspective_Cam"]
    for i,camera in enumerate(cameras):
        bpy.context.scene.camera = camera
        bpy.context.scene.render.filepath = output_path + camera_view_names[i]
        bpy.ops.render.render(write_still=True)
        print("Rendering camera ", camera_view_names[i])
    pass
#####################################################################################################


#####################################################################################################
# Execute
if __name__ == "__main__":
    # TODO: Set the file path to the provided T1 MRI file (e.g., "t1-head.tif")
    #       and the output path for saving the rendered images.
    t1_file = dir_path + "/t1-head.tif"          # TODO: update with actual path
    print(t1_file)
    output_path = dir_path + "/save/"   # TODO: update with actual path
    
    # Print file and output information.
    # Call process_t1_head() with appropriate parameters:
    #   - downsample (e.g., 4),
    #   - threshold for skull extraction (e.g., 0.65),
    #   - absolute_scale for final object scaling (e.g., 24.0).
    # Make note of how the 3D model changes (e.g., your expectations with downsampling vs. what actually happens
    # or how changing threshold, scale can impact the final render). 
    process_t1_head(
        file_path=t1_file,
        output_path=output_path,
        downsample=2,
        threshold=0.85,
        absolute_scale=1.0
    )
#####################################################################################################
