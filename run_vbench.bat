@echo off
call .venv\Scripts\activate.bat

python run_vbench.py vbench checkpoint/ ^
    --output_dir results_vbench/videos ^
    --num_samples 5 ^
    --image_types "indoor,scenery" ^
    --frames 161 ^
    --height 720 ^
    --width 960 ^
    --no_need_depth True ^
    --nf4 True
