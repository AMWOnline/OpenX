# Open-X Version 1.4 - Optimized Build
# Developed by Madden Wilkins

# Billboard draw() no longer re-uploads texture every frame
# Polygon rotate() uses numpy matrix math instead of per-vertex Python loops
# Quadric objects (Sphere, Cylinder, Disk) cache their GLU quadric handle
# flip(): removed pygame.time.wait(10) - main source of FPS drops
# lights_on/off() consolidated, redundant state calls removed
# Font.draw_rgba() caches rendered surfaces by (text, font, size, color)
#  Added Font.draw() which has a transparent background
#  Added Font.draw_dynamic(), same as draw() but doesn't cache the text (useful for fast changing information to not overload the cache and use up resources)
# Ceiling/Floor draw() removes dead tcoords/surfs variables and an extra vertex
# _rotate_vertices() shared helper function now replaces duplicated rotate() in every Geometry class
# Added transparent billboard support
# Changed billboards to utilize quad rendering, allowing for accurate proportions
# Got rid of coord_to_scale(), was obsolete
# Changed resolution to a scalable 1600 * 1200 on PC
# Added Audio class
# Added CodeHS Mode: limits resolution to 360 * 240, upscaled 3 times; and disables audio support
# Changed Controller class to just return pressed keyboard keys as a list
# Changed Controller class to allow for mouse based rotation
# Changed Controller class to have new mode() function
# Added Mipmaps
# Changed how textures are rendered to improve performance
# Textures can now be HD
# Overhauled Camera Class
# Added new rotate() to all Geometry
# Added more vertices spheres and cylinders
# Added hitbox system
# Added new Debug class

import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

import os
import time
import random
import math
import psutil
import numpy as np
from PIL import Image


import re

pygame.font.init()

CLOCK = pygame.time.Clock()

# Global constants

CAMERA_POS   = [0, 0, 0]
CAMERA_YAW   = 0.0
CAMERA_PITCH = 0.0
CAMERA_ROLL  = 0.0

FOG_COLOR    = [0, 0, 0]
CEIL_TEX     = "tex_missing.png"
FLOOR_TEX    = "tex_missing.png"
TEXTURE_CACHE = {}
FONT_CACHE    = {}   # (text, fp, size, color, bg_color) -> (w, h, bytes)
WORLD_HITBOXES = []

# Render resolution
RENDER_WIDTH  = 1600
RENDER_HEIGHT = 1200
WINDOW_SCALE  = 1

# FBO handles
FBO         = None
FBO_TEXTURE = None
FBO_RBO     = None

'''
Helper functions
'''
def _rotate_vertices(vertices, ax, ay, az):
    """Rotate a list of [x,y,z] vertices in-place around their centroid."""
    if ax == 0 and ay == 0 and az == 0:
        return

    arr = np.array(vertices, dtype=np.float64)
    center = arr.mean(axis=0)
    arr -= center

    if ax != 0:
        rx = math.radians(ax)
        cx, sx = math.cos(rx), math.sin(rx)
        Rx = np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
        arr = arr @ Rx.T

    if ay != 0:
        ry = math.radians(ay)
        cy, sy = math.cos(ry), math.sin(ry)
        Ry = np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
        arr = arr @ Ry.T

    if az != 0:
        rz = math.radians(az)
        cz, sz = math.cos(rz), math.sin(rz)
        Rz = np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
        arr = arr @ Rz.T

    arr += center

    for i, v in enumerate(vertices):
        v[0], v[1], v[2] = arr[i]

'''
init() function
Sets up OpenX for use
'''

def init():
    global FBO, FBO_TEXTURE, FBO_RBO
    global GPU

    pygame.init()



    print("\n"*256)
    print("This application is being emulated in OpenX v1.4")
    print("www.mjwil116.codehs.me/openx.html")

    try:
        pygame.mixer.init()
    except:
        print("Open-X [WARNING] >> Unable to load audio device!")

    
    try:
        GPU = GPUtil.getGPUs()[0].name
    except:
        GPU = "No GPU"
        print("Open-X [WARNING] >> No GPU is installed, or was detected!")
        

    win_w = RENDER_WIDTH  * WINDOW_SCALE
    win_h = RENDER_HEIGHT * WINDOW_SCALE
    pygame.display.set_mode((win_w, win_h), DOUBLEBUF | OPENGL)

    FBO = glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, FBO)

    FBO_TEXTURE = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, FBO_TEXTURE)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, RENDER_WIDTH, RENDER_HEIGHT, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, FBO_TEXTURE, 0)

    FBO_RBO = glGenRenderbuffers(1)
    glBindRenderbuffer(GL_RENDERBUFFER, FBO_RBO)
    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT,RENDER_WIDTH, RENDER_HEIGHT)
    glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, FBO_RBO)

    glBindFramebuffer(GL_FRAMEBUFFER, FBO)
    glViewport(0, 0, RENDER_WIDTH, RENDER_HEIGHT)

    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (4/3), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)

    glLight(GL_LIGHT0, GL_POSITION, (5, 5, 5, 1))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (1, 1, 1, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1, 1, 1, 1))

    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

