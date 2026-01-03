from typing import Dict, List, Any, Optional
import os
import dotenv
import random
import time
from smolagents import ToolCallingAgent, OpenAIServerModel, tool
import json

dotenv.load_dotenv(dotenv_path="../.env")
openai_api_key = os.getenv("UDACITY_OPENAI_API_KEY")

model = OpenAIServerModel(
    model_id="gpt-4o-mini",
    #api_key=os.getenv("UDACITY_OPENAI_API_KEY"),
    api_key="voc-197589463615876646835776955ac0fd972f4.32548273",
    api_base="https://openai.vocareum.com/v1",
)
class BookingManager:
    def __init__(self):
        self.bookings: Dict[str, List[Dict[str, Any]]] = {} 
        self.locations = ["Beijing Branch (北京分行)", "Shanghai Branch (上海分行)", "Guangzhou Branch (广州分行)"]
        self.special_services = {
            "VIP": ["deposit", "international_transfer"],
            "Regular": [], 
            "Student": ["loan"],
            "Senior": ["bill_payment"]
        }
        self.availability = {
            "deposit": 2, "postal": 2, "loan": 2, "bill_payment": 2,
            "international_transfer": 2, "general_inquiry": float('inf')
        }
        self.routing_accuracy = {
            "correct_service_type": 0, "total_requests": 0, "special_handling_applied": 0,
            "urgent_requests_identified_by_llm": 0, 
            "urgent_requests_processed_as_urgent": 0 
        }
        self.customer_profiles = {
            "Wang Xiaoming (王小明)": {"type": "VIP", "language": "Mandarin"},
            "Li Jiayi (李佳怡)": {"type": "Regular", "language": "Mandarin"},
            "Chen Student (陈学生)": {"type": "Student", "language": "Mandarin"},
            "Zhang Senior (张老先生)": {"type": "Senior", "language": "Cantonese"},
            "Ms. Qian (钱女士)": {"type": "VIP", "language": "English"},
            "Mr. Zhao (赵先生)": {"type": "Regular", "language": "Mandarin"},
            "Emergency Customer (紧急客户)": {"type": "Regular", "language": "Mandarin"}
        }

    def check_availability(self, service_type: str) -> bool:
        service_type_lower = service_type.lower()
        return self.availability.get(service_type_lower, 0) > 0

    def add_booking(self, service_type: str, customer_name: str, is_urgent: bool = False) -> str:
        service_type_lower = service_type.lower()
        
        if not self.check_availability(service_type_lower):
            return f"Sorry, no availability for {service_type_lower} service. (很抱歉，{service_type_lower}服务目前没有可用名额。)"
        
        if service_type_lower not in self.bookings:
            self.bookings[service_type_lower] = []
        
        booking_details = {"customer": customer_name, "is_urgent": is_urgent} 
        self.bookings[service_type_lower].append(booking_details)

        if self.availability.get(service_type_lower, 0) != float('inf'):
            self.availability[service_type_lower] -= 1
        
        if is_urgent:
            self.routing_accuracy["urgent_requests_processed_as_urgent"] += 1
        
        customer_type = "Regular"
        for cust, profile in self.customer_profiles.items():
            if customer_name.lower() in cust.lower():
                customer_type = profile["type"]
                break
                
        special_handling = ""
        if customer_type in self.special_services and service_type_lower in self.special_services[customer_type]:
            special_handling = f" with {customer_type} priority service (享受{customer_type}优先服务)"
            self.routing_accuracy["special_handling_applied"] += 1
        
        urgent_tag = " URGENTLY" if is_urgent else ""
        urgent_tag_zh = " (紧急优先处理)" if is_urgent else ""
        branch = random.choice(self.locations)
        
        confirmation_parts = [
            f"{customer_name}'s {service_type_lower} service booking is confirmed{urgent_tag} at {branch}{special_handling}.",
            f"({customer_name}的{service_type_lower}服务预约已确认{urgent_tag_zh}，地点在{branch}{special_handling}。)"
        ]
        return " ".join(confirmation_parts)

booking_manager = BookingManager()

