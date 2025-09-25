import bpy
import math
from mathutils import Vector
import random
import aud
import time
import os

### OPTIMIZATION
# - Put checking ghost collision from move_pacman() to move_ghost()
##      Because when pacman doesn't move, even when ghost and pacman collided, the function's not working properly.
##      That's why I move check ghosts collision to function move_ghost(), because the ghost always moving and not depending on human input.
# - Skip fancy visual effects
##      I only use simple Cube for the Maze and Sphere for other objects, and paint with basic color. No fancy effects.
# - Use simple colors and texture
##      Using function create_basic_material(), I only add basic color for object and no fancy texture.
# - Clear objects from memory
##      Whenever Pacman collecting an item, I delete this item from the scene.
##      Also, whenever I rerun the program, I delete all of the past objects using clear_scene()


# Getting the current directory of the program
filepath = bpy.data.filepath
dir_path = os.path.dirname(filepath)

class PacmanGame:
    def __init__(self):
        self.score = 0
        self.lives = 3
        
        self.wall_position = []
        self.dot_position = []
        self.game_over = False
        
        self.pacman = bpy.context
        self.pacman_initial_location = (0,0,0) # if pacman dead, it's going back to initial location
        self.pacman_direction = (0,0) # initial direction (not moving)
        self.pacman_speed = 0.5
        
        self.ghosts = []
        self.ghosts_initial_location = [(5,5,0), (-4,4,0), (10,3,0)] # initial location of each ghost, store in a list
        self.ghosts_speed = 0.3

        
    def initialize(self):
        # Again, more can be added here!
        self.clear_scene()
        self.setup_scene()
        self.setup_sound()
        self.play_sound(sound_name='intro')

        
    def clear_scene(self):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
    def setup_scene(self):
        #  Camera setup - change to suit your laptop's resources
        self.pacman = self.create_pacman(
            location=(0,0,0),
            radius=0.5
        )

        self.create_maze()

        for i in range(3):
            ghost = self.create_ghosts(
                location=self.ghosts_initial_location[i],
                radius=0.5
            )
            self.ghosts.append(ghost)
    
    def setup_sound(self):
        # get the sound device
        self.device = aud.Device()
        
        #load sound files
        sound_dir = dir_path + '/sound'
        print(sound_dir)
        
        self.sounds = {
            'intro': aud.Sound(os.path.join(sound_dir, "pacman_beginning.wav")),
            'death': aud.Sound(os.path.join(sound_dir, "pacman_dead.wav")),
            'eat_dot': aud.Sound(os.path.join(sound_dir, "pacman_chomp.wav")),
            'eat_ghost': aud.Sound(os.path.join(sound_dir, "pacman_eatghost.wav")),
        }
        
    def play_sound(self, sound_name):
        try:
            handle = self.device.play(self.sounds[sound_name])
            handle.volume = 0.5
        except KeyError:
            print(f"Sound {sound_name} not found")
        
    # Optimization: Use simple colors instead of textures    
    def create_basic_material(self, color):
        """
        A simple, efficient material color: tuple (R,G,B,A)
        """
        mat = bpy.data.materials.new(name="Basic")
        mat.use_nodes = False  # Faster than node-based materials
        mat.diffuse_color = color
        return mat

    def create_wall_material(self):
        """Create specific material for walls"""
        return self.create_basic_material((0, 0, 1, 1))  # Blue walls

    def create_maze(self):
        
        # This isn't even a maze, it's literally a box
        # Change it to look more like a maze.
        self.maze_layout = [
            "####################",
            "#         #        #",
            "# # # ###   ## ##  #",
            "# # # #   #  #     #",
            "#   # # # ##   ### #",
            "# # # #   #  # ### #",
            "#       #   #      #",
            "# ## ## ###   # # ##",
            "#           ###   ##",
            "####################",
        ]
        
        for y, row in enumerate(self.maze_layout):
            for x, cell in enumerate(row):
                location=(x-5, y-3, 0)
                if cell == '#':
                    bpy.ops.mesh.primitive_cube_add(location=location)
                    self.wall_position.append(location)
                    wall = bpy.context.active_object
                    wall.scale = (0.5, 0.5, 0.2)  # Flatter walls for performance
                    wall.data.materials.append(self.create_wall_material())
                elif location != self.pacman_initial_location: # Create dots at place not having walls and the initial place of pacman
                    self.create_dots(
                        location=location, 
                        radius=0.1
                    )
                    self.dot_position.append(location)

    def create_pacman(self, name="Pacman", location=(0,0,0), radius=0.5):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=64, 
            ring_count=16, 
            location=location, 
            radius=radius
        )
        pac = bpy.context.active_object
        pac.name = name
        
        # Create a material and assign a color
        mat = self.create_basic_material((1, 1, 0,1))  # Yellow color
        pac.data.materials.append(mat)
        
        return pac
        

    def create_dots(self, name="Dot", location=(0,0,0), radius=0.3):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=32, 
            ring_count=16, 
            location=location, 
            radius=radius
        )
        dot = bpy.context.active_object
        dot.name = name
        
        # Create a material and assign a color
        mat = self.create_basic_material((2, 2, 2,1))  # White color
        
        dot.data.materials.append(mat)

    def create_ghosts(self,name="Ghost", location=(0,0,0), radius=0.5, color=(0,0,0,1)):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=32, 
            ring_count=16, 
            location=location, 
            radius=radius
        )
        ghost = bpy.context.active_object
        ghost.name = name
        
        # Create a material and assign a color
        mat = self.create_basic_material(color)
        
        ghost.data.materials.append(mat)
        return ghost

    def check_collision(self, pos1, pos2, threshold=0.8):
        # calculate the distance between 2 object
        distance = math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2 + ((pos1[2] - pos2[2]) ** 2))
        return distance < threshold


    def move_pacman(self, direction):
        if self.game_over:
            return
        new_loc = self.pacman.location.copy()
        new_loc.x += direction[0] * self.pacman_speed
        new_loc.y += direction[1] * self.pacman_speed
        
        # Wall collision check
        for pos in self.wall_position:
            if(self.check_collision(new_loc, pos)):
                return
        
        bpy.ops.object.select_all(action='DESELECT')
        # Dot collection
        for pos in self.dot_position:
            if(self.check_collision(new_loc, pos)):
                for obj in bpy.data.objects:
                    # find the dot that pacman is eating from all object based on position
                    if ((obj.location[0]-pos[0])**2 + (obj.location[1]-pos[1])**2 + (obj.location[2]-pos[2])**2) <= 0.1: 
                        obj.select_set(True)
                        self.dot_position.remove(pos)
                        if not self.dot_position:
                            self.game_over=True
                        bpy.data.objects.remove(obj)
                        bpy.ops.object.delete() # delete this dot from scene
                        break
                self.play_sound('eat_dot')
                self.score += 10 # collecting dot score
                break
            
        self.pacman.location = new_loc # update pacman location
    
    # Choose direction for ghost to move
    def choose_direction(self, loc1, loc2):
        directions = [
            (1,0), (-1,0), (0,1), (0,-1)
        ]

        optimize_dir = (0,0)
        min_dis = 30

        # Checking wall collisions if ghost move in each direction
        for dir in directions:
            x = loc1.x + dir[0] * self.ghosts_speed
            y = loc1.y + dir[1] * self.ghosts_speed
            
            # if in this direction ghost meets wall collision => check another direction
            wall_col = False
            for pos in self.wall_position:
                if(self.check_collision((x,y,loc1.z), pos)):
                    wall_col = True
                    break
                
            if wall_col == False:
                # Calculate the direction with the minimum distance => choose this direction
                dis = math.sqrt((loc2[0] - x) ** 2 + (loc2[1] - y) ** 2)
                if dis < min_dis:
                    min_dis = dis
                    optimize_dir = dir
        return optimize_dir
        
    def move_ghosts(self):
        if self.game_over:
            return
        pacman_loc = self.pacman.location
        for ghost in self.ghosts:
            loc = ghost.location.copy()
            # choose direction for ghost to move
            direction = self.choose_direction(loc, pacman_loc)
            # Calculate new location
            loc.x += direction[0] * self.ghosts_speed
            loc.y += direction[1] * self.ghosts_speed
            
            ghost.location = loc
            
            # Check pacman ghost collision => Pacman dies
            if(self.check_collision(loc, pacman_loc)):
                self.lives -= 1
                self.play_sound('death')
                time.sleep(2)
                # if we have no more lives => End game
                if(self.lives==0):
                    print("Score:", self.score)
                    self.game_over = True
                # update pacman, ghost to initial location and initial direction(not moving)
                self.pacman.location = self.pacman_initial_location
                self.pacman_direction = (0,0)
                for i, ghost in enumerate(self.ghosts):
                    ghost.location = self.ghosts_initial_location[i]
                return
        

