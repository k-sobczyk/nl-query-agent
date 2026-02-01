"""CLI entry point for executing natural language queries against vehicle data."""

from dotenv import load_dotenv

from app.ai.agent.agent import VehicleQueryAgent

load_dotenv()


def main():
    """Interactive CLI for vehicle telemetry queries."""
    print('Ask questions about vehicle telemetry data in natural language.')
    print('Examples:')
    print('  - "Show vehicles with battery below 85%"')
    print('  - "Find vehicles starting with VVA1"')
    print('  - "Show vehicles from 2024-11-20"')
    print()
    print('Commands:')
    print('  - Type "exit" or "quit" to exit')
    print('  - Type "/clear" to clear conversation history')
    print()

    try:
        agent = VehicleQueryAgent()
    except ValueError as e:
        print(f'Error: {e}')
        return

    while True:
        try:
            user_input = input('You: ').strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit']:
                print('Goodbye!')
                break

            if user_input.lower() == '/clear':
                agent.reset_conversation()
                print('\n✓ Conversation history cleared. Starting fresh!\n')
                continue

            response = agent.query(user_input)
            print(f'\nAgent: {response}\n')

        except KeyboardInterrupt:
            print('\n\nInterrupted. Goodbye!')
            break

        except Exception as e:
            print(f'\nError: {e}\n')
            print('Please try again or type "/clear" to clear conversation history.')


if __name__ == '__main__':
    main()
