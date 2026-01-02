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
  conversationFinished = false;
  isWaitingForResponse = false;
  isViewingHistory = false;

  private sessionSubscription?: Subscription;

  @ViewChild('messagesContainer')
  private messagesContainer!: ElementRef<HTMLDivElement>;

  constructor(
    private chatService: ChatService,
    private route: ActivatedRoute,
    private router: Router
  ) { }

  ngOnInit() {
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
            
            const hasRealMessages = conversation.messages && 
                                   conversation.messages.length > 0 &&
                                   conversation.messages.some((m: any) => 
                                     m.role === 'user' && m.content.trim() !== ''
                                   );
            
            if (hasRealMessages) {
              console.log('Loading conversation history');
              this.loadConversation(urlSessionId);
            } else {
              console.log('Empty session, ready for input');
            }
          },
          error: () => {
            console.log('Fresh session');
          }
        });
      } else {
        console.log('No URL session, checking service');
        const serviceSessionId = this.chatService.getSessionId();
        
        if (serviceSessionId) {
          console.log('Found session in service:', serviceSessionId);
          this.sessionId = serviceSessionId;
          this.router.navigate(['/chat', serviceSessionId], { replaceUrl: true });
        } else {
          console.log('No session anywhere');
        }
      }
    });

    this.chatService.reset$.subscribe(reset => {
      if (reset) {
        this.performReset();
      }
    });

    this.sessionSubscription = this.chatService.sessionId$.subscribe(sessionId => {
      if (sessionId && sessionId !== this.sessionId) {
        console.log('Session changed to:', sessionId);
        this.sessionId = sessionId;
      }
    });
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  ngOnDestroy() {
    this.sessionSubscription?.unsubscribe();
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

    console.log('==========================================');
    console.log('SEND CALLED');
    console.log('this.sessionId =', this.sessionId);
    console.log('service.getSessionId() =', this.chatService.getSessionId());
    console.log('sessionStorage =', sessionStorage.getItem('current_session_id'));
    console.log('==========================================');

    if (this.sessionId) {
      console.log('Using POST /chat with session:', this.sessionId);
      
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
      console.log('No session, creating with POST /start');
      
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

        this.chatService.setSessionId(sessionId);
        
        this.router.navigate(['/chat', sessionId], { replaceUrl: true });
      },
      error: (error: any) => {
        console.error('Error loading conversation:', error);
        alert('Failed to load conversation');
      }
    });
  }

  startNewChat() {
    this.chatService.clearSession();
    
    this.sessionId = null;
    this.conversationFinished = false;
    this.isWaitingForResponse = false;
    this.isViewingHistory = false;
    
    this.messages = [
      {
        role: 'assistant',
        content: 'Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns.'
      }
    ];
    
    this.router.navigate(['/chat']);
  }
}
