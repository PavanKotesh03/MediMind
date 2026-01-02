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
  isWaitingForResponse = false;
  isViewingHistory = false;

  @ViewChild('messagesContainer')
  private messagesContainer!: ElementRef<HTMLDivElement>;

  constructor(private chatService: ChatService) {}

  // =====================================================
  // INIT
  // =====================================================
  ngOnInit() {
    this.messages.push({
      role: 'assistant',
      content:
        'Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns.'
    });

    this.chatService.reset$.subscribe(reset => {
      if (reset) {
        this.performReset();
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

  // =====================================================
  // INPUT HANDLING
  // =====================================================
  handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      if (!this.isWaitingForResponse && !this.conversationFinished && !this.isViewingHistory) {
        this.send();
      }
    }
  }

  private cleanText(text: string | null | undefined): string {
    if (!text) return '';
    return text.replace(/<END_OF_INTERVIEW>/gi, '').trim();
  }

  // =====================================================
  // SEND MESSAGE
  // =====================================================
  send() {
    if (
      !this.input.trim() ||
      this.conversationFinished ||
      this.isWaitingForResponse ||
      this.isViewingHistory
    ) {
      return;
    }

    const userMessage = this.input.trim();

    this.messages.push({ role: 'user', content: userMessage });

    const loadingMsg: Message = {
      role: 'assistant',
      content: '',
      loading: true
    };
    this.messages.push(loadingMsg);

    this.input = '';
    this.isWaitingForResponse = true;

    if (this.isFirstMessage) {
      this.chatService.startInterview(userMessage).subscribe({
        next: (res: any) => {
          const response = res.data;

          this.handleResponse(response, loadingMsg);
          this.sessionId = response.session_id;
          this.chatService.setSessionId(response.session_id);

          this.isFirstMessage = false;
          this.isWaitingForResponse = false;
        },
        error: (error: any) => {
          this.handleError(error, loadingMsg);
          this.isWaitingForResponse = false;
        }
      });
    } else if (this.sessionId) {
      this.chatService.sendMessage(this.sessionId, userMessage).subscribe({
        next: (res: any) => {
          this.handleResponse(res.data, loadingMsg);
          this.isWaitingForResponse = false;
        },
        error: (error: any) => {
          this.handleError(error, loadingMsg);
          this.isWaitingForResponse = false;
        }
      });
    }
  }

  // =====================================================
  // RESPONSE HANDLING
  // =====================================================
  private handleResponse(response: any, loadingMsg: Message) {
    loadingMsg.loading = false;

    if (response.finished && response.final) {
      this.conversationFinished = true;
      loadingMsg.isFinal = true;
      loadingMsg.finalData = response.final;
      loadingMsg.content = this.formatFinalAssessment(response.final);
    } else {
      loadingMsg.content = this.cleanText(response.reply || 'Please continue...');
    }
  }

  private formatFinalAssessment(final: any): string {
    return `Assessment Complete

Condition: ${final.disease}
Severity: ${final.severity}
Reason: ${final.reason}

Explanation:
${final.explanation}`;
  }

  private handleError(error: any, loadingMsg: Message) {
    loadingMsg.loading = false;
    loadingMsg.content = 'An error occurred. Please try again.';
  }

  // =====================================================
  // RESET
  // =====================================================
  private performReset() {
    this.messages = [
      {
        role: 'assistant',
        content:
          'Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns.'
      }
    ];

    this.sessionId = null;
    this.isFirstMessage = true;
    this.conversationFinished = false;
    this.isWaitingForResponse = false;
    this.isViewingHistory = false;
  }

  // =====================================================
  // LOAD HISTORY CONVERSATION
  // =====================================================
  loadConversation(sessionId: string) {
    this.chatService.getConversation(sessionId).subscribe({
      next: (res: any) => {
        const conversation = res.data;

        this.messages = conversation.messages
          .map((msg: any) => ({
            role: msg.role,
            content: this.cleanText(msg.content)
          }))
          .filter((m: Message) => m.content);

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
      error: (error: any) => {
        console.error('Error loading conversation:', error);
        alert('Failed to load conversation');
      }
    });
  }

  // =====================================================
  // NEW CHAT
  // =====================================================
  startNewChat() {
    this.performReset();
  }
}
