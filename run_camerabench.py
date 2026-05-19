"""
CameraBench evaluation for DeepVerse generated videos.

CameraBench (arXiv 2504.15376) measures camera motion understanding across three tasks:
  - Classification: identifies specific camera primitives (pan, tilt, zoom, track, roll, ...)
  - VQA: yes/no questions about camera behavior in a clip
  - Captioning: natural-language descriptions of camera motion

This script uses the VQAScore approach with a Qwen2.5-VL model fine-tuned on camera motion
to measure whether generated videos match their intended camera motion descriptions.

Install dependency:
  pip install git+https://github.com/chancharikmitra/t2v_metrics.git

Commands:
  python run_camerabench.py download [--save_dir ./camerabench_data] [--skip_videos]
  python run_camerabench.py score <video_dir> [--descriptions_file <json>] [--model_size 7b]
  python run_camerabench.py summarize [--results_csv results_camerabench/scores.csv]
"""
import csv
import glob
import json
import os
import subprocess
import sys
import time

import fire

try:
    import t2v_metrics
    HAS_T2V_METRICS = True
except ImportError:
    HAS_T2V_METRICS = False

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_OUTPUT_CSV = os.path.join(_SCRIPT_DIR, 'results_camerabench', 'scores.csv')


def download(save_dir='./camerabench_data', skip_videos=False):
    """Clone CameraBench repo and download test annotations and videos."""
    save_dir = os.path.abspath(save_dir)
    os.makedirs(save_dir, exist_ok=True)

    repo_dir = os.path.join(save_dir, 'CameraBench')
    if not os.path.exists(repo_dir):
        print(f'[camerabench] cloning repo → {repo_dir}')
        subprocess.run(['git', 'clone', 'https://github.com/sy77777en/CameraBench', repo_dir], check=True)
    else:
        print(f'[camerabench] repo exists, pulling latest')
        subprocess.run(['git', '-C', repo_dir, 'pull'], check=True)

    print('[camerabench] downloading test annotations...')
    subprocess.run([sys.executable, os.path.join(repo_dir, 'download_test_file.py'), '--save_dir', save_dir], check=True)

    if not skip_videos:
        print('[camerabench] downloading test videos (this may take a while)...')
        subprocess.run([sys.executable, os.path.join(repo_dir, 'download_test_videos.py'), '--save_dir', save_dir], check=True)

    print(f'[camerabench] done → {save_dir}')


def score(
    video_dir,
    descriptions_file=None,
    model_size='7b',
    output_csv=None,
):
    """
    Score videos against camera motion descriptions using CameraBench VQAScore.

    Args:
        video_dir:          Directory containing .mp4 files to evaluate.
        descriptions_file:  Optional JSON file: [{"video": "name.mp4", "description": "..."}].
                            If omitted, descriptions are parsed from DeepVerse filenames
                            ({prompt}-{sample_idx}-{seed}.mp4).
        model_size:         Qwen2.5-VL checkpoint size: 7b, 32b, or 72b.
        output_csv:         Output CSV path (default: results_camerabench/scores.csv).
    """
    if not HAS_T2V_METRICS:
        print('[camerabench] t2v_metrics not installed.')
        print('  pip install git+https://github.com/chancharikmitra/t2v_metrics.git')
        return

    output_csv = output_csv or _DEFAULT_OUTPUT_CSV
    out_dir = os.path.dirname(output_csv)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    checkpoint = f'chancharikm/qwen2.5-vl-{model_size}-cam-motion'
    model_id = f'qwen2.5-vl-{model_size}'

    print(f'[camerabench] loading {model_id} from {checkpoint}...')
    scorer = t2v_metrics.VQAScore(model=model_id, checkpoint=checkpoint)

    pairs = _collect_pairs(video_dir, descriptions_file)
    if not pairs:
        print(f'[camerabench] no videos found in {video_dir}')
        return

    print(f'[camerabench] scoring {len(pairs)} videos...')

    is_new = not os.path.exists(output_csv)
    all_scores = []
    t_start = time.time()

    with open(output_csv, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(['video', 'description', 'score', 'duration_s'])

        for i, (video_path, description) in enumerate(pairs):
            if not os.path.isfile(video_path):
                print(f'[camerabench] skip (not found): {video_path}')
                continue

            pct = 100 * i / len(pairs)
            elapsed_total = time.time() - t_start
            eta_str = ''
            if i > 0:
                secs_left = elapsed_total / i * (len(pairs) - i)
                eta_str = f'  ETA {int(secs_left // 3600):02d}h{int(secs_left % 3600 // 60):02d}m{int(secs_left % 60):02d}s'
            print(f'[camerabench] [{i+1}/{len(pairs)}  {pct:.0f}%{eta_str}]  {os.path.basename(video_path)}')

            st = time.time()
            result = scorer(images=[video_path], texts=[description])
            elapsed = time.time() - st
            s = float(result[0][0])
            all_scores.append(s)
            print(f'  score={s:.4f}  ({elapsed:.1f}s)  "{description[:70]}"')
            w.writerow([video_path, description, f'{s:.6f}', f'{elapsed:.2f}'])
            f.flush()

    if all_scores:
        avg = sum(all_scores) / len(all_scores)
        print(f'\n[camerabench] mean score: {avg:.4f}  (n={len(all_scores)})')
    print(f'[camerabench] results → {output_csv}')


def summarize(results_csv=None):
    """Print aggregate statistics from a previously saved scores CSV."""
    results_csv = results_csv or _DEFAULT_OUTPUT_CSV
    if not os.path.isfile(results_csv):
        print(f'[camerabench] no results file at {results_csv}')
        return

    scores = []
    with open(results_csv, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            try:
                scores.append(float(row['score']))
            except (KeyError, ValueError):
                pass

    if not scores:
        print('[camerabench] no scores found in CSV')
        return

    scores.sort()
    n = len(scores)
    avg = sum(scores) / n
    med = scores[n // 2]
    above50 = sum(1 for s in scores if s >= 0.5) / n * 100
    above70 = sum(1 for s in scores if s >= 0.7) / n * 100
    print(f'[camerabench] n={n}  mean={avg:.4f}  median={med:.4f}  >=0.5: {above50:.1f}%  >=0.7: {above70:.1f}%')
    print(f'[camerabench] min={scores[0]:.4f}  max={scores[-1]:.4f}')


def _collect_pairs(video_dir, descriptions_file):
    if descriptions_file:
        with open(descriptions_file, encoding='utf-8') as f:
            data = json.load(f)
        return [(os.path.join(video_dir, item['video']), item['description']) for item in data]

    pairs = []
    for mp4 in sorted(glob.glob(os.path.join(video_dir, '*.mp4'))):
        basename = os.path.splitext(os.path.basename(mp4))[0]
        # DeepVerse filenames: {safe_prompt}-{sample_idx}-{seed}
        parts = basename.rsplit('-', 2)
        description = parts[0].replace('_', ' ') if len(parts) == 3 else basename.replace('_', ' ')
        pairs.append((mp4, description))
    return pairs


if __name__ == '__main__':
    fire.Fire({'download': download, 'score': score, 'summarize': summarize})
