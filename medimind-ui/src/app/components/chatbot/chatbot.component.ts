import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';


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
export class ChatbotComponent implements OnInit {
  messages: Message[] = [];
  input = '';


  @ViewChild('textarea') textarea!: ElementRef<HTMLTextAreaElement>;


  ngOnInit() {
    this.messages.push({
      role: 'assistant',
      content: 'Hello! I’m MediMind. How can I help you today?'
    });
  }


  handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.send();
    }
  }


  send() {
    if (!this.input.trim()) return;


    this.messages.push({ role: 'user', content: this.input });
    const loading: Message = { role: 'assistant', content: '…', loading: true };
    this.messages.push(loading);


    this.input = '';


    setTimeout(() => {
      loading.loading = false;
      loading.content = 'This is a sample response from MediMind.';
    }, 1500);
  }
}