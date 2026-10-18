import sys,glob
from PIL import Image
for f in sys.argv[1:]:
    im=Image.open(f)
    if im.mode=='RGBA':
        bg=Image.new('RGBA',im.size,(236,236,238,255)); bg.alpha_composite(im); bg.convert('RGB').save(f)