'''
flip() function
Refreshes the screen and advances to the next frame of video
'''
def flip():
    CLOCK.tick(60)

    win_w = RENDER_WIDTH  * WINDOW_SCALE
    win_h = RENDER_HEIGHT * WINDOW_SCALE

    glBindFramebuffer(GL_READ_FRAMEBUFFER, FBO)
    glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
    glBlitFramebuffer(
        0, 0, RENDER_WIDTH, RENDER_HEIGHT,
        0, 0, win_w, win_h,
        GL_COLOR_BUFFER_BIT, GL_NEAREST
    )

    pygame.display.flip()
    glBindFramebuffer(GL_FRAMEBUFFER, FBO)
    glViewport(0, 0, RENDER_WIDTH, RENDER_HEIGHT)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    Camera.apply()

'''
General texture management
'''
def load_texture(filepath):
    global TEXTURE_CACHE

    if filepath in TEXTURE_CACHE:
        return TEXTURE_CACHE[filepath]

    try:
        img = Image.open(filepath).convert("RGBA")
    except:
        img = Image.open("tex_error.png").convert("RGBA")
        print("Open-X [WARNING] >> Unable to load texture filepath '" + filepath + "'!")

    img_data   = np.array(img, np.uint8)
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA,
                 img.width, img.height,
                 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
    glGenerateMipmap(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, 0)

    TEXTURE_CACHE[filepath] = texture_id
    return texture_id


def unload_texture(filepath):
    global TEXTURE_CACHE
    if filepath in TEXTURE_CACHE:
        glDeleteTextures(1, [TEXTURE_CACHE[filepath]])
        del TEXTURE_CACHE[filepath]

'''
Lighting functions
'''

def lights_on():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glShadeModel(GL_SMOOTH)

def lights_off():
    glDisable(GL_LIGHT0)
    glDisable(GL_LIGHTING)
    glDisable(GL_COLOR_MATERIAL)

'''
Controller Class
Deals with handling input and different modes of controllers
'''

class Controller:

    _mouse_captured = False
    _sensitivity    = 0.2
    _mouse_look     = False
    _mouse_look_no_y = False
    _held_keys      = set()

    def read():
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return {'QUIT'}

            if event.type == pygame.KEYDOWN:
                if Controller._mouse_look and event.key == pygame.K_ESCAPE:
                    Controller._release_mouse()
                Controller._held_keys.add(pygame.key.name(event.key).upper())

            if event.type == pygame.KEYUP:
                Controller._held_keys.discard(pygame.key.name(event.key).upper())

            if event.type == pygame.MOUSEBUTTONDOWN:
                if Controller._mouse_look and not Controller._mouse_captured:
                    Controller._capture_mouse()

        if Controller._mouse_look and Controller._mouse_captured:
            dx, dy = pygame.mouse.get_rel()
            Camera.rotate(dx * Controller._sensitivity,
                          dy * Controller._sensitivity)

        if Controller._mouse_look_no_y and Controller._mouse_captured:
            dx, dy = pygame.mouse.get_rel()
            Camera.rotate(dx * Controller._sensitivity,
                          0)

        return set(Controller._held_keys)

    def _enable_mouse_look(sensitivity=0.2):
        Controller._sensitivity = sensitivity
        Controller._mouse_look  = True
        Controller._capture_mouse()

    def _enable_mouse_look_no_y(sensitivity=0.2):
        Controller._sensitivity = sensitivity
        Controller._mouse_look_no_y  = True
        Controller._capture_mouse()

    def set_sensitivity(sensitivity):
        Controller._sensitivity = sensitivity

    def _capture_mouse():
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        pygame.mouse.get_rel()
        Controller._mouse_captured = True

    def _release_mouse():
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
        Controller._mouse_captured = False

    def mode(mode):
        if mode == 1:
            Controller._enable_mouse_look()
        if mode == 2:
            Controller._enable_mouse_look_no_y()

