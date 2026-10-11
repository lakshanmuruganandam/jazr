#!/bin/zsh
# Re-runs the whole 03_cfd_flow suite in order (cached flows are reused; unsteady snapshots are recomputed).
cd "$(dirname "$0")"
python3 t1_verification.py        > data/t1_log.txt 2>&1
python3 t2_face_velocity.py       > data/t2_log.txt 2>&1
python3 t3_particles.py flows A   > data/t3_flowsA_log.txt 2>&1
python3 t3_particles.py flows B   > data/t3_flowsB_log.txt 2>&1
python3 t3_particles.py flows X   > data/t3_flowsX_log.txt 2>&1
python3 t3_particles.py flows W   > data/t3_flowsW_log.txt 2>&1   
python3 t3_particles.py track     > data/t3_track_log.txt 2>&1
python3 t4_clogging.py            > data/t4_log.txt 2>&1
python3 t5_outer_guide.py A       > data/t5A_log.txt 2>&1
python3 t5_outer_guide.py B       > data/t5B_log.txt 2>&1
echo ALLDONE
