import chess.engine
import chess.pgn
import os
import multiprocessing
from datetime import datetime

def evaluate_game(pgn_file, stockfish_path, limit=150):
    with open(pgn_file) as f:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

        all_logs = []

        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break

            blunder_count = 0
            blunders = []
            
            # Write the game's name at the top of the log
            game_header = f"Evaluating Game: {pgn_file}\n"
            all_logs.append(game_header)

            result = None
            for node in game.mainline():
                next_node = node.board().copy()
                next_node.push(node.move)

                # Get the move in SAN format before making the move
                san_move = node.board().san(node.move)

                # If it's the first move, analyse the position
                if result is None:
                    result = engine.analyse(node.board(), chess.engine.Limit(depth=10))

                score_before = result["score"].relative.score()
                if score_before is None:
                    # Mate in x situation
                    score_before = (30000 if result["score"].relative.is_mate() else 0)

                # Evaluate the next position
                result = engine.analyse(next_node, chess.engine.Limit(depth=10))

                score_after = result["score"].relative.score()
                if score_after is None:
                    # Mate in x situation
                    score_after = (30000 if result["score"].relative.is_mate() else 0)

                if abs(score_before - score_after) > limit:
                    blunder_count += 1
                    blunder_msg = f"A blunder occurred on move: {san_move}"
                    blunders.append(blunder_msg)

            for blunder in blunders:
                all_logs.append(f"{blunder}\n")
            all_logs.append(f"Total blunders in game: {blunder_count}\n")

        # Create a unique filename for the log
        flag = datetime.now().strftime('%Y%m%d%H%M%S')
        log_file = os.path.join(log_dir, f"blunder_check_{flag}.log")

        with open(log_file, 'a') as log_f:
            log_f.writelines(all_logs)

        engine.quit()

if __name__ == "__main__":
    directory = 'test_data'
    pgn_files = [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.pgn')]
    stockfish_path = 'engines/stockfish'

    # create a process pool and start evaluation
    with multiprocessing.Pool() as pool:
        pool.starmap(evaluate_game, [(pgn_file, stockfish_path) for pgn_file in pgn_files])