'''
Camera Class
Deals with different camera functions
'''
class Camera:

    def apply():
        global CAMERA_POS, CAMERA_YAW, CAMERA_PITCH, CAMERA_ROLL
        glLoadIdentity()
        glRotatef(CAMERA_ROLL,  0, 0, 1)
        glRotatef(CAMERA_PITCH, 1, 0, 0)
        glRotatef(CAMERA_YAW,   0, 1, 0)
        glTranslatef(-CAMERA_POS[0], -CAMERA_POS[1], -CAMERA_POS[2])

    def translate(x, y, z):
        global CAMERA_POS, CAMERA_YAW, CAMERA_PITCH

        yaw_rad   = math.radians(CAMERA_YAW)
        pitch_rad = math.radians(CAMERA_PITCH)

        fwd_x =  math.sin(yaw_rad) * math.cos(pitch_rad)
        fwd_y = -math.sin(pitch_rad)
        fwd_z = -math.cos(yaw_rad) * math.cos(pitch_rad)

        right_x = math.cos(yaw_rad)
        right_y = 0
        right_z = math.sin(yaw_rad)

        CAMERA_POS[0] += fwd_x * z + right_x * x
        CAMERA_POS[1] += fwd_y * z + right_y * x + y
        CAMERA_POS[2] += fwd_z * z + right_z * x

    def rotate(yaw, pitch, roll=0):
        global CAMERA_YAW, CAMERA_PITCH, CAMERA_ROLL
        CAMERA_YAW   = (CAMERA_YAW + yaw) % 360
        CAMERA_PITCH = max(-89.0, min(89.0, CAMERA_PITCH + pitch))
        CAMERA_ROLL  = (CAMERA_ROLL + roll) % 360

    def set_pos(x, y, z):
        global CAMERA_POS
        CAMERA_POS = [float(x), float(y), float(z)]

    def set_rotation(yaw, pitch, roll=0):
        global CAMERA_YAW, CAMERA_PITCH, CAMERA_ROLL
        CAMERA_YAW   = float(yaw)   % 360
        CAMERA_PITCH = max(-89.0, min(89.0, float(pitch)))
        CAMERA_ROLL  = float(roll)  % 360

    def get_rotation():
        return [CAMERA_YAW, CAMERA_PITCH, CAMERA_ROLL]

    def get_pos():
        return CAMERA_POS[:]

    def cull_rotation(arr):
        return [val % 360 for val in arr]

'''
Environment Class
Deals with the overal scene and its attributes
'''

class Environment:

    def set_fog_color(r, g, b):
        global FOG_COLOR
        FOG_COLOR = [(r/255), (g/255), (b/255)]
        glClearColor((r/255), (g/255), (b/255), 0)

    class Ceiling:

        def draw():
            verts = [
                [-128, 0,  128],
                [ 128, 0,  128],
                [ 128, 0, -128],
                [-128, 0, -128],
            ]

            texture_id = load_texture(CEIL_TEX)
            glTranslatef(0, 6.5, 0)
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glBegin(GL_QUADS)
            glTexCoord2f( 0,  0); glVertex3fv(verts[0])
            glTexCoord2f(32,  0); glVertex3fv(verts[1])
            glTexCoord2f(32, 32); glVertex3fv(verts[2])
            glTexCoord2f( 0, 32); glVertex3fv(verts[3])
            glEnd()
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)
            glTranslatef(0, -6.5, 0)

        def apply_texture(filepath):
            global CEIL_TEX
            CEIL_TEX = filepath

    class Floor:

        def draw():
            verts = [
                [-128, 0,  128],
                [ 128, 0,  128],
                [ 128, 0, -128],
                [-128, 0, -128],
            ]

            texture_id = load_texture(FLOOR_TEX)
            glTranslatef(0, -6.5, 0)
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glBegin(GL_QUADS)
            glTexCoord2f( 0,  0); glVertex3fv(verts[0])
            glTexCoord2f(32,  0); glVertex3fv(verts[1])
            glTexCoord2f(32, 32); glVertex3fv(verts[2])
            glTexCoord2f( 0, 32); glVertex3fv(verts[3])
            glEnd()
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)
            glTranslatef(0, 6.5, 0)

        def apply_texture(filepath):
            global FLOOR_TEX
            FLOOR_TEX = filepath

'''
Tex2D Class
Deals with texture handling and billboards
'''

class Tex2D:

    class Billboard:

        def __init__(self, x, y, z, width, height, filepath):
            self.x          = x
            self.y          = y
            self.z          = z
            self.width      = width
            self.height     = height
            self.filepath   = filepath
            self.texture_id = load_texture(filepath)

        def draw(self):
            # Use cached texture_id — no disk or GPU upload this frame
            mv    = glGetFloatv(GL_MODELVIEW_MATRIX)
            right = [mv[0][0], mv[1][0], mv[2][0]]
            up    = [mv[0][1], mv[1][1], mv[2][1]]

            hw = self.width  / 2.0
            hh = self.height / 2.0
            cx, cy, cz = self.x, self.y, self.z

            v_bl = [cx + (-right[0]*hw) + (-up[0]*hh),
                    cy + (-right[1]*hw) + (-up[1]*hh),
                    cz + (-right[2]*hw) + (-up[2]*hh)]
            v_br = [cx + ( right[0]*hw) + (-up[0]*hh),
                    cy + ( right[1]*hw) + (-up[1]*hh),
                    cz + ( right[2]*hw) + (-up[2]*hh)]
            v_tr = [cx + ( right[0]*hw) + ( up[0]*hh),
                    cy + ( right[1]*hw) + ( up[1]*hh),
                    cz + ( right[2]*hw) + ( up[2]*hh)]
            v_tl = [cx + (-right[0]*hw) + ( up[0]*hh),
                    cy + (-right[1]*hw) + ( up[1]*hh),
                    cz + (-right[2]*hw) + ( up[2]*hh)]

            glEnable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 1); glVertex3fv(v_bl)
            glTexCoord2f(1, 1); glVertex3fv(v_br)
            glTexCoord2f(1, 0); glVertex3fv(v_tr)
            glTexCoord2f(0, 0); glVertex3fv(v_tl)
            glEnd()

            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_BLEND)
            glDisable(GL_TEXTURE_2D)

