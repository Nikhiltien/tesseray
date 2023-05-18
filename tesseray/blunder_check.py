import chess.engine
import chess.pgn
import os
import multiprocessing
from datetime import datetime

def log_blunders(log_dir, all_blunders):
    flag = datetime.now().strftime('%Y%m%d%H%M%S')
    log_file = os.path.join(log_dir, f"blunder_check_{flag}.log")

    with open(log_file, 'w') as log_f:
        for game_header, blunders_list in all_blunders:
            log_f.write(game_header)
            for blunder in blunders_list:
                log_f.write(f"{blunder}\n")
            log_f.write(f"Total blunders in game: {len(blunders_list)}\n")

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

    for game in game_generator(pgn_file):
        game_blunders = []
        node = game
        game_header = f"Evaluating Game: {pgn_file}\n"

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
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    with multiprocessing.Pool() as pool:
        results = pool.starmap(evaluate_game, [(pgn_file, stockfish_path) for pgn_file in new_pgn_files])

    all_blunders = [blunder for result in results for blunder in result]
    log_blunders(log_dir, all_blunders)