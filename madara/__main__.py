"""CLI entrypoint:  python -m madara <scope.yaml> "<task>" """
import sys
from .agent import Agent

def main() -> None:
    if len(sys.argv) < 3:
        print('usage: python -m madara <scope.yaml> "<task>"')
        raise SystemExit(2)
    agent = Agent(sys.argv[1])
    print(agent.run(sys.argv[2]))
    print("\nstate:", agent.findings.summary())

if __name__ == "__main__":
    main()