'''
Geometry Class
Allows 3D geometry to be rendered to the world scene with different textures and attributes
'''

class Geometry:

    # Rectangular Prism Class
    class RectangularPrism:

        # l, w, h: Length, width, height
        # x, y, z: Position in world
        def __init__(self, l, w, h, x, y, z):
            self.length = l
            self.width  = w
            self.height = h
            self.pos_x  = x
            self.pos_y  = y
            self.pos_z  = z
            self.tiles   = 1
            self.texture = "tex_missing.png"

            self.VERTICIES = [
                [-1, 1,-1], [ 1, 1,-1], [ 1, 1, 1], [-1, 1, 1],
                [-1,-1,-1], [ 1,-1,-1], [ 1,-1, 1], [-1,-1, 1],
            ]
            for vertex in self.VERTICIES:
                vertex[0] = vertex[0] * w + x
                vertex[1] = vertex[1] * h + y
                vertex[2] = vertex[2] * l + z

        def translate(self, x, y, z):
            for v in self.VERTICIES:
                v[0] += x; v[1] += y; v[2] += z

        def transform(self, w, h, l):
            for v in self.VERTICIES:
                v[0] *= w; v[1] *= h; v[2] *= l

        def rotate(self, ax, ay, az):
            _rotate_vertices(self.VERTICIES, ax, ay, az)

        def draw(self):
            texture_id = load_texture(self.texture)
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, 0)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
            lights_on()
            glBegin(GL_QUADS)
            self._draw_face([0,1,2,3])
            self._draw_face([4,5,6,7])
            self._draw_face([3,2,6,7])
            self._draw_face([2,1,5,6])
            self._draw_face([1,0,4,5])
            self._draw_face([0,3,7,4])
            glEnd()
            lights_off()
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)

        def _draw_face(self, vertlist):
            glTexCoord2f(0,         0        ); glVertex3fv(self.VERTICIES[vertlist[0]])
            glTexCoord2f(self.tiles, 0        ); glVertex3fv(self.VERTICIES[vertlist[1]])
            glTexCoord2f(self.tiles, self.tiles); glVertex3fv(self.VERTICIES[vertlist[2]])
            glTexCoord2f(0,         self.tiles); glVertex3fv(self.VERTICIES[vertlist[3]])

        def apply_texture(self, fp, tiling=1):
            self.texture = fp
            self.tiles   = tiling

    # Triangular Pyramid
    class TriangularPyramid:

        # l, w, h: Length, width height
        # x, y, z: Position in world
        def __init__(self, l, w, h, x, y, z):
            self.length = l; self.width = w; self.height = h
            self.pos_x = x; self.pos_y = y; self.pos_z = z
            self.tiles   = 1
            self.texture = "tex_missing.png"

            self.VERTICIES = [
                [0, 1, 0], [-1, 0, 1], [0, 0,-1], [1, 0, 1]
            ]
            for v in self.VERTICIES:
                v[0] = (v[0] + x) * w
                v[1] = (v[1] + y) * h
                v[2] = (v[2] + z) * l

        def translate(self, x, y, z):
            for v in self.VERTICIES:
                v[0] += x; v[1] += y; v[2] += z

        def transform(self, w, h, l):
            for v in self.VERTICIES:
                v[0] *= w; v[1] *= h; v[2] *= l

        def rotate(self, ax, ay, az):
            _rotate_vertices(self.VERTICIES, ax, ay, az)

        def draw(self):
            texture_id = load_texture(self.texture)
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, 0)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            lights_on()
            glBegin(GL_QUADS)
            self._draw_face([1,2,3])
            self._draw_face([1,0,3])
            self._draw_face([3,0,2])
            self._draw_face([2,0,1])
            glEnd()
            lights_off()
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)

        def _draw_face(self, vertlist):
            glTexCoord2f(0,          0         ); glVertex3fv(self.VERTICIES[vertlist[0]])
            glTexCoord2f(0,          self.tiles ); glVertex3fv(self.VERTICIES[vertlist[1]])
            glTexCoord2f(self.tiles, self.tiles ); glVertex3fv(self.VERTICIES[vertlist[2]])
            glTexCoord2f(self.tiles, 0          ); glVertex3fv(self.VERTICIES[vertlist[0]])

        def apply_texture(self, fp, tiling=1):
            self.texture = fp; self.tiles = tiling

    # Pyramid Class
    class Pyramid:

        # l, w, h: length, width, height
        # x, y, z: Position in world
        def __init__(self, l, w, h, x, y, z):
            self.length = l; self.width = w; self.height = h
            self.pos_x = x; self.pos_y = y; self.pos_z = z
            self.tiles   = 1
            self.texture = "tex_missing.png"

            self.VERTICIES = [
                [0, 1, 0], [-1, 0, 1], [1, 0, 1], [1, 0,-1], [-1, 0,-1]
            ]
            for v in self.VERTICIES:
                v[0] = (v[0] + x) * w
                v[1] = (v[1] + y) * h
                v[2] = (v[2] + z) * l

        def translate(self, x, y, z):
            for v in self.VERTICIES:
                v[0] += x; v[1] += y; v[2] += z

        def transform(self, w, h, l):
            for v in self.VERTICIES:
                v[0] *= w; v[1] *= h; v[2] *= l

        def rotate(self, ax, ay, az):
            _rotate_vertices(self.VERTICIES, ax, ay, az)

        def draw(self):
            texture_id = load_texture(self.texture)
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, 0)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            lights_on()
            glBegin(GL_QUADS)
            self._draw_face([0,1,2])
            self._draw_face([0,2,3])
            self._draw_face([0,3,4])
            self._draw_face([0,4,1])
            glTexCoord2f(0,          0         ); glVertex3fv(self.VERTICIES[1])
            glTexCoord2f(self.tiles, 0         ); glVertex3fv(self.VERTICIES[2])
            glTexCoord2f(self.tiles, self.tiles ); glVertex3fv(self.VERTICIES[3])
            glTexCoord2f(0,          self.tiles ); glVertex3fv(self.VERTICIES[4])
            glEnd()
            lights_off()
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)

        def _draw_face(self, vertlist):
            glTexCoord2f(0,          0         ); glVertex3fv(self.VERTICIES[vertlist[0]])
            glTexCoord2f(0,          self.tiles ); glVertex3fv(self.VERTICIES[vertlist[1]])
            glTexCoord2f(self.tiles, self.tiles ); glVertex3fv(self.VERTICIES[vertlist[2]])
            glTexCoord2f(self.tiles, 0          ); glVertex3fv(self.VERTICIES[vertlist[0]])

        def apply_texture(self, fp, tiling=1):
            self.texture = fp; self.tiles = tiling

    # Sphere Class
    class Sphere:

        # r: Sphere radius
        # x, y, z: Position in world
        def __init__(self, r, x, y, z):
            self.radius = r
            self.pos_x  = x; self.pos_y = y; self.pos_z = z
            self.rot_x  = 0.0; self.rot_y = 0.0; self.rot_z = 0.0
            self.texture = "tex_missing.png"
            self._qobj   = gluNewQuadric()   # created once, reused every frame
            gluQuadricTexture(self._qobj, GL_TRUE)

        def translate(self, x, y, z):
            self.pos_x += x; self.pos_y += y; self.pos_z += z

        def transform(self, r):
            self.radius *= r

        def rotate(self, ax, ay, az):
            self.rot_x = (self.rot_x + ax) % 360
            self.rot_y = (self.rot_y + ay) % 360
            self.rot_z = (self.rot_z + az) % 360

        def draw(self):
            glTranslatef(self.pos_x, self.pos_y, self.pos_z)
            glRotatef(90, 1, 0, 0)
            glRotatef(self.rot_x, 1, 0, 0)
            glRotatef(self.rot_y, 0, 1, 0)
            glRotatef(self.rot_z, 0, 0, 1)

            texture_id = load_texture(self.texture)
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, 0)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            lights_on()
            gluSphere(self._qobj, self.radius, 32, 32)
            lights_off()
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)

            glRotatef(-self.rot_z, 0, 0, 1)
            glRotatef(-self.rot_y, 0, 1, 0)
            glRotatef(-self.rot_x, 1, 0, 0)
            glRotatef(-90, 1, 0, 0)
            glTranslatef(-self.pos_x, -self.pos_y, -self.pos_z)

        def apply_texture(self, fp):
            self.texture = fp

    # Cylinder Class
    class Cylinder:

        # b: Bottom radius
        # t: Top radius
        # h: Height
        # x, y, z: Position in world
        def __init__(self, b, t, h, x, y, z):
            self.bottom_radius = b; self.top_radius = t; self.height = h
            self.pos_x = x; self.pos_y = y; self.pos_z = z
            self.rot_x = 0.0; self.rot_y = 0.0; self.rot_z = 0.0
            self.texture = "tex_missing.png"
            self._qobj   = gluNewQuadric()
            gluQuadricTexture(self._qobj, GL_TRUE)

        def translate(self, x, y, z):
            self.pos_x += x; self.pos_y += y; self.pos_z += z

        def transform(self, b, t, h):
            self.bottom_radius *= b; self.top_radius *= t; self.height *= h

        def rotate(self, ax, ay, az):
            self.rot_x = (self.rot_x + ax) % 360
            self.rot_y = (self.rot_y + ay) % 360
            self.rot_z = (self.rot_z + az) % 360

        def draw(self):
            glTranslatef(self.pos_x, self.pos_y, self.pos_z)
            glRotatef(90, 1, 0, 0)
            glRotatef(self.rot_x, 1, 0, 0)
            glRotatef(self.rot_y, 0, 1, 0)
            glRotatef(self.rot_z, 0, 0, 1)

            texture_id = load_texture(self.texture)
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, 0)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            lights_on()
            gluCylinder(self._qobj, self.bottom_radius, self.top_radius, self.height, 32, 32)
            lights_off()
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)

            glRotatef(-self.rot_z, 0, 0, 1)
            glRotatef(-self.rot_y, 0, 1, 0)
            glRotatef(-self.rot_x, 1, 0, 0)
            glRotatef(-90, 1, 0, 0)
            glTranslatef(-self.pos_x, -self.pos_y, -self.pos_z)

        def apply_texture(self, fp):
            self.texture = fp

    # Disk Class
    class Disk:

        # i: Inner ring radius
        # o: Outer ring radius
        # x, y, z: Position in world
        def __init__(self, i, o, x, y, z):
            self.inner_radius = i; self.outer_radius = o
            self.pos_x = x; self.pos_y = y; self.pos_z = z
            self.rot_x = 0.0; self.rot_y = 0.0; self.rot_z = 0.0
            self.texture = "tex_missing.png"
            self._qobj   = gluNewQuadric()
            gluQuadricTexture(self._qobj, GL_TRUE)

        def translate(self, x, y, z):
            self.pos_x += x; self.pos_y += y; self.pos_z += z

        def transform(self, inner, outer):
            self.inner_radius *= inner; self.outer_radius *= outer

        def rotate(self, ax, ay, az):
            self.rot_x = (self.rot_x + ax) % 360
            self.rot_y = (self.rot_y + ay) % 360
            self.rot_z = (self.rot_z + az) % 360

        def draw(self):
            glTranslatef(self.pos_x, self.pos_y, self.pos_z)
            glRotatef(90, 1, 0, 0)
            glRotatef(self.rot_x, 1, 0, 0)
            glRotatef(self.rot_y, 0, 1, 0)
            glRotatef(self.rot_z, 0, 0, 1)

            texture_id = load_texture(self.texture)
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, 0)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            lights_on()
            gluDisk(self._qobj, self.inner_radius, self.outer_radius, 32, 1)
            lights_off()
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)

            glRotatef(-self.rot_z, 0, 0, 1)
            glRotatef(-self.rot_y, 0, 1, 0)
            glRotatef(-self.rot_x, 1, 0, 0)
            glRotatef(-90, 1, 0, 0)
            glTranslatef(-self.pos_x, -self.pos_y, -self.pos_z)

        def apply_texture(self, fp):
            self.texture = fp