# TODO: Learner Task 1: Define and implement the 'analyze_request_urgency' tool
# This tool should take the user's request string as input.
# It should analyze the request for keywords indicating urgency.
# It MUST return the string "urgent" if urgency is detected, or "normal" otherwise.
@tool
def analyze_request(request: str) -> str:
    """Analyzes the customer request and identifies the service needed.
    This tool MUST return only the service type without additional text.

    Args:
        request: The customer's request.

    Returns:
        ONLY the identified service type (deposit, postal, loan, bill_payment, international_transfer, or general_inquiry).
    """
    # Map common request phrases to service types
    service_keywords = {
        "deposit": ["deposit", "save", "put money", "存", "存款", "存钱"],
        "postal": ["mail", "send", "package", "shipping", "邮寄", "包裹", "快递"],
        "loan": ["loan", "borrow", "贷款", "借钱"],
        "bill_payment": ["bill", "pay", "payment", "电费", "水费", "缴费", "账单"],
        "international_transfer": ["international", "transfer", "abroad", "foreign", "国际", "转账", "汇款"],
        "general_inquiry": ["hours", "information", "question", "when", "where", "how", "什么时候", "在哪里", "怎么样", "如何"]
    }
    
    request_lower = request.lower()
    for service, keywords in service_keywords.items():
        for keyword in keywords:
            if keyword.lower() in request_lower:
                return service
    
    # Default to general inquiry if no match
    return "general_inquiry"

@tool
def analyze_request_urgency(request: str) -> bool:
    """Analyzes whether a customer request is urgent.
    
    Args:
        request: The customer's request text.
        
    Returns:
        True if the request is urgent, False otherwise.
    """
    # Keywords that indicate urgency in both English and Chinese
    urgency_keywords = [
        "urgent", "urgently", "emergency", "immediately", "asap", "right away", "right now",
        "紧急", "急需", "立即", "马上", "立刻", "赶快", "尽快", "迫切", "急迫"
    ]
    
    request_lower = request.lower()
    for keyword in urgency_keywords:
        if keyword in request_lower:
            return True
    
    return False



@tool
def handle_deposit_request(customer_name: str, is_urgent: bool) -> str:
    """
    Handles a deposit request.

    Args:
        customer_name (str): The name of the customer.
        is_urgent (bool): True if the request is flagged as urgent.

    Returns:
        str: A confirmation message.
    """
    return booking_manager.add_booking("deposit", customer_name, is_urgent)

@tool
def handle_postal_request(customer_name: str, is_urgent: bool) -> str:
    """
    Handles a postal service request.

    Args:
        customer_name (str): The name of the customer.
        is_urgent (bool): True if the request is flagged as urgent.

    Returns:
        str: A confirmation message.
    """
    return booking_manager.add_booking("postal", customer_name, is_urgent)

@tool
def handle_loan_request(customer_name: str, is_urgent: bool) -> str:
    """
    Handles a loan application request.

    Args:
        customer_name (str): The name of the customer.
        is_urgent (bool): True if the request is flagged as urgent.

    Returns:
        str: A confirmation message.
    """
    return booking_manager.add_booking("loan", customer_name, is_urgent)

@tool
def handle_bill_payment_request(customer_name: str, is_urgent: bool) -> str:
    """
    Handles a bill payment request.

    Args:
        customer_name (str): The name of the customer.
        is_urgent (bool): True if the request is flagged as urgent.

    Returns:
        str: A confirmation message.
    """
    return booking_manager.add_booking("bill_payment", customer_name, is_urgent)

@tool
def handle_international_transfer_request(customer_name: str, is_urgent: bool) -> str:
    """
    Handles an international transfer request.

    Args:
        customer_name (str): The name of the customer.
        is_urgent (bool): True if the request is flagged as urgent.

    Returns:
        str: A confirmation message.
    """
    return booking_manager.add_booking("international_transfer", customer_name, is_urgent)

@tool
def handle_general_inquiry_request(customer_name: str, original_request: str, is_urgent: bool) -> str:
    """
    Handles a general inquiry.

    Args:
        customer_name (str): The name of the customer.
        original_request (str): The customer's original general inquiry.
        is_urgent (bool): True if the request is flagged as urgent.

    Returns:
        str: A helpful response.
    """
    urgency_note = " (This inquiry was flagged as urgent.)" if is_urgent else ""
    customer_profile = {}
    for cust_key, profile_val in booking_manager.customer_profiles.items():
        if customer_name.lower() in cust_key.lower(): customer_profile = profile_val; break
    lang = customer_profile.get("language", "Mandarin")
    
    response_text = ""
    if lang == "English":
        response_text = f"Thank you for your inquiry, {customer_name}. For general questions like '{original_request}', please refer to our FAQ or a bank representative can assist you shortly."
    elif lang == "Cantonese":
        response_text = f"{customer_name}，多謝你嘅查詢。關於一般問題，好似「{original_request}」，請參考我哋嘅常見問題，或者稍後銀行職員會協助你。"
    else: 
        response_text = f"{customer_name}，感谢您的咨询。关于一般问题，例如“{original_request}”，请参考我们的常见问题解答，或者稍后银行代表将为您提供帮助。"
    return response_text + urgency_note


