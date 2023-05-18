import chess.engine
import chess.pgn
import os
import threading
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

class GameEvaluator(threading.Thread):
    def __init__(self, pgn_file, stockfish_path, limit=150):
        super().__init__()
        self.pgn_file = pgn_file
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        self.limit = limit
        self.result = None  # This will hold the result

    def run(self):  # This is what's run when you call start()
        blunders = []
        while True:
            game = chess.pgn.read_game(self.pgn_file)
            if game is None:
                break

            blunder_count = 0
            game_blunders = []
            node = game
            game_header = f"Evaluating Game: {self.pgn_file}\n"

            while not node.is_end():
                next_node = node.variations[0]
                move = next_node.move

                # Evaluate the position before the move
                result = self.engine.analyse(node.board(), chess.engine.Limit(depth=10))
                score_before = result["score"].relative.score()
                if score_before is None:
                    # Mate in x situation
                    score_before = (30000 if result["score"].relative.is_mate() else 0)

                # Evaluate the position after the move
                result = self.engine.analyse(next_node.board(), chess.engine.Limit(depth=10))
                score_after = result["score"].relative.score()
                if score_after is None:
                    # Mate in x situation
                    score_after = (30000 if result["score"].relative.is_mate() else 0)

                if abs(score_before - score_after) > self.limit:
                    blunder_count += 1
                    blunder_msg = f"A blunder occurred on move: {node.board().san(move)}"
                    game_blunders.append(blunder_msg)
                node = next_node

            if blunder_count > 0:
                blunders.append((game_header, game_blunders))

        self.result = blunders
        self.engine.quit()  # Remember to quit the engine when done

if __name__ == "__main__":
    directory = 'test_data'
    pgn_files = [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.pgn')]
    stockfish_path = 'engines/stockfish'
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    threads = [GameEvaluator(pgn_file, stockfish_path) for pgn_file in pgn_files]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()  # Wait for thread to complete
    all_blunders = [blunder for thread in threads for blunder in thread.result]
    write_to_log(log_dir, all_blunders)
