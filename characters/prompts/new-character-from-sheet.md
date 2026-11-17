# Walking sheet prompt: a new character, redrawn from an existing sheet

Rule from Nano: every character after the first is made by giving the image model an existing
character sheet and asking for a DIFFERENT person in the same style, proportions and grid. Never
from words alone, or the proportions will not match the rest of the cast.

Attach `characters/nano.png` (or any finished sheet in `characters/`) as the reference. If the new
person comes from a photo, attach the photo as a second image for likeness only. Fill in the
Character block from what is visible or what Nano says; mark anything unknown as "not specified;
choose it to suit the character". Change nothing else.

```text
You are an expert character designer creating professional walk-cycle sprite sheets for game development.

# Task
The attached image is a finished walking character sheet from our game. Redraw it as a DIFFERENT person, described below. Keep everything else about the sheet exactly as it is: the art style, the body proportions, the size of the character, the grid, and the pose in each of the twelve frames. Only the person changes.

# Style (critical)
The reference sheet is 32-bit pixel art with crisp square pixels, flat colour in clean bands, a warm palette, light from the upper left, and a one-pixel dark outline in deep warm brown. Reproduce exactly this rendering method in every frame. Do not add photorealism, soft gradients, anti-aliased edges, dithering noise or 3D lighting. The new sheet must look like it was drawn by the same artist on the same day as the reference.

# Character
- Role: {{role in the village}}
- Build: {{build, within the same head-to-body proportions and the same height as the reference}}
- Face: {{face}}
- Skin: {{colour and undertone}}
- Hair: {{colour, cut}}
- Facial hair: {{or "none"}}
- Eyes: {{colour}}
- Outfit: {{piece by piece, with colour}}
- Accessories and props: {{or "none"}}

# Layout
The same grid as the reference: twelve equal-sized frames in 4 rows and 3 columns, the character the same size and on the same baseline as the reference in every frame, on a plain flat single-colour background.

**Row 1**: walking toward the camera (we see the front):
1. Left foot forward
2. Standing
3. Right foot forward

**Row 2**: walking to the right:
1. Left foot forward
2. Standing
3. Right foot forward

**Row 3**: walking to the left:
1. Left foot forward
2. Standing
3. Right foot forward

**Row 4**: walking away from the camera (we see the back):
1. Left foot forward
2. Standing
3. Right foot forward

Copy the stride and the arm swing of the reference frame for frame: a big, obvious stride, legs clearly different in each frame of a row, arms swinging opposite to the legs. "Left" and "right" always mean the character's own left and right.

# Consistency
- The new person is clearly a different individual from the one in the reference: do not carry over the reference's face, hair, glasses, beard or clothes unless the Character block asks for them.
- The identical new character, outfit and accessories appear in all twelve frames: same colours, proportions and size.
- Left and right stay correct across frames: an asymmetric feature keeps its side.
- Lighting matches the reference in every frame, with no shadow drawn on the background.
- For style, proportions, size, grid and poses, the reference sheet is correct. For who the person is, this description is correct.

# Quality
- All twelve frames are consistent with each other.
- Placed beside the reference sheet, the two characters look like members of the same cast.
- Precise grid alignment. No text, labels, numbers, watermarks or extra characters.
```
