import chess
import chess.engine
import chess.pgn

# Load the PGN file
pgn = open("data/Szparu_vs_Jospem_2023.04.11.pgn")
pgn_game = chess.pgn.read_game(pgn)

# Initialize the engine
engine = chess.engine.SimpleEngine.popen_uci("engine/stockfish")

# Iterate over the moves in the game
board = pgn_game.board()
for move in pgn_game.mainline_moves():
    # Make the move on the engine's board
    board.push(move)

    # Request an analysis from the engine
    result = engine.analysis(board, chess.engine.Limit(time=10.0))

    # Get the engine's suggested best move for the current position
    best_move = result.get()
    print(result.get())

with engine.analysis(board, chess.engine.Limit(depth=20)) as analysis:
        for info in analysis:
            print(info.get("score"))