# 캐릭터 핸드오프 문서 (dots 인계용)

작성일: 2026-10-18 · 대상: 이 저장소 루트 (원래 작업 경로는 `/workspace/character`)
이 문서 하나만 읽으면 작업을 이어받을 수 있도록 썼다. 스크립트 안의 경로는 원래 작업 환경 기준 절대 경로다(§5 참고).

---

## 0. 한눈에 보기 (TL;DR)
- **무엇:** 오리지널 스타일라이즈드(픽사·카툰풍) 금발 포니테일 소녀 캐릭터. Blender 스크립트로만 만들었다(사람 스컬프팅, Meshy, 외주 없음).
- **현재 상태:** 무표정 모델 **v4**는 사용자 승인 완료. 그 위에 **리그(57본, Unity Humanoid 이름)**, 셰이프키 **BigSmile/Blink**, 포즈 클립 **HandsOnHip**까지 완료.
- **결과물:** `export/character_game.glb`(스킨+모프+애니), `export/character_rigged.fbx`, 원본 `source/character_rigged.blend`.
- **삼각형:** 총 **37,519** (스펙 18–35k보다 약 2.5k 많다. 최적화 단계에서 줄여야 함).
- **남은 일:** 표정 13개 추가 (§1 목록 기준), 최적화(≤35k), 팔꿈치 소매 접힘, 입 안쪽 구조 개선 등 (§10).

## 1. 프로젝트 목표와 사용자 스펙 요약
- **목표:** 게임용 **새 오리지널** 스타일라이즈드 캐릭터. 레퍼런스(§2)는 분위기 참고용이며 **어떤 요소도 복제하지 않는다**.
- **디자인:** 금발, 높이 묶은 볼륨 포니테일과 앞머리, 큰 눈, 둥근 얼굴, 장난스럽고 밝은 성격.
- **의상 (variant A):** 코랄 후디(앞 지퍼 열림, 후드, 드로스트링) + 흰 티 + 차콜 반바지 + 흰/코랄 스니커즈와 줄무늬 양말.
- **비율:** 약 **5등신**. 허리–골반 곡선, 허벅지·종아리 형태가 있다.
- **폴리곤:** **18k–35k tris**. 텍스처는 PBR(BaseColor/Normal/Roughness).
- **표정 15개 (사용자 원 스펙 확정본).** 필수 8종 + 권장 확장 7종. Blink는 보조 셰이프(표정 수에 포함 안 함).
  - 필수: 1. Neutral ✅ 2. Smile 3. Big Smile ✅ 4. Surprised 5. Nervous 6. Embarrassed 7. Annoyed/Pout 8. Thinking
  - 권장: 9. Wink 10. Confident grin 11. Shocked 12. Silly / tongue out 13. Determined 14. Sad / worried 15. Laughing
  - 포인트: 눈썹 변화가 잘 보일 것. 입만이 아니라 눈·볼·눈썹이 같이 변할 것. 놀람은 눈과 입 모두 크게. 당황/수줍음은 시선·홍조·입꼬리로.
  - 보조 셰이프: Blink ✅
- **표정 원칙 (스펙):** 표정은 블렌드셰이프 방식이다. **입이 움직이면 눈·볼·눈썹도 같이 움직여야 한다**(입만 바뀌는 표정은 불합격).
- **산출물:** `character_master.blend`, `character_neutral.glb/.fbx`, 리그된 `character_rigged.fbx`, 게임용 `character_game.glb`(스켈레톤+셰이프+애니), 텍스처 PNG, 프리뷰(턴어라운드 정면/측면/후면, 3/4, 얼굴 클로즈업), 레퍼런스 비교 이미지.
- **작업 순서 (스펙):** **Neutral → 표정 → 최적화**. 단계마다 사용자 승인을 받는다.
- **제약:**
  - push/commit 금지, 결제 금지, 회원가입 금지.
  - 외부 발송·게시 금지.
  - 공개 파일에 사용자 실명이나 이메일을 넣지 않는다.
