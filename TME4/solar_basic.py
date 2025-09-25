import bpy
import random
from math import pi
import os

dir_path = os.getcwd()

def create_star(name="Star", location=(0,0,0), radius=1.0):
    # Low-poly sphere
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=64, 
        ring_count=16, 
        location=location, 
        radius=radius
    )
    star = bpy.context.active_object
    star.name = name

    # Simple yellow color
    mat = bpy.data.materials.new(name=f"{name}_Material")
#    mat.diffuse_color = (1.0, 0.9, 0.2, 1.0)  # bright yellow
    mat.use_nodes = True
    node_tree = mat.node_tree

    # Get the Principled BSDF node (default shader)
    principled_bsdf = node_tree.nodes.get("Principled BSDF")
    principled_bsdf.inputs["Emission Strength"].default_value = 2.0
    texture = bpy.data.images.load(dir_path+ "/textures/sun.jpg")
    
    # Create an Image Texture node and assign the texture
    image_texture = node_tree.nodes.new("ShaderNodeTexImage")
    image_texture.image = texture

    # Connect the Image Texture node to the Base Color input of Principled BSDF
    node_tree.links.new(image_texture.outputs["Color"], principled_bsdf.inputs["Base Color"])
    node_tree.links.new(image_texture.outputs["Color"], principled_bsdf.inputs["Emission Color"])
    
    star.data.materials.append(mat)
    
    scn =  bpy.context.scene
    scn.use_nodes = True
    tree = scn.node_tree
    nodes = tree.nodes
    links = tree.links
    
     # Clear existing nodes
    for node in nodes:
        nodes.remove(node)

    # Add Render Layers node
    render_layers = nodes.new(type="CompositorNodeRLayers")
    render_layers.location = (-400, 200)

    # Add Glare node for Bloom effect
    glare = nodes.new(type="CompositorNodeGlare")
    glare.location = (0, 200)
    glare.glare_type = 'BLOOM' 
    glare.threshold = 1
    glare.size = 30

    # Add Composite node
    composite = nodes.new(type="CompositorNodeComposite")
    composite.location = (400, 200)

    # Link nodes together
    links.new(render_layers.outputs["Image"], glare.inputs["Image"])
    links.new(glare.outputs["Image"], composite.inputs["Image"])

   
    return star

def create_planet(name="Planet", location=(0,0,0), radius=0.5, texture_path=""):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=32, 
        ring_count=16, 
        location=location, 
        radius=radius
    )
    planet = bpy.context.active_object
    planet.name = name

    # Assign texture
    mat = bpy.data.materials.new(name=f"{name}_Material")
    mat.use_nodes = True
    node_tree = mat.node_tree

    # Get the Principled BSDF node (default shader)
    principled_bsdf = node_tree.nodes.get("Principled BSDF")
    principled_bsdf.inputs["Emission Strength"].default_value = 0.3
    
    texture = bpy.data.images.load(texture_path)
    
    # Create an Image Texture node and assign the texture
    image_texture = node_tree.nodes.new("ShaderNodeTexImage")
    image_texture.image = texture

    # Connect the Image Texture node to the Base Color input of Principled BSDF
    node_tree.links.new(image_texture.outputs["Color"], principled_bsdf.inputs["Base Color"])
    node_tree.links.new(image_texture.outputs["Color"], principled_bsdf.inputs["Emission Color"])
    
    planet.data.materials.append(mat)

    return planet

def create_ring(name="Ring", location=(0,0,0), major_radius = 1):
    bpy.ops.mesh.primitive_torus_add(
            major_segments=64,
            minor_segments=16,
            major_radius= major_radius,
            minor_radius= 0.02,
            location=location,
            rotation = (0.4,0.3,0.0)
        )
    ring = bpy.context.active_object
    ring.name = name
    mat = bpy.data.materials.new(name=f"{name}_Material")
    mat.use_nodes = True
    node_tree = mat.node_tree
    
    principled_bsdf = node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    principled_bsdf.location = (0, 0)
    principled_bsdf.inputs["Base Color"].default_value = (0.945, 0.98, 0.024, 0.588)
    principled_bsdf.inputs["Roughness"].default_value = 0.8  # Slightly shiny
    principled_bsdf.inputs["Transmission Weight"].default_value = 0.5  # Partial transparency
    principled_bsdf.inputs["Alpha"].default_value = 0.5
    
    # Add Material Output
    material_output = node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    
    # Connect BSDF to Material Output
    node_tree.links.new(principled_bsdf.outputs["BSDF"], material_output.inputs["Surface"])

    # Enable transparency
    mat.blend_method = 'BLEND'  # Blend mode for transparency

    # Assign the material to the ring
    ring.data.materials.append(mat)
    return ring


