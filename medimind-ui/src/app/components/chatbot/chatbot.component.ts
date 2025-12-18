import { Component, Input, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';

interface ChatMessage {
  role: 'user' | 'bot';
  content: string;
  loading?: boolean;
}
@Component({
  selector: 'app-chatbot',
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.css']
})
export class ChatbotComponent implements OnInit {

  @Input() initialMessage = '';
  @Input() sessionId = '';

  constructor(private apiService: ApiService) {}



  messages: ChatMessage[] = [];
  input = '';

  ngOnInit(): void {
    if (this.initialMessage) {
      this.messages.push({
        role: 'bot',
        content: this.initialMessage
      });
    }
  }

  send() {
  if (!this.input.trim()) return;

  const userMessage = this.input;

  // show user message
  this.messages.push({
    role: 'user',
    content: userMessage
  });

  this.input = '';

  // loading bubble
  const loadingIndex = this.messages.push({
    role: 'bot',
    content: '',
    loading: true
  }) - 1;

  // call backend
  this.apiService.continueChat(this.sessionId, userMessage)
    .subscribe({
      next: (response) => {
        this.messages[loadingIndex] = {
          role: 'bot',
          content: response.response
        };
      },
      error: () => {
        this.messages[loadingIndex] = {
          role: 'bot',
          content: 'Something went wrong. Please try again.'
        };
      }
    });
}


  handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.send();
    }
  }
}
