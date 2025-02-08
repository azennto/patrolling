# maze_game.py
import pygame
import random
import time
import sys
import os
from pathlib import Path

# Pygameの初期化
pygame.init()

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
CYAN = (0, 255, 255)
GRAY = (192, 192, 192)

# マス目のサイズ
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

class MazeGame:
    def __init__(self, maze_file=None):
        if maze_file and Path(maze_file).is_file():
            self.load_maze(maze_file)
        else:
            print("Maze file not found. Generating a random maze...")
            self.generate_random_maze()
            self.generated_filename = self.save_maze("generated_maze.txt")
            self.load_maze(self.generated_filename)

        self.player_position = self.start
        self.visited = set()  # 探索済みマスを記録
        self.move_history = []  # 移動履歴
        self.start_time_ms = int(time.time() * 1000)  # 記録開始時間（エポックミリ秒）
        self.total_cost = 0  # 総コストの初期化
        self.mark_explored()

        # フォントの初期化
        self.font = pygame.font.Font(None, 24)

    def load_maze(self, maze_file):
        with open(maze_file, 'r') as f:
            self.maze = [list(line.strip()) for line in f.readlines()]
        self.rows = len(self.maze)
        self.cols = len(self.maze[0])
        self.start = self.find_start()

    def find_start(self):
        for i, row in enumerate(self.maze):
            for j, cell in enumerate(row):
                if cell.isdigit() and cell == '5':  # '5' をスタート地点とする
                    return (i, j)
        raise ValueError("Start position not found in the maze file.")

    def generate_random_maze(self):
        N = 9 * 2 - 1
        self.maze = [['#' for _ in range(N)] for _ in range(N)]
        K = random.randint(N, 2*N)

        for _ in range(K):
            d = random.randint(0, 1)
            i = random.randint(0, (N - 1) // 2) * 2
            j = random.randint(0, N - 1)
            h = random.randint(3, 10)
            w = str(random.randint(5, 9))

            for k in range(max(j - h, 0), min(j + h, N - 1) + 1):
                if d == 0:
                    self.maze[i][k] = w
                else:
                    self.maze[k][i] = w

        # スタート地点を設定
        valid_positions = [(i, j) for i in range(N) for j in range(N) if self.maze[i][j].isdigit()]
        self.start = random.choice(valid_positions)
        self.maze[self.start[0]][self.start[1]] = '5'  # スタート地点を '5' に設定

    def save_maze(self, filename):
        """迷路を保存"""
        directory = "exp_data/maze"
        filename = generate_unique_filename(directory, filename)
        with open(filename, 'w') as f:
            for row in self.maze:
                f.write(''.join(row) + '\n')
        print(f"Generated maze saved to {filename}.")
        return filename

    def mark_explored(self):
        """現在のマスから縦横に伸びるマスを探索済みにする"""
        x, y = self.player_position
        self.visited.add((x, y))
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            while 0 <= nx < self.rows and 0 <= ny < self.cols and self.maze[nx][ny].isdigit():
                self.visited.add((nx, ny))
                nx += dx
                ny += dy

    def move(self, direction):
        x, y = self.player_position
        new_position = {
            'up': (x - 1, y),
            'left': (x, y - 1),
            'down': (x + 1, y),
            'right': (x, y + 1)
        }.get(direction, (x, y))

        nx, ny = new_position
        if 0 <= nx < self.rows and 0 <= ny < self.cols and self.maze[nx][ny] != '#':
            # 現在のエポックミリ秒を記録
            current_time_ms = int(time.time() * 1000)
            self.move_history.append((direction, current_time_ms))

            # 移動コストを加算
            cost = int(self.maze[nx][ny]) if self.maze[nx][ny].isdigit() else 0
            self.total_cost += cost
            print(f"Moved {direction}. Cost: {cost}, Total Cost: {self.total_cost}")

            # プレイヤーを移動
            self.player_position = new_position
            self.mark_explored()

    def save_history(self, filename):
        """移動履歴を保存（500ms以上の間隔に#カウント追加）"""
        directory = "exp_data/move_history"
        filename = generate_unique_filename(directory, filename)
        
        with open(filename, 'w') as f:
            f.write(f'_ {self.start_time_ms}\n')
            prev_time = self.start_time_ms
            gap_count = 0  # 500ms以上間隔が空いた回数
            
            for direction, timestamp_ms in self.move_history:
                # 前回移動からの経過時間を計算
                elapsed = timestamp_ms - prev_time
                line = f"{direction} {timestamp_ms}"
                
                # 500ms以上の間隔があればカウントを追加
                if elapsed >= 500:
                    gap_count += 1
                    line += f" #{gap_count}"
                
                f.write(line + '\n')
                prev_time = timestamp_ms  # 前回時刻を更新
        
        print(f"Move history saved to {filename}.")

    #def save_history(self, filename):
    #    """移動履歴を保存"""
    #    directory = "exp_data/move_history"
    #    filename = generate_unique_filename(directory, filename)
    #    with open(filename, 'w') as f:
    #        f.write(f'_ {self.start_time_ms}\n')
    #        for direction, timestamp_ms in self.move_history:
    #            f.write(f'{direction} {timestamp_ms}\n')
    #    print(f"Move history saved to {filename}.")

    def is_goal_reached(self):
        """ゴール条件をチェック"""
        total_cells = sum(1 for row in self.maze for cell in row if cell.isdigit())
        return self.player_position == self.start and len(self.visited) == total_cells

    def draw_maze(self, screen):
        """迷路を描画"""
        for i, row in enumerate(self.maze):
            for j, cell in enumerate(row):
                x = j * TILE_SIZE
                y = i * TILE_SIZE

                # 背景色を決定
                if (i, j) == self.start:
                    color = RED  # ゴールは赤
                elif (i, j) == self.player_position:
                    color = YELLOW  # プレイヤーは黄色
                elif (i, j) in self.visited:
                    color = GRAY  # 探索済みマスは灰色
                elif cell.isdigit():
                    color = CYAN  # 未探索マスは青
                else:
                    color = BLACK  # 障害物は黒

                # マスを描画
                pygame.draw.rect(screen, color, (x, y, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(screen, WHITE, (x, y, TILE_SIZE, TILE_SIZE), 1)

                # 移動コストを表示
                if cell.isdigit():
                    text = self.font.render(cell, True, WHITE if color == CYAN else BLACK)
                    text_rect = text.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))
                    screen.blit(text, text_rect)

    def play(self):
        """ゲームループ"""
        screen_width = self.cols * TILE_SIZE
        screen_height = self.rows * TILE_SIZE
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Maze Game")

        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.move('up')
                    elif event.key == pygame.K_DOWN:
                        self.move('down')
                    elif event.key == pygame.K_LEFT:
                        self.move('left')
                    elif event.key == pygame.K_RIGHT:
                        self.move('right')

            # ゴール達成のチェック
            if self.is_goal_reached():
                print("Congratulations! You've completed the maze.")
                print(f"Total Cost: {self.total_cost}")
                self.save_history('move_history.txt')
                running = False

            screen.fill(BLACK)
            self.draw_maze(screen)
            pygame.display.flip()
            clock.tick(30)

        # 終了処理
        pygame.quit()
