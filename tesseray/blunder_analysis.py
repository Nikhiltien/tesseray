import chess.engine
import chess.pgn
import os
import logging
from multiprocessing import Pool, cpu_count

logging.basicConfig(filename='blunder_analysis.log', level=logging.INFO, format='%(message)s')

def analyze_game(game_info):
    stockfish_path, blunder_threshold, game_info = game_info
    file, game, game_num = game_info
    # Initialize the chess engine
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

    board = game.board()
    game_key = f'{file}-{game.headers["Event"]}-{game_num}'
    blunders = []
    for move in game.mainline_moves():
        board.push(move)

        # Get the best move
        result = engine.play(board, chess.engine.Limit(depth=10))
        best_move = result.move

        # If the best move is different from the actual move
        if best_move != move:
            info = engine.analyse(board, chess.engine.Limit(depth=10))
            score = info["score"].relative.score() if info["score"] else None

            # If the score is not None and the difference is greater than the threshold, it's a blunder
            if score is not None and score > blunder_threshold:
                blunders.append((board.fen(), move.uci(), best_move.uci(), score))

    engine.quit()
    return game_key, blunders

def find_blunders(pgn_dir_path, stockfish_path, blunder_threshold=100):
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
                            break  # end of file

                        game_infos.append((stockfish_path, blunder_threshold, (file, game, game_num)))
                        game_num += 1

    # use as many processes as there are CPUs
    with Pool(cpu_count()) as p:
        blunders = p.map(analyze_game, game_infos)

    return dict(blunders)

if __name__ == '__main__':
    stockfish_path = "engines/stockfish"
    pgn_dir_path = "test_data"
    blunders = find_blunders(pgn_dir_path, stockfish_path)
    for game, game_blunders in blunders.items():
        logging.info(f"In game {game}, there were {len(game_blunders)} blunders.")
        print(f"In game {game}, there were {len(game_blunders)} blunders.")
        for blunder in game_blunders:
            logging.info(f"FEN: {blunder[0]}, Actual Move: {blunder[1]}, Best Move: {blunder[2]}, Score: {blunder[3]}")
