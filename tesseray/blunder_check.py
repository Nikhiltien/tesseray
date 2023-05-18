import chess.engine
import chess.pgn

def evaluate_game(pgn_file, stockfish_path, limit=150):
    with open(pgn_file) as f:
        game = chess.pgn.read_game(f)
    
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

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
            print(f"A blunder occurred on move: {node.board().san(move)}")

        node = next_node

    engine.quit()

# Example usage
evaluate_game('test_data/chess_com_games_2023-05-16.pgn', 'engines/stockfish')
