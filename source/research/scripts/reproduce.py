"""Reproduce n05 from the versioned77 checkpoint; no installs or network calls."""
import argparse, os, shutil, subprocess, sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender', default='blender', help='Blender executable on PATH or its full path')
    parser.add_argument('--work-dir', type=Path, help='Separate output directory; default is ignored work/facial-research')
    parser.add_argument('--render', action='store_true', help='Also render front,90deg side and clay views')
    args = parser.parse_args()
    if args.work_dir:
        os.environ['RESEARCH_WORK'] = str(args.work_dir.resolve())
    from research_paths import WORK, PARAMETERS
    import numpy, scipy  # Fail early if the caller has not provided the documented environment.
    blender = shutil.which(args.blender)
    if not blender:
        raise SystemExit('Blender was not found. Supply --blender; this script does not install it.')
    scripts = Path(__file__).resolve().parent
    shutil.copy2(PARAMETERS / 'clean_surface_n02.json', WORK / 'clean_surface_n02.json')
    env = os.environ.copy()
    # Python package discovery for Blender --python, independent of launch directory.
    env['PYTHONPATH'] = str(scripts) + os.pathsep + env.get('PYTHONPATH', '')
    def run(script, use_blender=True):
        cmd = ([blender, '--background', '--factory-startup', '--disable-autoexec',
                '--python-exit-code', '1', '--python', str(scripts / script)] if use_blender
               else [sys.executable, str(scripts / script)])
        subprocess.run(cmd, env=env, cwd=WORK, check=True)
    run('prepare_state.py')
    env['NEUTRAL_REV'] = 'n02'; env.pop('NEUTRAL_INPUT', None)
    run('build_clean_head.py')
    env['NEUTRAL_REV'] = 'n03'; env['NEUTRAL_INPUT'] = str(WORK / 'neutral_n02.blend')
    run('export_clean_surface.py')
    run('solve_volume_surface.py', use_blender=False)
    run('apply_boundary_surface.py')
    run('author_n04.py')
    run('author_n05.py')
    env['NEUTRAL_REV'] = 'n05'; env['NEUTRAL_INPUT'] = str(WORK / 'neutral_n05.blend')
    run('validate_checkpoint.py')
    run('compare_reproduction.py')
    if args.render:
        env.update(STUDY_REV='n05', STUDY_INPUT=str(WORK / 'neutral_n05.blend'),
                   STUDY_SHOTS='face_front,face_side,clay_face_left', FACE_CLOSE='1', REFERENCE_POSE='0')
        run('render_checkpoint.py')
    print('Research checkpoint produced. Likeness and production facial rig remain unapproved.')

if __name__ == '__main__':
    main()
