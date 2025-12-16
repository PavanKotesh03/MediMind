import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ChatService {

  private key(email: string) {
    return `chat-${email}`;
  }

  getMessages(email: string) {
    return JSON.parse(localStorage.getItem(this.key(email)) || '[]');
  }

  sendMessage(email: string, text: string) {
    const messages = this.getMessages(email);
    messages.push({ text, sender: 'user' });
    messages.push({
      text: 'MediMind 🧠: Please describe your symptoms in detail. This is not a diagnosis.',
      sender: 'bot'
    });
    localStorage.setItem(this.key(email), JSON.stringify(messages));
  }

  clear(email: string) {
    localStorage.removeItem(this.key(email));
  }
}
