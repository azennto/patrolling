# maze_replay.py
import pygame
import time
import sys
from pathlib import Path
import tkinter as tk
import os

pygame.init()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
CYAN = (0, 255, 255)
GRAY = (192, 192, 192)

TILE_SIZE = 40

def generate_unique_filename(directory, filename):
    """重複を避けるためのファイル名生成"""
    os.makedirs(directory, exist_ok=True)  # ディレクトリが無ければ作成
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = os.path.join(directory, f"{base}{ext}")
    while os.path.exists(new_filename):
        new_filename = os.path.join(directory, f"{base}_{counter}{ext}")
        counter += 1
    return new_filename

def ask_operation_and_reason_window(direction, wait_time, timestamp_ms):
    """
    0.5秒以上待ちが発生した際に表示するウィンドウ。
    1) 次にどんな操作をしたか
    2) その操作の理由
    を入力してもらうフォームを Tkinter で作成。

    OK ボタン押下までブロッキングし、押下後にウィンドウを閉じる。
    """
    root = tk.Tk()
    root.title("操作の記録")

    label_op = tk.Label(
        root, 
        text=(
            f"次の移動 ({direction}) が行われるまで {wait_time:.2f}秒待ちが発生しました。\n"
            "1) 次にどんな操作をしたかを入力してください。"
        )
    )
    label_op.pack(padx=10, pady=10)

    text_box_op = tk.Text(root, width=50, height=3)
    text_box_op.pack(padx=10, pady=5)

    label_reason = tk.Label(root, text="2) その操作の理由を入力してください。")
    label_reason.pack(padx=10, pady=10)

    text_box_reason = tk.Text(root, width=50, height=5)
    text_box_reason.pack(padx=10, pady=5)

    container = {"operation": None, "reason": None}

    def on_submit():
        container["operation"] = text_box_op.get("1.0", tk.END).strip()
        container["reason"] = text_box_reason.get("1.0", tk.END).strip()
        root.destroy()

    submit_btn = tk.Button(root, text="OK", command=on_submit)
    submit_btn.pack(pady=5)

    # ウィンドウを表示し、ユーザ入力を待つ (ブロッキング)
    root.mainloop()

    return container["operation"], container["reason"]

# def save_operation_and_reason_with_metadata(filepath, operation, reason, direction, timestamp_ms, wait_time):
#     """
#     ユーザが入力した操作内容とその理由、およびメタデータをファイルに保存する。
#     ここで、常に同じファイル（operation_reason_log.txt）に追記する。
#     """
# 
#     # 'a' (append) モードで開いて、回答を追記していく
#     with open(filepath, 'a', encoding='utf-8') as f:
#         f.write(f"Direction: {direction}\n")
#         f.write(f"Timestamp(ms): {timestamp_ms}\n")
#         f.write(f"WaitTime(s): {wait_time:.3f}\n")
#         f.write(f"Operation: {operation}\n")
#         f.write(f"Reason: {reason}\n")
#         f.write("-------\n")
# 
#     print(f"Operation and reason appended to {filepath}.")

def save_operation_and_reason_with_metadata(filepath, operation, reason, direction, timestamp_ms, wait_time, coordinates):
    """
    ユーザが入力した操作内容とその理由、およびメタデータをファイルに保存する。
    座標情報を追加
    """
    x, y = coordinates  # 座標のアンパック
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(f"Direction: {direction}\n")
        f.write(f"Timestamp(ms): {timestamp_ms}\n")
        f.write(f"WaitTime(s): {wait_time:.3f}\n")
        f.write(f"Coordinates: ({x},{y})\n")  # 座標情報追加
        f.write(f"Operation: {operation}\n")
        f.write(f"Reason: {reason}\n")
        f.write("-------\n")