- **QA 체크리스트** (내부 모델링 가이드 체크리스트 + 작업 중 쓴 항목):
  - [ ] 정면·측면·45°에서 실루엣이 레퍼런스급 매력: 큰 눈, 둥근 볼, 볼륨 있는 머리
  - [ ] 눈 폭/얼굴 폭 ≥ 레퍼런스의 90%, 얼굴 최대 폭 지점이 눈높이보다 아래
  - [ ] 머리 클럼프 사이 V자 갈라짐, 끝 테이퍼, 다면체 느낌 없음
  - [ ] 눈: 각막 하이라이트 + 캐치라이트 + 눈꺼풀 테두리
  - [ ] 의상·피부·머리 관통 없음 (정지 상태와 포즈 상태 모두)
  - [ ] 어깨·팔꿈치·손목·골반·무릎 변형이 깨끗하고 후디가 찢어지지 않음
  - [ ] 15개 표정 모두에서 입·눈꺼풀 관통 없음, 눈·볼·눈썹이 같이 움직임
  - [ ] 삼각형 18–35k, GLB가 three.js에서 스킨+모프로 로드되고, Unity Humanoid 매핑 가능
  - [ ] 레퍼런스 복제 없음 (오리지널리티)

## 2. 레퍼런스 이미지 (영감 전용, **이 저장소에는 포함하지 않음**)
레퍼런스 두 장은 저작권이 확인되지 않은 제3자 이미지라서 공개 저장소에서 뺐다. 레퍼런스 패널을 넣었던 비교 이미지도 빼고, 레퍼런스 없는 버전(`preview/compare_*.png`)으로 다시 만들었다. 말로 설명하면 이렇다.
- **레퍼런스 1** (세로 1086×1448, 캐릭터 시트): 3D 카툰풍 금발 포니테일 소녀. 파란 티셔츠에 청바지, 운동화 차림이고 한 손을 허리에 얹은 자신감 있는 포즈. 큰 눈과 활짝 웃는 표정. 옆에 작은 표정·포즈 썸네일이 있다.
- **레퍼런스 2** (세로 1086×1448, 캐릭터 시트): 같은 계열의 금발 포니테일 소녀. 빨강/코랄 후디에 짧은 반바지, 하이삭스와 운동화 차림이고 손가락으로 가리키는 장난스러운 포즈. 옆에 표정 썸네일이 있다.
- 이 캐릭터가 참고한 것은 분위기뿐이다: 큰 눈, 볼륨 있는 포니테일, 밝은 성격, 캐주얼 스포티 의상. 얼굴, 의상 디자인, 포즈 디테일은 오리지널이다.

## 3. 현재 상태
### 3.1 무표정 모델 v4 (사용자 승인)
- 버전 이력:
  - v1: 초기 모델
  - v2: 얼굴, 비율, 의상 정리
  - v3: 머리카락을 SDF 방식으로 재구축
  - v4: 얼굴 매력과 체형 보강
    - 눈 키움(반지름 0.0465), 굵은 속눈썹 라인과 끝 3갈래
    - 흰자 은은한 자체발광, 코 브리지와 콧볼, 눈썹을 앞머리 아래로 내림
    - 스머크 입선, C자 귀
    - 5등신 다리 단축(remap), 허리–골반 곡선, 해부학 타원체
    - 손 회내 40°, 손목 굵게
    - 후드를 칼라에 붙은 카울로 재구성
- 비교 이미지: `preview/compare_versions_v1_to_v4.png`, `preview/turnaround_sheet.png`

### 3.2 리그 / 셰이프 / 포즈 (완료, 최종 보고 기준)
- **리그:** `CH_Armature` 57본 (§6). 웨이트는 스크립트로 자동 계산했다(손 페인팅 아님).
- **셰이프키** (`CH_Body`, 입 안쪽 메쉬 `CH_Mouth`를 합친 상태): `Basis`, `Blink`, `BigSmile`
- **BigSmile 내용:**
  - D자로 크게 벌린 입, 윗니 띠와 혀(텍스처 `T_Mouth_BaseColor.png`), 입꼬리 위·바깥으로
  - 턱 살짝 내려감
  - 볼이 올라가 아래 눈꺼풀을 밀어올림, 윗눈꺼풀 약간 내려감(찡그림)
  - 눈썹 상승과 아치
  - 오른쪽(+x)이 조금 더 강한 비대칭
