import random
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import os

def generate_random_maze(N=17):
    """
    ランダムな迷路を生成する関数
    :param N: 迷路のサイズ (奇数)
    :return: 迷路を表す2次元リスト
    """
    maze = [['#' for _ in range(N)] for _ in range(N)]
    K = random.randint(N, 2 * N)

    for _ in range(K):
        d = random.randint(0, 1)
        i = random.randint(0, (N - 1) // 2) * 2
        j = random.randint(0, N - 1)
        h = random.randint(3, 10)
        w = str(random.randint(5, 9))

        for k in range(max(j - h, 0), min(j + h, N - 1) + 1):
            if d == 0:
                maze[i][k] = w
            else:
                maze[k][i] = w

    return maze

def count_apparent_paths(maze):
    """
    見かけ上の道の本数をカウントする関数
    :param maze: 迷路を表す2次元リスト
    :return: 見かけ上の道の本数
    """
    rows = len(maze)
    cols = len(maze[0])
    apparent_paths = 0

    # 各行を調査
    for i in range(rows):
        j = 0
        while j < cols:
            if maze[i][j].isdigit():
                count = 0
                # 道を発見したら右方向に進み続ける
                while j < cols and maze[i][j].isdigit():
                    count += 1
                    j += 1
                if count > 1:
                    apparent_paths += 1
            j += 1

    # 各列を調査
    for j in range(cols):
        i = 0
        while i < rows:
            if maze[i][j].isdigit():
                count = 0
                # 道を発見したら下方向に進み続ける
                while i < rows and maze[i][j].isdigit():
                    count += 1
                    i += 1
                if count > 1:
                    apparent_paths += 1
            i += 1

    return apparent_paths

def save_maze(maze, filename):
    """
    迷路を指定のフォーマットで保存する関数
    :param maze: 迷路を表す2次元リスト
    :param filename: 保存先のファイル名
    """
    with open(filename, 'w') as f:
        for row in maze:
            f.write(''.join(row) + '\n')
    print(f"Saved maze to {filename}")

def main():
    N = 10000  # 迷路を生成する回数
    maze_size = 9 * 2 - 1  # 迷路のサイズ (奇数)
    path_counts = []

    # 迷路生成とカウント
    mazes = []
    for _ in tqdm(range(N)):
        maze = generate_random_maze(maze_size)
        path_count = count_apparent_paths(maze)
        path_counts.append(path_count)
        mazes.append((path_count, maze))

    # 四分位数を計算
    q25, q50, q75 = np.percentile(path_counts, [25, 50, 75])
    print(f"### Quartiles ###")
    print(f"25th Percentile (Q1): {q25}")
    print(f"50th Percentile (Median, Q2): {q50}")
    print(f"75th Percentile (Q3): {q75}")

    # 保存する迷路を選択
    quartiles = [q25, q50, q75]
    output_dir = "quartile_mazes"
    os.makedirs(output_dir, exist_ok=True)
    for q_idx, q in enumerate(quartiles, start=1):
        selected = [maze for path_count, maze in mazes if path_count == q]
        if len(selected) < 5:
            print(f"Warning: Less than 5 mazes found for Q{q_idx}. Found {len(selected)}.")
            selected = selected[:5]
        else:
            selected = selected[:5]
        
        for i, maze in enumerate(selected):
            filename = os.path.join(output_dir, f"maze_Q{q_idx}_{i+1}.txt")
            save_maze(maze, filename)

    # ヒストグラムをプロット
    plt.hist(path_counts, bins=range(min(path_counts), max(path_counts) + 1), edgecolor='black')
    plt.title("Distribution of Apparent Paths in Random Mazes")
    plt.xlabel("Number of Apparent Paths")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.show()

if __name__ == '__main__':
    main()
