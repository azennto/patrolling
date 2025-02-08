# main_experiment.py
import sys
from maze_game import MazeGame
from maze_replay import MazeReplay
import os
import pygame

def main():
    pygame.init()
    # 1) ゲームをプレイ
    # 引数に迷路ファイルがあればそれを使用し、なければランダム迷路を生成
    maze_file = sys.argv[1] if len(sys.argv) > 1 else None
    game = MazeGame(maze_file)
    game.play()  # プレイ後に移動履歴が exp_data/move_history に保存される

    # 2) ゲームの移動履歴ファイルを探す (例: move_history.txt の最後に生成されたもの)
    #   本サンプルでは MazeGame 側が "move_history.txt" という固定名で保存するため、
    #   exp_data/move_history フォルダ内から一番新しいファイルを選ぶイメージ。
    move_history_dir = "exp_data/move_history"
    files = [os.path.join(move_history_dir, f) for f in os.listdir(move_history_dir) if f.startswith("move_history")]
    if not files:
        print("No move_history file found. Exiting.")
        return

    # 更新時刻が最新のものを取り出す
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    newest_move_history = files[0]
    print(f"Using move_history file: {newest_move_history}")

    # 3) リプレイを流す
    #   - 0.5秒以上の待機時間があれば理由入力ウィンドウを表示
    #   - ユーザが入力した理由をメタデータ付きで保存
    replay = MazeReplay(maze_file if maze_file else game.generated_filename, newest_move_history)
    replay.replay()

if __name__ == "__main__":
    main()
