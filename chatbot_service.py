"""
Chatbot NLP Service for Order Processing
Handles intent recognition and entity extraction from natural language
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ChatbotNLPService:
    """Simple NLP service for processing restaurant orders"""
    
    def __init__(self, db):
        self.db = db
        self.menu_cache = {}
        
    async def refresh_menu_cache(self):
        """Cache menu items for faster lookup"""
        menu_items = await self.db.menu_items.find().to_list(length=None)
        self.menu_cache = {
            item['name'].lower(): item 
            for item in menu_items
        }
        
        # Also create partial match dictionary
        self.partial_matches = {}
        for name, item in self.menu_cache.items():
            words = name.split()
            for word in words:
                if word not in self.partial_matches:
                    self.partial_matches[word] = []
                self.partial_matches[word].append(item)
    
    def extract_quantity(self, text: str) -> Tuple[int, str]:
        """Extract quantity from text like '2 paneer tikka' or 'two butter naan'"""
        # Number words mapping
        number_words = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        
        # Try to find numeric quantity
        numeric_match = re.match(r'^(\d+)\s+(.+)$', text.strip())
        if numeric_match:
            return int(numeric_match.group(1)), numeric_match.group(2)
        
        # Try to find word quantity
        for word, num in number_words.items():
            if text.lower().startswith(word + ' '):
                return num, text[len(word):].strip()
        
        # Default to 1
        return 1, text.strip()
    
    async def find_menu_item(self, item_name: str) -> Optional[Dict]:
        """Find menu item by name with fuzzy matching"""
        item_lower = item_name.lower().strip()
        
        # Exact match
        if item_lower in self.menu_cache:
            return self.menu_cache[item_lower]
        
        # Partial match
        words = item_lower.split()
        matches = []
        for word in words:
            if word in self.partial_matches:
                matches.extend(self.partial_matches[word])
        
        if matches:
            # Return first match (can be improved with scoring)
            return matches[0]
        
        return None
    
    def extract_modifiers(self, text: str) -> Dict[str, str]:
        """Extract modifiers like 'extra spicy', 'no onion', etc."""
        modifiers = {}
        
        spice_levels = ['mild', 'medium', 'spicy', 'extra spicy']
        for level in spice_levels:
            if level in text.lower():
                modifiers['spice'] = level
        
        # Check for negations
        if 'no onion' in text.lower() or 'without onion' in text.lower():
            modifiers['special'] = 'No onion'
        
        if 'no garlic' in text.lower() or 'without garlic' in text.lower():
            modifiers['special'] = modifiers.get('special', '') + ' No garlic'
        
        return modifiers
    
    async def process_message(self, message: str, context: Dict) -> Dict:
        """
        Process user message and return intent + entities
        Returns: {
            'intent': 'add_item' | 'modify_item' | 'confirm_order' | 'cancel' | 'show_menu',
            'entities': {...},
            'response': 'Bot response text',
            'items': [...] # extracted items
        }
        """
        message = message.strip().lower()
        
        # Refresh menu cache if empty
        if not self.menu_cache:
            await self.refresh_menu_cache()
        
        # Intent: Show menu
        if any(word in message for word in ['menu', 'show menu', 'what do you have']):
            categories = set(item['category'] for item in self.menu_cache.values())
            return {
                'intent': 'show_menu',
                'categories': list(categories),
                'response': f"We have {', '.join(categories)}. What would you like to order?"
            }
        
        # Intent: Confirm order
        if any(word in message for word in ['confirm', 'yes', 'correct', 'done', 'that\'s all']):
            return {
                'intent': 'confirm_order',
                'response': 'Great! I\'ll process your order now.'
            }
        
        # Intent: Cancel
        if any(word in message for word in ['cancel', 'stop', 'no', 'forget it']):
            return {
                'intent': 'cancel',
                'response': 'Order cancelled. Let me know if you need anything else!'
            }
        
        # Intent: Add items (default)
        # Parse items from message
        items_found = []
        
        # Split by 'and' or comma
        parts = re.split(r'\s+and\s+|,\s*', message)
        
        for part in parts:
            quantity, item_text = self.extract_quantity(part)
            modifiers = self.extract_modifiers(part)
            
            menu_item = await self.find_menu_item(item_text)
            
            if menu_item:
                special_instructions = modifiers.get('special', '')
                if 'spice' in modifiers:
                    special_instructions = f"{modifiers['spice']} {special_instructions}".strip()
                
                items_found.append({
                    'menuitemid': str(menu_item['_id']),
                    'menuitemname': menu_item['name'],
                    'quantity': quantity,
                    'price': menu_item['price'],
                    'specialinstructions': special_instructions,
                    'foodtype': menu_item.get('foodtype', 'veg')
                })
        
        if items_found:
            return {
                'intent': 'add_items',
                'items': items_found,
                'response': self._format_items_response(items_found)
            }
        else:
            return {
                'intent': 'unknown',
                'response': 'I couldn\'t find those items. Could you try again or say "show menu" to see our options?'
            }
    
    def _format_items_response(self, items: List[Dict]) -> str:
        """Format items into readable response"""
        if not items:
            return "No items found."
        
        lines = ["Added to your order:"]
        for item in items:
            line = f"• {item['quantity']}x {item['menuitemname']} - ₹{item['price'] * item['quantity']}"
            if item.get('specialinstructions'):
                line += f" ({item['specialinstructions']})"
            lines.append(line)
        
        return "\n".join(lines)