- **Blink:** 눈꺼풀을 정점별 각도 스트레치로 완전히 덮고, 속눈썹 라인이 눈꺼풀 가장자리를 따라간다.
- **포즈 `HandsOnHip`** (프레임 1–30, 액션):
  - 양손을 엉덩이에, 팔꿈치는 바깥으로
  - 오른다리 지지 콘트라포스토, 골반 이동·기울기, 상체 역회전
  - 머리 기울임·회전, 포니테일 스윙
- **검증:**
  - three.js 0.169 헤드리스(node)에서 로드 확인: SkinnedMesh 7, 본 58(57 + glTF 익스포터가 만든 `neutral_bone`), 모프 `Blink`/`BigSmile`, 애니 `HandsOnHip` 1.25초·171트랙. 재생하면 손이 엉덩이에 온다.
  - FBX를 Blender에 다시 import: 아마추어 1개(57본), 셰이프 3개, 액션 `CH_Armature|HandsOnHip`(Blender 명명 규칙).
  - **Unity에서 Humanoid 자동 매핑은 실제로 테스트하지 않았다.**
- 비교 이미지: `preview/compare_rig_pose.png`

### 3.3 솔직한 약점
1. **팔꿈치:** 약 90° 굽힘에서 후디 소매 바깥쪽이 각진 모서리로 접힌다. 커프 경계에 아주 작은 어두운 틈이 있다(뒤에서 클로즈업할 때만 보임). 팔꿈치 웨이트를 스무딩해서 완화했지만 완전하지 않다. 정지 상태에서도 소매가 풍선처럼 보인다.
2. **입 안쪽:** 실제 치아·혀 지오메트리가 아니라 텍스처를 입힌 평면 인서트다. 정면과 3/4에서는 괜찮지만 극단적인 측면 클로즈업에서는 납작해 보인다. **턱 본이 없다**(입 벌림은 셰이프로만 한다).
3. **BigSmile:** 찡그림이 약한 편이다. 레퍼런스보다 입이 작고, 눈이 초승달 모양이 되지 않는다. 눈썹을 올리면 끝이 앞머리와 살짝 겹친다.
4. **웨이트:** 이 포즈와 일반적인 팔 스윙에는 문제가 없다. 만세나 깊은 스쿼트 같은 극단 포즈는 테스트하지 않았다.
5. **손가락:** 단순하게 말린 정도이고 손가락별 디테일 포즈가 없다.
6. **포즈:** 다소 꼿꼿해서 레퍼런스보다 덜 역동적이다. 히어로샷 프레이밍이 넓다.
7. **기타:** 티셔츠 목둘레 가장자리가 들쭉날쭉하다(v4부터). 후디가 저폴리라 굽힘 부위가 각져 보인다.
8. **삼각형:** 37.5k로 스펙 상한 35k를 넘는다.
9. **매력:** 레퍼런스 대비 얼굴 매력(눈 크기·표현력)과 머리 디테일은 여전히 한 단계 아래다. 손 스컬프팅 없이 스크립트로만 만든 한계다.

