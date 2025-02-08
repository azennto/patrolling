#!/usr/bin/env python3
import sys
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TABLEAU_COLORS

def process_file(file_path):
    timestamps_ms = []
    with open(file_path, 'r') as f:
        for line in f:
            tokens = line.strip().split()
            if len(tokens) != 2:
                continue
            try:
                timestamps_ms.append(int(tokens[1]))
            except (ValueError, IndexError):
                continue
    return timestamps_ms

def main():
    if len(sys.argv) != 2:
        print("Usage: ./script.py <directory_or_file_path>")
        return

    path = sys.argv[1]
    
    # データ収集
    all_diffs = []
    file_data = []
    
    if os.path.isfile(path):  # ファイル指定の場合
        data = process_file(path)
        if len(data) >= 2:
            diffs = [(data[j] - data[j-1])/1000.0 for j in range(1, len(data))]
            all_diffs.extend(diffs)
            file_data.append((os.path.basename(path), data))
    
    elif os.path.isdir(path):  # ディレクトリ指定の場合
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            if os.path.isfile(file_path):
                data = process_file(file_path)
                if len(data) >= 2:
                    diffs = [(data[j] - data[j-1])/1000.0 for j in range(1, len(data))]
                    all_diffs.extend(diffs)
                    file_data.append((filename, data))
    
    else:
        print(f"Error: {path} is not a valid file or directory")
        return
    
    if not file_data:
        print("有効なデータを含むファイルが見つかりませんでした")
        return

    plt.figure(figsize=(12, 8))
    colors = list(TABLEAU_COLORS.keys())

    # (1) ヒストグラム（単一ファイル/複数ファイル合算）
    plt.subplot(2, 1, 1)
    max_diff = max(all_diffs) if all_diffs else 1
    bins = np.arange(0, max_diff + 1, 0.25)
    
    hist_color = 'skyblue' if len(file_data) > 1 else colors[0]
    plt.hist(all_diffs, bins=bins, edgecolor='black', align='mid',
             color=hist_color, alpha=0.8, zorder=3)
    
    title_suffix = "(Combined)" if len(file_data) > 1 else "(Single File)"
    plt.title(f"Thinking Time Histogram {title_suffix}")
    plt.xlabel("Thinking time per move (seconds)")
    plt.ylabel("Frequency")
    plt.grid(axis='y', linestyle='--', alpha=0.7, zorder=0)
    plt.xticks(bins, rotation=45)

    # (2) 累積折れ線グラフ
    plt.subplot(2, 1, 2)
    
    for i, (filename, data) in enumerate(file_data):
        start_ms = data[0]
        elapsed = [(ts - start_ms)/1000.0 for ts in data]
        diffs = [(data[j] - data[j-1])/1000.0 for j in range(1, len(data))]
        cum_diffs = np.cumsum(diffs)
        
        step_x = elapsed
        step_y = [0] + list(cum_diffs)
        
        line_color = colors[i % len(colors)] if len(file_data) > 1 else colors[0]
        label = filename if len(file_data) > 1 else "Single File"
        
        plt.step(step_x, step_y, where='post', 
                 color=line_color,
                 label=f'{label} (Total: {cum_diffs[-1]:.1f}s)')
        
        for j, diff in enumerate(diffs):
            if diff >= 0.5:
                plt.plot(step_x[j+1], step_y[j+1], 'o', 
                         color=line_color,
                         markersize=8, alpha=0.7)

    plt.title("Cumulative Thinking Time" + 
              (" Comparison" if len(file_data) > 1 else ""))
    plt.xlabel("Elapsed Time from start (mm:ss)")
    plt.ylabel("Cumulative Time (seconds)")
    plt.grid(True)
    plt.legend()

    # X軸フォーマット変換
    ax = plt.gca()
    x_vals = ax.get_xticks()
    ax.set_xticklabels([f"{int(x//60)}:{int(x%60):02d}" for x in x_vals])

    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()