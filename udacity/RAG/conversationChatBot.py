"""
Customer Service Chatbot Implementation
Lesson 3: Implementing a Chatbot with an LLM

This exercise guides you through building a customer service chatbot for an e-commerce platform.
The bot handles common customer inquiries about orders, products, returns, and technical support.

Learning Objectives:
- Initialize and configure the OpenAI API client
- Design prompt templates for different intent types
- Maintain conversation history for context
- Classify customer intents and route to appropriate handlers
- Generate contextual, helpful responses
"""

from openai import OpenAI
import os
from typing import List, Dict, Optional
from datetime import datetime


class CustomerServiceBot:
    """
    A chatbot that handles common customer inquiries for an e-commerce platform.

    Capabilities:
    - Order status inquiries
    - Product information requests
    - Return and refund policies
    - Technical support
    - General customer service
    """

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """
        Initialize the customer service bot.

        Args:
            api_key: OpenAI API key (or Vocareum key)
            model: The model to use for responses (default: gpt-3.5-turbo)
        """
        # Initialize the OpenAI client
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openai.vocareum.com/v1"
        )

        # Store the model name
        self.model = model

        # Initialize conversation history with system prompt
        self.conversation_history: List[Dict[str, str]] = []
        self.conversation_history.append({
            "role": "system",
            "content": self._get_system_prompt()
        })
    

    def _get_system_prompt(self) -> str:
        """
        Define the system prompt that sets the bot's behavior and personality.
        """

        return """You are a helpful customer service assistant for ShopEasy, an e-commerce platform.

Your role is to assist customers with:
- Order status and tracking
- Product information and recommendations
- Return and refund policies
- Technical support issues
- Account questions

Guidelines:
- Be professional, friendly, and empathetic
- Provide clear, concise answers
- Ask clarifying questions when the customer's intent is unclear
- If you don't have specific information (like order numbers), ask for it
- Always prioritize customer satisfaction

If a request is outside your capabilities, politely explain and offer to escalate to a human agent."""

    def classify_intent(self, message: str) -> str:
        """
        Classify the customer's intent to route to the appropriate handler.

        Args:
            message: The customer's message

        Returns:
            Intent category: 'order_status', 'product_info', 'returns',
                           'technical_support', or 'general'
        """
        classification_prompt = f"""Classify the following customer message into ONE of these categories:
        - order_status: Questions about order tracking, delivery, or status
        - product_info: Questions about products, features, availability, or recommendations
        - returns: Questions about returns, refunds, or exchanges
        - technical_support: Technical issues with the website, app, or account
        - general: General inquiries or greetings

        Customer message: "{message}"

        Respond with ONLY the category name, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": classification_prompt}],
                temperature=0,
                max_tokens=20
            )

            intent = response.choices[0].message.content.strip().lower()
            valid_intents = ['order_status', 'product_info', 'returns', 'technical_support', 'general']
            
            if intent not in valid_intents:
                intent = "general"  # Default fallback

            return intent

        except Exception as e:
            print(f"Error classifying intent: {e}")
            return "general"  # Default to general on error

    def generate_response(self, user_message: str, intent: Optional[str] = None) -> str:
        """
        Generate a contextual response to the user's message.

        Args:
            user_message: The customer's message
            intent: Optional intent classification (will auto-classify if not provided)

        Returns:
            The bot's response as a string
        """
        # Classify intent if not provided
        if intent is None:
            intent = self.classify_intent(user_message)
            print(f"Classified intent: {intent}")

        # Add user's message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        try:
            # Generate response using conversation history
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=300
            )

            # Extract and store assistant's response
            assistant_message = response.choices[0].message.content
            
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message

        except Exception as e:
            error_msg = f"I apologize, but I'm having trouble processing your request right now. Please try again in a moment."
            print(f"Error generating response: {e}")
            return error_msg

    def reset_conversation(self):
        """
        Reset the conversation history, keeping only the system prompt.
        Useful when starting a new customer conversation.
        """
        self.conversation_history = [{
            "role": "system",
            "content": self._get_system_prompt()
        }]
        print("Conversation history has been reset.")

    def get_conversation_summary(self) -> str:
        """
        Get a summary of the conversation for handoff to human agent.

        Returns:
            A brief summary of the customer's inquiries and bot responses
        """
        if len(self.conversation_history) <= 1:  # Only system prompt
            return "No conversation history to summarize."

        summary_prompt = """Please provide a brief summary of this customer service conversation.
        Include:
        1. Main customer concerns or questions
        2. Information provided by the bot
        3. Current status or next steps

        Keep it concise (2-3 sentences)."""

        summary_messages = self.conversation_history + [
            {"role": "user", "content": summary_prompt}
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=summary_messages,
                temperature=0.5,
                max_tokens=150
            )

            summary = response.choices[0].message.content.strip()
            return summary
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Unable to generate summary at this time."


def main():
    """
    Demo the customer service bot with sample interactions.
    """
    # Get API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY") or "voc-197589463615876646835776955ac0fd972f4.32548273"

    if not api_key:
        print("Error: Please set OPENAI_API_KEY environment variable")
        print("\nFor Vocareum keys:")
        print('  export OPENAI_API_KEY="voc-..."')
        print("\nFor standard OpenAI keys:")
        print('  export OPENAI_API_KEY="sk-..."')
        return

    # Initialize the bot
    print("Initializing Customer Service Bot...")
    bot = CustomerServiceBot(api_key)

    print("\n" + "="*60)
    print("Customer Service Bot Ready!")
    print("="*60)
    print("\nCommands:")
    print("  'quit' or 'exit' - End the session")
    print("  'reset' - Start a new conversation")
    print("  'summary' - Get a conversation summary")
    print("\nSample questions to try:")


    # Sample questions to try:
    sample_questions = [
        "Where is my order? I placed it 3 days ago.",
        "Do you have wireless headphones in stock?",
        "What's your return policy?",
        "I can't log into my account"
    ]

    print("Sample questions you can try:")
    for i, q in enumerate(sample_questions, 1):
        print(f"{i}. {q}")
    print()

    # Main chat loop
    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit']:
                print("Thank you for using Customer Service Bot!")
                print("Have a great day!")
                break

            if user_input.lower() == 'reset':
                bot.reset_conversation()
                continue

            if user_input.lower() == 'summary':
                print("\n--- Conversation Summary ---")
                print(bot.get_conversation_summary())
                print("----------------------------\n")
                continue

            # Generate and print response
            response = bot.generate_response(user_input)
            print(f"Bot: {response}\n")
            
        except KeyboardInterrupt:
            print("\nSession ended by user. Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Type 'quit' to exit or continue chatting.\n")


if __name__ == "__main__":
    main()
