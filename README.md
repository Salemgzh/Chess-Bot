# ♟️ Chess Bot — ~1000 ELO

A playable chess game in Python where you face off against an AI bot calibrated to roughly **1000 ELO** strength. The bot plays reasonably but makes human-like mistakes — it won't crush you, but it won't just throw pieces away either.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python) ![Pygame](https://img.shields.io/badge/Pygame-2.x-green) ![ELO](https://img.shields.io/badge/Bot%20Strength-~1000%20ELO-orange)

---

## 🎮 How to Play

**Install dependencies:**
```bash
pip install pygame
```

**Run the game:**
```bash
python chess_bot.py
```

- You play as **White**, the bot plays as **Black**
- Click a piece to select it (highlights in yellow)
- Click a destination square to move (legal moves shown as dots)
- Press **R** to restart, **Q** to quit

---

## 🤖 How the Bot Works

The bot uses classic game tree search with a few intentional weaknesses to land around 1000 ELO:

| Feature | Detail |
|---|---|
| **Algorithm** | Minimax with alpha-beta pruning |
| **Search depth** | 2-ply — avoids one-move blunders but misses longer tactics |
| **Blunder rate** | 15% of moves are completely random |
| **Evaluation** | Material count + piece-square tables only |
| **No quiescence search** | Misses tactical sequences at the horizon |

This combination mimics a ~1000 ELO player: plays sensible moves most of the time, avoids hanging pieces, but misses combinations and makes occasional errors.

---

## 📁 Project Structure

```
chess-bot/
├── chess_bot.py   # All game logic, bot AI, and Pygame UI in one file
└── README.md
```

---

## 🛠️ Requirements

- Python 3.8+
- Pygame 2.x

---

## 📜 License

MIT — free to use, modify, and distribute.
