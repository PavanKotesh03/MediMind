import {
  Component,
  OnInit,
  ViewChild,
  ElementRef,
  AfterViewChecked,
  OnDestroy
} from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ChatService } from '../../shared/chat.service';
import { Subscription } from 'rxjs';

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
export class ChatbotComponent implements OnInit, AfterViewChecked, OnDestroy {
  messages: Message[] = [];
  input = '';
  sessionId: string | null = null;
  isLoading = false;
  isSidebarOpen = false; // Mobile Sidebar State

  conversationFinished = false;
  isWaitingForResponse = false;
  isViewingHistory = false;

  private sessionSubscription?: Subscription;
  private resetSubscription?: Subscription;

  @ViewChild('messagesContainer')
  private messagesContainer!: ElementRef<HTMLDivElement>;

  constructor(
    private chatService: ChatService,
    private route: ActivatedRoute,
    private router: Router
  ) { }

  ngOnInit() {
    // 1. Subscribe to Sidebar State (Mobile)
    this.chatService.sidebarOpen$.subscribe(isOpen => {
      this.isSidebarOpen = isOpen;
    });

    this.messages.push({
      role: 'assistant',
      content: 'Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns.'
    });

    this.route.params.subscribe(params => {
      const urlSessionId = params['sessionId'];

      if (urlSessionId) {
        console.log('URL has session ID:', urlSessionId);

        this.sessionId = urlSessionId;
        this.chatService.setSessionId(urlSessionId);

        console.log('Session ID set to:', this.sessionId);

        this.chatService.getConversation(urlSessionId).subscribe({
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

            this.sessionId = urlSessionId;
            this.conversationFinished = conversation.status === 'completed';
            this.isViewingHistory = conversation.status === 'completed';

            this.chatService.setSessionId(urlSessionId);
          },
          error: () => {
            // Handle error or new session logic
          }
        });
      } else {
        // ... existing logic ...
        const serviceSessionId = this.chatService.getSessionId();
        if (serviceSessionId) {
          this.sessionId = serviceSessionId;
          this.router.navigate(['/chat', serviceSessionId], { replaceUrl: true });
        } else {
          this.initializeSession();
        }
      }
    });

    this.resetSubscription = this.chatService.reset$.subscribe(reset => {
      if (reset) {
        this.performReset();
      }
    });

    this.sessionSubscription = this.chatService.sessionId$.subscribe(sessionId => {
      if (sessionId && sessionId !== this.sessionId) {
        this.sessionId = sessionId;
      }
    });
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

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

        // REMOVED POLLING LOGIC HERE

        if (conversation.assessment) {
          this.messages.push({
            role: 'assistant',
            content: '',
            isFinal: true,
            finalData: conversation.assessment
          });
        }

        // Close sidebar on mobile after selection
        if (this.isSidebarOpen) {
          this.chatService.toggleSidebar();
        }

        this.sessionId = sessionId;
        this.conversationFinished = conversation.status === 'completed';
        this.isViewingHistory = conversation.status === 'completed';

        this.chatService.setSessionId(sessionId);

        this.router.navigate(['/chat', sessionId], { replaceUrl: true });
      },
      error: (error: any) => {
        console.error('Error loading conversation:', error);
        alert('Failed to load conversation');
      }
    });
  }

  ngOnDestroy() {
    // ✅ FIXED: Unsubscribe to prevent duplicates/leaks
    this.sessionSubscription?.unsubscribe();
    this.resetSubscription?.unsubscribe();
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
      if (!this.isWaitingForResponse && !this.conversationFinished && !this.isViewingHistory) {
        this.send();
      }
    }
  }

  private cleanText(text: string | null | undefined): string {
    if (!text) return '';
    return text.replace(/<END_OF_INTERVIEW>/gi, '').trim();
  }

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

    if (this.sessionId) {
      this.chatService.sendMessage(this.sessionId, userMessage).subscribe({
        next: (res: any) => {
          const response = res.data;
          this.handleResponse(response, loadingMsg);
          this.isWaitingForResponse = false;
        },
        error: (error: any) => {
          this.handleError(error, loadingMsg);
          this.isWaitingForResponse = false;
        }
      });
    } else {
      this.chatService.startInterview(userMessage).subscribe({
        next: (res: any) => {
          const response = res.data;
          this.handleResponse(response, loadingMsg);

          this.sessionId = response.session_id;
          this.chatService.setSessionId(response.session_id);

          this.router.navigate(['/chat', response.session_id], { replaceUrl: true });

          this.isWaitingForResponse = false;
        },
        error: (error: any) => {
          this.handleError(error, loadingMsg);
          this.isWaitingForResponse = false;
        }
      });
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

  private isInitializing = false;

  private performReset() {
    this.messages = [
      {
        role: 'assistant',
        content: 'Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns.'
      }
    ];

    this.sessionId = null;
    this.conversationFinished = false;
    this.isWaitingForResponse = false;
    this.isViewingHistory = false;

    this.initializeSession();
  }

  private initializeSession() {
    if (this.isInitializing) return;
    this.isInitializing = true;

    this.chatService.startInterview().subscribe({
      next: (res: any) => {
        this.isInitializing = false;
        if (res.success && res.data) {
          console.log('Session initialized:', res.data.session_id);
          this.sessionId = res.data.session_id;
          this.chatService.setSessionId(this.sessionId!);

          this.router.navigate(['/chat', this.sessionId], { replaceUrl: true });
        }
      },
      error: (err) => {
        this.isInitializing = false;
        console.error('Failed to initialize session:', err);
      }
    });
  }

  startNewChat() {
    this.chatService.clearSession();
  }
}