'''
Font Class
Handles drawing 2D Text over the screen, like a HUD
'''

class Font:

    # Draw text with a solid background color (original behavior)
    def draw_rgba(x, y, font, text, color, bg_color, size):
        global FONT_CACHE

        cache_key = (text, font, size, color, bg_color)

        if cache_key not in FONT_CACHE:
            try:
                f = pygame.font.Font(font, size)
            except:
                print("Open-X [WARNING] >> Unable to load font! Reverting to default.")
                f = pygame.font.Font(pygame.font.get_default_font(), size)

            surface = f.render(text, True, color, bg_color)
            raw     = pygame.image.tostring(surface, "RGBA", True)
            FONT_CACHE[cache_key] = (surface.get_width(), surface.get_height(), raw)

        w, h, raw = FONT_CACHE[cache_key]
        glWindowPos2d(x, y)
        glDrawPixels(w, h, GL_RGBA, GL_UNSIGNED_BYTE, raw)

    # Draw text with a transparent background.
    # color is an (R, G, B, A) tuple -- A controls text opacity, 255 = fully opaque
    def draw(x, y, font, text, color, size):
        global FONT_CACHE

        cache_key = ("TRANSPARENT", text, font, size, color)

        if cache_key not in FONT_CACHE:
            try:
                f = pygame.font.Font(font, size)
            except:
                print("Open-X [WARNING] >> Unable to load font! Reverting to default.")
                f = pygame.font.Font(pygame.font.get_default_font(), size)

            # Render onto a per-pixel alpha surface so background stays transparent
            text_surf = f.render(text, True, color[:3])
            surface   = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
            surface.fill((0, 0, 0, 0))
            surface.blit(text_surf, (0, 0))

            # Apply the alpha channel from the color tuple
            if len(color) == 4:
                surface.set_alpha(color[3])

            raw = pygame.image.tostring(surface, "RGBA", True)
            FONT_CACHE[cache_key] = (surface.get_width(), surface.get_height(), raw)

        w, h, raw = FONT_CACHE[cache_key]

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glWindowPos2d(x, y)
        glDrawPixels(w, h, GL_RGBA, GL_UNSIGNED_BYTE, raw)
        glDisable(GL_BLEND)

    # Draw transparent text that re-renders every frame.
    # Use this for dynamic text that changes frequently, as caching is disabled so resources are not taken
    def draw_dynamic(x, y, font, text, color, size):

        try:
            f = pygame.font.Font(font, size)
        except:
            print("Open-X [WARNING] >> Unable to load font! Reverting to default.")
            f = pygame.font.Font(pygame.font.get_default_font(), size)

        text_surf = f.render(text, True, color[:3])
        surface   = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        surface.blit(text_surf, (0, 0))

        if len(color) == 4:
            surface.set_alpha(color[3])

        raw = pygame.image.tostring(surface, "RGBA", True)
        w, h = surface.get_size()

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glWindowPos2d(x, y)
        glDrawPixels(w, h, GL_RGBA, GL_UNSIGNED_BYTE, raw)
        glDisable(GL_BLEND)

