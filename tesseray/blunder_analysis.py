import chess.engine
import chess.pgn
import os
import logging
import re
import datetime
from multiprocessing import Pool, cpu_count
from dataclasses import dataclass

flag = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs('logs', exist_ok=True)

logging.basicConfig(filename=f'logs/blunder_analysis_{flag}.log', level=logging.INFO, format='%(message)s')

@dataclass
class GameInfo:
    stockfish_path: str
    blunder_threshold: int
    file: str
    game: chess.pgn.Game
    game_num: int
    blunder_definition: str

def analyze_game(game_info: GameInfo):
    engine = chess.engine.SimpleEngine.popen_uci(game_info.stockfish_path)

    board = game_info.game.board()
    game_key = f'{game_info.file}-{game_info.game.headers["Event"]}-{game_info.game_num}'
    blunders = []
    previous_info = None

    time_control = game_info.game.headers.get("TimeControl", "")
    initial_time = int(time_control.split("+")[0]) if "+" in time_control else None

    for node in game_info.game.mainline():
        move = node.move

        if previous_info is not None:
            best_move = previous_info["pv"][0]
            best_score = previous_info["score"].relative.score() if previous_info["score"] else None

            info = engine.analyse(board, chess.engine.Limit(depth=15))
            score = info["score"].relative.score() if info["score"] else None

            if game_info.blunder_definition == "bad_move":
                if best_move != move and score is not None and best_score is not None and best_score - score > game_info.blunder_threshold:
                    timestamp = get_timestamp(node.comment, initial_time)
                    blunders.append((board.fen(), move.uci(), best_move.uci(), score, timestamp))
            elif game_info.blunder_definition == "evaluation_drop":
                # define "evaluation_drop"
                pass

        board.push(move)
        previous_info = engine.analyse(board, chess.engine.Limit(depth=15))

    engine.quit()
    return game_key, blunders

def get_timestamp(comment, initial_time):
    # Extract the remaining time from the comment
    match = re.search(r'\[%clk\\n(\d+):(\d+):(\d+\.\d+)\]', comment)
    if match is None:
        return None
    else:
        # Convert the time to seconds
        hours, minutes, seconds = map(float, match.groups())
        remaining_time = hours * 3600 + minutes * 60 + seconds

        if initial_time is None:
            return None
        else:
            # Calculate the time remaining as a percentage of the initial time
            time_remaining = initial_time - remaining_time
            time_remaining_percentage = (time_remaining / initial_time) * 100
            return f"{time_remaining_percentage:.2f}%"

def find_blunders(pgn_dir_path, stockfish_path, blunder_definition="bad_move", blunder_threshold=150):
    game_infos = []
    
    def load_games():
        for root, _, files in os.walk(pgn_dir_path):
            for file in files:
                if file.endswith('.pgn'):
                    pgn_file_path = os.path.join(root, file)
                    with open(pgn_file_path) as pgn:
                        game_num = 1
                        while True:
                            game = chess.pgn.read_game(pgn)
                            if game is None:
                                break
                            
                            yield GameInfo(stockfish_path, blunder_threshold, file, game, game_num, blunder_definition)
                            game_num += 1

    with Pool(cpu_count()) as p:
        blunders = dict(p.map(analyze_game, load_games()))

    return blunders

if __name__ == '__main__':
    stockfish_path = "engines/stockfish"
    pgn_dir_path = "test_data"
    blunders = find_blunders(pgn_dir_path, stockfish_path, blunder_definition="bad_move")
    for game, game_blunders in blunders.items():
        logging.info(f"In game {game}, there were {len(game_blunders)} blunders.")
        print(f"In game {game}, there were {len(game_blunders)} blunders.")
        for blunder in game_blunders:
            logging.info(f"FEN: {blunder[0]}, Actual Move: {blunder[1]}, Best Move: {blunder[2]}, Score: {blunder[3]}, Time Remaining: {blunder[4]}")