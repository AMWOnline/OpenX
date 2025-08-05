# Open-X Version 1.3
# Developed by Madden Wilkins
# www.mjwil116.codehs.me/openx.html

import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

import os
import time
import random
import math
import numpy as np
from PIL import Image

import re

pygame.font.init()

# Global constants

CAMERA_POS = [0, 0, -6.5]
CAMERA_ROT = [0, 0, 0, 0]
FOG_COLOR = [0, 0, 0]
CEIL_TEX = "tex_missing.png"
FLOOR_TEX = "tex_missing.png"

# Initialize OpenGL and Pygame

def init():

    pygame.init()

    print("\n"*256)
    print("This application is being emulated in OpenX (v1.2).\n")
    print("Controls:")
    print("[Z] - A")
    print("[X] - B")
    print("[ARROWS/WASD] - D-Pad\n")
    print("Some programs may require the use of the mouse to simulate analog movement.\n")
    print("www.mjwil116.codehs.me/openx.html")

    display = (800, 600)
    screen = pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (4/3), 0.1, 100.0)
    
    glMatrixMode(GL_MODELVIEW)

    glLight(GL_LIGHT0, GL_POSITION,  (5, 5, 5, 1))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (1, 1, 1, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1, 1, 1, 1))
    
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    glTranslatef(CAMERA_POS[0], CAMERA_POS[1], CAMERA_POS[2])

# Refresh the screen

def flip():

        pygame.display.flip()
        pygame.time.wait(10)

        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

# Returns an OpenGL Texture ID from a provided filepath

def load_texture(filepath):
            
    try:
        img = Image.open(filepath)
    except:
        img = Image.open("tex_error.png")
        print("Open-X [WARNING] >> Unable to load texture filepath '" + filepath + "'!")
                
    img_data = np.array(list(img.getdata()), np.uint8)
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.width, img.height, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
    #glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
    glBindTexture(GL_TEXTURE_2D, 0)
    return texture_id

# For billboard sprites; returns a pixel width/height based on the distance of the sprite to the camera

def coord_to_scale(x, y, z, maximum):

    distance = math.sqrt(((CAMERA_POS[0] - x)**2) + ((CAMERA_POS[1] - y)**2) + ((CAMERA_POS[2] - z)**2))

    result = -(distance - maximum)
    
    if result < 0:

        return 0

    else:

        return result

# For loading and unloading lighting OpenGL methods

def lights_on():

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)

def lights_off():

        glDisable(GL_LIGHT0)
        glDisable(GL_LIGHTING)
        glDisable(GL_COLOR_MATERIAL)
        
'''
Controller Class

Methods to allow controller input (that conforms to the OpenX standard)
'''

class Controller:
    
    # Returns a string of the button pressed. Ex: 'a' for when A is pressed and 'u/l/d/r' for arrow keys, etc.
    
    # Always returns single character strings
    
    def read():
        
        for event in pygame.event.get():
                
            if event.type == pygame.KEYDOWN:
                
                if pygame.key.name(event.key).upper() == "Z":
                    
                    return 'a'
                    
                if pygame.key.name(event.key).upper() == "X":
                    
                    return 'b'
                    
                if pygame.key.name(event.key).upper() == "UP":
                    
                    return 'u'
                    
                if pygame.key.name(event.key).upper() == 'DOWN':
                    
                    return 'd'
                    
                if pygame.key.name(event.key).upper() == 'LEFT':
                    
                    return 'l'
                    
                if pygame.key.name(event.key).upper() == 'RIGHT':
                    
                    return 'r'