## 4. 파일 트리
```
/workspace/character/
├─ README.md                   ← 저장소 소개 (한국어)
├─ HANDOFF.md                  ← 이 문서
├─ LICENSE / LICENSE-ASSETS    ← MIT (스크립트) / CC BY 4.0 (모델·텍스처·프리뷰)
├─ source/
│  ├─ character_master.blend   ← 무표정 v4 최종(FINAL 빌드 결과: 합쳐진 CH_* 오브젝트, UV, 베이크된 텍스처 연결)
│  ├─ character_rigged.blend   ← 리그+셰이프+HandsOnHip 액션 포함 최종 원본
│  ├─ *.blend1                 ← Blender 자동 백업 (지워도 됨)
│  ├─ build.py                 ← 메인 빌드: 머리/얼굴/눈/몸/손 생성 → build_hair → build_outfit → (FINAL이 아니면 remap / FINAL이면 finalize) → render
│  ├─ build_hair.py            ← v3 SDF 머리카락: 앞머리 클럼프 7개(베지어 스윕), 포니테일, 잔머리, 머리끈. 볼륨을 work/hair/F.npy로 쓰고 mc.py로 메싱. env HAIR_VOX(기본 0.0025), HAIR_TRIS(기본 8600)
│  ├─ mc.py                    ← marching cubes (scikit-image). 반드시 venv /workspace/tools/hairenv/bin/python으로 실행 (build_hair가 subprocess로 호출)
│  ├─ build_outfit.py          ← v4 의상: 후디(카울 후드, 지퍼, 드로스트링, 애글릿), 티, 반바지, 양말, 신발, 끈
│  ├─ remap.py                 ← 5등신용 다리 단축 (DZ=-0.08, K2=(0.63-0.08)/0.63), 머티리얼 좌표 패치, ponytail_bones.json 갱신
│  ├─ finalize.py              ← FINAL 단계: 가려진 면 삭제, 데시메이트, 트랜스폼 적용, remap, part 속성, CH_*로 조인, UV/베이크, neutral GLB/FBX 익스포트, master.blend 저장
│  ├─ render.py                ← Cycles CPU 프리뷰 렌더 (SHOTS 목록)
│  ├─ rig.py                   ← master.blend 열기 → CH_Armature 57본 → 웨이트 → 셰이프(Blink/BigSmile) + 입 인서트 → Armature 모디파이어 → pose.py 실행
│  ├─ pose.py                  ← HandsOnHip 포즈 (해석적 2본 IK), 키프레임, 포즈/얼굴 렌더(RSHOTS), EXPORT=1이면 GLB/FBX 익스포트와 rigged.blend 저장
│  ├─ lib.py                   ← 공용 헬퍼 (clear, 메쉬 유틸, BVH 등)
│  ├─ post.py                  ← 렌더 PNG 후처리 (RGBA → 배경 합성)
│  ├─ run.sh                   ← 무표정 빌드/렌더 래퍼
│  ├─ rig.sh                   ← 리그/포즈/익스포트 래퍼
│  └─ *_v1/_v2a/_v3/_v4.py     ← 이전 버전 백업 (build_v1.py, build_v2a.py, build_v3.py, build_hair_v1/v2.py, build_outfit_v1/v2a/v3.py, finalize_v4.py, render_v3.py)
├─ export/
│  ├─ character_neutral.glb / .fbx ← 무표정 v4 (리그 없음)
│  ├─ character_game.glb       ← 게임용: 스켈레톤 + 모프 Blink/BigSmile + 애니 HandsOnHip, 텍스처 내장
│  ├─ character_rigged.fbx     ← 리그+셰이프+애니 (텍스처 embed, add_leaf_bones=False, 축 -Z forward / Y up)
│  └─ ponytail_bones.json      ← 포니테일 본 위치 (다리 단축이 이미 반영된 z)
├─ textures/                   ← §7
└─ preview/                    ← §8
(work/ ← 중간 렌더·로그·머리 SDF 캐시. 저장소에는 없고 빌드하면 생긴다)
```

## 5. 환경과 재빌드 방법
- **Blender 4.2.3 LTS** (헤드리스): `/workspace/tools/blender-4.2.3-linux-x64/blender`, 렌더는 Cycles CPU + 디노이즈. GPU 없음.
- **시스템 python3:** PIL 사용 (post.py와 스트립 이미지).
- **머리카락 venv:** `/workspace/tools/hairenv` (numpy, scikit-image). 시스템 pip 설치가 막혀 있어서 venv를 만들었다. 다른 박스라면 `python3 -m venv /workspace/tools/hairenv && /workspace/tools/hairenv/bin/pip install numpy scikit-image`.
- **three.js 검사:** node v20, `/workspace/tools/threetest/check.mjs` (three@0.169, GLTFLoader.parse, 이미지 스텁 사용). 실행: `cd /workspace/tools/threetest && node check.mjs`
- 스크립트 경로가 `/workspace/character`와 Blender 경로로 하드코딩돼 있다. 다른 위치로 옮기면 `run.sh`, `rig.sh`, `render.py`, `finalize.py`, `pose.py`, `build_hair.py`의 경로를 고쳐야 한다.