def animate_planet_rotation(planet, frames=60, orbit_distance=3, rate=1):
    # Create an empty as pivot at the star's location (0,0,0)
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,0))
    pivot = bpy.context.active_object
    pivot.name = f"{planet.name}_Pivot"

    # Parent the planet to the pivot and offset it by orbit_distance
    planet.parent = pivot
    planet.location.x = orbit_distance

    # Keyframe pivot rotation at frame 1
    pivot.rotation_euler[2] = 0
    pivot.keyframe_insert(data_path="rotation_euler", frame=1)
    

    # Keyframe pivot rotation at frame 'frames' (one full orbit)
    pivot.rotation_euler[2] = 2 * pi * rate
    pivot.keyframe_insert(data_path="rotation_euler", frame=frames)

    # Set interpolation to LINEAR for constant speed
    action = pivot.animation_data.action
    fcurve = action.fcurves.find('rotation_euler', index=2)
    for keyframe in fcurve.keyframe_points:
        keyframe.interpolation = 'LINEAR'

    # Adjust the scene frame range to match the animation
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = frames
    
def create_space():
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.world.use_nodes = True

    #select world node tree
    wd = scn.world
    wd.name = "World"
    nt = bpy.data.worlds[wd.name].node_tree

    #create new gradient texture node
    noiseNode = nt.nodes.new(type="ShaderNodeTexNoise")
    noiseNode.inputs['Detail'].default_value = 0.0
    
    
    mappingNode = nt.nodes.new("ShaderNodeMapping")
    mappingNode.inputs["Scale"].default_value = (20.0, 20.0, 20.0)
    
    textcoNode = nt.nodes.new(type="ShaderNodeTexCoord")
    colorRampNode = nt.nodes.new(type="ShaderNodeValToRGB")
    
    colorRampNode.color_ramp.elements[0].position = 0.75
    colorRampNode.color_ramp.elements[1].position = 0.8

#    #find location of Background node and position Grad node to the left
    bgNode = nt.nodes['Background']
#    gradNode.location.x = backNode.location.x-300
#    gradNode.location.y = backNode.location.y

    #Connect color out of Grad node to Color in of Background node

    nt.links.new(bgNode.inputs['Color'], colorRampNode.outputs['Color'])
    nt.links.new(colorRampNode.inputs['Fac'], noiseNode.outputs['Color'])
    nt.links.new(noiseNode.inputs['Vector'], mappingNode.outputs['Vector'])
    nt.links.new(mappingNode.inputs['Vector'], textcoNode.outputs['Generated'])

    #set gradient type to easing
#    gradNode.gradient_type = 'EASING'

    return scn

def main():
    
    print(dir_path)
    # Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Create one star
    star = create_star(name="Sun", radius=2)

    # Create a couple of planets
    num_planets = 5
    mercury = create_planet(
        name = f"Mercury",
        radius = 0.3,
        texture_path= dir_path + "/textures/mercury_brown.png"
    )
    animate_planet_rotation(
            mercury, 
            frames=180, 
            orbit_distance=3,
            rate = 6
    )
    venus = create_planet(name = f"Venus", radius = 0.35, texture_path = dir_path + "/textures/venus_brighter.jpg")
    animate_planet_rotation(venus, frames=180, orbit_distance=4, rate = 5)
    
    earth = create_planet(name = f"Earth", radius = 0.4, texture_path = dir_path + "/textures/earth.jpg")
    animate_planet_rotation(earth, frames=180, orbit_distance=5, rate=4)
    
    mars = create_planet(name = f"Nars", radius = 0.4, texture_path = dir_path + "/textures/mars.jpg")
    animate_planet_rotation(mars, frames=180, orbit_distance=6, rate=3)
    
    jupiter = create_planet(name = f"Jupiter", radius = 0.6, texture_path = dir_path + "/textures/jupiter.png")
    animate_planet_rotation(jupiter, frames=180, orbit_distance=7.2, rate=2.5)
    
    saturn = create_planet(name = f"Saturn", radius = 0.65, texture_path = dir_path + "/textures/saturn_bj.jpg")
    animate_planet_rotation(saturn, frames=180, orbit_distance=9, rate=2)
    for i in range(5):
        ring = create_ring(
            name=f"Saturn_Ring_{i}",
            major_radius = 0.8 + i*0.1,
        )
        animate_planet_rotation(ring, frames=180, orbit_distance=9, rate=2)
    
    uranus = create_planet(name = f"Uranus", radius = 0.4, texture_path = dir_path + "/textures/uranus.png")
    animate_planet_rotation(uranus, frames=180, orbit_distance=11, rate=1.5)
    
    neptune = create_planet(name = f"Neptune", radius = 0.4, texture_path = dir_path + "/textures/neptune.jpg")
    animate_planet_rotation(neptune, frames=180, orbit_distance=13, rate=1)
    
    # Create background
    space = create_space()

if __name__ == "__main__":
    main()