'''
Camera Class

Methods to allow for the environment/camera to be manipulated to show different perspectives of the scene.

'''
class Camera:

    # Rotate the environment, with specific angle along roll (X), pitch (Y), and yaw (Z).
    def rotate(angle, roll, pitch, yaw):
        
        global CAMERA_ROT
        
        CAMERA_ROT = [angle, roll, pitch, yaw]
        
        glRotatef(angle, roll, pitch, yaw)
        
    # Translate the entire environment by x, y, z units.   
    def translate(x,y,z):
        
        global CAMERA_POS
        CAMERA_POS = [CAMERA_POS[0] + x, CAMERA_POS[1] + y, CAMERA_POS[2] + z]
        glTranslatef(x,y,z)
    
    # Takes in a array of 3 elements, representing roll, pitch and yaw. If the rotation along one axis is above 360 deg, set it to 0 deg. Returns new array.
    def cull_rotation(arr):
        
        result_arr_0 = arr[0]
        result_arr_1 = arr[1]
        result_arr_2 = arr[2]
        
        if arr[0] >= 361:
            
            result_arr_0 = 0
            
        if arr[1] >= 361:
            
            result_arr_1 = 0
            
        if arr[2] >= 361:
            
            result_arr_2 = 0
            
        return [result_arr_0, result_arr_1, result_arr_2]
    
'''
Environment Class

Methods for controlling the behavior and appearance of the scene environment; such as lighting, fog, ceiling and roof properties, etc.

'''
class Environment:
    
    # Set fog color of the environment in RGB
    def set_fog_color(r, g, b):

        global FOG_COLOR
        FOG_COLOR = [(r/255), (g/255), (b/255)]
        glClearColor((r/255), (g/255), (b/255), 0)
    
    class Ceiling:
        
        def draw():

            global CEIL_TEXT

            tcoords = [
                [0,1,1,0,0],
                [0,0,1,1,0]
                ]

            verts = [
                [-128,0,128],
                [128,0,128],
                [128,0,-128],
                [-128,0,-128]
                ]
            
            surfs = [
                [0,1,2,3]
                ]
            
            texture_id = load_texture(CEIL_TEX)

            glTranslatef(0, 6.5, 0)
            
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, 0);
            
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glBegin(GL_QUADS)

            glTexCoord2f(0,0)
            glVertex3fv(verts[0])

            glTexCoord2f(32,0)
            glVertex3fv(verts[1])

            glTexCoord2f(32,32)
            glVertex3fv(verts[2])

            glTexCoord2f(0,32)
            glVertex3fv(verts[3])

            glTexCoord2f(0,0)
            glVertex3fv(verts[0])
                    
            glEnd()
            
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)

            glTranslatef(0, -6.5, 0)

        def apply_texture(filepath):

            global CEIL_TEX
            CEIL_TEX = filepath

    class Floor:
        
        def draw():

            global FLOOR_TEX

            tcoords = [
                [0,1,1,0,0],
                [0,0,1,1,0]
                ]

            verts = [
                [-128,0,128],
                [128,0,128],
                [128,0,-128],
                [-128,0,-128]
                ]
            
            surfs = [
                [0,1,2,3]
                ]
            
            texture_id = load_texture(FLOOR_TEX)

            glTranslatef(0, -6.5, 0)
            
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, 0);
            
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glBegin(GL_QUADS)

            glTexCoord2f(0,0)
            glVertex3fv(verts[0])

            glTexCoord2f(32,0)
            glVertex3fv(verts[1])

            glTexCoord2f(32,32)
            glVertex3fv(verts[2])

            glTexCoord2f(0,32)
            glVertex3fv(verts[3])

            glTexCoord2f(0,0)
            glVertex3fv(verts[0])
                    
            glEnd()
            
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)

            glTranslatef(0, 6.5, 0)

        def apply_texture(filepath):

            global FLOOR_TEX
            FLOOR_TEX = filepath