class RequestAnalysisAgent(ToolCallingAgent):
    def __init__(self, model_to_use: OpenAIServerModel):
        super().__init__(
            tools=[], 
            model=model_to_use, name="request_analysis_agent",
            description="Analyzes customer requests and directly outputs the categorized service type as its final answer."
        )
        self.possible_service_types = [
            "deposit", "postal", "loan", "bill_payment", 
            "international_transfer", "general_inquiry"
        ]
    def get_service_type_from_llm(self, user_request: str) -> str:
        self.memory.steps = []
        prompt = f"""
        A customer stated in a Chinese Postal Bank context: "{user_request}"
        Your ONLY task is to identify the primary banking or postal service the customer needs.
        Choose exactly ONE service type from this list: {json.dumps(self.possible_service_types)}.
        
        You MUST then use the 'final_answer' tool. The 'answer' argument for the 'final_answer' tool
        should be ONLY the chosen service type string (e.g., "deposit", "postal").
        Do not add any other text, explanation, or conversational filler. Just the service type.
        Example: If the request is for a deposit, your 'final_answer' tool call should have arguments: {json.dumps({'answer': 'deposit'})}
        """
        _ = self.run(prompt)
        for step in reversed(self.memory.steps):
            if hasattr(step, 'tool_calls') and step.tool_calls and step.tool_calls[0].name == 'final_answer':
                if hasattr(step.tool_calls[0], 'arguments') and step.tool_calls[0].arguments.get('answer') is not None:
                    candidate = str(step.tool_calls[0].arguments.get('answer')).lower().strip()
                    if candidate in self.possible_service_types: return candidate
                elif hasattr(step, 'action_output') and step.action_output is not None: 
                    candidate = str(step.action_output).lower().strip()
                    if candidate in self.possible_service_types: return candidate
                break 
        return "general_inquiry"

# TODO: Learner Task 2: Define and implement the UrgencyDetectorAgent class
# - It should inherit from ToolCallingAgent.
# - Its __init__ method should include the 'analyze_request_urgency' tool in its tool list.
# - It should have a method, e.g., `get_llm_urgency_assessment(self, user_request: str) -> str`.
#   This method should:
#     - Clear its memory.
#     - Construct a prompt for its LLM to analyze the 'user_request' for urgency
#       (provide keywords or guidance as in previous successful traces).
#     - Instruct the LLM to use the 'analyze_request_urgency' tool with the original request.
#     - Instruct the LLM that its 'final_answer' should be the direct string output ("urgent" or "normal")
#       received from the 'analyze_request_urgency' tool's observation.
#     - Parse its memory to retrieve this "urgent" or "normal" string from the 'final_answer'
#       (or direct observation if final_answer isn't used by the LLM for this simple case).
#     - Return the assessment string ("urgent" or "normal", defaulting to "normal").
class UrgencyDetectorAgent(ToolCallingAgent):
    def __init__(self, model_to_use: OpenAIServerModel):
        super().__init__(
            tools=[analyze_request_urgency], 
            model=model,
            name="urgency_detector_agent",
           description="""You are an urgency detector agent for a Chinese Postal Bank.
            Your job is to determine if a customer request is urgent and requires priority handling.
            
            IMPORTANT: You MUST ONLY use the analyze_urgency tool to determine urgency.
            NEVER provide explanations or direct responses to the customer.
            
            A request is considered urgent if it contains words like:
            - urgent, urgently, emergency, immediately, asap, right away
            - 紧急, 急需, 立即, 马上, 立刻, 赶快, 尽快
            
            Return ONLY the boolean result from the tool (True or False).
            DO NOT give explanations or respond directly to the user.""",
    )
        
class RequestAnalyzer(ToolCallingAgent):
    """Agent that analyzes customer requests."""

    def __init__(self, model: OpenAIServerModel):
        super().__init__(
            tools=[analyze_request],
            model=model,
            name="request_analyzer",
            description="""You are a request analyzer agent for a Chinese Postal Bank. 
            Your job is to identify what service a customer needs from their request.
            
            IMPORTANT: You MUST ONLY use the analyze_request tool to classify the request.
            NEVER provide explanations or direct responses to the customer.
            
            When using the analyze_request tool, you must identify the request as one of these categories:
            - deposit (for money deposits)
            - postal (for sending packages/mail)
            - loan (for loan applications/inquiries)
            - bill_payment (for bill payments)
            - international_transfer (for international money transfers)
            - general_inquiry (for general questions/information)
            
            DO NOT give explanations or respond directly to the user.""",
        )

