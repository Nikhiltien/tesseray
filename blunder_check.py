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
    result = engine.analysis(board, chess.engine.Limit(time=1.0))

    # Get the engine's suggested best move for the current position
    best_move = result.get()

    # Compare the engine's best move to the actual move played
    if move != best_move:
        # Calculate the difference in evaluation between the actual move and the engine's suggested move
        actual_eval = engine.analyse(board, chess.engine.Limit(depth=10))["score"].relative.score()
        suggested_eval = result.get()
        #eval_diff = abs(actual_eval - suggested_eval)
        print(actual_eval)
        print(suggested_eval)

        # Log a blunder if the evaluation difference exceeds a certain threshold
        #if eval_diff >= 1500:
            #print(f"Blunder detected at move {board.fullmove_number()}: {move} (eval diff: {eval_diff})")
            #print(f"Suggested move: {best_move}, actual move: {move}")

# Cleanup
engine.quit()