'''
Tex2D Class

Methods dealing with actors with 2D properties like Billboards.

'''
class Tex2D:

    class Billboard:

        # Creates a new billboard sprite object with at x, y, z, and texture filepath.
        def __init__(self, x, y, z, filepath):

            self.x = x
            self.y = y
            self.z = z
            self.filepath = filepath

        def draw(self):

             # Load texture filepath to a pygame surface
            
            try:

                img_load = pygame.image.load(self.filepath)
                surface = pygame.transform.scale(img_load, (coord_to_scale(self.x, self.y, self.z, img_load.get_width()), coord_to_scale(self.x, self.y, self.z, img_load.get_height())))
            
            except:
            
                # If filepath is invalid or doesn't exist, load the error texture, and raise a warning
                surface = pygame.image.load('tex_error.png')
                print("Open-X [WARNING] >> Unable to load Tex2D (StaticBillboard) filepath '" + self.filepath + "'!")

            # Get image pixel data string, and draw the data to screen at position (x,y,z)

            glTranslatef(0, 0, self.z)

            
            image_data = pygame.image.tostring(surface, 'RGBA', True)
            glRasterPos2d(self.x -0.2, self.y - 0.2)
            glDrawPixels(surface.get_width(), surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, image_data)

            glTranslatef(0, 0, -(self.z))
            
