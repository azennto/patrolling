import pygame
import time
import sys
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
class MazeReplay:
    def __init__(self, maze_file, replay_file):
        # 迷路をロード
        self.load_maze(maze_file)
        # リプレイデータをロード
        self.load_replay(replay_file)
        self.player_position = self.start
        self.visited = set()  # 探索済みのマスを記録
        self.total_cost = 0  # 総コストの初期化
        self.mark_explored()

        # フォントを初期化
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
                if cell == '5':  # スタート位置を示す
                    return (i, j)
        raise ValueError("Start position not found in the maze file.")

    def load_replay(self, replay_file):
        """リプレイデータをロード"""
        if not Path(replay_file).is_file():
            raise FileNotFoundError(f"Replay file not found: {replay_file}")
        
        self.replay_data = []
        with open(replay_file, 'r') as f:
            lines = f.readlines()
            # 最初の行は開始時間
            if lines[0].startswith('_'):
                self.start_time = int(lines[0].split()[1])
                lines = lines[1:]  # 残りの移動履歴を処理
            else:
                raise ValueError("Replay file does not contain a start_time.")
            
            for line in lines:
                direction, timestamp_ms = line.strip().split()
                self.replay_data.append((direction, int(timestamp_ms)))

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
            # 移動コストを加算
            cost = int(self.maze[nx][ny]) if self.maze[nx][ny].isdigit() else 0
            self.total_cost += cost
            print(f"Moved {direction}. Cost: {cost}, Total Cost: {self.total_cost}")

            self.player_position = new_position
            self.mark_explored()

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

    def draw_cost(self, screen, screen_height):
        """総コストを画面上に描画"""
        pygame.draw.rect(screen, BLACK, (0, screen_height - 40, screen.get_width(), 40))  # コスト表示用の背景
        cost_text = self.font.render(f"Total Cost: {self.total_cost}", True, WHITE)
        screen.blit(cost_text, (10, screen_height- 30))  # 画面下に表示

    def replay(self):
        """リプレイを再現"""
        screen_width = self.cols * TILE_SIZE
        screen_height = self.rows * TILE_SIZE + 40
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Maze Replay")

        clock = pygame.time.Clock()
        running = True

        # 開始時刻を基準に再現
        for i, (direction, timestamp_ms) in enumerate(self.replay_data):
            if not running:
                break
            # 最初の移動か、それ以降の差分で待機時間を計算
            previous_timestamp = self.start_time if i == 0 else self.replay_data[i - 1][1]
            wait_time = (timestamp_ms - previous_timestamp) / 1000.0

            start_time = time.time()
            self.move(direction)

            # 描画
            screen.fill(BLACK)
            self.draw_maze(screen)
            self.draw_cost(screen, screen_height)
            pygame.display.flip()

            # 指定された時間だけ待機
            while time.time() - start_time < wait_time:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break
                clock.tick(30)

        # リプレイ終了
        time.sleep(1)
        pygame.quit()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python replay.py <maze_file> <replay_file>")
        sys.exit(1)

    maze_file = sys.argv[1]
    replay_file = sys.argv[2]

    replay = MazeReplay(maze_file, replay_file)
    replay.replay()
