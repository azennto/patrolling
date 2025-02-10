#!/usr/bin/env python3
"""
maze_agent.py

【仕様】
- 入力：
    ・迷路ファイルのパス
    ・意思決定ポイントの指定方法：
         ① 実験で得た意思決定ポイントが記録されたファイルのパス（各ブロック中に "Coordinates: (x,y)" あり）
         ② またはセミコロン区切りの座標リスト（例："2,3; 5,6; 7,4"）
    ・スタート座標
    ・ゴール座標
- エージェントは以下のルールで移動する：
    1. 現在位置から各意思決定ポイントまでの「マンハッタン距離」を求め、
       最小の距離の候補からさらに「実際に移動する際の総コスト（ダイクストラによる重み付き最短路のコスト）」が最小のものを選択する．
       さらに、候補同士でコストが同じ場合は、「その移動経路上に未探索マス（visited に入っていないセル）があるかどうか」
       で優先順位を付け、さらに複数あればランダムに決定する．
    2. 選んだ意思決定ポイントへは、ダイクストラ法で求めた最短経路に沿って移動する．  
       なお、移動は「1マス移動あたり10 ms」としてシミュレートする．
    3. 目的地に到着したら、「その区間の移動ステップ数＋経路上の各マスの移動コストの和」×10 msだけ待機する．
    4. すべての意思決定ポイントを巡回した後、ゴールへ移動する．  
       ゴールへは、移動開始前に（移動ステップ数＋移動コスト）×10 ms待機した後、10 ms 単位の移動で到着する．
- また、各到達位置では、そのマスから上下左右に連続して伸びる通路を探索済み（visited）とする．
- 最終的に、移動履歴を以下のフォーマットでファイルに書き出す：
      _ 0
      left 150
      up 160
      down 220
      … 
  （最初の行はシミュレータ開始時刻（ここでは 0 ms）を表し、各行は移動方向とその時刻を示す）
"""

import os
import sys
import time
import random
from heapq import heappush, heappop

# --- 補助関数 ---

def parse_coordinate(coord_str):
    """
    "x,y" 形式の文字列をタプル (x, y)（整数）に変換する
    """
    parts = coord_str.split(',')
    if len(parts) != 2:
        raise ValueError("座標は 'x,y' 形式で入力してください．")
    return (int(parts[0].strip()), int(parts[1].strip()))

def load_decision_points_from_file(file_path):
    """
    実験データ形式のファイルから、各ブロック内の "Coordinates: (x,y)" 部分を抽出し
    意思決定ポイントのリストとして返す．
    """
    decision_points = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("Coordinates:"):
                    # 例："Coordinates: (8,16)" → "(8,16)" を抽出
                    coord_part = line.split("Coordinates:")[1].strip()
                    if coord_part.startswith("(") and coord_part.endswith(")"):
                        coord_part = coord_part[1:-1]
                    # カンマ区切りで整数に変換
                    parts = coord_part.split(',')
                    if len(parts) == 2:
                        try:
                            point = (int(parts[0].strip()), int(parts[1].strip()))
                            decision_points.append(point)
                        except ValueError:
                            continue
    except Exception as e:
        print(f"意思決定ポイントファイルの読み込みに失敗しました: {e}")
    return decision_points

# --- エージェント本体 ---

