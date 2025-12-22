import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { AuthService } from './auth.service';

// Backend response interfaces
interface FinalAssessment {
  disease: string;
  severity: string;
  reason: string;
  explanation: string;
}

interface ChatResponse {
  session_id: string;
  finished: boolean;
  reply?: string;
  final?: FinalAssessment;
}

// History interfaces
interface SessionSummary {
  session_id: string;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  message_count: number;
}

interface MessageResponse {
  message_id: number;
  role: string;
  content: string;
  message_order: number;
  created_at: string;
}

interface ConversationDetail {
  session_id: string;
  title: string;
  status: string;
  created_at: string;
  messages: MessageResponse[];
  assessment?: FinalAssessment;
}

interface GroupedHistory {
  today: SessionSummary[];
  yesterday: SessionSummary[];
  this_week: SessionSummary[];
  this_month: SessionSummary[];
  older: SessionSummary[];
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private API_URL = 'http://127.0.0.1:8000/api';
  
  private currentSessionId: string | null = null;
  
  public resetSubject = new BehaviorSubject<boolean>(false);
  reset$ = this.resetSubject.asObservable();

  constructor(
    private http: HttpClient,
    private authService: AuthService  // INJECT AuthService
  ) {}

  // =====================================================
  // CHAT METHODS
  // =====================================================
  
  //  UPDATED: Include user_email from AuthService
  startInterview(message: string): Observable<ChatResponse> {
    const userData = this.authService.getUserData();
    
    return this.http.post<ChatResponse>(`${this.API_URL}/start`, {
      message: message,
      user_email: userData?.email || ''  //  ADD user_email
    });
  }

  sendMessage(sessionId: string, message: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.API_URL}/chat`, {
      session_id: sessionId,
      message: message
    });
  }

  resetChat(sessionId: string): Observable<any> {
    return this.http.post(`${this.API_URL}/reset`, {
      session_id: sessionId
    });
  }

  setSessionId(sessionId: string) {
    this.currentSessionId = sessionId;
  }

  getSessionId(): string | null {
    return this.currentSessionId;
  }

  clearSession() {
    this.currentSessionId = null;
    this.resetSubject.next(true);
  }

  // =====================================================
  // HISTORY METHODS
  // =====================================================

  // Get all chat history for user
  getHistory(userEmail: string, limit: number = 50): Observable<SessionSummary[]> {
    const params = new HttpParams()
      .set('user_email', userEmail)
      .set('limit', limit.toString());
    
    return this.http.get<SessionSummary[]>(`${this.API_URL}/chat/history/`, { params });
  }

  // Get grouped history (Today, Yesterday, etc.)
  getGroupedHistory(userEmail: string): Observable<GroupedHistory> {
    const params = new HttpParams().set('user_email', userEmail);
    return this.http.get<GroupedHistory>(`${this.API_URL}/chat/history/grouped`, { params });
  }

  // Get specific conversation
  getConversation(sessionId: string, userEmail: string): Observable<ConversationDetail> {
    const params = new HttpParams().set('user_email', userEmail);
    return this.http.get<ConversationDetail>(
      `${this.API_URL}/chat/history/${sessionId}`,
      { params }
    );
  }

  // Delete conversation
  deleteConversation(sessionId: string, userEmail: string): Observable<any> {
    const params = new HttpParams().set('user_email', userEmail);
    return this.http.delete(`${this.API_URL}/chat/history/${sessionId}`, { params });
  }
}