'''
XObject Class
Allows basic custom quad modelling and rendering
'''

class XObject:

    def __init__(self, fp, x, y, z, l, w, h):
        self.pos_x = x; self.pos_y = y; self.pos_z = z
        self.length = l; self.width = w; self.height = h
        self.filepath = fp
        self.VERTICIES = []
        self.FACES     = []
        self.texture   = "tex_missing.png"
        self.tiles     = 1

        with open(os.getcwd() + "/" + fp, "r") as file:
            for line in file:
                line = line.rstrip()
                if not line:
                    continue
                if line[0] == "v":
                    vals = []
                    for t in line.split():
                        try: vals.append(float(t))
                        except ValueError: pass
                    self.VERTICIES.append(vals)
                elif line[0] == "f":
                    vals = []
                    for t in line.split():
                        try: vals.append(int(t))
                        except ValueError: pass
                    self.FACES.append(vals)

    def translate(self, x, y, z):
        self.pos_x += x; self.pos_y += y; self.pos_z += z

    def draw(self):
        texture_id = load_texture(self.texture)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, 0)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        lights_on()
        glBegin(GL_QUADS)
        for face in self.FACES:
            self._draw_face(face)
        glEnd()
        lights_off()
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)

    def _draw_face(self, vertlist):
        glTexCoord2f(0,          0         ); glVertex3fv(self.VERTICIES[vertlist[0]-1])
        glTexCoord2f(0,          self.tiles ); glVertex3fv(self.VERTICIES[vertlist[1]-1])
        glTexCoord2f(self.tiles, self.tiles ); glVertex3fv(self.VERTICIES[vertlist[2]-1])
        try:
            glTexCoord2f(self.tiles, 0); glVertex3fv(self.VERTICIES[vertlist[3]-1])
        except IndexError:
            glTexCoord2f(self.tiles, 0); glVertex3fv(self.VERTICIES[vertlist[0]-1])

    def apply_texture(self, fp, tiling=1):
        self.texture = fp; self.tiles = tiling