class MazeAgent:
    def __init__(self, maze_file, decision_points, start, goal):
        """
        maze_file       : 迷路仕様ファイルのパス
        decision_points : 意思決定ポイントの座標（リスト of (row, col)）
        start           : スタート位置 (row, col)
        goal            : ゴール位置 (row, col)
        """
        self.maze_file = maze_file
        self.decision_points = decision_points[:]  # コピーしておく
        self.start = start
        self.goal = goal
        self.current_pos = None    # シミュレーション開始後にセット
        self.visited = set()       # 探索済みセルの集合
        self.move_history = []     # (方向, 時刻) のリスト
        self.sim_time = 0          # シミュレーション時刻（ms 単位・相対時間）
        self._read_maze()

    def _read_maze(self):
        """迷路ファイルを読み込み、2次元リスト self.maze に格納する"""
        if not os.path.isfile(self.maze_file):
            raise FileNotFoundError(f"迷路ファイルが見つかりません: {self.maze_file}")
        with open(self.maze_file, 'r', encoding='utf-8') as f:
            self.maze = [list(line.rstrip("\n")) for line in f if line.strip()]
        self.rows = len(self.maze)
        self.cols = len(self.maze[0]) if self.rows > 0 else 0

    def is_traversable(self, pos):
        """pos が迷路内でかつ障害物でないかチェックする"""
        x, y = pos
        if 0 <= x < self.rows and 0 <= y < self.cols:
            return self.maze[x][y] != '#'
        return False

    def cell_cost(self, pos):
        """pos のマスの移動コスト（数字）を返す（数字でなければ None）"""
        x, y = pos
        if self.maze[x][y].isdigit():
            return int(self.maze[x][y])
        return None

    def mark_explored(self, pos):
        """
        現在位置 pos から、上下左右に連続して伸びる（障害物に当たるまで）のセルを
        探索済みとして self.visited に追加する
        """
        x, y = pos
        self.visited.add(pos)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            while 0 <= nx < self.rows and 0 <= ny < self.cols and self.maze[nx][ny].isdigit():
                self.visited.add((nx, ny))
                nx += dx
                ny += dy

    def bfs_path(self, start, goal):
        """
        ダイクストラ法を用いて、start から goal までの「総移動コストが最小」の経路を求める
        各移動は 1 マス移動（実際の移動時間は10 ms としてシミュレーションするが、
        コストとしては1マス移動とし、経路上の各セルに記載の数字を加算）とする

        戻り値：
            path  : 移動方向のリスト（例：['right', 'right', 'up', …]）
            steps : 移動ステップ数（経路の長さ）
            cost  : 経路上（移動先セル）のコスト合計
        到達不能の場合は (None, None, None) を返す
        """
        heap = []
        # (cost_so_far, steps, current_pos, path)
        heappush(heap, (0, 0, start, []))
        visited_local = dict()  # pos -> cost_so_far

        while heap:
            cost, steps, pos, path = heappop(heap)
            if pos in visited_local and visited_local[pos] <= cost:
                continue
            visited_local[pos] = cost
            if pos == goal:
                return path, steps, cost
            for d, (dx, dy) in zip(['up', 'down', 'left', 'right'],
                                     [(-1, 0), (1, 0), (0, -1), (0, 1)]):
                new_pos = (pos[0] + dx, pos[1] + dy)
                if (0 <= new_pos[0] < self.rows and 0 <= new_pos[1] < self.cols and 
                    self.maze[new_pos[0]][new_pos[1]].isdigit()):
                    new_cost = cost + int(self.maze[new_pos[0]][new_pos[1]])
                    heappush(heap, (new_cost, steps + 1, new_pos, path + [d]))
        return None, None, None  # 到達不能の場合

    def compute_manhattan(self, a, b):
        """2点 a, b のマンハッタン距離を返す"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def choose_decision_point(self):
        """
        現在位置 self.current_pos から、残っている意思決定ポイントの中で
        ルールに基づいて次の目的点を決定する

        ルール：
          1. 各候補とのマンハッタン距離を求め、最小の候補群を抽出
          2. その中から、ダイクストラ法で求めた経路の総コストが最小のものを選択
          3. さらに、経路上に「未探索セル」が含まれている候補があれば優先
          4. 複数あればランダムに選択

        戻り値：
            (point, m_dist, cost, unexplored, path, steps)
            ※ point : 候補の座標
                m_dist: マンハッタン距離
                cost  : 経路の総コスト
                unexplored: 経路上に未探索セルがあるか（True/False）
                path, steps: 経路情報
        """
        candidates = []
        for point in self.decision_points:
            m_dist = self.compute_manhattan(self.current_pos, point)
            path, steps, cost = self.bfs_path(self.current_pos, point)
            if path is None:
                continue  # 到達不能なら除外
            # 経路上で、新たに探索できる（visited に入っていない）セルがあるかチェック
            pos = self.current_pos
            has_new = False
            for move in path:
                dx, dy = {'up': (-1, 0), 'down': (1, 0),
                          'left': (0, -1), 'right': (0, 1)}[move]
                pos = (pos[0] + dx, pos[1] + dy)
                if pos not in self.visited:
                    has_new = True
                    break
            candidates.append( (point, m_dist, cost, has_new, path, steps) )
        if not candidates:
            return None
        # (1) マンハッタン距離が最小の候補群
        min_m = min(c[1] for c in candidates)
        filtered = [c for c in candidates if c[1] == min_m]
        # (2) 経路の総コストが最小の候補群
        min_cost = min(c[2] for c in filtered)
        filtered = [c for c in filtered if c[2] == min_cost]
        # (3) 未探索セルを通る経路があれば優先
        if any(c[3] for c in filtered):
            filtered = [c for c in filtered if c[3]]
        # (4) 複数あればランダムに選択
        chosen = random.choice(filtered)
        return chosen  # (point, m_dist, cost, unexplored, path, steps)

    def simulate_path(self, path, path_cost, path_steps, wait_after=True):
        """
        与えられた path（移動方向のリスト）に沿って移動をシミュレートする
         - 各マス移動は 10 ms として move_history に (方向, 時刻) を記録する
         - wait_after が True の場合、移動後に「移動ステップ数＋経路の総コスト」×10 ms 待機する
        """
        for move in path:
            self.sim_time += 20  # 1マス移動：10 ms
            self.move_history.append((move, self.sim_time))
            # 現在位置を更新
            dx, dy = {'up': (-1, 0), 'down': (1, 0),
                      'left': (0, -1), 'right': (0, 1)}[move]
            self.current_pos = (self.current_pos[0] + dx, self.current_pos[1] + dy)
            # 移動先から上下左右に伸びる通路を探索済みとする
            self.mark_explored(self.current_pos)
        if wait_after:
            wait_time = (path_steps + path_cost) * 20
            self.sim_time += wait_time

    def run(self):
        """
        エージェントのシミュレーションを実行する
         1. スタート位置に設定し、探索済みマスを記録
         2. 残る意思決定ポイントがある間、ルールに従い次の候補点を選択し移動
         3. 全意思決定ポイントを巡回後、ゴールへ移動（移動前に待機）
        """
        # スタートに設定し、探索済みマスを記録
        self.current_pos = self.start
        self.sim_time = 0
        self.move_history = []
        self.visited = set()
        self.mark_explored(self.current_pos)
        
        # 意思決定ポイントをすべて巡回
        while self.decision_points:
            candidate = self.choose_decision_point()
            if candidate is None:
                print("到達可能な意思決定ポイントがありません．")
                break
            point, m_dist, cost, unexplored, path, steps = candidate
            # シミュレーション：候補点へ移動
            self.simulate_path(path, cost, steps, wait_after=True)
            # 巡回済みとする
            self.decision_points.remove(point)
        
        # 全意思決定ポイント巡回後、ゴールへ移動
        path, steps, cost = self.bfs_path(self.current_pos, self.goal)
        if path is None:
            print("ゴールへ到達できませんでした．")
            return
        # ゴール移動前に待機（移動ステップ数＋移動コスト）×10 ms
        self.sim_time += (steps + cost) * 10
        # ゴールへ向けて移動（移動後の待機は不要）
        self.simulate_path(path, cost, steps, wait_after=False)
    
    def save_move_history(self, filename):
        """
        移動履歴を指定のファイルに出力する
        出力フォーマット：
            _ 0
            left 150
            up 160
            …
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"_ 0\n")
            for move, t in self.move_history:
                f.write(f"{move} {t}\n")
        print(f"移動履歴を {filename} に保存しました．")

