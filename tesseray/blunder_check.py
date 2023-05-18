import chess.engine
import chess.pgn
import os
import multiprocessing
from datetime import datetime

def write_to_log(log_dir, blunders):
    flag = datetime.now().strftime('%Y%m%d%H%M%S')
    log_file = os.path.join(log_dir, f"blunder_check_{flag}.log")

    with open(log_file, 'a') as log_f:
        for game_header, blunders_list in blunders:
            log_f.write(game_header)
            for blunder in blunders_list:
                log_f.write(f"{blunder}\n")
            log_f.write(f"Total blunders in game: {len(blunders_list)}\n")

def evaluate_game(pgn_file, stockfish_path, limit=150):
    with open(pgn_file) as f:
        blunders = []

        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break

            blunder_count = 0
            game_blunders = []
            node = game
            game_header = f"Evaluating Game: {pgn_file}\n"

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
                score_after = result["score"].relative.score()
                if score_after is None:
                    # Mate in x situation
                    score_after = (30000 if result["score"].relative.is_mate() else 0)

                if abs(score_before + score_after) > limit:
                    blunder_count += 1
                    move_number = (node.ply() + 1) // 2
                    if node.board().turn:
                        move_notation = f"{move_number}. {node.board().san(move)}"
                    else:
                        move_notation = f"{move_number}. ...{node.board().san(move)}"
                    blunder_msg = f"A blunder occurred on move: {move_notation}"
                    game_blunders.append(blunder_msg)

                node = next_node

            blunders.append((game_header, game_blunders))

        engine.quit()

    return blunders

if __name__ == "__main__":
    directory = 'test_data'
    pgn_files = [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.pgn')]
    stockfish_path = 'engines/stockfish'
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # create a process pool and start evaluation
    with multiprocessing.Pool() as pool:
        results = pool.starmap(evaluate_game, [(pgn_file, stockfish_path) for pgn_file in pgn_files])

    all_blunders = [blunder for result in results for blunder in result]
    write_to_log(log_dir, all_blunders)