### 5.1 무표정 모델 빌드 (`run.sh`)
```bash
cd /workspace/character
# 빠른 확인 빌드 (remap만, 조인/베이크 없음)
SAMPLES=16 SHOTS=front,face,q34 OUTN=t001 source/run.sh
# 최종 빌드: finalize → master.blend 저장 + export/character_neutral.* + 텍스처 베이크
FINAL=1 COUNT=1 SAMPLES=40 SHOTS=front,side,back,face,faceq,faces,q34,feet,hback,hside,hand OUTN=t002 source/run.sh
```
- env:
  - `FINAL=1`: finalize 단계 실행
  - `COUNT=1`: 오브젝트별 TRIS 출력
  - `SAMPLES`: Cycles 샘플 수
  - `SHOTS`: 렌더 샷, 쉼표 구분. 가능한 값: front, side, back, face, q34, faceq, faces, feet, hback, hside, hand, save
  - `OUTN`: 결과 스트립 이름 → `work/<OUTN>.png`
- 렌더는 `work/r/`에 저장된다. FINAL 빌드는 수 분 걸린다(머리 SDF와 베이크 포함).
- 주의: **Blender 출력을 `| head`로 직접 자르지 말 것.** SIGPIPE로 Blender가 죽는다(run.sh는 grep을 거친 뒤 자른다).

### 5.2 리그/표정/포즈/익스포트 (`rig.sh`)
`source/character_master.blend`가 필요하다. 무표정을 바꿨다면 §5.1 FINAL 빌드를 먼저 돌린다.
```bash
cd /workspace/character
SAMPLES=16 RSHOTS=hero,pfront,fsmile,fblink OUTN=r001 source/rig.sh            # 확인용
SAMPLES=48 RSHOTS=hero,pfront,pside,pback,pclose,pelbow,fneutral,fsmile,fsmile34,fblink EXPORT=1 OUTN=r002 source/rig.sh   # 최종 + 익스포트
```
- `RSHOTS` 값:
  - 포즈: hero, pfront, pside, pback, pclose, pelbow
  - 얼굴(레스트 포즈): fneutral, fsmile, fsmile34, fsmileside, fblink
- 다른 env:
  - `EXPORT=1`: GLB/FBX 익스포트와 rigged.blend 저장
  - `NOPOSE=1`: 포즈 끔
- 렌더는 `work/rr/`, 로그는 `work/rig.log`(EYES/BONES/WEIGHTS/SHAPES/RIGTRIS/EXPORT 줄 확인). 한 번에 약 1–3분.
- 팁: 이미지 뷰어 캐시 때문에 매번 새 `OUTN`을 쓰는 게 좋다.

## 6. 리그
- 아마추어 `CH_Armature`, 본 57개. 이름은 Unity Humanoid 자동 매핑 규칙을 따른다.
- 몸통: `Hips` → `Spine` → `Chest` → `UpperChest` → `Neck` → `Head`
- 눈: `LeftEye`, `RightEye` (Head 자식, 각막·캐치라이트·안구 웨이트)
- 포니테일: `Pony_0` → `Pony_1` → `Pony_2` (Head 자식, 머리끈 위치 z≈1.515에서 시작)
- 팔 (Left/Right): `Shoulder` → `UpperArm` → `LowerArm` → `Hand`
- 손가락 (Left/Right × Thumb/Index/Middle/Ring/Little × Proximal/Intermediate/Distal): 예) `LeftIndexProximal`
- 다리 (Left/Right): `UpperLeg` → `LowerLeg` → `Foot` → `Toes`
- **턱 본 없음.** 입은 셰이프로 처리한다.
- 롤: Y축 방향 본은 align_roll(0,0,1), 나머지는 (0,-1,0).
- 주요 위치 (m, Blender Z-up, 캐릭터는 -Y를 바라봄):
  - 골반 0.90, 목 1.255, 머리 1.45
  - 어깨 (±0.145, 1.142), 팔꿈치 (±0.240, 0.905), 손목 (±0.292, 0.695)
  - 발목 z 0.095
  - 눈 (±0.0615, -0.0868, 1.340)
  - 신장 약 1.53
