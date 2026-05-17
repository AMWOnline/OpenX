# OpenX
OpenX is a 3D rendering engine for Python developed using PyGame and pyOpenGL. It is intended to make developing basic 3D scenes (with interactivity) using Python and OpenGL easier and more intutive. OpenX is useful for developing beginner 3D games from scratch, or developing primitve 3D rendering.

## What's New in Version 1.4.1 - "More FX" Update
- Added new effects in a new "FX" class
- Pixel mosaic effect with FX.pixelate() and FX.depixelate()
- Dissolve screen effect with FX.dissolve_in() and FX.dissolve_out()
- Wipe effect using FX.wipe_in() and FX.wipe_out()
- Removed GPU name check
### v1.4 Major Update Changelog
- Tex2D.Billboard.draw() no longer re-uploads the billboard texture every time, adds it to a cache
- Billboards can now support alpha channels
- Billboards now use quad rendering, fixes un-accurate rendering with distance changes
- Got rid of the coord_to_scale() function, obsolete
- Replaced every instance of a rotate() function with a helper function ( _rotate_vertices() ), and uses numpy matrix path instead of python loops
- Quadric objects (Sphere, Cylinder, Disk) now cache their GLU quadric handle
- flip(): removed the pygame.time.wait(10) - was meant to cap the FPS but instead tanked it, replaced it with correct method
- lights_on() and lights_off(): consolidated and removed redundant calls
- Font.draw_rgba(): now caches rendered surfaces
- Added Font.draw() function, which allows for text with a transparent background
- Added Font.draw_dynamic(): same as Font.draw() but doesn't cache the text (useful for fast changing information to not overload the font cache)
- Ceiling.draw() and Floor.draw(): removed dead tcoords and surfs variables and a redundant vertex
- Changed resolution to 1600x1200px when not on CodeHS mode
- Added CodeHS mode: scales the resolution down when enabled to allow OpenX to run faster when loaded in CodeHS
- Added new Audio class: allows for music in the Mixer class and sound effect handling in the SFX class
- Changed the Controller class to just return the current keyboard key pressed, instead of 'wrapping' it with other button names
- Changed the Controller class to support new mouse based Camera rotation
- Changed the Controller class to have new mode() function, which has different controller presets
- Added Mipmaps
- Changed how textures are rendered to improve performance (added the texture cache)
- Larger textures can now be easily handled without tanking performance (tested up to 1024*1024 on PC)
- Added more vertices to Sphere and Cylinder draw methods to make them look more realistic
- Added new Debug class


<img width="400" height="300" alt="Demo screenshot of a bouncing ball rendered with OpenX v1.3" src="https://github.com/user-attachments/assets/7cd3722b-6c54-4e71-9159-678607e2d0bb" />
<img width="400" height="300" alt="A demo scene of the interior of a building" src="https://codehs.com/uploads/3b5226120571e86cc1769d76f0505dff">
<img width="400" height="300" alt="A simulation of the Artemis II mission in OpenX" src="https://codehs.com/uploads/655a15b7251ac9245991e7e292ca1d6e">
<img width="400" height="300" alt="An early development screenshot of a demo scene in OpenX" src="https://codehs.com/uploads/99e3418cca05f2a14ac4761353e6fcb9">
<img width="400" height="300" alt="A simple 3D house scene made in OpenX 1.4, in CodeHS" src="https://codehs.com/uploads/e289d2e12ada3f5cf50f9a9fb1badd7c">
