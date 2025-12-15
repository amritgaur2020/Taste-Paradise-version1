import React from 'react';
import { MessageCircle } from 'lucide-react';
import './ChatbotButton.css';

const ChatbotButton = ({ onClick }) => {
  return (
    <button className="chatbot-fab" onClick={onClick}>
      <MessageCircle size={24} />
    </button>
  );
};

export default ChatbotButton;
