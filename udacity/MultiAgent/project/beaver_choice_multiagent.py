"""
Beaver's Choice Paper Company - Multi-Agent System
==================================================
A comprehensive multi-agent system for managing inventory, generating quotes, and processing sales.

Author: AI Consultant
Date: January 2026
Framework: smolagents with OpenAI
"""

import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union, Optional, Any
from sqlalchemy import create_engine, Engine
from dataclasses import dataclass, field
from smolagents import OpenAIServerModel, ToolCallingAgent, tool

# Load environment variables
dotenv.load_dotenv()

# Database engine
db_engine = create_engine("sqlite:///munder_difflin.db")

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class InventoryItem:
    """Represents an inventory item with pricing and stock information"""
    item_name: str
    category: str
    unit_price: float
    current_stock: int = 0
    min_stock_level: int = 100

@dataclass
class QuoteRequest:
    """Represents a customer quote request"""
    customer_request: str
    request_date: str
    job_type: Optional[str] = None
    order_size: Optional[str] = None
    event_type: Optional[str] = None

@dataclass
class Quote:
    """Represents a generated quote"""
    items: List[Dict[str, Any]]
    total_amount: float
    quote_explanation: str
    estimated_delivery_date: str
    request_date: str

@dataclass
class SalesTransaction:
    """Represents a completed sales transaction"""
    item_name: str
    quantity: int
    unit_price: float
    total_price: float
    transaction_date: str
    customer_info: str

@dataclass
class StockOrder:
    """Represents a stock replenishment order"""
    item_name: str
    quantity: int
    unit_price: float
    total_cost: float
    order_date: str
    expected_delivery: str

# ============================================================================
# PAPER SUPPLIES DATABASE
# ============================================================================

paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},

    # Large-format items
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# ============================================================================
# DATABASE UTILITY FUNCTIONS
# ============================================================================

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """Generate inventory for a random subset of paper supplies"""
    np.random.seed(seed)
    num_items = int(len(paper_supplies) * coverage)
    selected_indices = np.random.choice(range(len(paper_supplies)), size=num_items, replace=False)
    selected_items = [paper_supplies[i] for i in selected_indices]
    
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),
            "min_stock_level": np.random.randint(50, 150)
        })
    
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:
    """Initialize the database with all required tables and initial data"""
    try:
        # Create transactions table
        transactions_schema = pd.DataFrame({
            "id": [], "item_name": [], "transaction_type": [],
            "units": [], "price": [], "transaction_date": []
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)
        
        initial_date = datetime(2025, 1, 1).isoformat()
        
        # Load quote requests
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)
        
        # Load quotes
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date
        
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))
        
        quotes_df = quotes_df[["request_id", "total_amount", "quote_explanation", "order_date", "job_type", "order_size", "event_type"]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)
        
        # Generate inventory
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)
        
        # Seed initial transactions
        initial_transactions = []
        initial_transactions.append({
            "item_name": None, "transaction_type": "sales",
            "units": None, "price": 50000.0, "transaction_date": initial_date
        })
        
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"], "transaction_type": "stock_orders",
                "units": item["current_stock"], "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date
            })
        
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)
        
        return db_engine
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(item_name: str, transaction_type: str, quantity: int, price: float, date: Union[str, datetime]) -> int:
    """Create a new transaction record"""
    try:
        date_str = date.isoformat() if isinstance(date, datetime) else date
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")
        
        transaction = pd.DataFrame([{
            "item_name": item_name, "transaction_type": transaction_type,
            "units": quantity, "price": price, "transaction_date": date_str
        }])
        
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])
    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """Get all inventory levels as of a specific date"""
    query = """
        SELECT item_name,
               SUM(CASE WHEN transaction_type = 'stock_orders' THEN units
                        WHEN transaction_type = 'sales' THEN -units
                        ELSE 0 END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """Get stock level for a specific item"""
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()
    
    query = """
        SELECT item_name,
               COALESCE(SUM(CASE WHEN transaction_type = 'stock_orders' THEN units
                                 WHEN transaction_type = 'sales' THEN -units
                                 ELSE 0 END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name AND transaction_date <= :as_of_date
    """
    return pd.read_sql(query, db_engine, params={"item_name": item_name, "as_of_date": as_of_date})

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """Calculate supplier delivery date based on quantity"""
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        input_date_dt = datetime.now()
    
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7
    
    delivery_date_dt = input_date_dt + timedelta(days=days)
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """Get current cash balance"""
    try:
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()
        
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine, params={"as_of_date": as_of_date}
        )
        
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)
        return 0.0
    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0

def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """Generate comprehensive financial report"""
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()
    
    cash = get_cash_balance(as_of_date)
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []
    
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value
        inventory_summary.append({
            "item_name": item["item_name"], "stock": stock,
            "unit_price": item["unit_price"], "value": item_value
        })
    
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    
    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_sales.to_dict(orient="records")
    }

def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """Search historical quotes by keywords"""
    conditions = []
    params = {}
    
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(f"(LOWER(qr.response) LIKE :{param_name} OR LOWER(q.quote_explanation) LIKE :{param_name})")
        params[param_name] = f"%{term.lower()}%"
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    query = f"""
        SELECT qr.response AS original_request, q.total_amount, q.quote_explanation,
               q.job_type, q.order_size, q.event_type, q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """
    
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

# ============================================================================
# SMOLAGENTS TOOLS
# ============================================================================

@tool
def check_inventory_status(item_name: str, request_date: str) -> str:
    """
    Check the current stock level for a specific item.
    
    Args:
        item_name: The exact name of the inventory item
        request_date: The date in YYYY-MM-DD format
    
    Returns:
        A string describing the current stock level and pricing information
    """
    try:
        # Get item info from inventory catalog
        inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
        item_info = inventory_df[inventory_df["item_name"] == item_name]
        
        if item_info.empty:
            return f"Item '{item_name}' not found in inventory catalog."
        
        # Get current stock level
        stock_info = get_stock_level(item_name, request_date)
        current_stock = int(stock_info["current_stock"].iloc[0])
        unit_price = float(item_info["unit_price"].iloc[0])
        min_stock = int(item_info["min_stock_level"].iloc[0])
        
        result = f"Item: {item_name}\n"
        result += f"Current Stock: {current_stock} units\n"
        result += f"Unit Price: ${unit_price:.2f}\n"
        result += f"Minimum Stock Level: {min_stock} units\n"
        
        if current_stock < min_stock:
            result += f"⚠️ WARNING: Stock is below minimum level. Reorder recommended.\n"
        
        return result
    except Exception as e:
        return f"Error checking inventory: {str(e)}"

@tool
def get_all_available_items(request_date: str) -> str:
    """
    Get a list of all items currently in stock.
    
    Args:
        request_date: The date in YYYY-MM-DD format
    
    Returns:
        A formatted string listing all available items with stock levels
    """
    try:
        inventory = get_all_inventory(request_date)
        inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
        
        result = "Available Inventory:\n"
        result += "=" * 80 + "\n"
        
        for item_name, stock in inventory.items():
            item_info = inventory_df[inventory_df["item_name"] == item_name]
            if not item_info.empty:
                price = float(item_info["unit_price"].iloc[0])
                category = item_info["category"].iloc[0]
                result += f"- {item_name} ({category}): {stock} units @ ${price:.2f}/unit\n"
        
        return result
    except Exception as e:
        return f"Error getting inventory list: {str(e)}"

@tool
def reorder_inventory(item_name: str, quantity: int, request_date: str) -> str:
    """
    Place an order to restock inventory for a specific item.
    
    Args:
        item_name: The exact name of the item to reorder
        quantity: The number of units to order
        request_date: The date in YYYY-MM-DD format
    
    Returns:
        Confirmation of the order with delivery date and cost
    """
    try:
        # Get item pricing
        inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
        item_info = inventory_df[inventory_df["item_name"] == item_name]
        
        if item_info.empty:
            return f"Error: Item '{item_name}' not found in catalog."
        
        unit_price = float(item_info["unit_price"].iloc[0])
        total_cost = unit_price * quantity
        
        # Check if we have enough cash
        current_cash = get_cash_balance(request_date)
        if current_cash < total_cost:
            return f"Error: Insufficient funds. Cost: ${total_cost:.2f}, Available: ${current_cash:.2f}"
        
        # Calculate delivery date
        delivery_date = get_supplier_delivery_date(request_date, quantity)
        
        # Create stock order transaction
        transaction_id = create_transaction(
            item_name=item_name,
            transaction_type="stock_orders",
            quantity=quantity,
            price=total_cost,
            date=delivery_date
        )
        
        result = f"✓ Stock order placed successfully!\n"
        result += f"Transaction ID: {transaction_id}\n"
        result += f"Item: {item_name}\n"
        result += f"Quantity: {quantity} units\n"
        result += f"Unit Price: ${unit_price:.2f}\n"
        result += f"Total Cost: ${total_cost:.2f}\n"
        result += f"Order Date: {request_date}\n"
        result += f"Expected Delivery: {delivery_date}\n"
        
        return result
    except Exception as e:
        return f"Error placing stock order: {str(e)}"

@tool
def search_historical_quotes(keywords: str) -> str:
    """
    Search through historical quotes to find similar past orders.
    
    Args:
        keywords: Comma-separated keywords to search for (e.g., "wedding, party, corporate")
    
    Returns:
        A formatted string with relevant historical quotes
    """
    try:
        search_terms = [term.strip() for term in keywords.split(",")]
        quotes = search_quote_history(search_terms, limit=5)
        
        if not quotes:
            return "No matching historical quotes found."
        
        result = f"Found {len(quotes)} relevant historical quotes:\n"
        result += "=" * 80 + "\n"
        
        for i, quote in enumerate(quotes, 1):
            result += f"\n{i}. Request: {quote['original_request'][:100]}...\n"
            result += f"   Total Amount: ${quote['total_amount']:.2f}\n"
            result += f"   Job Type: {quote.get('job_type', 'N/A')}\n"
            result += f"   Order Size: {quote.get('order_size', 'N/A')}\n"
            result += f"   Explanation: {quote['quote_explanation'][:150]}...\n"
        
        return result
    except Exception as e:
        return f"Error searching quotes: {str(e)}"

@tool
def generate_customer_quote(items_and_quantities: str, request_date: str) -> str:
    """
    Generate a detailed quote for a customer order.
    
    Args:
        items_and_quantities: A string in format "item1:qty1,item2:qty2" (e.g., "A4 paper:500,Envelopes:100")
        request_date: The date in YYYY-MM-DD format
    
    Returns:
        A detailed quote with pricing and delivery information
    """
    try:
        # Parse items and quantities
        items_list = []
        for item_spec in items_and_quantities.split(","):
            parts = item_spec.strip().split(":")
            if len(parts) == 2:
                items_list.append({"item": parts[0].strip(), "quantity": int(parts[1].strip())})
        
        if not items_list:
            return "Error: Invalid format. Use 'item1:qty1,item2:qty2'"
        
        # Get inventory and pricing
        inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
        current_inventory = get_all_inventory(request_date)
        
        quote_items = []
        total_amount = 0.0
        unavailable_items = []
        max_delivery_days = 0
        
        for item_dict in items_list:
            item_name = item_dict["item"]
            quantity = item_dict["quantity"]
            
            # Check if item exists in catalog
            item_info = inventory_df[inventory_df["item_name"] == item_name]
            if item_info.empty:
                unavailable_items.append(f"{item_name} (not in catalog)")
                continue
            
            unit_price = float(item_info["unit_price"].iloc[0])
            available_stock = current_inventory.get(item_name, 0)
            
            if available_stock < quantity:
                unavailable_items.append(f"{item_name} (only {available_stock} available, need {quantity})")
                continue
            
            # Calculate delivery time based on quantity
            if quantity <= 10:
                delivery_days = 0
            elif quantity <= 100:
                delivery_days = 1
            elif quantity <= 1000:
                delivery_days = 3
            else:
                delivery_days = 5
            
            max_delivery_days = max(max_delivery_days, delivery_days)
            
            item_total = unit_price * quantity
            total_amount += item_total
            
            quote_items.append({
                "item": item_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "total": item_total
            })
        
        # Calculate delivery date
        delivery_date = (datetime.fromisoformat(request_date) + timedelta(days=max_delivery_days)).strftime("%Y-%m-%d")
        
        # Build quote response
        result = "QUOTE DETAILS\n"
        result += "=" * 80 + "\n"
        result += f"Quote Date: {request_date}\n"
        result += f"Estimated Delivery: {delivery_date}\n\n"
        
        if quote_items:
            result += "Items:\n"
            for item in quote_items:
                result += f"  - {item['item']}: {item['quantity']} units @ ${item['unit_price']:.2f} = ${item['total']:.2f}\n"
            
            result += f"\nSubtotal: ${total_amount:.2f}\n"
            tax = total_amount * 0.08  # 8% tax
            result += f"Tax (8%): ${tax:.2f}\n"
            result += f"TOTAL: ${total_amount + tax:.2f}\n"
        
        if unavailable_items:
            result += f"\n⚠️ Unavailable Items:\n"
            for item in unavailable_items:
                result += f"  - {item}\n"
        
        return result
    except Exception as e:
        return f"Error generating quote: {str(e)}"

@tool
def finalize_sale(items_and_quantities: str, request_date: str) -> str:
    """
    Process and finalize a sale transaction.
    
    Args:
        items_and_quantities: A string in format "item1:qty1,item2:qty2"
        request_date: The date in YYYY-MM-DD format
    
    Returns:
        Confirmation of the completed sale
    """
    try:
        # Parse items
        items_list = []
        for item_spec in items_and_quantities.split(","):
            parts = item_spec.strip().split(":")
            if len(parts) == 2:
                items_list.append({"item": parts[0].strip(), "quantity": int(parts[1].strip())})
        
        if not items_list:
            return "Error: Invalid format. Use 'item1:qty1,item2:qty2'"
        
        # Get inventory
        inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
        current_inventory = get_all_inventory(request_date)
        
        transaction_ids = []
        total_revenue = 0.0
        errors = []
        
        for item_dict in items_list:
            item_name = item_dict["item"]
            quantity = item_dict["quantity"]
            
            # Validate item
            item_info = inventory_df[inventory_df["item_name"] == item_name]
            if item_info.empty:
                errors.append(f"{item_name}: not in catalog")
                continue
            
            unit_price = float(item_info["unit_price"].iloc[0])
            available_stock = current_inventory.get(item_name, 0)
            
            if available_stock < quantity:
                errors.append(f"{item_name}: insufficient stock (available: {available_stock}, requested: {quantity})")
                continue
            
            # Create sales transaction
            sale_total = unit_price * quantity
            transaction_id = create_transaction(
                item_name=item_name,
                transaction_type="sales",
                quantity=quantity,
                price=sale_total,
                date=request_date
            )
            
            transaction_ids.append(transaction_id)
            total_revenue += sale_total
        
        # Build response
        result = "SALE COMPLETED\n"
        result += "=" * 80 + "\n"
        result += f"Transaction Date: {request_date}\n"
        result += f"Transaction IDs: {', '.join(map(str, transaction_ids))}\n"
        result += f"Total Revenue: ${total_revenue:.2f}\n"
        
        if errors:
            result += f"\n⚠️ Errors:\n"
            for error in errors:
                result += f"  - {error}\n"
        
        # Update inventory and check for reorder needs
        result += f"\n✓ Sale processed successfully!\n"
        
        return result
    except Exception as e:
        return f"Error processing sale: {str(e)}"

@tool
def get_current_financial_status(request_date: str) -> str:
    """
    Get the current financial status including cash and inventory value.
    
    Args:
        request_date: The date in YYYY-MM-DD format
    
    Returns:
        A financial summary report
    """
    try:
        report = generate_financial_report(request_date)
        
        result = "FINANCIAL STATUS REPORT\n"
        result += "=" * 80 + "\n"
        result += f"Report Date: {report['as_of_date']}\n\n"
        result += f"Cash Balance: ${report['cash_balance']:.2f}\n"
        result += f"Inventory Value: ${report['inventory_value']:.2f}\n"
        result += f"Total Assets: ${report['total_assets']:.2f}\n\n"
        
        if report['top_selling_products']:
            result += "Top Selling Products:\n"
            for product in report['top_selling_products']:
                result += f"  - {product['item_name']}: {product['total_units']} units, ${product['total_revenue']:.2f} revenue\n"
        
        return result
    except Exception as e:
        return f"Error generating financial report: {str(e)}"

# ============================================================================
# MULTI-AGENT SYSTEM
# ============================================================================

# Initialize model
model = OpenAIServerModel(
    model_id="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    api_base="https://api.openai.com/v1"
)

# ============================================================================
# SPECIALIZED AGENTS
# ============================================================================

# Inventory Management Agent
inventory_agent = ToolCallingAgent(
    tools=[check_inventory_status, get_all_available_items, reorder_inventory, get_current_financial_status],
    model=model,
    name="inventory_agent",
    description="Manages inventory levels, checks stock, and handles reordering"
)

# Quote Generation Agent
quote_agent = ToolCallingAgent(
    tools=[search_historical_quotes, generate_customer_quote, check_inventory_status, get_all_available_items],
    model=model,
    name="quote_agent",
    description="Generates accurate quotes based on customer requests and historical data"
)

# Sales Agent
sales_agent = ToolCallingAgent(
    tools=[finalize_sale, check_inventory_status, get_current_financial_status],
    model=model,
    name="sales_agent",
    description="Processes and finalizes sales transactions"
)

# ============================================================================
# ORCHESTRATOR AGENT
# ============================================================================

orchestrator_agent = ToolCallingAgent(
    tools=[
        check_inventory_status,
        get_all_available_items,
        reorder_inventory,
        search_historical_quotes,
        generate_customer_quote,
        finalize_sale,
        get_current_financial_status
    ],
    model=model,
    name="orchestrator",
    description="Main orchestrator that coordinates all operations for Beaver's Choice Paper Company"
)

# ============================================================================
# MAIN ORCHESTRATION FUNCTION
# ============================================================================

def process_customer_request(request: str, request_date: str) -> str:
    """
    Process a customer request through the multi-agent system.
    
    Args:
        request: The customer's request text
        request_date: The date of the request in YYYY-MM-DD format
    
    Returns:
        The agent's response
    """
    try:
        # Create a comprehensive prompt for the orchestrator
        prompt = f"""
You are the main orchestrator for Beaver's Choice Paper Company. Process the following customer request.

Current Date: {request_date}

Customer Request: {request}

Your tasks:
1. If the request is about inventory status or checking stock, use inventory tools
2. If the request asks for a quote, search historical quotes for context, check inventory availability, and generate a detailed quote
3. If the request is to complete a purchase/sale, verify inventory, finalize the sale, and check if reordering is needed
4. Always provide clear, professional responses with specific details

Important guidelines:
- Check current inventory availability before making commitments
- Review historical quotes for similar requests to ensure competitive pricing
- After completing a sale, check if any items need reordering (below minimum stock levels)
- Always include relevant dates in your response
- Be specific about quantities, prices, and delivery timelines

Now process the request and provide a comprehensive response.
"""
        
        response = orchestrator_agent.run(prompt)
        return str(response)
        
    except Exception as e:
        return f"Error processing request: {str(e)}"

# ============================================================================
# TEST SCENARIOS
# ============================================================================

def run_test_scenarios():
    """Run the multi-agent system through test scenarios"""
    print("\n" + "=" * 80)
    print("BEAVER'S CHOICE PAPER COMPANY - MULTI-AGENT SYSTEM")
    print("=" * 80 + "\n")
    
    print("Initializing Database...")
    init_database(db_engine)
    
    try:
        # Load test data
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
        
        print(f"✓ Loaded {len(quote_requests_sample)} test requests\n")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return
    
    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]
    
    print(f"Initial Financial Status (as of {initial_date}):")
    print(f"  Cash Balance: ${current_cash:.2f}")
    print(f"  Inventory Value: ${current_inventory:.2f}")
    print(f"  Total Assets: ${current_cash + current_inventory:.2f}\n")
    
    results = []
    
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")
        
        print("\n" + "=" * 80)
        print(f"REQUEST {idx+1} of {len(quote_requests_sample)}")
        print("=" * 80)
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")
        print(f"\nCustomer Request: {row['request']}")
        print("-" * 80)
        
        # Process request through multi-agent system
        request_with_date = f"{row['request']} (Date of request: {request_date})"
        
        try:
            response = process_customer_request(request_with_date, request_date)
            print(f"\nAgent Response:\n{response}")
        except Exception as e:
            response = f"Error processing request: {str(e)}"
            print(f"\n⚠️ {response}")
        
        # Update financial state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]
        
        print(f"\nUpdated Financial Status:")
        print(f"  Cash: ${current_cash:.2f}")
        print(f"  Inventory: ${current_inventory:.2f}")
        
        results.append({
            "request_id": idx + 1,
            "request_date": request_date,
            "job": row['job'],
            "event": row['event'],
            "request": row['request'],
            "cash_balance": current_cash,
            "inventory_value": current_inventory,
            "response": response
        })
        
        time.sleep(2)  # Rate limiting
    
    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    
    print("\n" + "=" * 80)
    print("FINAL FINANCIAL REPORT")
    print("=" * 80)
    print(f"Report Date: {final_date}")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")
    print(f"Total Assets: ${final_report['total_assets']:.2f}")
    
    if final_report['top_selling_products']:
        print(f"\nTop Selling Products:")
        for i, product in enumerate(final_report['top_selling_products'], 1):
            print(f"  {i}. {product['item_name']}: {product['total_units']} units, ${product['total_revenue']:.2f}")
    
    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)
    print(f"\n✓ Results saved to test_results.csv")
    
    return results

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    results = run_test_scenarios()