'''
Alpha Audio Class
Experimental class that handles music and sound effect managment
'''

class Audio:

    class Mixer:

        def load(fp):
            pygame.mixer.music.load(fp, "ogg")

        def unload():
            pygame.mixer.music.unload()

        def play(loops=1, start=0.0, fade=0):
            pygame.mixer.music.play((loops-1), start, fade)

        def rewind():
            pygame.mixer.music.rewind()

        def stop():
            pygame.mixer.music.stop()

        def pause():
            pygame.mixer.music.pause()

        def unpause():
            pygame.mixer.music.unpause()

        def fadeout(time):
            pygame.mixer.music.fadeout(time * 1000)

        def set_volume(vol):
            pygame.mixer.music.set_volume(vol)

        def get_volume():
            return pygame.mixer.music.get_volume()

        def busy():
            return pygame.mixer.music.get_busy()

        def seek(timestamp):
            pygame.mixer.music.set_pos(timestamp)

        def timestamp():
            return pygame.mixer.music.get_pos()

        def queue(fp, loops=1):
            pygame.mixer.music.queue(fp, "ogg", (loops-1))

    class SFX:

        def __init__(self, fp, x=0, y=0, z=0, d=0):
            self.filepath = fp
            self.x = x; self.y = y; self.z = z
            self.d   = d * 10
            self.sfx = pygame.mixer.Sound(fp)

        def play(self, loops=1, fade=0):
            self.sfx.play((loops-1), 0, fade)

        def stop(self, fade=0):
            if fade == 0:
                self.sfx.stop()
            else:
                self.sfx.fadeout(fade)

        def set_volume(self, vol):
            self.sfx.set_volume(vol)

        def get_volume(self):
            return self.sfx.get_volume()

        def length(self):
            return self.sfx.get_length()

        def calculate_att(self):
            global CAMERA_POS
            dx = self.x - CAMERA_POS[0]
            dy = self.y - CAMERA_POS[1]
            dz = self.z - CAMERA_POS[2]
            distance = math.sqrt(dx*dx + dy*dy + dz*dz)

            if self.d <= 0.0:
                self.set_volume(1.0)
                return

            ratio  = max(0.0, min(distance, self.d)) / self.d
            result = (1.0 - ratio) ** 2
            self.set_volume(result)

