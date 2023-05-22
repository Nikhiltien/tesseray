import chess.engine
import chess.pgn
import os
import multiprocessing
import csv
from datetime import datetime

def log_blunders(csv_dir, all_blunders):
    flag = datetime.now().strftime('%Y%m%d%H%M%S')
    csv_file = os.path.join(csv_dir, f"blunder_check_{flag}.csv")

    with open(csv_file, 'w', newline='') as csv_f:
        writer = csv.writer(csv_f)
        writer.writerow(["game_file", "game_id", "move_type", "move_number", "actual_move", "best_move"])
        for game_header, blunders_list in all_blunders:
            game_info = game_header.split(", Game ID: ")
            game_file, game_id = game_info[0].split(": ")[1], game_info[1]
            for blunder in blunders_list:
                blunder_info = blunder.split(', Best move: ')
                move_info = blunder_info[0].split(": ")
                move_type, actual_move_full = move_info[0], move_info[1]
                move_number, actual_move = actual_move_full.split('. ')
                best_move = blunder_info[1]
                writer.writerow([game_file, game_id, move_type, move_number, actual_move, best_move])

def game_generator(pgn_file):
    with open(pgn_file) as f:
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break
            yield game

def evaluate_game(pgn_file, stockfish_path, limit=150):
    blunders = []

    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

    game_id = 0  # Identifier for each game in a file
    for game in game_generator(pgn_file):
        game_id += 1  
        game_blunders = []
        node = game
        game_header = f"Game File: {pgn_file}, Game ID: {game_id}\n"
        best_move = None
        while not node.is_end():
            next_node = node.variations[0]
            move = next_node.move

            # Evaluate the position before the move
            result = engine.analyse(node.board(), chess.engine.Limit(depth=10))
            score_before = result["score"].relative.score()
            if score_before is None:
                # Mate in x situation
                score_before = (30000 if result["score"].relative.is_mate() else 0)

            # Find the best move before the blunder
            if best_move is None:
                best_move_result = engine.play(node.board(), chess.engine.Limit(depth=10))
                best_move = best_move_result.move

            # Evaluate the position after the move
            result = engine.analyse(next_node.board(), chess.engine.Limit(depth=10))
            score_after = result["score"].relative.score()
            if score_after is None:
                # Mate in x situation
                score_after = (30000 if result["score"].relative.is_mate() else 0)

            if abs(score_before + score_after) > limit:
                move_number = (node.ply() + 1) // 2
                if node.board().turn:
                    move_notation = f"{move_number}. {node.board().san(move)}"
                else:
                    move_notation = f"{move_number}. ...{node.board().san(move)}"
                best_move_notation = node.board().san(best_move)
                blunder_msg = f"??: {move_notation}, Best move: {best_move_notation}"
                game_blunders.append(blunder_msg)

            node = next_node
            best_move = None
        
        if len(game_blunders) == 0:
            print(f"No blunders found in Game ID {game_id} from file {pgn_file}")
        
        blunders.append((game_header, game_blunders))

    engine.quit()

    return blunders

def process_new_files(previous_files, directory):
    current_files = set(os.listdir(directory))
    new_files = current_files.difference(previous_files)
    return new_files

if __name__ == "__main__":
    directory = 'test_data'
    previous_files = set()  # load this from disk if you have it saved
    new_pgn_files = process_new_files(previous_files, directory)
    new_pgn_files = [os.path.join(directory, file) for file in new_pgn_files if file.endswith('.pgn')]

    stockfish_path = 'engines/stockfish'
    csv_dir = "csv"
    os.makedirs(csv_dir, exist_ok=True)

    with multiprocessing.Pool() as pool:
        results = pool.starmap(evaluate_game, [(pgn_file, stockfish_path) for pgn_file in new_pgn_files])

    all_blunders = [blunder for result in results for blunder in result]
    log_blunders(csv_dir, all_blunders)