- **웨이트 방식:**
  - 몸: 본 세그먼트까지의 역거리(4제곱)에 영역 마스크를 씌우고 라플라시안 스무딩, 팔꿈치는 추가 스무딩. 손은 8제곱.
  - 옷: 가장 가까운 몸 면에서 전이한 뒤 팔꿈치 스무딩.
  - 양말: 아랫다리/발. 신발: 발만.
  - 머리카락: 기존 그룹(Pony_*), 나머지는 Head.
- 메쉬별 영향 본은 최대 4개(topk=4)다.

## 7. 셰이프키와 텍스처
- **셰이프키** (`CH_Body`에만 있음): `Basis`, `Blink`, `BigSmile`. GLB 모프 이름도 같다.
- 입 인서트: 25×9 그리드를 `CH_Body`에 합쳐 두었다(part 13). Basis와 Blink에서는 피부 6 mm 안쪽에 숨어 있고, BigSmile에서 D자로 열린다.
- `part` 정수 속성 (정점별 부위 코드, finalize와 rig에서 마스크로 사용):
  - 얼굴: Head 1, Ear 2, Eyeball 3, Lid 4, LashLine 5, Lash 6, Brow 7, Mouth line 8, Mouth insert 13
  - 몸: Body 9, Hand 10
  - 눈 부속: Cornea 11, Catch 12
  - 머리카락: Hair 20, HairTie 21, HairFly 22
  - 의상: Hoodie계 30, Shorts 31, Sock 33, 기타 35
  - 신발: Sole 40, Shoe 41, Lace 42
- **텍스처** (`textures/`):

| 파일 | 해상도 | 용도 |
|---|---|---|
| T_FaceHair_BaseColor/Normal/Roughness.png | 2048² | 몸·얼굴·머리 (M_FaceHair) |
| T_Clothes_BaseColor/Normal/Roughness.png | 2048² | 의상 (M_Clothes) |
| T_Shoes_BaseColor/Normal/Roughness.png | 1024² | 신발 (M_Shoes) |
| T_Mouth_BaseColor.png | 256² | 입 안쪽: 어두운 내부, 윗니 띠, 혀, 입술 테두리 (M_Mouth) |

- 각막(M_Cornea)과 캐치라이트(M_Catchlight)는 텍스처 없는 머티리얼이다.

## 8. 프리뷰 (`preview/`)
- 최신 무표정 v4:
  - turnaround_front/side/back.png, turnaround_sheet.png
  - three_quarter.png
  - face_closeup/face_34/face_side.png
  - hair_back/hair_side.png, hand.png, feet.png
- 리그/표정/포즈:
  - rig_pose_hero_34, rig_pose_front/side/back, rig_pose_upper_34, rig_pose_elbow_back
  - rig_face_neutral, rig_face_bigsmile, rig_face_bigsmile_34, rig_face_blink
- 비교 이미지:
  - **compare_rig_pose.png** (최신, 레퍼런스 패널 없음)
  - compare_versions_v1_to_v4.png (버전별 3/4 샷과 얼굴)
- 이전 버전: `v1_*`, `v2_*`, `v3_*`

## 9. 삼각형 수 (리그 최종, 총 37,519)