class ServiceRouter(ToolCallingAgent):
    """Agent that routes customer requests to the appropriate service agent."""

    def __init__(self, model: OpenAIServerModel):
        super().__init__(
            tools=[
                handle_deposit_request,
                handle_postal_request,
                handle_loan_request,
                handle_bill_payment_request,
                handle_international_transfer_request,
                handle_general_inquiry_request,
            ],
            model=model,
            name="service_router",
            description="""You are a service router agent for a Chinese Postal Bank.
            Your job is to route the customer to the appropriate service handler based on the service type.
            
            IMPORTANT: You MUST ONLY use the appropriate handle_* tool. 
            DO NOT add additional explanations or messages.
            
            You will receive a direct instruction with the service and customer name to process,
            and whether the request is urgent. Simply execute the correct tool and return the result.
            
            If the request is urgent, make sure to set the is_urgent parameter to True.""",
        )


    def get_llm_urgency_assessment(self, user_request: str) -> str:
        self.memory.steps = []
        prompt = f"""
        Analyze the following customer request for urgency: "{user_request}"
        Keywords like 'urgent', 'emergency', 'immediately', 'asap', 'right away', 'right now',
        '紧急', '急需', '立即', '马上', '立刻', '赶快', '尽快', '迫切', '急迫' often indicate urgency.
        
        You MUST use the 'analyze_request_urgency' tool with the original request.
        Your final response, using the 'final_answer' tool, MUST be the direct string output ("urgent" or "normal") from the 'analyze_request_urgency' tool's observation.
        """
        _ = self.run(prompt)
        urgency_assessment = "normal" 
        for step in reversed(self.memory.steps):
            if hasattr(step, 'tool_calls') and step.tool_calls and step.tool_calls[0].name == 'final_answer':
                if hasattr(step.tool_calls[0], 'arguments') and step.tool_calls[0].arguments.get('answer') is not None:
                    assessment = str(step.tool_calls[0].arguments.get('answer')).lower().strip()
                    if assessment in ["urgent", "normal"]: return assessment
            elif hasattr(step, 'observations') and step.observations is not None: 
                assessment = str(step.observations).lower().strip()
                if assessment in ["urgent", "normal"]: return assessment
        return urgency_assessment


class ChineseBankPostOfficeAgent(ToolCallingAgent): 
    """Enhanced agent for the Chinese Bank Post Office that includes urgency detection."""

    def __init__(self, model: OpenAIServerModel):
        self.urgency_detector = UrgencyDetectorAgent(model)
        self.request_analyzer = RequestAnalyzer(model)
        self.service_router = ServiceRouter(model)
        super().__init__(
            tools=[],
            model=model,
            name="enhanced_bank_post_office_agent",
            description="Enhanced agent for the Chinese Postal Bank that analyzes urgency and routes customer requests.",
        )

    def handle_customer_request(self, customer_name: str, request: str, expected_service: str) -> str:
        """Handles a customer request by analyzing urgency, service type, and routing appropriately.

        Args:
            customer_name: The name of the customer.
            request: The customer's request.
            expected_service: The service we expect this request to be routed to.

        Returns:
            The response from the service agent.
        """
        # Track total requests
        booking_manager.routing_accuracy["total_requests"] += 1
        
        # Step 1: Detect if the request is urgent
        urgency_prompt = f"""
        Determine if this customer request is urgent: "{request}"
        
        Use the analyze_urgency tool and return ONLY true or false.
        Do not include any explanation or additional text.
        """
        
        urgency_result = self.urgency_detector.run(urgency_prompt).strip().lower()
        is_urgent = "true" in urgency_result  # Parse the string response to a boolean
        
        # Step 2: Get the service type
        analyzer_prompt = f"""
        You are a service classifier that ONLY returns service type categories.
        
        Analyze this customer request: "{request}"
        
        Choose EXACTLY ONE service type from this list:
        - deposit
        - postal
        - loan
        - bill_payment
        - international_transfer
        - general_inquiry
        
        Return ONLY the service type as a single word. Do not include any explanation, 
        additional text, or punctuation. Just the service type alone.
        """
        
        service_type = self.request_analyzer.run(analyzer_prompt).strip().lower()
        
        # Clean up response to ensure it's just a service type
        for valid_type in ["deposit", "postal", "loan", "bill_payment", "international_transfer", "general_inquiry"]:
            if valid_type in service_type:
                service_type = valid_type
                break
        else:
            # Default if no valid type found
            service_type = "general_inquiry"
        
        # Step 3: Route to the service handler with urgency information
        router_prompt = f"""
        Execute the handle_{service_type} tool with:
        - customer_name: '{customer_name}'
        - is_urgent: {is_urgent}
        
        Do not add any explanation or additional text. Just execute the tool.
        """
        
        # Route to the service handler with explicit prompt
        return self.service_router.run(router_prompt)
    
