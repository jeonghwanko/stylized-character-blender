"""Repository-relative inputs; all generated research outputs stay in ignored work/."""
import os
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
ROOT = RESEARCH.parents[1]
PARAMETERS = RESEARCH / 'parameters'
BASE = RESEARCH / 'checkpoints/face_study_77.blend'
PUBLISHED = RESEARCH / 'checkpoints/neutral_n05.blend'
WORK = Path(os.environ.get('RESEARCH_WORK', str(ROOT / 'work/facial-research'))).resolve()
if WORK == RESEARCH or RESEARCH in WORK.parents:
    raise ValueError('Use a separate work directory, not the published research sources.')
WORK.mkdir(parents=True, exist_ok=True)
