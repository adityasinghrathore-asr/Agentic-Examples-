from dotenv import load_dotenv
from lib.memory import ShortTermMemory
from lib.messages import UserMessage, SystemMessage, AIMessage
from lib.llm import LLM

load_dotenv()


# ============================================================================
# ChatBot Implementation
# ============================================================================

class ChatBot:
    """ChatBot class that uses LLM and session-based memory.
    
    This chatbot maintains separate conversation contexts for different sessions,
    allowing multiple personas to be active simultaneously.
    """
    
    def __init__(self):
        """Initialize the chatbot with an LLM instance."""
        self.chat_model = LLM()
    
    def chat(self, message: str, memory: ShortTermMemory, session_id: str = None) -> str:
        """Process a user message and return the AI response.
        
        Args:
            message: The user's input message
            memory: ShortTermMemory instance managing conversation history
            session_id: Optional session identifier for context isolation
            
        Returns:
            The AI's response as a string
        """
        # Add user message to memory
        user_message = UserMessage(content=message)
        memory.add(user_message, session_id)
        
        # Retrieve conversation history
        messages = memory.get_all_objects(session_id)
        
        # Get AI response
        ai_message = self.chat_model.invoke(messages)
        
        # Store AI response in memory
        memory.add(ai_message, session_id)
        
        return ai_message.content


# ============================================================================
# Demo Implementations
# ============================================================================

def football_commentator_demo(chat_bot: ChatBot, memory: ShortTermMemory):
    """Demo: Football Commentator Persona Session.
    
    Creates a chatbot persona that responds like a dramatic Premier League
    football commentator, full of excitement and football metaphors.
    """
    print("=" * 60)
    print("Demo 1: Football Commentator Persona Session")
    print("=" * 60)
    
    # Create session
    session_id = "football_commentator"
    memory.create_session(session_id)
    print(f"\nCreated session: {session_id}")
  
    # Define persona
    football_commentator_voice = SystemMessage(
        content=(
            "You are a dramatic Premier League football commentator. "
            "Respond to every user query as if narrating a live match — full of excitement, "
            "flair, and football metaphors. Use phrases like 'What a move!' or "
            "'Against all odds!' and always sound like something incredible just happened, "
            "no matter the topic."
        )
    )

    memory.add(football_commentator_voice, session_id)
    print(f"Added persona to session")

    # Test the persona
    query = "What's stoicism?"
    print(f"\nUser: {query}")
    response = chat_bot.chat(
        message=query,
        memory=memory,
        session_id=session_id
    )
    print(f"Bot: {response}")
    
    # Show conversation history
    messages = memory.get_all_objects(session_id)
    print(f"\nTotal messages in session: {len(messages)}")
    print()


def gps_navigation_demo(chat_bot: ChatBot, memory: ShortTermMemory):
    """Demo: GPS Navigation Persona Session.
    
    Creates a chatbot persona that responds like a GPS navigation system,
    giving driving directions for any query.
    """
    print("=" * 60)
    print("Demo 2: GPS Navigation Persona Session")
    print("=" * 60)
    
    # Create session
    session_id = "gps_navigation"
    memory.create_session(session_id)
    print(f"\nCreated session: {session_id}")

    # Define persona
    gps_navigation_voice = SystemMessage(
        content=(
            "You are a GPS navigation voice. No matter what the user asks, "
            "respond as if you're giving driving directions. Use phrases like 'In 300 meters, "
            "turn left,' or 'Recalculating route…' to deliver answers, even to unrelated questions. "
            "Be dry, overly calm, and unintentionally funny."
        )
    )

    memory.add(gps_navigation_voice, session_id)
    print(f"Added persona to session")

    # Test the persona
    query = "What's stoicism?"
    print(f"\nUser: {query}")
    response = chat_bot.chat(
        message=query,
        memory=memory,
        session_id=session_id
    )
    print(f"Bot: {response}")
    
    # Show conversation history
    messages = memory.get_all_objects(session_id)
    print(f"\nTotal messages in session: {len(messages)}")
    print()


def default_session_demo(chat_bot: ChatBot, memory: ShortTermMemory):
    """Demo: Default Session Without Persona.
    
    Shows how the chatbot behaves without a specific persona,
    using the default session.
    """
    print("=" * 60)
    print("Demo 3: Default Session Without Persona")
    print("=" * 60)
    
    query = "What's stoicism?"
    print(f"\nUser: {query}")
    response = chat_bot.chat(
        message=query,
        memory=memory,
    )
    print(f"Bot: {response}")
    
    # Show all active sessions
    all_sessions = memory.get_all_sessions()
    print(f"\nTotal active sessions: {len(all_sessions)}")
    print(f"Session IDs: {all_sessions}")
    print()


def main():
    """Main function to run all demos.
    
    Demonstrates how session-based memory allows multiple personas
    to maintain separate conversation contexts simultaneously.
    """
    # Initialize memory and chatbot
    memory = ShortTermMemory()
    chat_bot = ChatBot()
    
    # Run demos
    football_commentator_demo(chat_bot, memory)
    gps_navigation_demo(chat_bot, memory)
    default_session_demo(chat_bot, memory)


if __name__ == "__main__":
    main()