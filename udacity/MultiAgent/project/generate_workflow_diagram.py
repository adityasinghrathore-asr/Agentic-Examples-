"""
Flow Diagram Generator for Beaver's Choice Paper Company Multi-Agent System
===========================================================================
This script generates a comprehensive workflow diagram showing the multi-agent
system architecture using NetworkX and Matplotlib.

Author: AI Consultant
Date: January 2026
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import networkx as nx
from datetime import datetime

def create_workflow_diagram():
    """Generate a comprehensive workflow diagram for the multi-agent system"""
    
    # Create figure with larger size for better visibility
    fig, ax = plt.subplots(1, 1, figsize=(20, 14))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Define colors
    color_customer = '#FFE6E6'
    color_orchestrator = '#E6F3FF'
    color_agent = '#E6FFE6'
    color_tool = '#FFF9E6'
    color_database = '#F0E6FF'
    
    # Title
    title_text = "Beaver's Choice Paper Company\nMulti-Agent System Workflow"
    ax.text(5, 9.5, title_text, ha='center', va='top', fontsize=20, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', edgecolor='navy', linewidth=2))
    
    # ========================================================================
    # LAYER 1: Customer Input
    # ========================================================================
    customer_box = FancyBboxPatch((0.5, 8), 2, 0.6, 
                                   boxstyle="round,pad=0.1", 
                                   facecolor=color_customer,
                                   edgecolor='darkred', linewidth=2)
    ax.add_patch(customer_box)
    ax.text(1.5, 8.3, "Customer Request", ha='center', va='center', 
            fontsize=12, fontweight='bold')
    ax.text(1.5, 8.15, "(Inventory/Quote/Sale)", ha='center', va='center', 
            fontsize=9, style='italic')
    
    # ========================================================================
    # LAYER 2: Orchestrator Agent
    # ========================================================================
    orchestrator_box = FancyBboxPatch((3.5, 7.5), 3, 1, 
                                      boxstyle="round,pad=0.15", 
                                      facecolor=color_orchestrator,
                                      edgecolor='darkblue', linewidth=3)
    ax.add_patch(orchestrator_box)
    ax.text(5, 8.2, "ORCHESTRATOR AGENT", ha='center', va='center', 
            fontsize=14, fontweight='bold')
    ax.text(5, 7.9, "Request Router & Coordinator", ha='center', va='center', 
            fontsize=10, style='italic')
    ax.text(5, 7.7, "• Analyzes request type", ha='center', va='center', fontsize=8)
    
    # Arrow from customer to orchestrator
    arrow1 = FancyArrowPatch((2.5, 8.3), (3.5, 8),
                            arrowstyle='->', mutation_scale=30, linewidth=2.5,
                            color='darkblue')
    ax.add_patch(arrow1)
    ax.text(3, 8.5, "Submit\nRequest", ha='center', va='center', 
            fontsize=9, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # ========================================================================
    # LAYER 3: Specialized Agents
    # ========================================================================
    agent_y = 5.8
    
    # Inventory Agent
    inv_agent = FancyBboxPatch((0.2, agent_y), 2.5, 1.2, 
                               boxstyle="round,pad=0.1", 
                               facecolor=color_agent,
                               edgecolor='darkgreen', linewidth=2)
    ax.add_patch(inv_agent)
    ax.text(1.45, agent_y + 0.95, "INVENTORY AGENT", ha='center', va='center', 
            fontsize=11, fontweight='bold')
    ax.text(1.45, agent_y + 0.65, "Responsibilities:", ha='center', va='center', 
            fontsize=9, fontweight='bold')
    ax.text(1.45, agent_y + 0.45, "• Check stock levels", ha='center', va='center', fontsize=8)
    ax.text(1.45, agent_y + 0.25, "• Monitor inventory", ha='center', va='center', fontsize=8)
    ax.text(1.45, agent_y + 0.05, "• Reorder supplies", ha='center', va='center', fontsize=8)
    
    # Quote Agent
    quote_agent = FancyBboxPatch((3.5, agent_y), 2.5, 1.2, 
                                 boxstyle="round,pad=0.1", 
                                 facecolor=color_agent,
                                 edgecolor='darkgreen', linewidth=2)
    ax.add_patch(quote_agent)
    ax.text(4.75, agent_y + 0.95, "QUOTE AGENT", ha='center', va='center', 
            fontsize=11, fontweight='bold')
    ax.text(4.75, agent_y + 0.65, "Responsibilities:", ha='center', va='center', 
            fontsize=9, fontweight='bold')
    ax.text(4.75, agent_y + 0.45, "• Search historical data", ha='center', va='center', fontsize=8)
    ax.text(4.75, agent_y + 0.25, "• Generate quotes", ha='center', va='center', fontsize=8)
    ax.text(4.75, agent_y + 0.05, "• Calculate pricing", ha='center', va='center', fontsize=8)
    
    # Sales Agent
    sales_agent = FancyBboxPatch((6.8, agent_y), 2.5, 1.2, 
                                 boxstyle="round,pad=0.1", 
                                 facecolor=color_agent,
                                 edgecolor='darkgreen', linewidth=2)
    ax.add_patch(sales_agent)
    ax.text(8.05, agent_y + 0.95, "SALES AGENT", ha='center', va='center', 
            fontsize=11, fontweight='bold')
    ax.text(8.05, agent_y + 0.65, "Responsibilities:", ha='center', va='center', 
            fontsize=9, fontweight='bold')
    ax.text(8.05, agent_y + 0.45, "• Process transactions", ha='center', va='center', fontsize=8)
    ax.text(8.05, agent_y + 0.25, "• Finalize sales", ha='center', va='center', fontsize=8)
    ax.text(8.05, agent_y + 0.05, "• Update records", ha='center', va='center', fontsize=8)
    
    # Arrows from orchestrator to agents
    arrow2 = FancyArrowPatch((4.2, 7.5), (1.8, 7.0),
                            arrowstyle='->', mutation_scale=25, linewidth=2,
                            color='green', linestyle='--')
    ax.add_patch(arrow2)
    ax.text(2.8, 7.3, "Inventory\nQuery", ha='center', va='center', 
            fontsize=8, bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    arrow3 = FancyArrowPatch((5, 7.5), (4.75, 7.0),
                            arrowstyle='->', mutation_scale=25, linewidth=2,
                            color='green', linestyle='--')
    ax.add_patch(arrow3)
    ax.text(5.2, 7.3, "Quote\nRequest", ha='center', va='center', 
            fontsize=8, bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    arrow4 = FancyArrowPatch((5.8, 7.5), (7.7, 7.0),
                            arrowstyle='->', mutation_scale=25, linewidth=2,
                            color='green', linestyle='--')
    ax.add_patch(arrow4)
    ax.text(7.0, 7.3, "Sales\nOrder", ha='center', va='center', 
            fontsize=8, bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    # ========================================================================
    # LAYER 4: Tools
    # ========================================================================
    tool_y = 3.8
    
    # Tool boxes
    tools = [
        (0.3, "check_inventory_status", "Check Stock\nLevels"),
        (1.5, "reorder_inventory", "Place Stock\nOrders"),
        (2.7, "get_all_available_items", "List All\nInventory"),
        (3.9, "search_historical_quotes", "Search Past\nQuotes"),
        (5.1, "generate_customer_quote", "Generate\nQuotes"),
        (6.3, "finalize_sale", "Process\nSales"),
        (7.5, "get_current_financial_status", "Financial\nReport")
    ]
    
    ax.text(5, tool_y + 1.5, "TOOL LAYER - Specialized Functions", ha='center', va='center', 
            fontsize=12, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightyellow', edgecolor='orange', linewidth=2))
    
    for x_pos, tool_id, tool_label in tools:
        tool_box = FancyBboxPatch((x_pos, tool_y), 1.0, 0.7, 
                                  boxstyle="round,pad=0.05", 
                                  facecolor=color_tool,
                                  edgecolor='darkorange', linewidth=1.5)
        ax.add_patch(tool_box)
        ax.text(x_pos + 0.5, tool_y + 0.35, tool_label, ha='center', va='center', 
                fontsize=7, fontweight='bold')
    
    # Arrows from agents to tools
    # Inventory Agent to Tools
    for x_pos in [0.8, 2.0, 3.2]:
        arrow = FancyArrowPatch((1.45, agent_y), (x_pos, tool_y + 0.7),
                               arrowstyle='->', mutation_scale=15, linewidth=1.5,
                               color='gray', alpha=0.6, linestyle=':')
        ax.add_patch(arrow)
    
    # Quote Agent to Tools
    for x_pos in [3.2, 4.4, 5.6]:
        arrow = FancyArrowPatch((4.75, agent_y), (x_pos, tool_y + 0.7),
                               arrowstyle='->', mutation_scale=15, linewidth=1.5,
                               color='gray', alpha=0.6, linestyle=':')
        ax.add_patch(arrow)
    
    # Sales Agent to Tools
    for x_pos in [6.8, 8.0]:
        arrow = FancyArrowPatch((8.05, agent_y), (x_pos, tool_y + 0.7),
                               arrowstyle='->', mutation_scale=15, linewidth=1.5,
                               color='gray', alpha=0.6, linestyle=':')
        ax.add_patch(arrow)
    
    # ========================================================================
    # LAYER 5: Database Layer
    # ========================================================================
    db_y = 2.0
    
    # Database main box
    db_box = FancyBboxPatch((2.5, db_y), 5, 1.3, 
                           boxstyle="round,pad=0.15", 
                           facecolor=color_database,
                           edgecolor='purple', linewidth=3)
    ax.add_patch(db_box)
    ax.text(5, db_y + 1.05, "DATABASE LAYER (SQLite)", ha='center', va='center', 
            fontsize=13, fontweight='bold')
    
    # Database tables
    tables = [
        (2.7, "Inventory"),
        (3.6, "Transactions"),
        (4.5, "Quotes"),
        (5.4, "Quote Requests"),
        (6.3, "Financial Records")
    ]
    
    for x_pos, table_name in tables:
        table_box = FancyBboxPatch((x_pos, db_y + 0.15), 0.8, 0.4, 
                                   boxstyle="round,pad=0.03", 
                                   facecolor='white',
                                   edgecolor='purple', linewidth=1)
        ax.add_patch(table_box)
        ax.text(x_pos + 0.4, db_y + 0.35, table_name, ha='center', va='center', 
                fontsize=7, fontweight='bold')
    
    # Arrows from tools to database
    for x_pos, _, _ in tools:
        arrow = FancyArrowPatch((x_pos + 0.5, tool_y), (5, db_y + 1.3),
                               arrowstyle='<->', mutation_scale=15, linewidth=1,
                               color='purple', alpha=0.4, linestyle='-.')
        ax.add_patch(arrow)
    
    # ========================================================================
    # LAYER 6: Output Layer
    # ========================================================================
    output_y = 0.5
    
    output_box = FancyBboxPatch((3, output_y), 4, 0.8, 
                               boxstyle="round,pad=0.1", 
                               facecolor=color_customer,
                               edgecolor='darkred', linewidth=2)
    ax.add_patch(output_box)
    ax.text(5, output_y + 0.5, "RESPONSE TO CUSTOMER", ha='center', va='center', 
            fontsize=13, fontweight='bold')
    ax.text(5, output_y + 0.2, "Quote | Confirmation | Status Update", ha='center', va='center', 
            fontsize=9, style='italic')
    
    # Arrow from orchestrator to output
    arrow_final = FancyArrowPatch((5, 7.5), (5, 1.3),
                                 arrowstyle='->', mutation_scale=30, linewidth=3,
                                 color='darkblue',
                                 connectionstyle="arc3,rad=0.3")
    ax.add_patch(arrow_final)
    ax.text(6.5, 4, "Process &\nReturn Result", ha='center', va='center', 
            fontsize=10, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.9))
    
    # ========================================================================
    # Legend
    # ========================================================================
    legend_elements = [
        mpatches.Patch(facecolor=color_customer, edgecolor='darkred', label='Customer Interface'),
        mpatches.Patch(facecolor=color_orchestrator, edgecolor='darkblue', label='Orchestrator'),
        mpatches.Patch(facecolor=color_agent, edgecolor='darkgreen', label='Specialized Agents'),
        mpatches.Patch(facecolor=color_tool, edgecolor='darkorange', label='Tools'),
        mpatches.Patch(facecolor=color_database, edgecolor='purple', label='Database')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9, 
              framealpha=0.9, title='Component Types', title_fontsize=10)
    
    # ========================================================================
    # Workflow Steps Box
    # ========================================================================
    steps_box = FancyBboxPatch((0.1, 0.5), 2.5, 1.6, 
                              boxstyle="round,pad=0.1", 
                              facecolor='lightyellow',
                              edgecolor='black', linewidth=1.5)
    ax.add_patch(steps_box)
    ax.text(1.35, 1.95, "Workflow Steps:", ha='center', va='center', 
            fontsize=10, fontweight='bold')
    
    steps = [
        "1. Customer submits request",
        "2. Orchestrator analyzes intent",
        "3. Routes to appropriate agent",
        "4. Agent uses tools to process",
        "5. Tools query/update database",
        "6. Response sent to customer"
    ]
    
    y_step = 1.65
    for step in steps:
        ax.text(0.2, y_step, step, ha='left', va='center', fontsize=7)
        y_step -= 0.18
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ax.text(5, 0.05, f"Generated: {timestamp}", ha='center', va='bottom', 
            fontsize=8, style='italic', color='gray')
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig('workflow_diagram.png', dpi=300, bbox_inches='tight', facecolor='white')
    print("✓ Workflow diagram saved as 'workflow_diagram.png'")
    
    # Also create a high-resolution version for documentation
    plt.savefig('workflow_diagram_highres.png', dpi=600, bbox_inches='tight', facecolor='white')
    print("✓ High-resolution diagram saved as 'workflow_diagram_highres.png'")
    
    plt.show()

def create_network_graph_diagram():
    """Create an alternative network graph representation"""
    
    # Create directed graph
    G = nx.DiGraph()
    
    # Add nodes with categories
    nodes = {
        'Customer': {'category': 'interface', 'color': '#FFE6E6'},
        'Orchestrator': {'category': 'orchestrator', 'color': '#E6F3FF'},
        'Inventory_Agent': {'category': 'agent', 'color': '#E6FFE6'},
        'Quote_Agent': {'category': 'agent', 'color': '#E6FFE6'},
        'Sales_Agent': {'category': 'agent', 'color': '#E6FFE6'},
        'check_inventory': {'category': 'tool', 'color': '#FFF9E6'},
        'reorder': {'category': 'tool', 'color': '#FFF9E6'},
        'search_quotes': {'category': 'tool', 'color': '#FFF9E6'},
        'generate_quote': {'category': 'tool', 'color': '#FFF9E6'},
        'finalize_sale': {'category': 'tool', 'color': '#FFF9E6'},
        'financial_status': {'category': 'tool', 'color': '#FFF9E6'},
        'Database': {'category': 'database', 'color': '#F0E6FF'}
    }
    
    for node, attrs in nodes.items():
        G.add_node(node, **attrs)
    
    # Add edges
    edges = [
        ('Customer', 'Orchestrator'),
        ('Orchestrator', 'Inventory_Agent'),
        ('Orchestrator', 'Quote_Agent'),
        ('Orchestrator', 'Sales_Agent'),
        ('Inventory_Agent', 'check_inventory'),
        ('Inventory_Agent', 'reorder'),
        ('Inventory_Agent', 'financial_status'),
        ('Quote_Agent', 'search_quotes'),
        ('Quote_Agent', 'generate_quote'),
        ('Quote_Agent', 'check_inventory'),
        ('Sales_Agent', 'finalize_sale'),
        ('Sales_Agent', 'financial_status'),
        ('check_inventory', 'Database'),
        ('reorder', 'Database'),
        ('search_quotes', 'Database'),
        ('generate_quote', 'Database'),
        ('finalize_sale', 'Database'),
        ('financial_status', 'Database'),
        ('Orchestrator', 'Customer')
    ]
    
    G.add_edges_from(edges)
    
    # Create layout
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Draw nodes by category
    for category, color_val in [('interface', '#FFE6E6'), ('orchestrator', '#E6F3FF'), 
                                  ('agent', '#E6FFE6'), ('tool', '#FFF9E6'), 
                                  ('database', '#F0E6FF')]:
        nodelist = [n for n, d in G.nodes(data=True) if d['category'] == category]
        nx.draw_networkx_nodes(G, pos, nodelist=nodelist, node_color=color_val,
                              node_size=3000, edgecolors='black', linewidths=2, ax=ax)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, 
                          arrowsize=20, width=2, alpha=0.6, ax=ax,
                          connectionstyle='arc3,rad=0.1')
    
    # Draw labels
    labels = {
        'Customer': 'Customer\nInterface',
        'Orchestrator': 'Orchestrator\nAgent',
        'Inventory_Agent': 'Inventory\nAgent',
        'Quote_Agent': 'Quote\nAgent',
        'Sales_Agent': 'Sales\nAgent',
        'check_inventory': 'Check\nInventory',
        'reorder': 'Reorder\nStock',
        'search_quotes': 'Search\nQuotes',
        'generate_quote': 'Generate\nQuote',
        'finalize_sale': 'Finalize\nSale',
        'financial_status': 'Financial\nStatus',
        'Database': 'Database\n(SQLite)'
    }
    
    nx.draw_networkx_labels(G, pos, labels, font_size=9, font_weight='bold', ax=ax)
    
    # Title
    plt.title("Beaver's Choice Paper Company\nMulti-Agent System Network Graph", 
             fontsize=18, fontweight='bold', pad=20)
    
    # Remove axes
    ax.axis('off')
    
    # Add legend
    legend_elements = [
        mpatches.Patch(facecolor='#FFE6E6', edgecolor='black', label='Customer Interface'),
        mpatches.Patch(facecolor='#E6F3FF', edgecolor='black', label='Orchestrator'),
        mpatches.Patch(facecolor='#E6FFE6', edgecolor='black', label='Agents'),
        mpatches.Patch(facecolor='#FFF9E6', edgecolor='black', label='Tools'),
        mpatches.Patch(facecolor='#F0E6FF', edgecolor='black', label='Database')
    ]
    plt.legend(handles=legend_elements, loc='upper left', fontsize=10, 
              framealpha=0.9, title='Component Types')
    
    plt.tight_layout()
    plt.savefig('network_graph_diagram.png', dpi=300, bbox_inches='tight', facecolor='white')
    print("✓ Network graph diagram saved as 'network_graph_diagram.png'")
    
    plt.show()

if __name__ == "__main__":
    print("=" * 80)
    print("Generating Workflow Diagrams for Beaver's Choice Paper Company")
    print("=" * 80)
    print("\nCreating comprehensive workflow diagram...")
    create_workflow_diagram()
    
    print("\nCreating network graph representation...")
    create_network_graph_diagram()
    
    print("\n" + "=" * 80)
    print("✓ All diagrams generated successfully!")
    print("=" * 80)
