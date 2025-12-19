import {
  Component,
  OnInit,
  ViewChild,
  ElementRef,
  AfterViewChecked
} from '@angular/core';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  loading?: boolean;
}

@Component({
  selector: 'app-chatbot',
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.css']
})
export class ChatbotComponent implements OnInit, AfterViewChecked {

  messages: Message[] = [];
  input = '';

  // 🔥 Reference to messages container
  @ViewChild('messagesContainer')
  private messagesContainer!: ElementRef<HTMLDivElement>;

  ngOnInit() {
    this.messages.push({
      role: 'assistant',
      content: 'Hello! I’m MediMind. How can I help you today?'
    });
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  private scrollToBottom(): void {
    if (this.messagesContainer) {
      this.messagesContainer.nativeElement.scrollTop =
        this.messagesContainer.nativeElement.scrollHeight;
    }
  }

  handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.send();
    }
  }

  send() {
    if (!this.input.trim()) return;

    // User message
    this.messages.push({
      role: 'user',
      content: this.input
    });

    const loading: Message = {
      role: 'assistant',
      content: '',
      loading: true
    };

    this.messages.push(loading);
    this.input = '';

    // Simulated backend response
    setTimeout(() => {
      loading.loading = false;
      loading.content = 'This is a sample response from MediMind.';
    }, 1500);
  }
}
