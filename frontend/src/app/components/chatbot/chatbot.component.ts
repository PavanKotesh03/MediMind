import {
  Component,
  OnInit,
  ViewChild,
  ElementRef,
  AfterViewChecked,
  OnDestroy
} from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ChatService } from 'src/app/shared/chat.service';
import { Subscription } from 'rxjs';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  loading?: boolean;
  thinking?: boolean;
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
  isSidebarOpen = false;

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
    // Subscribe to sidebar state
    this.chatService.sidebarOpen$.subscribe(isOpen => {
      this.isSidebarOpen = isOpen;
    });

    // Initial greeting
    this.messages.push({
      role: 'assistant',
      content: 'Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns.'
    });

    // Handle URL session ID
    this.route.params.subscribe(params => {
      const urlSessionId = params['sessionId'];

      if (urlSessionId) {
        console.log('🔗 URL has session ID:', urlSessionId);

        this.sessionId = urlSessionId;
        this.chatService.setSessionId(urlSessionId);

        // Load conversation from history
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
          error: (err: any) => {
            console.error('❌ Error loading conversation:', err);
          }
        });
      } else {
        // No URL session, check if we have one in service
        const serviceSessionId = this.chatService.getSessionId();
        if (serviceSessionId) {
          this.sessionId = serviceSessionId;
          this.router.navigate(['/chat', serviceSessionId], { replaceUrl: true });
        } else {
          // Initialize new session
          this.initializeSession();
        }
      }
    });

    // Listen for reset events
    this.resetSubscription = this.chatService.reset$.subscribe(reset => {
      if (reset) {
        this.performReset();
      }
    });

    // Listen for session ID changes
    this.sessionSubscription = this.chatService.sessionId$.subscribe(sessionId => {
      if (sessionId && sessionId !== this.sessionId) {
        this.sessionId = sessionId;
      }
    });
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  ngOnDestroy() {
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
    // Remove END_OF_INTERVIEW tag in all variations (aggressive cleaning)
    return text
        .replace(/<END_OF_INTERVIEW>/gi, '')
        .replace(/END_OF_INTERVIEW/gi, '')
        .replace(/<end_of_interview>/gi, '')
        .replace(/< END_OF_INTERVIEW >/gi, '')
        .replace(/< END OF INTERVIEW >/gi, '')
        .replace(/\<END_OF_INTERVIEW\>/gi, '')
        .trim();
}


  // =====================================================
  // SEND WITH STREAMING
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

    // Add user message to UI
    this.messages.push({ role: 'user', content: userMessage });

    // Add thinking message
    const thinkingMsg: Message = {
      role: 'assistant',
      content: '',
      thinking: true
    };
    this.messages.push(thinkingMsg);

    this.input = '';
    this.isWaitingForResponse = true;

    if (this.sessionId) {
      // ✅ EXISTING SESSION - STREAMING CHAT
      console.log('📡 Sending message with streaming...');
      
      this.chatService.sendMessage(
        this.sessionId,
        userMessage,
        // onToken: Append streaming tokens (cleaned)
        (token: string) => {
          if (thinkingMsg.thinking) {
            thinkingMsg.thinking = false;
            thinkingMsg.content = '';
          }
          
          // 🆕 Check if this is the "Finalizing..." message
          if (token.includes('Finalizing')) {
            // Show finalizing state
            thinkingMsg.thinking = false;
            thinkingMsg.content = 'Finalizing your assessment...';
            this.scrollToBottom();
            return;
          }
          
          // Clean any remaining END_OF_INTERVIEW tokens
          let cleanToken = token
              .replace(/<END_OF_INTERVIEW>/gi, '')
              .replace(/END_OF_INTERVIEW/gi, '')
              .replace(/<end_of_interview>/gi, '');
          
          // Only add if there's actual content after cleaning
          if (cleanToken.trim()) {
            thinkingMsg.content += cleanToken;
            this.scrollToBottom();
          }
        },
        // onFinal: Show assessment header immediately
        (final: any) => {
          console.log('🏁 Final assessment received:', final);
          thinkingMsg.thinking = false;
          this.conversationFinished = true;
          thinkingMsg.isFinal = true;
          thinkingMsg.finalData = final;
          
          // Clear finalizing message and show header
          thinkingMsg.content = '';
          
          const header = `Assessment Complete\n\nCondition: ${final.disease}\nSeverity: ${final.severity}\nReason: ${final.reason}\n\nMedical Explanation:\n`;
          thinkingMsg.content = header;
          
          this.scrollToBottom();
        },
        // onComplete: Mark response as complete
        (finished: boolean) => {
          console.log('✅ Response complete, finished:', finished);
          thinkingMsg.thinking = false;
          this.isWaitingForResponse = false;
          
          // Final cleanup
          if (thinkingMsg.content) {
            thinkingMsg.content = this.cleanText(thinkingMsg.content);
          }
        },
        // onError: Handle errors
        (error: any) => {
          console.error('❌ Streaming error:', error);
          thinkingMsg.thinking = false;
          this.handleError(error, thinkingMsg);
          this.isWaitingForResponse = false;
        }
      );
    } else {
      // ✅ NEW SESSION - STREAMING START
      console.log('📡 Starting new session with streaming...');
      
      this.chatService.startChat(
        userMessage,
        // onToken: Append streaming tokens (cleaned)
        (token: string) => {
          if (thinkingMsg.thinking) {
            thinkingMsg.thinking = false;
            thinkingMsg.content = '';
          }
          
          // Clean any END_OF_INTERVIEW tokens
          let cleanToken = token
              .replace(/<END_OF_INTERVIEW>/gi, '')
              .replace(/END_OF_INTERVIEW/gi, '')
              .replace(/<end_of_interview>/gi, '');
          
          // Only add if there's actual content after cleaning
          if (cleanToken.trim()) {
            thinkingMsg.content += cleanToken;
            this.scrollToBottom();
          }
        },
        // onSessionId: Save session ID
        (sessionId: string) => {
          console.log('🆔 Session ID received:', sessionId);
          this.sessionId = sessionId;
          this.chatService.setSessionId(sessionId);
          this.router.navigate(['/chat', sessionId], { replaceUrl: true });
        },
        // onComplete: Mark response as complete
        (finished: boolean) => {
          console.log('✅ Start complete, finished:', finished);
          thinkingMsg.thinking = false;
          this.isWaitingForResponse = false;
          
          if (thinkingMsg.content) {
            thinkingMsg.content = this.cleanText(thinkingMsg.content);
          }
        },
        // onError: Handle errors
        (error: any) => {
          console.error('❌ Streaming error:', error);
          thinkingMsg.thinking = false;
          this.handleError(error, thinkingMsg);
          this.isWaitingForResponse = false;
        }
      );
    }
  }



  // =====================================================
  // HELPER METHODS
  // =====================================================

  private formatFinalAssessment(final: any): string {
    return `Assessment Complete

Condition: ${final.disease}
Severity: ${final.severity}
Reason: ${final.reason}

Medical Explanation:
${final.explanation}`;
  }

  private handleError(error: any, loadingMsg: Message) {
    loadingMsg.loading = false;
    
    if (error.message) {
      loadingMsg.content = error.message;
    } else if (error.error) {
      loadingMsg.content = error.error;
    } else {
      loadingMsg.content = 'An error occurred. Please try again.';
    }
  }

  private isInitializing = false;

  private initializeSession() {
    if (this.isInitializing) return;
    this.isInitializing = true;

    console.log('🚀 Initializing new session...');

    // Create empty session with greeting
    this.chatService.startChat(
      null, // No message, just greeting
      // onToken: Greeting already shown in ngOnInit
      (token: string) => {
        // Greeting already displayed
      },
      // onSessionId: Save session ID
      (sessionId: string) => {
        console.log('✅ Session initialized:', sessionId);
        this.sessionId = sessionId;
        this.chatService.setSessionId(sessionId);
        this.router.navigate(['/chat', sessionId], { replaceUrl: true });
        this.isInitializing = false;
      },
      // onComplete
      (finished: boolean) => {
        this.isInitializing = false;
      },
      // onError
      (error: any) => {
        console.error('❌ Failed to initialize session:', error);
        this.isInitializing = false;
      }
    );
  }

  private performReset() {
    console.log('🔄 Performing reset...');
    
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

  // =====================================================
  // HISTORY NAVIGATION
  // =====================================================

  loadConversation(sessionId: string) {
    console.log('📂 Loading conversation:', sessionId);
    
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
        console.error('❌ Error loading conversation:', error);
        alert('Failed to load conversation');
      }
    });
  }

  startNewChat() {
    console.log('🆕 Starting new chat...');
    this.chatService.clearSession();
  }
}
