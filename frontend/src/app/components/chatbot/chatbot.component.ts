import {
  Component,
  OnInit,
  ViewChild,
  ElementRef,
  AfterViewChecked
} from '@angular/core';
import { ChatService } from '../../shared/chat.service';
import { AuthService } from '../../shared/auth.service';

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
  isWaitingForResponse = false;
  isViewingHistory = false;
  userEmail: string = '';

  @ViewChild('messagesContainer')
  private messagesContainer!: ElementRef<HTMLDivElement>;

  constructor(
    private chatService: ChatService,
    private authService: AuthService
  ) {}

  ngOnInit() {
    // Get user email
    this.authService.userData$.subscribe(userData => {
      if (userData) {
        this.userEmail = userData.email;
      }
    });

    // Initial greeting message
    this.messages.push({
      role: 'assistant',
      content: 'Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns.'
    });

    // Listen for reset events
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
      if (!this.isWaitingForResponse && !this.conversationFinished) {
        this.send();
      }
    }
  }

  //  Helper to clean END marker
  private cleanText(text: string | null | undefined): string {
    if (!text) return '';
    return text
      .replace(/<END_OF_INTERVIEW>/gi, '')
      .trim();
  }

  send() {
    if (!this.input.trim() || this.conversationFinished || this.isWaitingForResponse) {
      return;
    }

    const userMessage = this.input.trim();

    // Add user message to chat
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
    this.isWaitingForResponse = true;

    // Start new session or continue existing
    if (this.isFirstMessage) {
      this.chatService.startInterview(userMessage).subscribe({
        next: (response) => {
          this.handleResponse(response, loadingMsg);
          this.sessionId = response.session_id;
          this.chatService.setSessionId(response.session_id);
          this.isFirstMessage = false;
          this.isWaitingForResponse = false;
        },
        error: (error) => {
          this.handleError(error, loadingMsg);
          this.isWaitingForResponse = false;
        }
      });
    } else {
      if (this.sessionId) {
        this.chatService.sendMessage(this.sessionId, userMessage).subscribe({
          next: (response) => {
            this.handleResponse(response, loadingMsg);
            this.isWaitingForResponse = false;
          },
          error: (error) => {
            this.handleError(error, loadingMsg);
            this.isWaitingForResponse = false;
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
      //  Clean END marker from live replies
      loadingMsg.content = this.cleanText(response.reply || 'Please continue...');
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

  private performReset() {
    this.messages = [{
      role: 'assistant',
      content: 'Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns.'
    }];
    this.sessionId = null;
    this.isFirstMessage = true;
    this.conversationFinished = false;
    this.isWaitingForResponse = false;
    this.isViewingHistory = false;
    this.chatService.clearSession();
  }

  // ===== HISTORY METHODS =====

  loadConversation(sessionId: string) {
    if (!this.userEmail) return;

    this.chatService.getConversation(sessionId, this.userEmail).subscribe({
      next: (conversation) => {
        // Clear existing messages
        this.messages = [];

        //  Clean text when loading from history
        this.messages = conversation.messages
          .map(msg => ({
            role: msg.role as 'user' | 'assistant',
            content: this.cleanText(msg.content),
            loading: false
          }))
          .filter(m => m.content && m.content.trim().length > 0);

        // Add final assessment if conversation is completed
        if (conversation.assessment) {
          this.messages.push({
            role: 'assistant',
            content: '',
            isFinal: true,
            finalData: conversation.assessment
          });
        }

        this.sessionId = sessionId;
        this.conversationFinished = conversation.status === 'completed';
        this.isViewingHistory = conversation.status === 'completed';
        this.isFirstMessage = false;
        this.chatService.setSessionId(sessionId);
      },
      error: (error) => {
        console.error('Error loading conversation:', error);
        alert('Failed to load conversation');
      }
    });
  }

  startNewChat() {
    this.performReset();
  }
}