| 오브젝트 | Tris | 내용 |
|---|---|---|
| CH_Body | 13,871 | 머리·얼굴·눈·눈꺼풀·속눈썹·눈썹·귀·몸·손 + 입 인서트 |
| CH_Hair | 9,380 | 앞머리·포니테일·잔머리·머리끈 |
| CH_Clothes | 9,780 | 후디·후드·드로스트링·티·반바지·양말 |
| CH_Shoes | 3,904 | 밑창·갑피·끈 |
| CH_EyeCornea | 528 | 각막 |
| CH_EyeCatchlight | 56 | 캐치라이트 |

## 10. 알려진 문제와 다음 단계 (우선순위 순)
1. **표정 목록은 §1에 사용자 원 스펙대로 확정됨.** (Neutral, Big Smile 완료)
2. **표정 13개 추가 (§1 목록 기준).** `rig.py`의 BigSmile 방식을 재사용한다: 부위별 가우시안 변위 + `lid_close()` 눈꺼풀 함수 + 입선 `ztop()` 매핑 + 입 인서트. 표정마다 눈·볼·눈썹을 같이 움직이고, 정면·3/4·측면 렌더로 관통을 검사한다. 필요하면 ARKit 이름 체계로 기본 셰이프(eyeBlinkL/R, mouthSmileL/R, jawOpen, browInnerUp 등)를 나눠서 조합하는 것도 고려.
3. **입 안쪽 개선:** 실제 윗니/아랫니 지오메트리와 혀 메쉬, 입 안쪽 공간을 넣고, 가능하면 Jaw 본을 추가한다. Surprised/Laugh 같은 큰 입 표정 전에 해야 한다.
4. **팔꿈치 소매 접힘 수정:** 팔꿈치 보조 본(corrective/helper) 또는 굽힘 각도 기반 corrective 셰이프를 쓰거나, 소매 지오메트리를 다시 만든다(팔꿈치 루프 추가, 풍선 형태 줄이기). 커프 경계의 틈도 같이 고친다.
5. **최적화 (≤35k, 가능하면 30k 부근):** 머리 HAIR_TRIS 8600 → 7000, 의상과 신발 데시메이트, 안 보이는 면 정리. 표정이 확정된 뒤 셰이프 보존 데시메이트를 하거나 셰이프를 다시 굽는다.
6. **Unity 실제 검증:** FBX를 Humanoid로 임포트해 Avatar 매핑을 확인하고, 블렌드셰이프·애니 클립 이름(`CH_Armature|HandsOnHip`)을 정리한다. 원하면 액션 이름을 `HandsOnHip`만 남게 바꾼다.
7. **BigSmile 다듬기:** 찡그림 강화(눈을 초승달 쪽으로), 입 크기 소폭 확대, 눈썹과 앞머리 겹침 해소.
8. **웨이트 검증:** 극단 포즈(만세, T-pose ↔ A-pose, 스쿼트, 발차기) 테스트 렌더, 어깨 후디 부피 유지.
9. **포즈 역동성:** 골반 기울기·어깨 대비 강화, 손가락별 포즈, 히어로샷 프레이밍.
10. **기타 마감:** 티셔츠 목둘레 가장자리 정리, 후디 굽힘 부위 폴리곤 분배.

## 11. 하지 말 것 / 유의
- 레퍼런스 이미지의 디자인·얼굴·의상 디테일을 복제하지 말 것.
- 공개 파일에 사용자 실명이나 이메일을 넣지 말 것.
- `work/hair/F.npy`(약 47 MB)는 빌드 캐시라서 저장소에 넣지 않았다. 빌드하면 다시 생긴다.

## 얼굴 표면 연구 인계 추가

새 연구 체크포인트77·n05는 source/research/checkpoints/에 있습니다. 기존 v4 파일과 수출물은 그대로 보존했습니다. n05는 닮음 미통과이며 새 피부의 표정키·UV·전체 포즈 검증이 끝나지 않았습니다. 세부 상태와 재현 명령은 [연구 README](source/research/README.md), 실패 분석 및 아직 생성되지 않은 전체 얼굴 제어 메시의 재개 지점은 [NEXT_STEPS](source/research/NEXT_STEPS.md)를 따릅니다. 반복 실패 파일·참조 이미지·개인 파일 관리 자료는 공개 범위에서 제외했습니다.