# --- main ---

def main():
    print("【エージェント・迷路自動解答プログラム】")
    # 迷路ファイルのパス
    maze_file = input("迷路ファイルのパスを入力してください： ").strip()
    
    # 意思決定ポイントの指定方法
    dp_file = input("意思決定ポイントのファイルパスを入力してください（省略可）： ").strip()
    if dp_file:
        if os.path.isfile(dp_file):
            decision_points = load_decision_points_from_file(dp_file)
            if decision_points:
                print(f"{len(decision_points)} 個の意思決定ポイントを読み込みました。")
            else:
                print("ファイルから意思決定ポイントを取得できませんでした。手入力に切り替えます。")
                dp_str = input("意思決定ポイントの座標をセミコロン区切りで入力してください（例: 2,3; 5,6; 7,4）： ").strip()
                decision_points = [parse_coordinate(s) for s in dp_str.split(';') if s.strip()]
        else:
            print("指定された意思決定ポイントファイルが存在しません。手入力に切り替えます。")
            dp_str = input("意思決定ポイントの座標をセミコロン区切りで入力してください（例: 2,3; 5,6; 7,4）： ").strip()
            decision_points = [parse_coordinate(s) for s in dp_str.split(';') if s.strip()]
    else:
        dp_str = input("意思決定ポイントの座標をセミコロン区切りで入力してください（例: 2,3; 5,6; 7,4）： ").strip()
        decision_points = [parse_coordinate(s) for s in dp_str.split(';') if s.strip()]
    
    # スタート座標、ゴール座標の入力
    start_str = input("スタート座標を (x,y) 形式で入力してください： ").strip()
    start = parse_coordinate(start_str)
    goal_str = input("ゴール座標を (x,y) 形式で入力してください： ").strip()
    goal = parse_coordinate(goal_str)
    
    # エージェント初期化・シミュレーション実行
    agent = MazeAgent(maze_file, decision_points, start, goal)
    agent.run()
    
    # 移動履歴をファイルへ出力（例：agent_move_history.txt）
    out_filename = "agent_move_history.txt"
    agent.save_move_history(out_filename)

if __name__ == "__main__":
    main()
