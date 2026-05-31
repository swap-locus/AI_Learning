from backend.chat import chat
from backend.observability import SessionStats


def main():
    print("AI Support Bot. Type 'quit' to exit.\n")
    history = []
    stats = SessionStats()
    while True:
        try:
            user_input = input("Your query: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit"):
                break
            chat(user_input, history, stats)
        except KeyboardInterrupt:
            break
    stats.print_summary()


if __name__ == "__main__":
    main()
