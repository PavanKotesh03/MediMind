import {
  Component,
  OnInit,
  ViewChild,
  ElementRef,
  AfterViewChecked,
  OnDestroy,
  ChangeDetectorRef
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
  isTyping?: boolean;
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
  
  currentStreamingMessage: string = '';
  isStreaming = false;
  
  private processingFinalAssessment = false;
  private finalAssessmentTimeout: any = null;

  private sessionSubscription?: Subscription;
  private routeSubscription?: Subscription;
  private scrollNeeded = false;

  @ViewChild('messagesContainer')
  private messagesContainer!: ElementRef<HTMLDivElement>;

  constructor(
    private chatService: ChatService,
    private route: ActivatedRoute,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    console.log('COMPONENT: ngOnInit');
    
    // Initialize with welcome message
    this.resetToWelcome();

    // Listen to session changes from service
    this.sessionSubscription = this.chatService.sessionId$.subscribe(sessionId => {
      if (sessionId && sessionId !== this.sessionId) {
        console.log('COMPONENT: Session updated from service:', sessionId);
        this.handleSessionChange(sessionId);
      }
    });

    // Listen to route parameter changes (important for detecting new chat clicks)
    this.routeSubscription = this.route.params.subscribe(params => {
      const urlSessionId = params['sessionId'];
      
      console.log('COMPONENT: Route changed, sessionId:', urlSessionId);
      
      if (urlSessionId && urlSessionId !== this.sessionId) {
        this.handleSessionChange(urlSessionId);
      } else if (!urlSessionId) {
        // No session in URL - check service
        const serviceSessionId = this.chatService.getSessionId();
        if (serviceSessionId) {
          console.log('COMPONENT: Using service session:', serviceSessionId);
          this.router.navigate(['/chat', serviceSessionId], { replaceUrl: true });
        }
      }
    });
  }

  ngAfterViewChecked() {
    if (this.scrollNeeded) {
      this.scrollToBottom();
      this.scrollNeeded = false;
    }
  }

  ngOnDestroy() {
    this.sessionSubscription?.unsubscribe();
    this.routeSubscription?.unsubscribe();
    
    if (this.finalAssessmentTimeout) {
      clearTimeout(this.finalAssessmentTimeout);
    }
  }

  private resetToWelcome() {
    this.messages = [{
      role: 'assistant',
      content: 'Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns.'
    }];
    this.conversationFinished = false;
    this.isWaitingForResponse = false;
    this.isViewingHistory = false;
    this.isStreaming = false;
    this.currentStreamingMessage = '';
    this.input = '';
  }

  private handleSessionChange(newSessionId: string) {
    console.log('COMPONENT: Handling session change to:', newSessionId);
    
    this.sessionId = newSessionId;
    this.chatService.setSessionId(newSessionId);
    
    // Check if this is an existing conversation or new one
    this.chatService.getConversation(newSessionId).subscribe({
      next: (res: any) => {
        const conversation = res.data;
        
        const hasRealMessages = conversation.messages && 
                               conversation.messages.length > 0 &&
                               conversation.messages.some((m: any) => 
                                 m.role === 'user' && m.content.trim() !== ''
                               );
        
        if (hasRealMessages) {
          console.log('COMPONENT: Loading existing conversation');
          this.loadConversation(newSessionId);
        } else {
          console.log('COMPONENT: New empty session, showing welcome');
          this.resetToWelcome();
          this.scrollNeeded = true;
          this.cdr.detectChanges();
        }
      },
      error: () => {
        console.log('COMPONENT: Fresh session, showing welcome');
        this.resetToWelcome();
        this.scrollNeeded = true;
        this.cdr.detectChanges();
      }
    });
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
    this.scrollNeeded = true;

    const streamingMsg: Message = {
      role: 'assistant',
      content: 'Thinking...',
      loading: false,
      isTyping: true
    };
    this.messages.push(streamingMsg);

    this.input = '';
    this.isWaitingForResponse = true;
    this.isStreaming = true;
    this.currentStreamingMessage = '';
    this.processingFinalAssessment = false;
    this.cdr.detectChanges();

    console.log('COMPONENT: Sending message via STREAMING API');
    console.log('COMPONENT: sessionId:', this.sessionId);

    if (this.sessionId) {
      console.log('COMPONENT: Using streaming API (saves to DB automatically)');
      this.sendWithStreaming(userMessage, streamingMsg);
    } else {
      console.error('COMPONENT: No session ID - user must click New Chat or login first');
      streamingMsg.isTyping = false;
      streamingMsg.content = 'Error: No session available. Please click "New Chat" button.';
      this.isWaitingForResponse = false;
      this.isStreaming = false;
      this.cdr.detectChanges();
    }
  }

  private sendWithStreaming(message: string, streamingMsg: Message) {
  console.log('COMPONENT: Starting stream - DB save happens automatically');
  
  let firstChunkReceived = false;
  let streamComplete = false;
  let finalAssessmentData: any = null;
  let finalExplanationText = '';
  
  this.finalAssessmentTimeout = setTimeout(() => {
    if (this.processingFinalAssessment && !streamComplete) {
      console.warn('COMPONENT: Final assessment timeout - completing anyway');
      this.completeFinalAssessment(streamingMsg);
    }
  }, 30000);
  
  this.chatService.sendMessageStreaming(this.sessionId!, message).subscribe({
    next: (chunk: any) => {
      console.log('COMPONENT: Received chunk:', chunk);
      
      if (!firstChunkReceived && chunk.type === 'text') {
        streamingMsg.isTyping = false;
        streamingMsg.content = '';
        firstChunkReceived = true;
      }
      
      if (chunk.type === 'text') {
        // Regular conversation streaming
        let cleanContent = chunk.content.replace(/<END_OF_INTERVIEW>/gi, '');
        this.currentStreamingMessage += cleanContent;
        streamingMsg.content = this.currentStreamingMessage;
        this.scrollNeeded = true;
        this.cdr.detectChanges();
        
      } else if (chunk.type === 'final_header') {
        // Received final assessment header (disease, severity, reason)
        console.log('COMPONENT: Received final assessment header');
        this.processingFinalAssessment = true;
        this.conversationFinished = true;
        
        // Clear conversation message
        this.currentStreamingMessage = '';
        streamingMsg.content = '';
        streamingMsg.isTyping = false;
        
        // Store header data
        finalAssessmentData = chunk.data;
        finalExplanationText = '';
        
        // Create final assessment structure
        streamingMsg.isFinal = true;
        streamingMsg.finalData = {
          disease: finalAssessmentData.disease,
          severity: finalAssessmentData.severity,
          reason: finalAssessmentData.reason,
          explanation: '' // Will be filled by streaming
        };
        
        this.scrollNeeded = true;
        this.cdr.detectChanges();
        
      } else if (chunk.type === 'final_text') {
        // Stream explanation text word by word
        if (streamingMsg.finalData) {
          finalExplanationText += chunk.content;
          streamingMsg.finalData.explanation = finalExplanationText;
          this.scrollNeeded = true;
          this.cdr.detectChanges();
        }
        
      } else if (chunk.type === 'final_complete') {
        // Final assessment streaming complete
        console.log('COMPONENT: Final assessment streaming complete');
        this.processingFinalAssessment = false;
        
      } else if (chunk.type === 'error') {
        console.log('COMPONENT: Error chunk received:', chunk);
        streamingMsg.isTyping = false;
        streamingMsg.content = 'Error: ' + (chunk.error || 'An error occurred');
        this.scrollNeeded = true;
        this.cdr.detectChanges();
      }
    },
    complete: () => {
      console.log('COMPONENT: Stream complete - message saved to DB');
      streamComplete = true;
      streamingMsg.isTyping = false;
      this.isWaitingForResponse = false;
      this.isStreaming = false;
      this.currentStreamingMessage = '';
      
      if (this.finalAssessmentTimeout) {
        clearTimeout(this.finalAssessmentTimeout);
        this.finalAssessmentTimeout = null;
      }
      
      this.cdr.detectChanges();
    },
    error: (error: any) => {
      console.error('COMPONENT: Stream error:', error);
      streamComplete = true;
      streamingMsg.isTyping = false;
      streamingMsg.content = 'An error occurred. Please try again.';
      this.isWaitingForResponse = false;
      this.isStreaming = false;
      this.currentStreamingMessage = '';
      
      if (this.finalAssessmentTimeout) {
        clearTimeout(this.finalAssessmentTimeout);
        this.finalAssessmentTimeout = null;
      }
      
      this.scrollNeeded = true;
      this.cdr.detectChanges();
    }
  });
}


  private completeFinalAssessment(streamingMsg: Message) {
    if (streamingMsg.finalData) {
      this.conversationFinished = true;
      streamingMsg.isFinal = true;
      streamingMsg.content = this.formatFinalAssessment(streamingMsg.finalData);
      this.scrollNeeded = true;
      this.cdr.detectChanges();
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

  loadConversation(sessionId: string) {
  this.chatService.getConversation(sessionId).subscribe({
    next: (res: any) => {
      const conversation = res.data;

      // Check if first message is already a welcome message
      const firstMsg = conversation.messages?.[0];
      const hasWelcome = firstMsg && 
                        firstMsg.role === 'assistant' && 
                        firstMsg.content.includes('MediMind');

      if (hasWelcome) {
        // Use existing messages including welcome
        this.messages = conversation.messages
          .map((msg: any) => ({
            role: msg.role,
            content: this.cleanText(msg.content)
          }))
          .filter((m: Message) => m.content);
      } else {
        // Add welcome message first, then conversation
        this.messages = [{
          role: 'assistant',
          content: 'Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns.'
        }];

        const conversationMessages = conversation.messages
          .map((msg: any) => ({
            role: msg.role,
            content: this.cleanText(msg.content)
          }))
          .filter((m: Message) => m.content);
        
        this.messages.push(...conversationMessages);
      }

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
      
      this.scrollNeeded = true;
      this.cdr.detectChanges();
    },
    error: (error: any) => {
      console.error('Error loading conversation:', error);
      alert('Failed to load conversation');
    }
  });
}


  startNewChat() {
    console.log('COMPONENT: Starting new chat - calling /start API');
    
    // Clear any pending timeouts first
    if (this.finalAssessmentTimeout) {
      clearTimeout(this.finalAssessmentTimeout);
      this.finalAssessmentTimeout = null;
    }
    
    // Reset UI state immediately
    this.sessionId = null;
    this.resetToWelcome();
    
    // First clear the session in service
    this.chatService.clearSession();
    
    // Then call /start API to create new session
    this.chatService.startInterview('').subscribe({
      next: (res: any) => {
        const newSessionId = res.data?.session_id;
        
        if (newSessionId) {
          console.log('COMPONENT: New empty session created via /start:', newSessionId);
          this.sessionId = newSessionId;
          this.chatService.setSessionId(newSessionId);
          this.router.navigate(['/chat', newSessionId], { replaceUrl: true });
        } else {
          console.error('COMPONENT: No session_id in response');
          alert('Failed to create session. Please try again.');
        }
      },
      error: (error) => {
        console.error('COMPONENT: Failed to create new session:', error);
        alert('Failed to start new chat. Please try again.');
      }
    });
    
    this.cdr.detectChanges();
  }
}