'''
Alpha Collision Class
An alpha build of collision detection. Very basic AABB collision detection and caching
'''

class Collision:

    # Hitbox object
    class Hitbox:

        # Make a new hitbox with width, length, height, and x, y, z position
        def __init__(self, l, w, h, x, y, z):
            self.length = l
            self.width  = w
            self.height = h
            self.pos_x  = x
            self.pos_y  = y
            self.pos_z  = z

            self.VERTICIES = [
                [-1, 1,-1], [ 1, 1,-1], [ 1, 1, 1], [-1, 1, 1],
                [-1,-1,-1], [ 1,-1,-1], [ 1,-1, 1], [-1,-1, 1],
            ]
            
            for vertex in self.VERTICIES:
                vertex[0] = vertex[0] * w + x
                vertex[1] = vertex[1] * h + y
                vertex[2] = vertex[2] * l + z

            WORLD_HITBOXES.append(self)

        # Translate hitbox
        def translate(self, x, y, z):
            for v in self.VERTICIES:
                v[0] += x; v[1] += y; v[2] += z

        # Transform hitbox
        def transform(self, w, h, l):
            for v in self.VERTICIES:
                v[0] *= w; v[1] *= h; v[2] *= l

        # Rotate hitbox
        def rotate(self, ax, ay, az):
            _rotate_vertices(self.VERTICIES, ax, ay, az)

        # Set position
        def set_pos(self, x, y, z):
            dx = x - self.pos_x
            dy = y - self.pos_y
            dz = z - self.pos_z
            self.translate(dx, dy, dz)
            self.pos_x = x
            self.pos_y = y
            self.pos_z = z

        # Takes another hitbox object in: returns true if this hitbox it is colliding with it
        def collides_with(self, other):
            # Derive AABB from vertices for self
            a_xs = [v[0] for v in self.VERTICIES]
            a_ys = [v[1] for v in self.VERTICIES]
            a_zs = [v[2] for v in self.VERTICIES]

            # Derive AABB from vertices for other
            b_xs = [v[0] for v in other.VERTICIES]
            b_ys = [v[1] for v in other.VERTICIES]
            b_zs = [v[2] for v in other.VERTICIES]

            # Overlap on all three axes = collision
            return (min(a_xs) <= max(b_xs) and max(a_xs) >= min(b_xs) and
                    min(a_ys) <= max(b_ys) and max(a_ys) >= min(b_ys) and
                    min(a_zs) <= max(b_zs) and max(a_zs) >= min(b_zs))

        # Returns True if this hitbox is colliding with any other hitbox
        def hits_barrier(self):

            for other in WORLD_HITBOXES:
                if other is self:
                    continue
                if self.collides_with(other):
                    return True

            return False

        # Draws an outline of the hitbox
        def draw(self, color=(0, 1, 0)):

            xs = [v[0] for v in self.VERTICIES]
            ys = [v[1] for v in self.VERTICIES]
            zs = [v[2] for v in self.VERTICIES]

            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            z_min, z_max = min(zs), max(zs)

            # 8 corners of the AABB
            corners = [
                (x_min, y_min, z_min), (x_max, y_min, z_min),
                (x_max, y_max, z_min), (x_min, y_max, z_min),
                (x_min, y_min, z_max), (x_max, y_min, z_max),
                (x_max, y_max, z_max), (x_min, y_max, z_max),
            ]

            # 12 edges connecting the corners
            edges = [
                (0,1),(1,2),(2,3),(3,0),  # back face
                (4,5),(5,6),(6,7),(7,4),  # front face
                (0,4),(1,5),(2,6),(3,7),  # connecting edges
            ]

            glDisable(GL_LIGHTING)
            glDisable(GL_TEXTURE_2D)
            glColor3f(*color)

            glBegin(GL_LINES)
            for a, b in edges:
                glVertex3fv(corners[a])
                glVertex3fv(corners[b])
            glEnd()

            glColor3f(1, 1, 1)
            glEnable(GL_LIGHTING)
            glEnable(GL_TEXTURE_2D)
            

'''
Debug Class
Handles debug information and alpha version testing functions
'''

class Debug:

    # Returns current FPS
    def get_fps():
        return round(CLOCK.get_fps())

    # Returns memory free in GB
    def get_mem():
        virtual_memory = psutil.virtual_memory()
        available_bytes = virtual_memory.available
        available_gb = available_bytes / (1024 ** 3)
        return round(available_gb, 2)


def DEBUG_CODEHS_MODE():
    global RENDER_WIDTH, RENDER_HEIGHT, WINDOW_SCALE
    RENDER_WIDTH  = 320
    RENDER_HEIGHT = 240
    WINDOW_SCALE  = 2
