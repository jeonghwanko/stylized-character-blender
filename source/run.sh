#!/bin/bash
# usage: SHOTS=front,q34 OUTN=v007 run.sh
cd /workspace/character
export OUT=/workspace/character/work/r
rm -rf $OUT; mkdir -p $OUT
/workspace/tools/blender-4.2.3-linux-x64/blender -b -P source/build.py 2>&1 | grep -E "Error|Traceback|line [0-9]|TRIS|WPTS|HAIR" | head -20
python3 source/post.py $OUT/*.png
python3 - <<PY
from PIL import Image; import glob,os
fs=sorted(glob.glob('$OUT/*.png'))
ims=[Image.open(f) for f in fs]
H=800; ims=[i.resize((int(i.width*H/i.height),H)) for i in ims]
c=Image.new('RGB',(sum(i.width for i in ims),H),'white'); x=0
for i in ims: c.paste(i,(x,0)); x+=i.width
c.save('/workspace/character/work/${OUTN:-vx}.png'); print([os.path.basename(f) for f in fs])
PY