class MazeReplay:
    def __init__(self, maze_file, replay_file):
        if not pygame.get_init():
            pygame.init()

        self.load_maze(maze_file)
        self.load_replay(replay_file)
        self.player_position = self.start
        self.visited = set()
        self.total_cost = 0
        self.mark_explored()

        self.font = pygame.font.Font(None, 24)

        directory = "exp_data/reasons"
        self.filepath = generate_unique_filename(directory, "operation_reason_log.txt")

    def load_maze(self, maze_file):
        with open(maze_file, 'r') as f:
            self.maze = [list(line.strip()) for line in f.readlines()]
        self.rows = len(self.maze)
        self.cols = len(self.maze[0])
        self.start = self.find_start()

    def find_start(self):
        for i, row in enumerate(self.maze):
            for j, cell in enumerate(row):
                if cell == '5':
                    return (i, j)
        raise ValueError("Start position not found in the maze file.")

    def load_replay(self, replay_file):
        if not Path(replay_file).is_file():
            raise FileNotFoundError(f"Replay file not found: {replay_file}")
        
        self.replay_data = []
        with open(replay_file, 'r') as f:
            lines = f.readlines()
            if lines[0].startswith('_'):
                self.start_time = int(lines[0].split()[1])
                lines = lines[1:]
            else:
                raise ValueError("Replay file does not contain a start_time.")
            
            for line in lines:
                direction, timestamp_ms, *_ = line.strip().split()
                self.replay_data.append((direction, int(timestamp_ms)))

    def mark_explored(self):
        """現在のマスと上下左右に伸びる連続した数字マスを探索済みにする"""
        x, y = self.player_position
        self.visited.add((x, y))
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            while 0 <= nx < self.rows and 0 <= ny < self.cols and self.maze[nx][ny].isdigit():
                self.visited.add((nx, ny))
                nx += dx
                ny += dy

    def move(self, direction):
        """プレイヤーを指定方向へ移動し、コストを加算する"""
        x, y = self.player_position
        new_position = {
            'up':    (x - 1, y),
            'left':  (x, y - 1),
            'down':  (x + 1, y),
            'right': (x, y + 1)
        }.get(direction, (x, y))

        nx, ny = new_position
        # 壁でない場合のみ移動
        if 0 <= nx < self.rows and 0 <= ny < self.cols and self.maze[nx][ny] != '#':
            cost = int(self.maze[nx][ny]) if self.maze[nx][ny].isdigit() else 0
            self.total_cost += cost
            print(f"Moved {direction}. Cost: {cost}, Total Cost: {self.total_cost}")

            self.player_position = new_position
            self.mark_explored()

    def draw_maze(self, screen):
        """迷路とプレイヤー、探索状況を描画"""
        for i, row in enumerate(self.maze):
            for j, cell in enumerate(row):
                x = j * TILE_SIZE
                y = i * TILE_SIZE

                if (i, j) == self.start:
                    color = RED
                elif (i, j) == self.player_position:
                    color = YELLOW
                elif (i, j) in self.visited:
                    color = GRAY
                elif cell.isdigit():
                    color = CYAN
                else:
                    color = BLACK

                pygame.draw.rect(screen, color, (x, y, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(screen, WHITE, (x, y, TILE_SIZE, TILE_SIZE), 1)

                # 数字セルの場合はコストを描画
                if cell.isdigit():
                    text = self.font.render(cell, True, WHITE if color == CYAN else BLACK)
                    text_rect = text.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))
                    screen.blit(text, text_rect)

    def draw_cost(self, screen, screen_height):
        """画面下部に総コストを描画"""
        pygame.draw.rect(screen, BLACK, (0, screen_height - 40, screen.get_width(), 40))
        cost_text = self.font.render(f"Total Cost: {self.total_cost}", True, WHITE)
        screen.blit(cost_text, (10, screen_height - 30))

    def replay(self):
        """リプレイを再生する"""
        screen_width = self.cols * TILE_SIZE
        screen_height = self.rows * TILE_SIZE + 40
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Maze Replay")

        clock = pygame.time.Clock()
        running = True

        for i, (direction, timestamp_ms) in enumerate(self.replay_data):
            if not running:
                break

            # 前回の移動時刻 or start_time からの差分 (秒)
            previous_timestamp = self.start_time if i == 0 else self.replay_data[i - 1][1]
            wait_time = (timestamp_ms - previous_timestamp) / 1000.0

            # 待機時間が 0.5秒以上ならば一時停止して操作内容・理由入力
            if wait_time >= 0.5:
                operation, reason = ask_operation_and_reason_window(direction, wait_time, timestamp_ms)
                if operation.strip() or reason.strip():
                    # 現在の座標を取得（移動前の位置）
                    current_coords = self.player_position
                    save_operation_and_reason_with_metadata(
                        self.filepath, 
                        operation, 
                        reason, 
                        direction, 
                        timestamp_ms, 
                        wait_time,
                        current_coords  # 座標情報を追加
                    )

            # 実際に再生上は wait_time だけ停止
            start_time_loop = time.time()

            # 現在の状況を描画して表示
            screen.fill(BLACK)
            self.draw_maze(screen)
            self.draw_cost(screen, screen_height)
            pygame.display.flip()

            # 指定の待機時間が経過するまでループ
            while time.time() - start_time_loop < wait_time:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break
                clock.tick(30)

            # 移動を実行
            self.move(direction)

        # 最後に少し待ってから終了
        time.sleep(1)
        pygame.quit()
