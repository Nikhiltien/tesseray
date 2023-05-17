import chess.engine
import chess.pgn
import os
import logging
from multiprocessing import Pool, cpu_count

os.makedirs('logs', exist_ok=True)

logging.basicConfig(filename='logs/blunder_analysis.log', level=logging.INFO, format='%(message)s')

def analyze_game(game_info):
    stockfish_path, blunder_threshold, game_info, blunder_definition = game_info
    file, game, game_num = game_info
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

    board = game.board()
    game_key = f'{file}-{game.headers["Event"]}-{game_num}'
    blunders = []
    previous_score = 0
    for move in game.mainline_moves():
        board.push(move)

        result = engine.play(board, chess.engine.Limit(depth=10))
        best_move = result.move

        info = engine.analyse(board, chess.engine.Limit(depth=10))
        score = info["score"].relative.score() if info["score"] else None

        if score is not None:
            if blunder_definition == "bad_move" and best_move != move and score > blunder_threshold:
                blunders.append((board.fen(), move.uci(), best_move.uci(), score))
            elif blunder_definition == "evaluation_drop" and score - previous_score < -blunder_threshold:
                blunders.append((board.fen(), move.uci(), best_move.uci(), score))

        previous_score = score if score is not None else previous_score

    engine.quit()
    return game_key, blunders

# change defintion of blunder
def find_blunders(pgn_dir_path, stockfish_path, blunder_definition="bad_move", blunder_threshold=100):
    game_infos = []

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

                        game_infos.append((stockfish_path, blunder_threshold, (file, game, game_num), blunder_definition))
                        game_num += 1

    with Pool(cpu_count()) as p:
        blunders = p.map(analyze_game, game_infos)

    return dict(blunders)

if __name__ == '__main__':
    stockfish_path = "engines/stockfish"
    pgn_dir_path = "test_data"
    blunders = find_blunders(pgn_dir_path, stockfish_path, blunder_definition="evaluation_drop")
    for game, game_blunders in blunders.items():
        logging.info(f"In game {game}, there were {len(game_blunders)} blunders.")
        print(f"In game {game}, there were {len(game_blunders)} blunders.")
        for blunder in game_blunders:
            logging.info(f"FEN: {blunder[0]}, Actual Move: {blunder[1]}, Best Move: {blunder[2]}, Score: {blunder[3]}")