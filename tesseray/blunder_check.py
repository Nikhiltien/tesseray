import chess.engine
import chess.pgn
import os
from datetime import datetime

def evaluate_game(pgn_file, stockfish_path, limit=150):
    with open(pgn_file) as f:
        # Create a unique filename for the log
        flag = datetime.now().strftime('%Y%m%d%H%M%S')
        log_dir = "logs"
        log_file = os.path.join(log_dir, f"blunder_check_{flag}.log")

        os.makedirs(log_dir, exist_ok=True)

        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break

            node = game
            while not node.is_end():
                next_node = node.variations[0]
                move = next_node.move

                # Evaluate the position before the move
                result = engine.analyse(node.board(), chess.engine.Limit(depth=10))
                score_before = result["score"].relative.score()
                if score_before is None:
                    # Mate in x situation
                    score_before = (30000 if result["score"].relative.is_mate() else 0)

                # Evaluate the position after the move
                result = engine.analyse(next_node.board(), chess.engine.Limit(depth=10))
                score_after = result["score"].relative.score() * -1
                if score_after is None:
                    # Mate in x situation
                    score_after = (30000 if result["score"].relative.is_mate() else 0) * -1

                if abs(score_before - score_after) > limit:
                    blunder_msg = f"A blunder occurred on move: {node.board().san(move)}"
                    print(blunder_msg)

                    # Write blunder to log
                    with open(log_file, 'a') as log_f:
                        log_f.write(f"{blunder_msg}\n")

                node = next_node

        engine.quit()

evaluate_game('test_data/chess_com_games_2023-05-16.pgn', 'engines/stockfish')
