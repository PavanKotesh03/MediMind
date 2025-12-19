import {
  Component,
  OnInit,
  ViewChild,
  ElementRef,
  AfterViewChecked
} from '@angular/core';
import { ChatService } from '../../shared/chat.service';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  loading?: boolean;
  isFinal?: boolean;
  finalData?: any;
}

@Component({
  selector: 'app-chatbot',
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.css']
})
export class ChatbotComponent implements OnInit, AfterViewChecked {
  messages: Message[] = [];
  input = '';
  sessionId: string | null = null;
  isFirstMessage = true;
  conversationFinished = false;
  isWaitingForResponse = false; // ADD THIS

  @ViewChild('messagesContainer')
  private messagesContainer!: ElementRef<HTMLDivElement>;

  constructor(private chatService: ChatService) {}

  ngOnInit() {
    this.messages.push({
      role: 'assistant',
      content: 'Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns.'
    });

    this.chatService.reset$.subscribe(reset => {
      if (reset) {
        this.performReset();
        this.chatService.resetSubject.next(false);
      }
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
      // Only send if not waiting for response
      if (!this.isWaitingForResponse && !this.conversationFinished) {
        this.send();
      }
    }
  }

  send() {
    if (!this.input.trim() || this.conversationFinished || this.isWaitingForResponse) return;

    const userMessage = this.input.trim();

    // Add user message
    this.messages.push({
      role: 'user',
      content: userMessage
    });

    // Add loading indicator
    const loadingMsg: Message = {
      role: 'assistant',
      content: '',
      loading: true
    };
    this.messages.push(loadingMsg);

    this.input = '';
    this.isWaitingForResponse = true; // DISABLE SEND

    // Call appropriate API
    if (this.isFirstMessage) {
      this.chatService.startInterview(userMessage).subscribe({
        next: (response) => {
          this.handleResponse(response, loadingMsg);
          this.sessionId = response.session_id;
          this.chatService.setSessionId(response.session_id);
          this.isFirstMessage = false;
          this.isWaitingForResponse = false; // RE-ENABLE SEND
        },
        error: (error) => {
          this.handleError(error, loadingMsg);
          this.isWaitingForResponse = false; // RE-ENABLE SEND
        }
      });
    } else {
      if (this.sessionId) {
        this.chatService.sendMessage(this.sessionId, userMessage).subscribe({
          next: (response) => {
            this.handleResponse(response, loadingMsg);
            this.isWaitingForResponse = false; // RE-ENABLE SEND
          },
          error: (error) => {
            this.handleError(error, loadingMsg);
            this.isWaitingForResponse = false; // RE-ENABLE SEND
          }
        });
      }
    }
  }

  private handleResponse(response: any, loadingMsg: Message) {
    loadingMsg.loading = false;

    if (response.finished && response.final) {
      this.conversationFinished = true;
      loadingMsg.isFinal = true;
      loadingMsg.finalData = response.final;
      loadingMsg.content = this.formatFinalAssessment(response.final);
    } else {
      loadingMsg.content = response.reply || 'Please continue...';
    }
  }

  private formatFinalAssessment(final: any): string {
    return `Assessment Complete\n\nCondition: ${final.disease}\nSeverity: ${final.severity}\nReason: ${final.reason}\n\nExplanation:\n${final.explanation}`;
  }

  private handleError(error: any, loadingMsg: Message) {
    loadingMsg.loading = false;
    
    if (error.status === 0) {
      loadingMsg.content = 'Cannot connect to server. Please ensure the backend is running.';
    } else if (error.status === 400) {
      loadingMsg.content = error.error?.detail || 'Invalid request';
    } else {
      loadingMsg.content = 'An error occurred. Please try again.';
    }
  }

  resetConversation() {
    if (this.sessionId) {
      this.chatService.resetChat(this.sessionId).subscribe({
        next: () => {
          this.performReset();
        },
        error: () => {
          this.performReset();
        }
      });
    } else {
      this.performReset();
    }
  }

  private performReset() {
    this.messages = [{
      role: 'assistant',
      content: 'Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns.'
    }];
    this.sessionId = null;
    this.isFirstMessage = true;
    this.conversationFinished = false;
    this.isWaitingForResponse = false; // RESET LOADING STATE
    this.chatService.clearSession();
  }

  onResetClick() {
    this.resetConversation();
  }
}