'''
Geometry Class

Methods for creating in-scene geometry objects such as cubes, spheres, cones, etc.

'''    
class Geometry:
    
    # CLASS - Rectangular Prism
    class RectangularPrism:
        
        # Creates new rectangular prism 3D Object with length, width, height, at x, y, z
        def __init__(self, l, w, h, x, y, z):
            
            self.length = l
            self.width = w
            self.height = h
            self.pos_x = x
            self.pos_y = y
            self.pos_z = z

            self.tiles = 1
            
            self.texture = "tex_missing.png"
            
            self.VERTICIES = [
                [-1,1,-1],
                [1,1,-1],
                [1,1,1],
                [-1,1,1],
                [-1,-1,-1],
                [1,-1,-1],
                [1,-1,1],
                [-1,-1,1],
                ]
                
            for vertex in self.VERTICIES:
                vertex[0] += x
                vertex[1] += y
                vertex[2] += z
                vertex[0] *= w
                vertex[1] *= h
                vertex[2] *= l

        # Move / translate the object by moving it in the x,y,z coordinate plane.
        def translate(self, x, y, z):
            
            for vertex in self.VERTICIES:
                vertex[0] += x
                vertex[1] += y
                vertex[2] += z

        # Transform the object by stretching or shrinking its length, width and/or height.
        def transform(self, x, y, z):
            
            for vertex in self.VERTICIES:
                vertex[0] *= w
                vertex[1] *= h
                vertex[2] *= l

        
        # Render object to screen.
        def draw(self):
                
            texture_id = load_texture(self.texture)
            
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, 0);
            
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE )
            
            lights_on()
            
            glBegin(GL_QUADS)
            
            Geometry.RectangularPrism._draw_face(self, [0,1,2,3])
            Geometry.RectangularPrism._draw_face(self, [4,5,6,7])
            Geometry.RectangularPrism._draw_face(self, [3,2,6,7])
            Geometry.RectangularPrism._draw_face(self, [2,1,5,6])
            Geometry.RectangularPrism._draw_face(self, [1,0,4,5])
            Geometry.RectangularPrism._draw_face(self, [0,3,7,4])
  
            glEnd()

            lights_off()
            
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)
            
        def _draw_face(self, vertlist):
                        
            glTexCoord2f(0,0)
            glVertex3fv(self.VERTICIES[vertlist[0]])

            glTexCoord2f(self.tiles,0)
            glVertex3fv(self.VERTICIES[vertlist[1]])

            glTexCoord2f(self.tiles,self.tiles)
            glVertex3fv(self.VERTICIES[vertlist[2]])

            glTexCoord2f(0,self.tiles)
            glVertex3fv(self.VERTICIES[vertlist[3]])


        # Applies a new texture to the object, with how many times that texture should be tiled.
        def apply_texture(self, fp, tiling):
            
            self.texture = fp
            self.tiles = tiling


        
    # CLASS - Triangular Pyramid
    class TriangularPyramid:
        
        # Creates new triangular pyramid 3D Object with length, width, height, at x, y, z
        def __init__(self, l, w, h, x, y, z):
            
            self.length = l
            self.width = w
            self.height = h
            self.pos_x = x
            self.pos_y = y
            self.pos_z = z

            self.tiles = 1
            
            self.texture = "tex_missing.png"
            
            self.TEX_COORDS = [
                [0,1,1,0,0],
                [0,0,1,1,0]
                ]
            
            self.VERTICIES = [
                [0,1,0],
                [-1,0,1],
                [0,0,-1],
                [1,0,1]
                ]
                
            for vertex in self.VERTICIES:
                vertex[0] += x
                vertex[1] += y
                vertex[2] += z
                vertex[0] *= w
                vertex[1] *= h
                vertex[2] *= l

        # Move / translate the object by moving it in the x,y,z coordinate plane.
        def translate(self, x, y, z):
            
            for vertex in self.VERTICIES:
                vertex[0] += x
                vertex[1] += y
                vertex[2] += z

        # Transform the object by stretching or shrinking its length, width and/or height.
        def transform(self, x, y, z):
            
            for vertex in self.VERTICIES:
                vertex[0] *= w
                vertex[1] *= h
                vertex[2] *= l

        
        # Render object to screen.
        def draw(self):
                
            texture_id = load_texture(self.texture)
            
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, 0);
            
            glBindTexture(GL_TEXTURE_2D, texture_id)

            lights_on()
            
            glBegin(GL_QUADS)

            Geometry.TriangularPyramid._draw_face(self, [1,2,3])
            Geometry.TriangularPyramid._draw_face(self,[1,0,3])
            Geometry.TriangularPyramid._draw_face(self,[3,0,2])
            Geometry.TriangularPyramid._draw_face(self,[2,0,1])
                    
            glEnd()

            lights_off()
            
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)

        def _draw_face(self, vertlist):

            glTexCoord2f(0,0)
            glVertex3fv(self.VERTICIES[vertlist[0]])

            glTexCoord2f(0,self.tiles)
            glVertex3fv(self.VERTICIES[vertlist[1]])

            glTexCoord2f(self.tiles,self.tiles)
            glVertex3fv(self.VERTICIES[vertlist[2]])

            glTexCoord2f(self.tiles,0)
            glVertex3fv(self.VERTICIES[vertlist[0]])
        
        # Applies a new texture to the object, with how many times that texture should be tiled.
        def apply_texture(self, fp, tiling):
            
            self.texture = fp
            self.tiles = tiling

    # CLASS - Rectangular Pyramid
    class Pyramid:
        
        # Creates new pyramid 3D Object with length, width, height, at x, y, z
        def __init__(self, l, w, h, x, y, z):
            
            self.length = l
            self.width = w
            self.height = h
            self.pos_x = x
            self.pos_y = y
            self.pos_z = z

            self.tiles = 1
            
            self.texture = "tex_missing.png"
            
            self.TEX_COORDS = [
                [0,1,1,0,0],
                [0,0,1,1,0]
                ]
            
            self.VERTICIES = [
                [0,1,0],
                [-1,0,1],
                [1,0,1],
                [1,0,-1],
                [-1,0,-1]
                ]
                
            for vertex in self.VERTICIES:
                vertex[0] += x
                vertex[1] += y
                vertex[2] += z
                vertex[0] *= w
                vertex[1] *= h
                vertex[2] *= l

        # Move / translate the object by moving it in the x,y,z coordinate plane.
        def translate(self, x, y, z):
            
            for vertex in self.VERTICIES:
                vertex[0] += x
                vertex[1] += y
                vertex[2] += z

        # Transform the object by stretching or shrinking its length, width and/or height.
        def transform(self, x, y, z):
            
            for vertex in self.VERTICIES:
                vertex[0] *= w
                vertex[1] *= h
                vertex[2] *= l

        
        # Render object to screen.
        def draw(self):
                
            texture_id = load_texture(self.texture)
            
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, 0);
            
            glBindTexture(GL_TEXTURE_2D, texture_id)

            lights_on()
            
            glBegin(GL_QUADS)

            Geometry.TriangularPyramid._draw_face(self, [0,1,2])
            Geometry.TriangularPyramid._draw_face(self, [0,2,3])
            Geometry.TriangularPyramid._draw_face(self, [0,3,4])
            Geometry.TriangularPyramid._draw_face(self, [0,4,1])

            glTexCoord2f(0,0)
            glVertex3fv(self.VERTICIES[1])
            
            glTexCoord2f(self.tiles,0)
            glVertex3fv(self.VERTICIES[2])
            
            glTexCoord2f(self.tiles,self.tiles)
            glVertex3fv(self.VERTICIES[3])
            
            glTexCoord2f(0,self.tiles)
            glVertex3fv(self.VERTICIES[4])

            glTexCoord2f(0,0)
            glVertex3fv(self.VERTICIES[1])
                    
            glEnd()

            lights_off()
            
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)

        def _draw_face(self, vertlist):

            glTexCoord2f(0,0)
            glVertex3fv(self.VERTICIES[vertlist[0]])

            glTexCoord2f(0,self.tiles)
            glVertex3fv(self.VERTICIES[vertlist[1]])

            glTexCoord2f(self.tiles,self.tiles)
            glVertex3fv(self.VERTICIES[vertlist[2]])

            glTexCoord2f(self.tiles,0)
            glVertex3fv(self.VERTICIES[vertlist[0]])
        
        # Applies a new texture to the object, with how many times that texture should be tiled.
        def apply_texture(self, fp, tiling):
            
            self.texture = fp
            self.tiles = tiling

    # CLASS - Sphere
    class Sphere:
        
        # Creates new Sphere Object with radius, at x, y, z
        def __init__(self, r, x, y, z):
            
            self.radius = r
            self.pos_x = x
            self.pos_y = y
            self.pos_z = z

            self.texture = "tex_missing.png"
            
        # Move / translate the object by moving it in the x,y,z coordinate plane.
        def translate(self, x, y, z):
            
            self.pos_x += x
            self.pos_y += y
            self.pos_z += z

        # Transform the object by stretching or shrinking its length, width and/or height.
        def transform(self, r):
            
            self *= r

        
        # Render object to screen.
        def draw(self):
            glTranslatef(self.pos_x, self.pos_y, self.pos_z)
            glRotatef(90, 1, 0, 0)

            
            qobj = gluNewQuadric()
            gluQuadricTexture(qobj, GL_TRUE)
            
            texture_id = load_texture(self.texture)
            
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, 0);
            
            glBindTexture(GL_TEXTURE_2D, texture_id)

            lights_on()
            
            gluSphere(qobj, self.radius, 20, 20)
            
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)

            lights_off()
            
            gluDeleteQuadric(qobj)
            
            glRotatef(-90, 1, 0, 0)
            glTranslatef(-self.pos_x, -self.pos_y, -self.pos_z)
        
        # Applies a new texture to the object.
        def apply_texture(self, fp):
            
            self.texture = fp

    # CLASS - Cylinder
    class Cylinder:
        
        # Creates new Cylinder Object with bottom and top radii, height, at x, y, z
        def __init__(self, b, t, h, x, y, z):
            
            self.bottom_radius = b
            self.top_radius = t
            self.height = h
            self.pos_x = x
            self.pos_y = y
            self.pos_z = z

            self.texture = "tex_missing.png"
            
        # Move / translate the object by moving it in the x,y,z coordinate plane.
        def translate(self, x, y, z):
            
            self.pos_x += x
            self.pos_y += y
            self.pos_z += z

        # Transform the object by stretching or shrinking its length, width and/or height.
        def transform(self, b, t, h):
            
            self.bottom_radius *= b
            self.top_radius *= t
            self.height *= h

        
        # Render object to screen.
        def draw(self):
            glTranslatef(self.pos_x, self.pos_y, self.pos_z)
            glRotatef(90, 1, 0, 0)

            qobj = gluNewQuadric()
            gluQuadricTexture(qobj, GL_TRUE)
            
            texture_id = load_texture(self.texture)
            
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, 0);
            
            glBindTexture(GL_TEXTURE_2D, texture_id)

            lights_on()
            
            gluCylinder(qobj, self.bottom_radius, self.top_radius, self.height, 8, 8)
            
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)

            lights_off()

            gluDeleteQuadric(qobj)
            
            glRotatef(-90, 1, 0, 0)
            glTranslatef(-self.pos_x, -self.pos_y, -self.pos_z)
        
        # Applies a new texture to the object.
        def apply_texture(self, fp):
            
            self.texture = fp
            
