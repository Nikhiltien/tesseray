import chess
import chess.engine
import chess.pgn

engine = chess.engine.SimpleEngine.popen_uci("engine/stockfish")
board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
info = engine.analyse(board, chess.engine.Limit(time=0.1))
actual_eval = info['score']

print(actual_eval)
