"""Vehicle telemetry query agent with LLM function calling."""

import os

from google import genai
from google.genai import types

from app.ai.common.constants import GEMINI_MODEL
from app.ai.common.prompts import get_system_instruction
from app.ai.tools.query_tool import query_vehicle_data


class VehicleQueryAgent:
    """Conversational agent for querying vehicle telemetry data using Gemini."""

    def __init__(self):
        """Initialize the agent with Gemini client and tool configuration."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError('GEMINI_API_KEY environment variable is required')

        self.client = genai.Client(api_key=api_key)
        self.model = GEMINI_MODEL
        self.conversation_history: list[types.Content] = []
        self.system_instruction = get_system_instruction()

    def _execute_function_calls(self, content: types.Content) -> types.Content:
        """Process all function calls and return tool responses."""
        tool_responses = []

        if not content.parts:
            return types.Content(role='model', parts=[])

        for part in content.parts:
            if part.function_call:
                # Validate function_call has required fields
                if not part.function_call.name or not part.function_call.args:
                    continue

                result = query_vehicle_data(**part.function_call.args)
                tool_responses.append(
                    types.Part.from_function_response(
                        name=part.function_call.name,
                        response=result,
                    )
                )
        return types.Content(role='model', parts=tool_responses)

    def query(self, user_message: str) -> str:
        """Send user message and handle function calling loop."""
        self.conversation_history.append(types.Content(role='user', parts=[types.Part.from_text(text=user_message)]))

        while True:
            response = self.client.models.generate_content(
                model=self.model,
                contents=self.conversation_history,
                config=types.GenerateContentConfig(
                    tools=[query_vehicle_data],
                    system_instruction=self.system_instruction,
                ),
            )

            # Validate response structure
            if not response.candidates or len(response.candidates) == 0:
                return 'I encountered an issue processing your request. Please try again.'

            content = response.candidates[0].content
            if not content:
                return 'I encountered an issue processing your request. Please try again.'

            self.conversation_history.append(content)

            # Check if there's a function call
            if content.parts and content.parts[0].function_call:
                tool_content = self._execute_function_calls(content)
                self.conversation_history.append(tool_content)
                continue

            # Return text response
            if content.parts and content.parts[0].text:
                return content.parts[0].text

            return 'I encountered an issue processing your request. Please try again.'

    def reset_conversation(self):
        """Clear conversation history to start a new conversation."""
        self.conversation_history = []