'''
Font Class

Methods for rendering fonts on screen.

'''  
class Font:
    
    # Draws default pygame font at (x, y) with str text, with fg and bg colors, with size in px
    # Input: float x, floay y, str text, (r,g,b,a), (r,g,b,a), int size
    
    def draw_rgba(x, y, font, text, color, bg_color, size):        

        try:
            
            font = pygame.font.Font(font, size)
            
        except:

            print("Open-X [WARNING] >> Unable to load font filepath '" + filepath + "'! Reverting to default font.")
            font = pygame.font.Font(pygame.font.get_default_font(), size)
        
        textSurface = font.render(text, True, color, bg_color)
        textData = pygame.image.tostring(textSurface, "RGBA", True)
        glWindowPos2d(x, y)
        glDrawPixels(textSurface.get_width(), textSurface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, textData)

'''

XObject Class
Allows for the use of custom 3D models made using the '.xobj' file format

'''
        
class XObject:
    
    # Creates a new XObject with xobj file at path fp with position x, y, z and transform of l, w, h
    def __init__(self, fp, x, y, z, l, w, h):
        
        self.pos_x = x
        self.pos_y = y
        self.pos_z = z
        self.length = l
        self.width = w
        self.height = h
        self.filepath = fp
    
        self.VERTICIES = []
        self.FACES = []
        
        self.texture = "tex_missing.png"
        self.tiles = 1
        
        with open(os.getcwd() + "/" + self.filepath, "r") as file:
            lines = [line.rstrip() for line in file]
            
            for line in lines:
                
                if line[0] == "v":
                    
                    
                    l = []
        
                    for t in line.split():
                        
                        try:
                            l.append(float(t))
                            
                        except ValueError:
                            pass
                        
                        
                    self.VERTICIES.append(l)
                    
                if line[0] == "f":
                    
                    
                    l = []
        
                    for t in line.split():
                        
                        try:
                            l.append(int(t))
                            
                        except ValueError:
                            pass
                        
                        
                    self.FACES.append(l)
                        
    # Move / translate the object by moving it in the x,y,z coordinate plane.
    def translate(self, x, y, z):
            
        self.pos_x += x
        self.pos_y += y
        self.pos_z += z
        
    # Renders the XObject in the scene
    def draw(self):
        
        texture_id = load_texture(self.texture)
            
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)
            
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, 0);
            
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE )
            
        lights_on()
            
        glBegin(GL_QUADS)
        
        for i in range(len(self.FACES)):
            XObject._draw_face(self, self.FACES[i])
  
        glEnd()

        lights_off()
            
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)
        
        
    def _draw_face(self, vertlist):
        
        #print(vertlist)

        glTexCoord2f(0,0)
        glVertex3fv(self.VERTICIES[vertlist[0] - 1])

        glTexCoord2f(0,self.tiles)
        glVertex3fv(self.VERTICIES[vertlist[1] - 1])

        glTexCoord2f(self.tiles,self.tiles)
        glVertex3fv(self.VERTICIES[vertlist[2] - 1])
        
        try:
            glTexCoord2f(self.tiles,0)
            glVertex3fv(self.VERTICIES[vertlist[3] - 1])
        except:
            glTexCoord2f(self.tiles,0)
            glVertex3fv(self.VERTICIES[vertlist[0] - 1])
        
        
    # Applies a new texture to the object (with tiling factor).
    def apply_texture(self, fp, tiling):
            
        self.texture = fp
        self.tiles = tiling