def print_state():
    print("\n" + "=" * 80 + "\nFINAL SYSTEM STATE\n" + "=" * 80)
    print("\nRemaining Service Availability:")
    for service, count in booking_manager.availability.items():
        print(f"  - {service}: {'∞' if count == float('inf') else count} slots")
    print("\nBookings Completed:")
    if not any(booking_manager.bookings.values()):
        print("  No bookings were made.")
    else:
        for service, bookings_list in booking_manager.bookings.items():
            if bookings_list: 
                customers_details = []
                for b_detail in bookings_list:
                    cust_str = b_detail["customer"]
                    if b_detail.get("is_urgent"): 
                        cust_str += " (URGENT)"
                    customers_details.append(cust_str)
                print(f"  - {service}: {', '.join(customers_details)}")
    
    accuracy = 0
    if booking_manager.routing_accuracy["total_requests"] > 0:
        accuracy = (booking_manager.routing_accuracy["correct_service_type"] / 
                   booking_manager.routing_accuracy["total_requests"]) * 100
    
    print("\nPerformance Metrics:")
    print(f"  - Total Requests: {booking_manager.routing_accuracy['total_requests']}")
    print(f"  - Correctly Routed (metric): {booking_manager.routing_accuracy['correct_service_type']}")
    print(f"  - Routing Accuracy: {accuracy:.1f}%")
    print(f"  - Special Handling Applied: {booking_manager.routing_accuracy['special_handling_applied']} times")
    print(f"  - Urgent Requests Identified by LLM: {booking_manager.routing_accuracy['urgent_requests_identified_by_llm']}")
    print(f"  - Urgent Requests Processed as Urgent: {booking_manager.routing_accuracy['urgent_requests_processed_as_urgent']}")

    if accuracy >= 80 and booking_manager.routing_accuracy["special_handling_applied"] >= 2: 
        print("\n✅ System demonstrated effective routing and special case handling!")
    else:
        print("\n⚠️ System may need improvement in routing or special case handling (or urgency metrics if added to criteria).")
    print("=" * 80)

if __name__ == "__main__":
    bank_post_office_agent = ChineseBankPostOfficeAgent(model)
    
    print("🏦 Chinese Postal Bank Service Demo - Urgency Exercise Starter 🏦\n")

    test_cases = [
        {"name": "Wang Xiaoming (王小明)", "request": "I need to deposit money into my account. (我需要存一些钱到我的账户。)", "expected_service": "deposit"},
        {"name": "Li Jiayi (李佳怡)", "request": "I want to send a package to Shanghai. (我想邮寄一个包裹到上海。)", "expected_service": "postal"},
        {"name": "Emergency Customer (紧急客户)", "request": "URGENT! I must transfer money abroad immediately for an emergency! (紧急！我必须立即向国外汇款处理急事！)", "expected_service": "international_transfer"},
        {"name": "Chen Student (陈学生)", "request": "How do I apply for a student loan? (我该如何申请学生贷款？)", "expected_service": "loan"},
        {"name": "Zhang Senior (张老先生)", "request": "I need help paying my electricity bill. It's due tomorrow!", "expected_service": "bill_payment"}, 
        {"name": "Ms. Qian (钱女士)", "request": "I want to transfer money to my son in Canada. (我想给我在加拿大的儿子转账。)", "expected_service": "international_transfer"},
        {"name": "Mr. Zhao (赵先生)", "request": "What are the business hours for the Beijing branch? (北京分行的营业时间是什么时候？)", "expected_service": "general_inquiry"}
    ]
    
    for case in test_cases:
        response = bank_post_office_agent.handle_customer_request(case['name'], case['request'], case['expected_service'])
        time.sleep(0.5) 
    
    print_state()