"""Vehicle telemetry query agent with LLM function calling."""

import json
import os

from anthropic import Anthropic

from app.ai.common.constants import CLAUDE_MODEL, CLAUDE_TEMPERATURE
from app.ai.common.prompts import get_system_instruction
from app.ai.tools.query_tool import query_vehicle_data


class VehicleQueryAgent:
    """Conversational agent for querying vehicle telemetry data using Claude."""

    def __init__(self, temperature: float | None = None):
        """Initialize the agent with Anthropic client and tool configuration."""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError('ANTHROPIC_API_KEY environment variable is required')

        self.client = Anthropic(api_key=api_key)
        self.model = CLAUDE_MODEL
        self.temperature = temperature if temperature is not None else CLAUDE_TEMPERATURE
        self.conversation_history: list = []
        self.system_instruction = get_system_instruction()

    def _get_tool_schema(self) -> list:
        """Return the tool schema for Claude API."""
        return [
            {
                'name': 'query_vehicle_data',
                'description': 'Query vehicle telemetry data with optional filters',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'vehicle_id': {
                            'type': 'string',
                            'description': 'Vehicle ID (supports wildcards * and ?)',
                        },
                        'timestamp_start': {
                            'type': 'string',
                            'description': 'Start timestamp in YYYY-MM-DD-HH format',
                        },
                        'timestamp_end': {
                            'type': 'string',
                            'description': 'End timestamp in YYYY-MM-DD-HH format',
                        },
                        'battery_health_min': {
                            'type': 'number',
                            'description': 'Minimum battery health percentage (0-100)',
                        },
                        'battery_health_max': {
                            'type': 'number',
                            'description': 'Maximum battery health percentage (0-100)',
                        },
                        'odometer_km_min': {
                            'type': 'integer',
                            'description': 'Minimum odometer reading in kilometers',
                        },
                        'odometer_km_max': {
                            'type': 'integer',
                            'description': 'Maximum odometer reading in kilometers',
                        },
                    },
                },
            }
        ]

    def _execute_tool_calls(self, content_blocks: list) -> list:
        """Process all tool calls and return tool results."""
        tool_results = []

        for block in content_blocks:
            if block.type == 'tool_use':
                if block.name == 'query_vehicle_data':
                    result = query_vehicle_data(**block.input)
                else:
                    result = {'error': f'Unknown tool: {block.name}'}

                tool_results.append({'type': 'tool_result', 'tool_use_id': block.id, 'content': json.dumps(result)})

        return tool_results

    def query(self, user_message: str) -> str:
        """Send user message and handle tool calling loop."""
        self.conversation_history.append({'role': 'user', 'content': user_message})

        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=self.temperature,
                system=self.system_instruction,
                messages=self.conversation_history,
                tools=self._get_tool_schema(),
            )

            # Add assistant's response to history
            self.conversation_history.append({'role': 'assistant', 'content': response.content})

            # Check for tool use
            if response.stop_reason == 'tool_use':
                tool_results = self._execute_tool_calls(response.content)
                self.conversation_history.append({'role': 'user', 'content': tool_results})
                continue

            # Return text response
            for block in response.content:
                if block.type == 'text':
                    return block.text

            return 'I encountered an issue processing your request. Please try again.'

    def reset_conversation(self):
        """Clear conversation history to start a new conversation."""
        self.conversation_history = []