class PacmanGameOperator(bpy.types.Operator):
    bl_idname = "game.pacman"
    bl_label = "Pacman Game"
    
    timer = None
    game_instance = None
    
    def modal(self, context, event):
        # Remember, event types can be LEFT_ARROW, RIGHT_ARROW, etc.
        # Also include a way to cancel the event
        if event.type == 'ESC':
            return {'CANCELLED'}
        
        arrows = {
            'LEFT_ARROW':   (-1,0),
            'RIGHT_ARROW':  (1,0), 
            'UP_ARROW':     (0,1), 
            'DOWN_ARROW':   (0,-1),
        }
        
        
        if event.type in arrows and event.value =='PRESS':
            type = event.type
            self.game_instance.pacman_direction = arrows[event.type]
            return {'RUNNING_MODAL'}
        
        # Update pacman location and ghost location constantly
        if event.type == 'TIMER':
            self.game_instance.move_pacman(self.game_instance.pacman_direction)
            self.game_instance.move_ghosts()
        
        if self.game_instance.game_over: 
            return {'FINISHED'}
        
        return {'PASS_THROUGH'}
    
    def execute(self, context):
        self.game_instance = PacmanGame()
        self.game_instance.initialize()
        
        wm = context.window_manager
        # Slower timer for better performance
        self.timer = wm.event_timer_add(0.4, window=context.window)
        wm.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        if self.timer:
            context.window_manager.event_timer_remove(self.timer)

def register():
    bpy.utils.register_class(PacmanGameOperator)


def unregister():
    bpy.utils.unregister_class(PacmanGameOperator)


if __name__ == "__main__":
    register()
    bpy.ops.game.pacman()