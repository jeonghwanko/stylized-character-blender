"""Save a portable publication copy, leaving the supplied source unchanged.
Run with Blender --factory-startup --disable-autoexec --python SCRIPT -- INPUT OUTPUT.
All used textures must already be packed. Embedded text and local UI paths are removed.
An uncompressed copy permits inspection and removal of the saved FileGlobal filename.
"""
import bpy, json, os, re, struct, sys, tempfile
from pathlib import Path

def fingerprint():
    import hashlib
    data = {}
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            payload = ([v.co[:] for v in obj.data.vertices], [p.vertices[:] for p in obj.data.polygons],
                       [[(g.group, g.weight) for g in v.groups] for v in obj.data.vertices])
            data[obj.name] = hashlib.sha256(repr(payload).encode()).hexdigest()
    return data

def strip_png_metadata(data):
    """Keep pixel/alpha/color-encoding chunks; remove ancillary identity metadata."""
    signature = b'\x89PNG\r\n\x1a\n'
    assert data.startswith(signature), 'Review non-PNG packed media separately.'
    keep = {b'IHDR', b'PLTE', b'IDAT', b'IEND', b'tRNS', b'gAMA', b'cHRM', b'sRGB', b'iCCP'}
    result = bytearray(signature); offset = 8; removed = 0
    while offset + 12 <= len(data):
        length = struct.unpack_from('>I', data, offset)[0]
        end = offset + length + 12; kind = data[offset + 4:offset + 8]
        assert end <= len(data)
        if kind in keep: result.extend(data[offset:end])
        else: removed += 1
        offset = end
        if kind == b'IEND': break
    assert offset == len(data), 'Unexpected data after the PNG image.'
    return bytes(result), removed

def main():
    source, target = [Path(p).resolve() for p in sys.argv[sys.argv.index('--') + 1:]]
    if source == target or target.exists():
        raise ValueError('Publication must create a new copy, never overwrite a checkpoint.')
    bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False, load_ui=False)
    before = fingerprint()
    assert not bpy.data.libraries, 'Resolve linked assets before publication.'
    assert not bpy.data.movieclips and not bpy.data.sounds, 'Unexpected media needs review.'
    allowed = {'T_Clothes_BaseColor', 'T_Clothes_Normal', 'T_Clothes_Roughness',
               'T_FaceHair_BaseColor', 'T_FaceHair_Normal', 'T_FaceHair_Roughness',
               'T_Mouth_BaseColor.png', 'T_V5_HairFlow_BaseColor', 'T_V5_HairFlow_Normal'}
    metadata_chunks_removed = 0
    bpy.data.use_autopack = False
    scratch_root = Path(__file__).resolve().parents[3] / 'work/public-sanitize'
    scratch_root.mkdir(parents=True, exist_ok=True)
    # Retain the ignored scratch files until Blender exits; Windows may keep
    # the freshly loaded image handles open while the file is being saved.
    scratch = Path(tempfile.mkdtemp(prefix='textures-', dir=scratch_root))
    for image in list(bpy.data.images):
        if image.name == 'Render Result' or image.source == 'VIEWER' or (image.source == 'GENERATED' and not image.users):
            bpy.data.images.remove(image); continue
        assert image.name in allowed and image.packed_file, f'Unexpected or unpacked image: {image.name}'
        clean_bytes, removed_chunks = strip_png_metadata(bytes(image.packed_file.data))
        metadata_chunks_removed += removed_chunks
        if removed_chunks:
            # Refresh the cached image buffer as well as its packed bytes:
            # otherwise Blender can serialize the old metadata on save.
            color_space = image.colorspace_settings.name
            clean_path = scratch / (image.name.removesuffix('.png') + '.png')
            clean_path.write_bytes(clean_bytes)
            image.unpack(method='REMOVE')  # in-memory removal; no file write
            image.filepath = str(clean_path)
            image.reload()
            image.colorspace_settings.name = color_space
            image.pack()
            assert bytes(image.packed_file.data) == clean_bytes
        image.filepath = '//../../../textures/' + image.name.removesuffix('.png') + '.png'
    for text in list(bpy.data.texts):
        bpy.data.texts.remove(text)
    # Remove private string annotations, preserving numeric rig controls.
    private_string = re.compile(r'(?:[A-Za-z]:[\\/]|/(?:home|Users|workspace|tmp)/|libfile_|private_reference|library_receipt)', re.I)
    def clean_annotations(group):
        for key in list(group.keys()):
            value = group[key]
            if isinstance(value, str) and private_string.search(value): del group[key]
            elif hasattr(value, 'keys'): clean_annotations(value)
    for prop in bpy.data.bl_rna.properties:
        if prop.type != 'COLLECTION': continue
        for block in getattr(bpy.data, prop.identifier):
            if isinstance(block, bpy.types.ID):
                clean_annotations(block)
    for scene in bpy.data.scenes:
        scene.render.filepath = '//render/'
        scene.render.use_stamp = False
        scene.render.stamp_note_text = ''
    if hasattr(bpy.context.preferences.filepaths, 'save_preview_images'):
        bpy.context.preferences.filepaths.save_preview_images = False
    bpy.context.preferences.filepaths.save_version = 0
    target.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(target), compress=False, relative_remap=False)
    raw = bytearray(target.read_bytes()); assert raw[:7] == b'BLENDER'
    # Blender records its own absolute saved filename even after RNA paths are
    # made relative. Replace only complete NUL-terminated absolute path strings
    # in place; the field size and all block offsets remain unchanged.
    pattern = re.compile(rb'(?:[A-Za-z]:[\\/]|/(?:home|Users|workspace|tmp)/)[\x20-\x7e]{2,2048}')
    removed = 0
    for match in list(pattern.finditer(raw)):
        if match.end() >= len(raw) or raw[match.end()] != 0: continue
        tail = bytes(match.group()).replace(b'\\', b'/').rsplit(b'/', 1)[-1]
        replacement = b'//' + tail
        if len(replacement) > len(match.group()): replacement = b'//'
        raw[match.start():match.end()] = replacement + b'\0' * (len(match.group()) - len(replacement))
        removed += 1
    target.write_bytes(raw)
    assert not re.search(rb'[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/]|/(?:home|Users|workspace)/', raw, re.I), 'A local user path remains; do not publish this copy.'
    bpy.ops.wm.open_mainfile(filepath=str(target), use_scripts=False, load_ui=False)
    assert before == fingerprint(), 'Mesh geometry or weights changed during sanitization.'
    assert all(i.packed_file for i in bpy.data.images if i.users), 'A texture lost its packed data.'
    assert all(strip_png_metadata(bytes(i.packed_file.data))[1] == 0 for i in bpy.data.images if i.users), 'Texture metadata survived the save.'
    assert not bpy.data.texts and not bpy.data.libraries
    print(json.dumps({'publication_copy_validated': True, 'absolute_path_fields_removed': removed,
                      'texture_metadata_chunks_removed': metadata_chunks_removed,
                      'meshes_unchanged': len(before), 'packed_images': len(bpy.data.images)}))

if __name__ == '__main__':
    main()
